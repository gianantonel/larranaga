"""E3-01 + F3-13: Test E2E del pipeline completo de conciliación bancaria.

Flujo:
  1. Crear clientes con CUIT y pagos correspondientes a los movs entrantes
  2. POST /conciliacion/import-extracto con el extracto Pampa Feb-2026 sintético
  3. POST /{id}/run-matching → debe matchear ~5 movs auto, ~10 quedan pendientes
  4. POST /movimiento/{id}/match-manual sobre uno pendiente → conciliado
  5. GET /extracto/{id}/movimientos?solo_pendientes=true → confirma que el matcheado salió de la cola

El extracto sintético está en `larranaga-accounting-agent/tests/fixtures/extracto_pampa_feb2026.xlsx`.
Para ejecutar contra extractos REALES del banco: reemplazá ese archivo y re-corré los tests.
"""
import pytest
from datetime import date
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app import database, models
from app.main import app
from app.security import get_password_hash


FIXTURE = Path(__file__).resolve().parent.parent.parent / "larranaga-accounting-agent" / "tests" / "fixtures" / "extracto_pampa_feb2026.xlsx"


@pytest.fixture(scope="module")
def engine_conn():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TS = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    orig_eng, orig_ses = database.engine, database.SessionLocal
    database.engine, database.SessionLocal = eng, TS
    database.Base.metadata.create_all(bind=eng)
    yield eng, TS
    database.engine, database.SessionLocal = orig_eng, orig_ses
    eng.dispose()


@pytest.fixture(scope="module")
def seeded(engine_conn):
    eng, TS = engine_conn
    db = TS()

    # Clientes con CUIT que aparecerán en el extracto
    clientes = [
        models.Client(name="BUTALO SRL", cuit="30709212083", is_active=True),
        models.Client(name="Gesualdo Guillermo", cuit="20123456789", is_active=True),
        models.Client(name="Restaurante El Gaucho", cuit="30716234561", is_active=True),
        models.Client(name="Farmacia del Centro", cuit="27987654321", is_active=True),
    ]
    db.add_all(clientes)
    db.add(models.User(
        name="Admin", last_name="QA", email="qa@conc.com",
        password_hash=get_password_hash("admin123"),
        is_active=True, role="admin", status="active",
    ))
    db.commit()
    for c in clientes:
        db.refresh(c)

    # Pagos esperados por transferencia (matchearán con créditos del extracto)
    pagos = [
        models.Pago(client_id=clientes[0].id, fecha=date(2026, 2, 1), importe=150000.0, forma_pago="transferencia"),
        models.Pago(client_id=clientes[1].id, fecha=date(2026, 2, 3), importe=300000.0, forma_pago="transferencia"),
        models.Pago(client_id=clientes[2].id, fecha=date(2026, 2, 8), importe=8500.0, forma_pago="transferencia"),
        models.Pago(client_id=clientes[0].id, fecha=date(2026, 2, 12), importe=75000.0, forma_pago="transferencia"),
        models.Pago(client_id=clientes[3].id, fecha=date(2026, 2, 27), importe=25000.0, forma_pago="transferencia"),
        # Pago sin movimiento bancario correspondiente
        models.Pago(client_id=clientes[0].id, fecha=date(2026, 2, 28), importe=999999.0, forma_pago="transferencia"),
    ]
    db.add_all(pagos)
    db.commit()
    for p in pagos:
        db.refresh(p)

    yield {"session": TS, "clientes": [c.id for c in clientes], "pagos": [p.id for p in pagos]}
    db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    r = client.post("/auth/login", json={"email": "qa@conc.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ─── Tests E2E ───────────────────────────────────────────────────────────────

def test_pipeline_e2e_conciliacion(client, seeded, auth_headers):
    """Flujo completo: import → matching → match manual → desconciliar."""
    assert FIXTURE.exists(), f"Fixture no encontrada: {FIXTURE}"

    # 1. Importar extracto
    with open(FIXTURE, "rb") as f:
        files = {"file": ("extracto_pampa_feb2026.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"banco": "pampa", "periodo": "2026-02"}
        r = client.post("/conciliacion/import-extracto", data=data, files=files, headers=auth_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    extracto_id = body["extracto"]["id"]
    assert body["extracto"]["n_movimientos"] >= 14, f"Esperaba >=14 movs, got {body['extracto']['n_movimientos']}"
    assert body["n_creditos"] >= 5
    assert body["n_debitos"] >= 5

    # 2. Run matching automático
    r = client.post(f"/conciliacion/{extracto_id}/run-matching", headers=auth_headers)
    assert r.status_code == 200, r.text
    stats = r.json()["stats"]
    # Esperamos: 4 créditos con CUIT (BUTALO×2, Gesualdo, Gaucho, Farmacia) → 5 matches
    # + 1 crédito sin CUIT pero por importe → opcional
    assert stats["auto"] >= 4, f"Esperaba >=4 matches automáticos, got {stats['auto']}"
    # Comisiones detectadas
    assert stats["by_type"].get("comision_bancaria", 0) >= 1
    assert stats["by_type"].get("debito_automatico", 0) >= 1

    # 3. Listar movimientos pendientes
    r = client.get(f"/conciliacion/extracto/{extracto_id}/movimientos",
                   params={"solo_pendientes": "true"}, headers=auth_headers)
    assert r.status_code == 200
    pendientes = r.json()
    assert len(pendientes) >= 1

    # 4. Match manual del primer pendiente que sea crédito
    pendientes_credito = [m for m in pendientes if m["tipo"] == "C"]
    if pendientes_credito:
        mov_id = pendientes_credito[0]["id"]
        # Pedimos sugerencias
        r = client.get(f"/conciliacion/movimiento/{mov_id}/sugerencias",
                       params={"top_n": 3}, headers=auth_headers)
        assert r.status_code == 200
        sugs = r.json()
        if sugs:
            pago_id = sugs[0]["pago_id"]
            r = client.post(f"/conciliacion/movimiento/{mov_id}/match-manual",
                            json={"pago_id": pago_id, "nota": "test E2E"},
                            headers=auth_headers)
            assert r.status_code == 200, r.text
            assert r.json()["conciliado"] is True

            # 5. Desconciliar
            r = client.post(f"/conciliacion/movimiento/{mov_id}/desconciliar", headers=auth_headers)
            assert r.status_code == 200
            assert r.json()["conciliado"] is False

    # 6. Verificar contadores actualizados
    r = client.get("/conciliacion/extractos", params={"banco": "pampa"}, headers=auth_headers)
    assert r.status_code == 200
    extr = next(e for e in r.json() if e["id"] == extracto_id)
    assert extr["n_conciliados"] >= 4
    assert extr["n_pendientes"] >= 1


def test_import_extracto_banco_invalido(client, auth_headers):
    """Banco no soportado debe retornar 400."""
    fake = b"dummy"
    r = client.post(
        "/conciliacion/import-extracto",
        data={"banco": "galicia", "periodo": "2026-02"},
        files={"file": ("x.xlsx", fake, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_import_extracto_periodo_invalido(client, auth_headers):
    """Periodo mal formado debe retornar 400."""
    fake = b"dummy"
    r = client.post(
        "/conciliacion/import-extracto",
        data={"banco": "pampa", "periodo": "Feb2026"},
        files={"file": ("x.xlsx", fake, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 400
