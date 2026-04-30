from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from .. import models, schemas
from ..database import get_db
from ..services import billetes as billetes_service
from .auth import get_current_user

router = APIRouter(prefix="/pagos", tags=["pagos"])


def _saldo_cc(db: Session, client_id: int) -> float:
    """Calcula el saldo actual de la CC del cliente sumando todos sus movimientos."""
    result = db.query(
        func.sum(
            case(
                (models.MovimientoCuentaCorriente.tipo == "ingreso",
                 models.MovimientoCuentaCorriente.monto),
                else_=-models.MovimientoCuentaCorriente.monto,
            )
        )
    ).filter(models.MovimientoCuentaCorriente.client_id == client_id).scalar()
    return round(result or 0.0, 2)


def _build_pago_out(pago: models.Pago) -> schemas.PagoOut:
    out = schemas.PagoOut.model_validate(pago)
    out.client_name = pago.client.name if pago.client else None
    out.profesional_destinatario_nombre = (
        pago.profesional_destinatario.nombre if pago.profesional_destinatario else None
    )
    return out


# ─── POST /pagos/ ─────────────────────────────────────────────────────────────

@router.post("/", response_model=schemas.PagoImpactoOut, status_code=201)
def registrar_cobro(
    data: schemas.PagoCreateV2,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Registra un cobro de cliente con impacto automático en su cuenta corriente.

    Si forma_pago = 'efectivo' y se proveen billetes, valida que la suma cuadre
    con el importe y actualiza el stock de caja.
    """
    # ── Validaciones ─────────────────────────────────────────────────────────
    cliente = db.get(models.Client, data.cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    if data.profesional_destino_id:
        if not db.get(models.Profesional, data.profesional_destino_id):
            raise HTTPException(404, "Profesional no encontrado")

    if data.honorario_id:
        hon = db.get(models.Honorario, data.honorario_id)
        if not hon or hon.client_id != data.cliente_id:
            raise HTTPException(400, "Honorario no encontrado o no pertenece al cliente")

    # ── Validación billetes (F2-06) ───────────────────────────────────────────
    if data.forma_pago == "efectivo" and data.billetes:
        total_billetes = sum(int(denom) * qty for denom, qty in data.billetes.items())
        if abs(total_billetes - data.importe) > 1:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "La suma de billetes no coincide con el importe",
                    "total_billetes": total_billetes,
                    "importe": data.importe,
                    "diferencia": total_billetes - data.importe,
                },
            )

    # ── Crear Pago ────────────────────────────────────────────────────────────
    fecha_pago = data.fecha or date.today()
    pago = models.Pago(
        client_id=data.cliente_id,
        honorario_id=data.honorario_id,
        fecha=fecha_pago,
        importe=data.importe,
        forma_pago=data.forma_pago,
        fuente_pago=data.fuente_pago,
        banco_destino=data.banco_destino,
        profesional_destinatario_id=data.profesional_destino_id,
        notas=data.notas,
    )
    db.add(pago)
    db.flush()  # obtener pago.id antes del commit

    # ── Impacto automático en CC ──────────────────────────────────────────────
    concepto = "Cobro de honorario"
    if data.fuente_pago:
        concepto += f" — {data.fuente_pago}"
    if data.profesional_destino_id and pago.profesional_destinatario:
        concepto += f" ({pago.profesional_destinatario.nombre})"

    mov_cc = models.MovimientoCuentaCorriente(
        client_id=data.cliente_id,
        tipo="ingreso",
        monto=data.importe,
        concepto=concepto,
        fecha=fecha_pago,
        forma_pago=data.forma_pago,
        profesional_id=data.profesional_destino_id,
        notas=data.notas,
    )
    db.add(mov_cc)
    db.flush()

    # ── Actualizar stock de billetes (F2-06) ──────────────────────────────────
    if data.forma_pago == "efectivo" and data.billetes:
        for denom_str, qty in data.billetes.items():
            if qty > 0:
                billetes_service.aplicar_movimiento(
                    db,
                    denominacion=int(denom_str),
                    delta=qty,
                    concepto=f"cobro_pago_{pago.id}",
                    pago_id=pago.id,
                )

    db.commit()
    db.refresh(pago)
    db.refresh(mov_cc)

    saldo = _saldo_cc(db, data.cliente_id)

    return schemas.PagoImpactoOut(
        pago=_build_pago_out(pago),
        movimiento_cc_id=mov_cc.id,
        saldo_cc_actual=saldo,
    )


# ─── GET /pagos/ ──────────────────────────────────────────────────────────────

@router.get("/", response_model=list[schemas.PagoOut])
def listar_pagos(
    client_id: Optional[int] = Query(None),
    profesional_id: Optional[int] = Query(None),
    period: Optional[str] = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Lista cobros registrados. Filtra por cliente, profesional y/o período."""
    import calendar
    q = db.query(models.Pago)
    if client_id:
        q = q.filter(models.Pago.client_id == client_id)
    if profesional_id:
        q = q.filter(models.Pago.profesional_destinatario_id == profesional_id)
    if period:
        year, month = int(period[:4]), int(period[5:7])
        first = date(year, month, 1)
        last = date(year, month, calendar.monthrange(year, month)[1])
        q = q.filter(models.Pago.fecha >= first, models.Pago.fecha <= last)

    return [_build_pago_out(p) for p in q.order_by(models.Pago.fecha.desc()).all()]


# ─── GET /pagos/{id} ──────────────────────────────────────────────────────────

@router.get("/{pago_id}", response_model=schemas.PagoOut)
def get_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    pago = db.get(models.Pago, pago_id)
    if not pago:
        raise HTTPException(404, "Pago no encontrado")
    return _build_pago_out(pago)
