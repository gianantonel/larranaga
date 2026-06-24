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


def compute_saldo_cc(db: Session, client_id: int) -> float:
    """Saldo de cuenta corriente calculado en la BD con un único SUM(CASE...).

    Convención: `ingreso` (el cliente nos paga) suma; cualquier otro tipo
    (`egreso`/cargo) resta. Saldo > 0 = a favor del cliente; < 0 = deuda.
    Reemplaza el loop en Python que cargaba todos los movimientos a memoria.
    """
    tipo = func.lower(models.MovimientoCuentaCorriente.tipo)
    monto = models.MovimientoCuentaCorriente.monto
    expr = func.sum(case((tipo == "ingreso", monto), else_=-monto))
    saldo = (
        db.query(expr)
        .filter(models.MovimientoCuentaCorriente.client_id == client_id)
        .scalar()
    )
    return float(saldo or 0.0)

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
