"""E3-02: Test E2E del flujo completo de pago + retiro de socio + consistencia.

Escenario base (según docs/FASE3_TAREAS_GERO.md):
  1. Registrar pago de cliente $3.050.000 en transferencia
  2. Registrar retiro de socio $500.000 en efectivo
  3. /flujo-fondos/verificar-consistencia → debe retornar ok=true
  4. /flujo-fondos/?periodo=AAAA-MM refleja devengado/cobrado/saldo correctos

Tests adicionales:
  - El hook de consistencia detecta cuando un Honorario no se reflejó en CC
  - El flujo anual coincide con la suma de los meses individuales
  - Aplicar un IndiceActualizacion modifica los importes y persiste el historial
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app import database, models
from app.main import app
from app.security import get_password_hash


PERIODO = date.today().strftime("%Y-%m")


@pytest.fixture(scope="module")
def test_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=eng)

    original_engine = database.engine
    original_session = database.SessionLocal
    database.engine = eng
    database.SessionLocal = TestSession
    database.Base.metadata.create_all(bind=eng)

    yield eng, TestSession

    database.engine = original_engine
    database.SessionLocal = original_session
    eng.dispose()


@pytest.fixture(scope="module")
def seeded(test_engine):
    """Sembrá: 1 cliente fijo, 1 socio, 1 profesional, stock billetes, admin user."""
    eng, TestSession = test_engine
    db = TestSession()

    cliente = models.Client(name="Gesualdo G.", is_active=True,
                            tipo_honorario=models.TipoHonorario.fijo,
                            importe_honorario=3050000.0)
    socio = models.Profesional(nombre="Pablo Larrañaga", tipo=models.TipoProfesional.socio, activo=True)
    prof = models.Profesional(nombre="Stefania Vicente", tipo=models.TipoProfesional.profesional, activo=True)
    user = models.User(
        name="Admin", last_name="Test",
        email="admin@test.com",
        password_hash=get_password_hash("admin123"),
        is_active=True, role="admin", status="active",
    )
    db.add_all([cliente, socio, prof, user])
    for denom in [1000, 2000, 5000, 10000, 20000]:
        db.add(models.ControlBillete(denominacion=denom, cantidad=0))
    db.commit()
    db.refresh(cliente)
    db.refresh(socio)
    db.refresh(prof)

    yield {"cliente_id": cliente.id, "socio_id": socio.id, "prof_id": prof.id, "session": TestSession}
    db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth(client):
    r = client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_e2e_pago_retiro_consistencia_ok(client, seeded, auth):
    """E3-02 escenario principal: pago + retiro → consistencia OK + flujo correcto."""
    cid = seeded["cliente_id"]
    sid = seeded["socio_id"]
    Session = seeded["session"]

    # Cargar stock de billetes para el retiro en efectivo (10x $20.000 = $200.000)
    # PERO necesitamos $500.000 → cargo 25x $20.000
    db = Session()
    b20 = db.query(models.ControlBillete).filter_by(denominacion=20000).first()
    b20.cantidad = 30
    db.commit()
    db.close()

    # ── 1. Pago del cliente $3.050.000 transferencia ─────────────────────────
    r1 = client.post("/pagos/", json={
        "cliente_id": cid,
        "importe": 3050000,
        "forma_pago": "transferencia",
        "fuente_pago": "Gesualdo G.",
        "fecha": str(date.today()),
    }, headers=auth)
    assert r1.status_code == 201, r1.text

    # ── 2. Retiro de Pablo $500.000 efectivo (25 x $20k) ─────────────────────
    r2 = client.post("/retiros/", json={
        "profesional_id": sid,
        "importe": 500000,
        "forma_pago": "efectivo",
        "fecha": str(date.today()),
        "billetes": {"20000": 25},
    }, headers=auth)
    assert r2.status_code == 201, r2.text
    assert r2.json()["retiro"]["forma_pago"] == "efectivo"

    # ── 3. Verificar consistencia → ok=true ──────────────────────────────────
    r3 = client.get(f"/flujo-fondos/verificar-consistencia?periodo={PERIODO}", headers=auth)
    assert r3.status_code == 200, r3.text
    cons = r3.json()
    assert cons["ok"] is True, f"Inconsistencias: {cons['inconsistencias']}"
    assert cons["n_inconsistencias"] == 0
    assert cons["periodo"] == PERIODO

    # ── 4. Flujo de fondos del período ───────────────────────────────────────
    r4 = client.get(f"/flujo-fondos/?periodo={PERIODO}", headers=auth)
    assert r4.status_code == 200
    flujo = r4.json()
    fila = next((r for r in flujo["rows"] if r["cliente_id"] == cid), None)
    assert fila is not None, "Cliente no encontrado en el flujo"
    assert fila["cobrado"] == 3050000.0
    # devengado=0 porque no se creó Honorario en período
    assert fila["honorario_devengado"] == 0.0
    # Cliente pagó sin haber devengado → saldo a favor → deuda negativa
    assert fila["deuda_fin"] == -3050000.0

    # ── 5. Stock de billetes descontado (30 - 25 = 5) ────────────────────────
    db = Session()
    try:
        b20_after = db.query(models.ControlBillete).filter_by(denominacion=20000).first()
        assert b20_after.cantidad == 5

        # MovimientoTesoreria del retiro
        movs_tes = db.query(models.MovimientoTesoreria).filter_by(
            categoria=models.CategoriaTesoreria.retiro_socio
        ).all()
        assert len(movs_tes) == 1
        assert movs_tes[0].importe == 500000
        assert movs_tes[0].profesional_id == sid

        # RetiroSocio persistido y vinculado a la tesorería
        retiros = db.query(models.RetiroSocio).filter_by(profesional_id=sid).all()
        assert len(retiros) == 1
        assert retiros[0].movimiento_tesoreria_id == movs_tes[0].id
    finally:
        db.close()


def test_consistencia_detecta_honorario_sin_cc(client, seeded, auth):
    """Hook detecta cuando un Honorario fue devengado pero no se reflejó en CC."""
    cid = seeded["cliente_id"]
    Session = seeded["session"]

    # Sembrar un honorario devengado en otro período (sin movimiento_cc paralelo)
    periodo_test = "2025-03"
    db = Session()
    hon = models.Honorario(
        client_id=cid, period=periodo_test,
        importe=850000, tipo="fijo",
    )
    db.add(hon)
    db.commit()
    db.close()

    r = client.get(f"/flujo-fondos/verificar-consistencia?periodo={periodo_test}", headers=auth)
    assert r.status_code == 200
    cons = r.json()
    assert cons["ok"] is False
    assert cons["n_inconsistencias"] >= 1
    incons = next((i for i in cons["inconsistencias"] if i["cliente_id"] == cid), None)
    assert incons is not None
    assert incons["devengado"] == 850000
    assert incons["cobrado"] == 0
    # Esperado: 850k devengado, 0 real → diff 850k
    assert incons["diferencia"] == 850000


def test_flujo_anual_coincide_con_mensual(client, seeded, auth):
    """El total devengado/cobrado anual coincide con la suma de los meses."""
    year = int(PERIODO[:4])
    month_idx = int(PERIODO[5:7]) - 1   # 0-based

    r_anual = client.get(f"/flujo-fondos/anual?year={year}", headers=auth)
    assert r_anual.status_code == 200
    anual = r_anual.json()

    r_mensual = client.get(f"/flujo-fondos/?periodo={PERIODO}", headers=auth)
    mensual = r_mensual.json()

    cobrado_anual_mes = anual["total"]["meses"][month_idx]["cobrado"]
    cobrado_mensual = mensual["total"]["cobrado"]
    assert cobrado_anual_mes == cobrado_mensual, (
        f"Discrepancia en cobrado: anual[{month_idx}]={cobrado_anual_mes}, mensual={cobrado_mensual}"
    )


def test_aplicar_indice_actualizacion_persiste_historial(client, seeded, auth):
    """Preview crea índice (sin aplicar) → aplicar marca aplicado y registra historial."""
    cid = seeded["cliente_id"]
    Session = seeded["session"]

    # Preview con +10%
    r_prev = client.post("/honorarios/preview-actualizacion", json={
        "indice_pct": 10,
        "periodo_aplicacion": "2027-01",
        "fuente": "ipc",
    }, headers=auth)
    assert r_prev.status_code == 200, r_prev.text
    prev = r_prev.json()
    indice_id = prev["indice_id"]
    assert prev["aplicado"] is False

    # El cliente debe figurar en el preview con propuesto = actual * 1.10
    fila = next((r for r in prev["rows"] if r["cliente_id"] == cid), None)
    assert fila is not None
    importe_anterior = fila["importe_actual"]
    importe_propuesto = fila["importe_propuesto"]
    assert round(importe_propuesto, 2) == round(importe_anterior * 1.10, 2)

    # Aplicar al cliente
    r_apl = client.post("/honorarios/aplicar-actualizacion", json={
        "indice_id": indice_id,
        "client_ids": [cid],
    }, headers=auth)
    assert r_apl.status_code == 200, r_apl.text
    apl = r_apl.json()
    assert apl["aplicados"] == 1
    assert apl["saltados"] == 0

    # Verificar persistencia
    db = Session()
    try:
        cli = db.get(models.Client, cid)
        assert round(cli.importe_honorario, 2) == round(importe_propuesto, 2)

        indice = db.get(models.IndiceActualizacion, indice_id)
        assert indice.aplicado is True
        assert indice.fecha_aplicacion is not None

        hist = db.query(models.HistorialActualizacionHonorario).filter_by(
            indice_id=indice_id, client_id=cid,
        ).all()
        assert len(hist) == 1
        assert hist[0].importe_anterior == importe_anterior
        assert hist[0].importe_nuevo == importe_propuesto
    finally:
        db.close()

    # Re-aplicar el mismo índice → 409
    r_dup = client.post("/honorarios/aplicar-actualizacion", json={
        "indice_id": indice_id,
        "client_ids": [cid],
    }, headers=auth)
    assert r_dup.status_code == 409


def test_retiro_no_socio_rechazado(client, seeded, auth):
    """Solo profesionales tipo=socio pueden registrar retiros."""
    pid = seeded["prof_id"]   # Stefania, profesional (no socio)

    r = client.post("/retiros/", json={
        "profesional_id": pid,
        "importe": 100000,
        "forma_pago": "transferencia",
    }, headers=auth)
    assert r.status_code == 400
    assert "no es socio" in r.json()["detail"].lower()
