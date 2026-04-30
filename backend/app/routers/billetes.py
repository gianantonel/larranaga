from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import billetes as billetes_service
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/billetes", tags=["billetes"])


@router.get("/", response_model=schemas.BilletesStockOut)
def get_stock(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Devuelve el stock actual de billetes en caja por denominación."""
    stock = billetes_service.get_stock_all(db)
    billetes_out = []
    for denom in billetes_service.DENOMINACIONES:
        cb = stock.get(denom)
        cantidad = cb.cantidad if cb else 0
        billetes_out.append(schemas.BilleteOut(
            denominacion=denom,
            cantidad=cantidad,
            subtotal=float(denom * cantidad),
        ))
    total = sum(b.subtotal for b in billetes_out)
    return schemas.BilletesStockOut(billetes=billetes_out, total_efectivo=total)


@router.post("/movimiento", response_model=schemas.MovimientoBilleteOut, status_code=201)
def registrar_movimiento(
    data: schemas.MovimientoBilleteCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    """Registra un movimiento manual de billetes (solo admin)."""
    billetes_service.aplicar_movimiento(
        db,
        denominacion=data.denominacion,
        delta=data.delta,
        concepto=data.concepto,
    )
    db.commit()

    mov = db.query(models.MovimientoBillete).filter(
        models.MovimientoBillete.denominacion == data.denominacion,
        models.MovimientoBillete.concepto == data.concepto,
    ).order_by(models.MovimientoBillete.created_at.desc()).first()

    return schemas.MovimientoBilleteOut.model_validate(mov)
