from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime
import calendar

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, require_admin
from ..services import liquidacion as liquidacion_service

router = APIRouter(prefix="/profesionales", tags=["profesionales"])


# ─── Helper ───────────────────────────────────────────────────────────────────

def _period_bounds(period: str) -> tuple[date, date]:
    """'YYYY-MM' → (primer día, último día del mes)."""
    year, month = int(period[:4]), int(period[5:7])
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return first, last


def _build_liquidacion_out(liq: models.Liquidacion, db: Session) -> schemas.LiquidacionOut:
    """Calcula los campos derivados de una Liquidacion y devuelve el schema."""
    first, last = _period_bounds(liq.period)

    adelantos = db.query(func.sum(models.Pago.importe)).filter(
        models.Pago.profesional_destinatario_id == liq.profesional_id,
        models.Pago.fecha >= first,
        models.Pago.fecha <= last,
    ).scalar() or 0.0

    reintegros_total = sum(r.importe for r in liq.reintegros)
    total_a_cobrar = liq.honorarios_totales - adelantos + liq.saldo_anterior + reintegros_total
    saldo_siguiente = total_a_cobrar - liq.cobro_efectivo - liq.cobro_transferencia

    return schemas.LiquidacionOut(
        id=liq.id,
        profesional_id=liq.profesional_id,
        profesional_nombre=liq.profesional.nombre if liq.profesional else None,
        period=liq.period,
        honorarios_totales=liq.honorarios_totales,
        adelantos_percibidos=round(adelantos, 2),
        saldo_anterior=liq.saldo_anterior,
        reintegros_gastos=round(reintegros_total, 2),
        total_a_cobrar=round(total_a_cobrar, 2),
        cobro_efectivo=liq.cobro_efectivo,
        cobro_transferencia=liq.cobro_transferencia,
        saldo_siguiente=round(saldo_siguiente, 2),
        cerrada=liq.cerrada,
        cerrada_en=liq.cerrada_en,
        reintegros=[schemas.ReintegroGastoOut.model_validate(r) for r in liq.reintegros],
        alerta_sobreadelanto=adelantos > liq.honorarios_totales,
    )


def _prev_period(period: str) -> str:
    year, month = int(period[:4]), int(period[5:7])
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


# ─── Profesionales ────────────────────────────────────────────────────────────

@router.get("/", response_model=List[schemas.ProfesionalOut])
def list_profesionales(activo: Optional[bool] = None,
                       db: Session = Depends(get_db),
                       _: models.User = Depends(get_current_user)):
    q = db.query(models.Profesional)
    if activo is not None:
        q = q.filter(models.Profesional.activo == activo)
    return q.order_by(models.Profesional.nombre).all()


