"""E-02: Test de integración del flujo completo de cobro (registrar_cobro).

Verifica los 4 impactos esperados al registrar un cobro en efectivo:
  (a) CC del cliente: nuevo movimiento tipo "ingreso"
  (b) Pago: registrado en tabla pagos
  (c) Liquidación: el preview del profesional descuenta el adelanto
  (d) Billetes: stock actualizado por denominación

Si alguna validación falla (ej: billetes no cuadran con importe), todo
debe rollbackearse y NO impactar en ninguna tabla.
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


@pytest.fixture(scope="module")
def test_engine():
    """Reemplaza el engine de la app por un SQLite en memoria con esquema fresco."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # comparte misma conexión para que la DB en memoria persista
    )
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=eng)

    # Patch de la app para que TODOS los get_db usen este engine
    original_engine = database.engine
    original_session = database.SessionLocal
    database.engine = eng
    database.SessionLocal = TestSession

    # Crear esquema
    database.Base.metadata.create_all(bind=eng)

    yield eng, TestSession

    database.engine = original_engine
    database.SessionLocal = original_session
    eng.dispose()


@pytest.fixture(scope="module")
def seeded(test_engine):
    """Crea un cliente, profesional, user admin y stock inicial de billetes."""
    eng, TestSession = test_engine
    db = TestSession()

    cliente = models.Client(name="Restaurante El Gaucho", is_active=True)
    prof = models.Profesional(nombre="Manuel Larrañaga", activo=True)
    user = models.User(
        name="Admin",
        last_name="Test",
        email="admin@test.com",
        password_hash=get_password_hash("admin123"),
        is_active=True,
        role="admin",
        status="active",
    )
    db.add_all([cliente, prof, user])
    for denom in [1000, 2000, 5000, 10000, 20000]:
        db.add(models.ControlBillete(denominacion=denom, cantidad=0))
    db.commit()
    db.refresh(cliente)
    db.refresh(prof)

    yield {"cliente_id": cliente.id, "prof_id": prof.id, "session": TestSession}
    db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    r = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "admin123"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_cobro_efectivo_impacta_4_modulos(client, seeded, auth_headers):
    """E-02: cobro en efectivo con billetes desglosados → 4 impactos verificados."""
    cid = seeded["cliente_id"]
    pid = seeded["prof_id"]
    Session = seeded["session"]

    # 3 billetes de $5000 + 1 de $10000 = $25.000
    payload = {
        "cliente_id": cid,
        "importe": 25000,
        "forma_pago": "efectivo",
        "profesional_destino_id": pid,
        "fecha": str(date.today()),
        "billetes": {"5000": 3, "10000": 1},
    }

    r = client.post("/pagos/", json=payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    data = r.json()
    pago_id = data["pago"]["id"]

    db = Session()
    try:
        # (a) CC del cliente actualizada con un movimiento "ingreso" $25.000
        movs = db.query(models.MovimientoCuentaCorriente).filter_by(client_id=cid).all()
        assert len(movs) == 1
        assert movs[0].tipo == "ingreso"
        assert movs[0].monto == 25000
        assert data["saldo_cc_actual"] == 25000

        # (b) Pago registrado en tabla pagos
        pago = db.get(models.Pago, pago_id)
        assert pago is not None
        assert pago.importe == 25000
        assert pago.forma_pago == "efectivo"
        assert pago.profesional_destinatario_id == pid

        # (d) Stock de billetes actualizado
        b5000 = db.query(models.ControlBillete).filter_by(denominacion=5000).first()
        b10000 = db.query(models.ControlBillete).filter_by(denominacion=10000).first()
        assert b5000.cantidad == 3
        assert b10000.cantidad == 1

        # Auditoría: 2 movimientos de billete vinculados al pago
        movs_b = db.query(models.MovimientoBillete).filter_by(pago_id=pago_id).all()
        assert len(movs_b) == 2
    finally:
        db.close()

    # (c) Liquidación preview descuenta el adelanto
    periodo = date.today().strftime("%Y-%m")
    r2 = client.get(
        f"/profesionales/liquidaciones/{pid}/preview",
        params={"periodo": periodo},
        headers=auth_headers,
    )
    assert r2.status_code == 200, r2.text
    prev = r2.json()
    assert prev["adelantos_cobrados"] == 25000
    assert len(prev["detalle_adelantos"]) == 1
    assert prev["detalle_adelantos"][0]["pago_id"] == pago_id


def test_cobro_efectivo_billetes_no_cuadran_rollback(client, seeded, auth_headers):
    """Si los billetes no cuadran con el importe, todo debe rollbackearse."""
    cid = seeded["cliente_id"]
    Session = seeded["session"]

    db = Session()
    pagos_antes = db.query(models.Pago).count()
    movs_antes = db.query(models.MovimientoCuentaCorriente).count()
    db.close()

    payload = {
        "cliente_id": cid,
        "importe": 25000,
        "forma_pago": "efectivo",
        "billetes": {"5000": 1, "1000": 8},  # = 13000, no cuadra
    }

    r = client.post("/pagos/", json=payload, headers=auth_headers)
    assert r.status_code == 422
    assert "billetes" in r.json()["detail"]["error"].lower()

    # Verificar rollback
    db = Session()
    try:
        assert db.query(models.Pago).count() == pagos_antes
        assert db.query(models.MovimientoCuentaCorriente).count() == movs_antes
    finally:
        db.close()


def test_cobro_transferencia_no_toca_billetes(client, seeded, auth_headers):
    """Cobro por transferencia NO debe alterar el stock de billetes."""
    cid = seeded["cliente_id"]
    Session = seeded["session"]

    db = Session()
    stock_antes = {b.denominacion: b.cantidad for b in db.query(models.ControlBillete).all()}
    db.close()

    payload = {
        "cliente_id": cid,
        "importe": 50000,
        "forma_pago": "transferencia",
        "fuente_pago": "Banco Galicia",
    }

    r = client.post("/pagos/", json=payload, headers=auth_headers)
    assert r.status_code == 201, r.text

    db = Session()
    try:
        stock_despues = {b.denominacion: b.cantidad for b in db.query(models.ControlBillete).all()}
        assert stock_despues == stock_antes
    finally:
        db.close()
