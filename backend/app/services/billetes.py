from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models

DENOMINACIONES = [1000, 2000, 5000, 10000, 20000]


def get_stock_all(db: Session) -> dict[int, models.ControlBillete]:
    """Devuelve {denominacion: ControlBillete} para las 5 denominaciones conocidas."""
    registros = db.query(models.ControlBillete).filter(
        models.ControlBillete.denominacion.in_(DENOMINACIONES)
    ).all()
    return {r.denominacion: r for r in registros}


def aplicar_movimiento(
    db: Session,
    denominacion: int,
    delta: int,
    concepto: str,
    pago_id: int | None = None,
) -> models.ControlBillete:
    """Aplica un delta al stock de una denominación y registra la auditoría.

    delta > 0 = entrada de billetes, delta < 0 = salida.
    Lanza 400 si la denominación no es válida o el stock resultante queda negativo.
    No hace commit — el llamador es responsable del commit.
    """
    if denominacion not in DENOMINACIONES:
        raise HTTPException(
            status_code=400,
            detail=f"Denominación ${denominacion} no válida. Opciones: {DENOMINACIONES}",
        )

    billete = db.query(models.ControlBillete).filter_by(denominacion=denominacion).first()
    if billete is None:
        raise HTTPException(
            status_code=500,
            detail=f"Stock de billete ${denominacion} no inicializado. Contactar al admin.",
        )

    nueva_cantidad = billete.cantidad + delta
    if nueva_cantidad < 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Stock insuficiente de billete ${denominacion:,}",
                "stock_actual": billete.cantidad,
                "salida_solicitada": abs(delta),
                "faltante": abs(nueva_cantidad),
            },
        )

    billete.cantidad = nueva_cantidad
    db.add(models.MovimientoBillete(
        denominacion=denominacion,
        delta=delta,
        concepto=concepto,
        pago_id=pago_id,
    ))

    return billete
