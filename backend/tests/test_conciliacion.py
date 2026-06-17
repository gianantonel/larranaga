"""F3-05/06/07 (E3-01): Tests del algoritmo de matching y endpoints de conciliación."""
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app import database, models
from app.main import app
from app.security import get_password_hash
from app.services import conciliacion as svc


@pytest.fixture(scope="module")
def test_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    orig_eng, orig_ses = database.engine, database.SessionLocal
    database.engine = eng
    database.SessionLocal = TestSession
    database.Base.metadata.create_all(bind=eng)
    yield eng, TestSession
    database.engine, database.SessionLocal = orig_eng, orig_ses
    eng.dispose()


@pytest.fixture(scope="module")
def seeded(test_engine):
    eng, TS = test_engine
    db = TS()

    # 2 clientes con CUIT
    c1 = models.Client(name="BUTALO SRL", cuit="30709212083", is_active=True)
    c2 = models.Client(name="Gesualdo Guillermo", cuit="20123456789", is_active=True)

    user = models.User(
        name="Admin", last_name="Test", email="admin@conc.com",
        password_hash=get_password_hash("admin123"),
        is_active=True, role="admin", status="active",
    )
    db.add_all([c1, c2, user])
    db.commit()
    db.refresh(c1); db.refresh(c2)

    # 3 pagos por transferencia
    p1 = models.Pago(client_id=c1.id, fecha=date(2026, 2, 15), importe=150000.0, forma_pago="transferencia")
    p2 = models.Pago(client_id=c2.id, fecha=date(2026, 2, 20), importe=300000.0, forma_pago="transferencia")
    p3 = models.Pago(client_id=c1.id, fecha=date(2026, 2, 25), importe=75000.0, forma_pago="transferencia")
    db.add_all([p1, p2, p3])
    db.commit()
    db.refresh(p1); db.refresh(p2); db.refresh(p3)

    # 1 extracto Pampa con 5 movimientos
    extr = models.ExtractoBancario(
        banco="pampa", periodo="2026-02", archivo_nombre="test.xlsx",
        n_movimientos=5, n_conciliados=0, n_pendientes=5,
    )
    db.add(extr); db.commit(); db.refresh(extr)

    # M1: crédito match exacto (CUIT + fecha + importe) → p1
    m1 = models.MovimientoBancario(
        extracto_id=extr.id, banco="pampa", fecha=date(2026, 2, 15),
        descripcion="TRANSF DE 30709212083 BUTALO SRL", importe=150000.0,
        tipo="C", saldo=1000000.0, cuit_detectado="30709212083", conciliado=False,
    )
    # M2: crédito match aproximado (CUIT + fecha ±1 + importe) → p2
    m2 = models.MovimientoBancario(
        extracto_id=extr.id, banco="pampa", fecha=date(2026, 2, 21),
        descripcion="TRANSF DE 20123456789 GESUALDO", importe=300000.0,
        tipo="C", saldo=1300000.0, cuit_detectado="20123456789", conciliado=False,
    )
    # M3: crédito sin CUIT pero importe + fecha exacta → p3
    m3 = models.MovimientoBancario(
        extracto_id=extr.id, banco="pampa", fecha=date(2026, 2, 25),
        descripcion="DEPOSITO EN EFECTIVO", importe=75000.0,
        tipo="C", saldo=1375000.0, cuit_detectado=None, conciliado=False,
    )
    # M4: débito comisión bancaria
    m4 = models.MovimientoBancario(
        extracto_id=extr.id, banco="pampa", fecha=date(2026, 2, 28),
        descripcion="COM. MANTENIMIENTO CUENTA", importe=2500.0,
        tipo="D", saldo=1372500.0, conciliado=False,
    )
    # M5: crédito sin match (importe distinto a todos)
    m5 = models.MovimientoBancario(
        extracto_id=extr.id, banco="pampa", fecha=date(2026, 2, 27),
        descripcion="TRANSF DESCONOCIDA", importe=99999.0,
        tipo="C", saldo=1472499.0, conciliado=False,
    )
    db.add_all([m1, m2, m3, m4, m5])
    db.commit()
    db.refresh(m1); db.refresh(m2); db.refresh(m3); db.refresh(m4); db.refresh(m5)

    yield {
        "session": TS, "extracto_id": extr.id,
        "c1_id": c1.id, "c2_id": c2.id,
        "p1": p1.id, "p2": p2.id, "p3": p3.id,
        "m1": m1.id, "m2": m2.id, "m3": m3.id, "m4": m4.id, "m5": m5.id,
    }
    db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    r = client.post("/auth/login", json={"email": "admin@conc.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ─── Tests del servicio ──────────────────────────────────────────────────────

def test_importe_match_tolerancia_absoluta():
    assert svc._importe_match(100.0, 100.5) is True
    assert svc._importe_match(100.0, 101.5) is False


def test_importe_match_tolerancia_relativa():
    # Para 1.000.000 una diferencia de $500 es <0.1%
    assert svc._importe_match(1000000.0, 1000500.0) is True


def test_fecha_dentro_tolerancia():
    assert svc._fecha_dentro(date(2026, 2, 15), date(2026, 2, 16)) is True
    assert svc._fecha_dentro(date(2026, 2, 15), date(2026, 2, 17)) is False


def test_keyword_comision():
    res = svc._match_debito_comision(type("M", (), {"descripcion": "COMISION DE MANTENIMIENTO"})())
    assert res == ("comision_bancaria", 0.6)


# ─── Tests del matching completo ─────────────────────────────────────────────

def test_correr_matching_pampa(seeded):
    Session = seeded["session"]
    db = Session()
    try:
        result = svc.correr_matching(db, seeded["extracto_id"])
        # 3 créditos matcheados (M1 exacto, M2 aprox, M3 importe)
        assert result["stats"]["auto"] == 3
        # M5 queda pendiente; M4 es débito categorizado pero no conciliado (también pending)
        assert result["stats"]["manual_required"] == 2
        assert result["stats"]["by_type"]["credito_cuit_exacto"] >= 1
        assert result["stats"]["by_type"]["credito_cuit_aprox"] >= 1
        assert result["stats"]["by_type"]["comision_bancaria"] >= 1

        # Verificar persistencia
        m1 = db.get(models.MovimientoBancario, seeded["m1"])
        assert m1.conciliado is True
        assert m1.pago_id == seeded["p1"]

        m5 = db.get(models.MovimientoBancario, seeded["m5"])
        assert m5.conciliado is False

        # Extracto contadores actualizados (forzar refresh — el commit fue en otra session)
        extr = db.get(models.ExtractoBancario, seeded["extracto_id"])
        db.refresh(extr)
        assert extr.n_conciliados == 3
        assert extr.n_pendientes == 2
    finally:
        db.close()


def test_sugerir_candidatos(seeded):
    Session = seeded["session"]
    db = Session()
    try:
        # M5 no matcheado: pedir sugerencias
        candidatos = svc.sugerir_candidatos(db, seeded["m5"], top_n=3)
        # No quedan pagos sin conciliar (el matching anterior usó todos), o quedan pocos
        assert isinstance(candidatos, list)
    finally:
        db.close()


# ─── Tests de endpoints ──────────────────────────────────────────────────────

def test_endpoint_run_matching_404(client, auth_headers):
    r = client.post("/conciliacion/9999/run-matching", headers=auth_headers)
    assert r.status_code == 404


def test_endpoint_match_manual_y_desconciliar(client, seeded, auth_headers):
    Session = seeded["session"]
    # Importar de nuevo: ya M5 está pendiente; pero todos los pagos están matcheados,
    # creemos un pago nuevo extra y matcheemoslo manualmente con M5
    db = Session()
    try:
        cliente_id = seeded["c1_id"]
        nuevo_pago = models.Pago(
            client_id=cliente_id, fecha=date(2026, 2, 27),
            importe=99999.0, forma_pago="transferencia",
        )
        db.add(nuevo_pago); db.commit(); db.refresh(nuevo_pago)
        nuevo_pago_id = nuevo_pago.id
    finally:
        db.close()

    r = client.post(
        f"/conciliacion/movimiento/{seeded['m5']}/match-manual",
        json={"pago_id": nuevo_pago_id, "nota": "validado por operador"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["conciliado"] is True
    assert r.json()["pago_id"] == nuevo_pago_id

    # Desconciliar
    r2 = client.post(
        f"/conciliacion/movimiento/{seeded['m5']}/desconciliar",
        headers=auth_headers,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["conciliado"] is False
    assert r2.json()["pago_id"] is None