@router.post("/", response_model=schemas.ProfesionalOut, status_code=201)
def create_profesional(data: schemas.ProfesionalCreate, db: Session = Depends(get_db),
                       _: models.User = Depends(require_admin)):
    p = models.Profesional(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{id}", response_model=schemas.ProfesionalOut)
def update_profesional(id: int, data: schemas.ProfesionalUpdate, db: Session = Depends(get_db),
                       _: models.User = Depends(require_admin)):
    p = db.get(models.Profesional, id)
    if not p:
        raise HTTPException(404, "Profesional no encontrado")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(p, field, val)
    db.commit()
    db.refresh(p)
    return p


# ─── Pagos ────────────────────────────────────────────────────────────────────

@router.get("/pagos", response_model=List[schemas.PagoOut])
def list_pagos(client_id: Optional[int] = None,
               profesional_id: Optional[int] = None,
               period: Optional[str] = None,
               db: Session = Depends(get_db),
               _: models.User = Depends(get_current_user)):
    q = db.query(models.Pago)
    if client_id:
        q = q.filter(models.Pago.client_id == client_id)
    if profesional_id:
        q = q.filter(models.Pago.profesional_destinatario_id == profesional_id)
    if period:
        first, last = _period_bounds(period)
        q = q.filter(models.Pago.fecha >= first, models.Pago.fecha <= last)

    result = []
    for p in q.order_by(models.Pago.fecha.desc()).all():
        out = schemas.PagoOut.model_validate(p)
        out.client_name = p.client.name if p.client else None
        out.profesional_destinatario_nombre = (
            p.profesional_destinatario.nombre if p.profesional_destinatario else None
        )
        result.append(out)
    return result


@router.post("/pagos", response_model=schemas.PagoOut, status_code=201)
def create_pago(data: schemas.PagoCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    """Registra un pago e impacta automáticamente en la CC del cliente."""
    client = db.get(models.Client, data.client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    if data.profesional_destinatario_id:
        prof = db.get(models.Profesional, data.profesional_destinatario_id)
        if not prof:
            raise HTTPException(404, "Profesional no encontrado")

    if data.honorario_id:
        hon = db.get(models.Honorario, data.honorario_id)
        if not hon or hon.client_id != data.client_id:
            raise HTTPException(400, "Honorario no encontrado o no pertenece al cliente")

    pago = models.Pago(**data.model_dump())
    db.add(pago)
    db.flush()

    # Impacto automático en CC del cliente
    concepto = "Pago de honorario"
    if data.fuente_pago:
        concepto += f" — {data.fuente_pago}"
    if data.profesional_destinatario_id and pago.profesional_destinatario:
        concepto += f" → {pago.profesional_destinatario.nombre}"

    db.add(models.MovimientoCuentaCorriente(
        client_id=data.client_id,
        tipo="ingreso",
        monto=data.importe,
        concepto=concepto,
        fecha=data.fecha,
        notas=data.notas,
    ))

    db.commit()
    db.refresh(pago)

    out = schemas.PagoOut.model_validate(pago)
    out.client_name = client.name
    out.profesional_destinatario_nombre = (
        pago.profesional_destinatario.nombre if pago.profesional_destinatario else None
    )
    return out


@router.delete("/pagos/{id}", status_code=204)
def delete_pago(id: int, db: Session = Depends(get_db),
                _: models.User = Depends(require_admin)):
    pago = db.get(models.Pago, id)
    if not pago:
        raise HTTPException(404, "Pago no encontrado")
    db.delete(pago)
    db.commit()


# ─── Liquidaciones — preview F2-11 ───────────────────────────────────────────
# IMPORTANTE: estos endpoints deben ir ANTES de /{profesional_id}/{period}
# para que FastAPI no interprete "preview" como un profesional_id numérico.

@router.get("/liquidaciones/preview", response_model=list[schemas.LiquidacionPreviewOut])
def get_liquidaciones_preview_all(
    periodo: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Devuelve el preview de liquidación para TODOS los profesionales activos en el período."""
    profesionales = db.query(models.Profesional).filter(
        models.Profesional.activo == True
    ).order_by(models.Profesional.nombre).all()

    return [
        liquidacion_service.calcular_preview(db, prof.id, periodo)
        for prof in profesionales
    ]


@router.get("/liquidaciones/{profesional_id}/preview", response_model=schemas.LiquidacionPreviewOut)
def get_liquidacion_preview(
    profesional_id: int,
    periodo: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Devuelve el preview de liquidación de un profesional para el período indicado."""
    return liquidacion_service.calcular_preview(db, profesional_id, periodo)


# ─── Liquidaciones ────────────────────────────────────────────────────────────

@router.get("/liquidaciones", response_model=List[schemas.LiquidacionOut])
def list_liquidaciones(profesional_id: Optional[int] = None,
                       period: Optional[str] = None,
                       db: Session = Depends(get_db),
                       _: models.User = Depends(get_current_user)):
    q = db.query(models.Liquidacion)
    if profesional_id:
        q = q.filter(models.Liquidacion.profesional_id == profesional_id)
    if period:
        q = q.filter(models.Liquidacion.period == period)
    return [_build_liquidacion_out(liq, db)
            for liq in q.order_by(models.Liquidacion.period.desc()).all()]


@router.get("/liquidaciones/{profesional_id}/{period}", response_model=schemas.LiquidacionOut)
def get_or_create_liquidacion(profesional_id: int, period: str,
                               db: Session = Depends(get_db),
                               _: models.User = Depends(get_current_user)):
    """Devuelve la liquidación del período. Si no existe la crea con saldo arrastrado."""
    if not db.get(models.Profesional, profesional_id):
        raise HTTPException(404, "Profesional no encontrado")

    liq = db.query(models.Liquidacion).filter(
        models.Liquidacion.profesional_id == profesional_id,
        models.Liquidacion.period == period,
    ).first()

    if not liq:
        # Buscar saldo_siguiente del mes anterior cerrado
        prev = db.query(models.Liquidacion).filter(
            models.Liquidacion.profesional_id == profesional_id,
            models.Liquidacion.period == _prev_period(period),
            models.Liquidacion.cerrada == True,
        ).first()

        saldo_anterior = 0.0
        if prev:
            # Recalcular saldo_siguiente del mes anterior para usarlo como saldo_anterior
            prev_out = _build_liquidacion_out(prev, db)
            saldo_anterior = prev_out.saldo_siguiente

        liq = models.Liquidacion(
            profesional_id=profesional_id,
            period=period,
            saldo_anterior=saldo_anterior,
        )
        db.add(liq)
        db.commit()
        db.refresh(liq)

    return _build_liquidacion_out(liq, db)


@router.put("/liquidaciones/{profesional_id}/{period}/honorarios",
            response_model=schemas.LiquidacionOut)
def set_honorarios_totales(profesional_id: int, period: str,
                           data: schemas.LiquidacionHonorariosSet,
                           db: Session = Depends(get_db),
                           _: models.User = Depends(require_admin)):
    liq = db.query(models.Liquidacion).filter(
        models.Liquidacion.profesional_id == profesional_id,
        models.Liquidacion.period == period,
    ).first()
    if not liq:
        raise HTTPException(404, "Liquidación no encontrada — obtenela primero con GET")
    if liq.cerrada:
        raise HTTPException(400, "La liquidación ya está cerrada")

    liq.honorarios_totales = data.honorarios_totales
    db.commit()
    db.refresh(liq)
    return _build_liquidacion_out(liq, db)


@router.post("/liquidaciones/{profesional_id}/{period}/reintegros",
             response_model=schemas.LiquidacionOut, status_code=201)
def add_reintegro(profesional_id: int, period: str,
                  data: schemas.ReintegroGastoCreate,
                  db: Session = Depends(get_db),
                  _: models.User = Depends(require_admin)):
    liq = db.query(models.Liquidacion).filter(
        models.Liquidacion.profesional_id == profesional_id,
        models.Liquidacion.period == period,
    ).first()
    if not liq:
        raise HTTPException(404, "Liquidación no encontrada")
    if liq.cerrada:
        raise HTTPException(400, "La liquidación ya está cerrada")

    db.add(models.ReintegroGasto(liquidacion_id=liq.id, **data.model_dump()))
    db.commit()
    db.refresh(liq)
    return _build_liquidacion_out(liq, db)


@router.delete("/liquidaciones/{profesional_id}/{period}/reintegros/{reintegro_id}",
               response_model=schemas.LiquidacionOut)
def delete_reintegro(profesional_id: int, period: str, reintegro_id: int,
                     db: Session = Depends(get_db),
                     _: models.User = Depends(require_admin)):
    liq = db.query(models.Liquidacion).filter(
        models.Liquidacion.profesional_id == profesional_id,
        models.Liquidacion.period == period,
    ).first()
    if not liq:
        raise HTTPException(404, "Liquidación no encontrada")
    if liq.cerrada:
        raise HTTPException(400, "La liquidación ya está cerrada")

    r = db.query(models.ReintegroGasto).filter(
        models.ReintegroGasto.id == reintegro_id,
        models.ReintegroGasto.liquidacion_id == liq.id,
    ).first()
    if not r:
        raise HTTPException(404, "Reintegro no encontrado")

    db.delete(r)
    db.commit()
    db.refresh(liq)
    return _build_liquidacion_out(liq, db)


@router.post("/liquidaciones/{profesional_id}/{period}/cerrar",
             response_model=schemas.LiquidacionOut)
def cerrar_liquidacion(profesional_id: int, period: str,
                       data: schemas.LiquidacionCerrarRequest,
                       db: Session = Depends(get_db),
                       _: models.User = Depends(require_admin)):
    """Cierra el mes: fija cobros y calcula el saldo que arrastra al mes siguiente."""
    liq = db.query(models.Liquidacion).filter(
        models.Liquidacion.profesional_id == profesional_id,
        models.Liquidacion.period == period,
    ).first()
    if not liq:
        raise HTTPException(404, "Liquidación no encontrada")
    if liq.cerrada:
        raise HTTPException(400, "La liquidación ya está cerrada")

    liq.cobro_efectivo = data.cobro_efectivo
    liq.cobro_transferencia = data.cobro_transferencia
    liq.cerrada = True
    liq.cerrada_en = datetime.utcnow()
    db.commit()
    db.refresh(liq)
    return _build_liquidacion_out(liq, db)


# ─── Pagos a profesional (total / parcial) ───────────────────────────────────

def _get_or_create_liq(db: Session, profesional_id: int, period: str) -> models.Liquidacion:
    liq = db.query(models.Liquidacion).filter(
        models.Liquidacion.profesional_id == profesional_id,
        models.Liquidacion.period == period,
    ).first()
    if liq:
        return liq
    prev = db.query(models.Liquidacion).filter(
        models.Liquidacion.profesional_id == profesional_id,
        models.Liquidacion.period == _prev_period(period),
        models.Liquidacion.cerrada == True,                     # noqa: E712
    ).first()
    saldo_anterior = _build_liquidacion_out(prev, db).saldo_siguiente if prev else 0.0
    liq = models.Liquidacion(profesional_id=profesional_id, period=period, saldo_anterior=saldo_anterior)
    db.add(liq)
    db.commit()
    db.refresh(liq)
    return liq


@router.post("/liquidaciones/pago", response_model=schemas.LiquidacionPreviewOut)
def registrar_pago_profesional(body: schemas.PagoProfesionalCreate,
                               db: Session = Depends(get_db),
                               _: models.User = Depends(require_admin)):
    """Registra un pago (parcial o total) contra la liquidación del profesional."""
    if not db.get(models.Profesional, body.profesional_id):
        raise HTTPException(404, "Profesional no encontrado")
    preview = liquidacion_service.calcular_preview(db, body.profesional_id, body.period)
    liq = _get_or_create_liq(db, body.profesional_id, body.period)

    pagado = round(sum(p.monto for p in liq.pagos), 2)
    restante = round(max(0.0, preview.total_a_cobrar - pagado), 2)
    if body.monto > restante + 0.01:
        raise HTTPException(422, {"error": "El pago supera el restante a pagar",
                                  "restante": restante, "intento": body.monto})

    db.add(models.PagoProfesional(
        liquidacion_id=liq.id, monto=body.monto,
        medio_pago=body.medio_pago, fecha=body.fecha or date.today(),
    ))
    db.commit()
    return liquidacion_service.calcular_preview(db, body.profesional_id, body.period)


@router.delete("/liquidaciones/pago/{pago_id}", response_model=schemas.LiquidacionPreviewOut)
def eliminar_pago_profesional(pago_id: int,
                              db: Session = Depends(get_db),
                              _: models.User = Depends(require_admin)):
    pago = db.get(models.PagoProfesional, pago_id)
    if not pago:
        raise HTTPException(404, "Pago no encontrado")
    liq = pago.liquidacion
    pid, period = liq.profesional_id, liq.period
    db.delete(pago)
    db.commit()
    return liquidacion_service.calcular_preview(db, pid, period)


@router.post("/liquidaciones/{profesional_id}/{period}/liquidar",
             response_model=schemas.LiquidacionPreviewOut)
def liquidar_profesional(profesional_id: int, period: str,
                         data: schemas.LiquidarProfRequest,
                         db: Session = Depends(get_db),
                         _: models.User = Depends(require_admin)):
    """Liquida al profesional: modo 'total' registra el pago completo del total a cobrar;
    modo 'parcial' deja la obligación para cargar pagos en el modal."""
    if not db.get(models.Profesional, profesional_id):
        raise HTTPException(404, "Profesional no encontrado")
    preview = liquidacion_service.calcular_preview(db, profesional_id, period)
    liq = _get_or_create_liq(db, profesional_id, period)
    liq.medio_pago = data.medio_pago
    db.flush()

    if data.modo == "total":
        for p in list(liq.pagos):
            db.delete(p)
        db.flush()
        if preview.total_a_cobrar > 0.005:
            db.add(models.PagoProfesional(
                liquidacion_id=liq.id, monto=round(preview.total_a_cobrar, 2),
                medio_pago=data.medio_pago, fecha=date.today(),
            ))
    db.commit()
    return liquidacion_service.calcular_preview(db, profesional_id, period)
