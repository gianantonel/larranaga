import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..access import ensure_client_access

router = APIRouter(
    prefix="/cuentas-corrientes",
    tags=["cuentas_corrientes"]
)


def _monto_ars_expr():
    """Expresión SQL del importe convertido a ARS: si moneda='USD' multiplica por
    la cotización (ARS por USD); en cualquier otro caso (ARS o NULL) usa el monto tal cual."""
    M = models.MovimientoCuentaCorriente
    return case(
        (func.upper(func.coalesce(M.moneda, "ARS")) == "USD",
         M.monto * func.coalesce(M.cotizacion, 1.0)),
        else_=M.monto,
    )


def compute_saldo_cc(db: Session, client_id: int) -> float:
    """Saldo de cuenta corriente calculado en la BD con un único SUM(CASE...).

    Convención: `ingreso` (el cliente nos paga) suma; cualquier otro tipo
    (`egreso`/cargo) resta. Los movimientos en USD se convierten a ARS con su
    cotización. Saldo > 0 = a favor del cliente; < 0 = deuda.
    """
    tipo = func.lower(models.MovimientoCuentaCorriente.tipo)
    monto_ars = _monto_ars_expr()
    expr = func.sum(case((tipo == "ingreso", monto_ars), else_=-monto_ars))
    saldo = (
        db.query(expr)
        .filter(models.MovimientoCuentaCorriente.client_id == client_id)
        .scalar()
    )
    return float(saldo or 0.0)


@router.get("/cotizacion-dolar")
def cotizacion_dolar(current_user: models.User = Depends(get_current_user)):
    """Cotización sugerida del dólar oficial (dolarapi.com). Devuelve compra/venta/
    promedio. Si la fuente no responde, devuelve `disponible=False` sin romper la UI."""
    try:
        resp = httpx.get("https://dolarapi.com/v1/dolares/oficial", timeout=6.0)
        resp.raise_for_status()
        d = resp.json()
        compra = d.get("compra")
        venta = d.get("venta")
        promedio = round((compra + venta) / 2, 2) if compra and venta else (venta or compra)
        return {
            "disponible": True,
            "fuente": "dolarapi.com · oficial",
            "compra": compra,
            "venta": venta,
            "sugerida": promedio,
            "fecha": d.get("fechaActualizacion"),
        }
    except Exception as e:  # noqa: BLE001 — la UI debe seguir funcionando con carga manual
        return {"disponible": False, "error": str(e)}

@router.get("/client/{client_id}", response_model=List[schemas.MovimientoCCOut])
def read_movimientos(client_id: int, db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    # Check if client exists
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    ensure_client_access(db, current_user, client_id)

    movimientos = db.query(models.MovimientoCuentaCorriente)\
        .filter(models.MovimientoCuentaCorriente.client_id == client_id)\
        .order_by(models.MovimientoCuentaCorriente.fecha.desc(), models.MovimientoCuentaCorriente.created_at.desc())\
        .all()
    return movimientos

@router.post("/", response_model=schemas.MovimientoCCOut, status_code=status.HTTP_201_CREATED)
def create_movimiento(movimiento: schemas.MovimientoCCCreate, db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user)):
    # Check if client exists
    client = db.query(models.Client).filter(models.Client.id == movimiento.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    ensure_client_access(db, current_user, movimiento.client_id)

    db_movimiento = models.MovimientoCuentaCorriente(**movimiento.model_dump())
    db.add(db_movimiento)
    db.commit()
    db.refresh(db_movimiento)
    return db_movimiento

@router.get("/client/{client_id}/saldo", response_model=float)
def get_saldo(client_id: int, db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    ensure_client_access(db, current_user, client_id)

    return compute_saldo_cc(db, client_id)
