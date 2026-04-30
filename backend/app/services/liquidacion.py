import calendar
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas


def _period_bounds(periodo: str) -> tuple[date, date]:
    year, month = int(periodo[:4]), int(periodo[5:7])
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return first, last


def _prev_period(periodo: str) -> str:
    year, month = int(periodo[:4]), int(periodo[5:7])
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


def calcular_preview(
    db: Session,
    profesional_id: int,
    periodo: str,
) -> schemas.LiquidacionPreviewOut:
    """Calcula el preview de liquidación de un profesional para un período.

    - honorarios_brutos: suma real de la tabla honorarios para los clientes
      asignados al profesional en ese período.
    - adelantos_cobrados: suma de pagos donde este profesional es destinatario
      en el período.
    - saldo_anterior: del cierre del mes anterior (0 si no existe o no está cerrado).
    - reintegros_total: de los ReintegroGasto de la Liquidacion del período.
    - total_a_cobrar = honorarios − adelantos + saldo_anterior + reintegros
    """
    prof = db.get(models.Profesional, profesional_id)
    if not prof:
        raise HTTPException(404, "Profesional no encontrado")

    first, last = _period_bounds(periodo)

    # ── Honorarios brutos ─────────────────────────────────────────────────────
    honorarios = (
        db.query(models.Honorario)
        .join(models.Client, models.Honorario.client_id == models.Client.id)
        .filter(
            models.Client.profesional_id == profesional_id,
            models.Honorario.period == periodo,
        )
        .all()
    )
    honorarios_brutos = sum(h.importe for h in honorarios)
    detalle_honorarios = [
        schemas.HonorarioDetalleItem(
            cliente_id=h.client_id,
            cliente_nombre=h.client.name if h.client else "",
            honorario_id=h.id,
            importe=h.importe,
            tipo=h.tipo,
        )
        for h in honorarios
    ]

    # ── Adelantos cobrados ────────────────────────────────────────────────────
    pagos = (
        db.query(models.Pago)
        .filter(
            models.Pago.profesional_destinatario_id == profesional_id,
            models.Pago.fecha >= first,
            models.Pago.fecha <= last,
        )
        .all()
    )
    adelantos_cobrados = sum(p.importe for p in pagos)
    detalle_adelantos = [
        schemas.AdelantoDetalleItem(
            pago_id=p.id,
            fecha=p.fecha,
            importe=p.importe,
            forma_pago=p.forma_pago,
            fuente_pago=p.fuente_pago,
            cliente_nombre=p.client.name if p.client else "",
        )
        for p in pagos
    ]

    # ── Saldo anterior (del cierre del mes previo) ────────────────────────────
    saldo_anterior = 0.0
    liq_prev = (
        db.query(models.Liquidacion)
        .filter(
            models.Liquidacion.profesional_id == profesional_id,
            models.Liquidacion.period == _prev_period(periodo),
            models.Liquidacion.cerrada == True,
        )
        .first()
    )
    if liq_prev:
        # Recalcular adelantos del mes anterior para obtener el saldo_siguiente real
        prev_first, prev_last = _period_bounds(liq_prev.period)
        prev_adelantos = (
            db.query(models.Pago)
            .filter(
                models.Pago.profesional_destinatario_id == profesional_id,
                models.Pago.fecha >= prev_first,
                models.Pago.fecha <= prev_last,
            )
            .with_entities(__import__('sqlalchemy', fromlist=['func']).func.sum(models.Pago.importe))
            .scalar() or 0.0
        )
        prev_reintegros = sum(r.importe for r in liq_prev.reintegros)
        total_prev = (
            liq_prev.honorarios_totales
            - prev_adelantos
            + liq_prev.saldo_anterior
            + prev_reintegros
        )
        saldo_anterior = round(
            total_prev - liq_prev.cobro_efectivo - liq_prev.cobro_transferencia, 2
        )

    # ── Reintegros del período ────────────────────────────────────────────────
    reintegros_total = 0.0
    detalle_reintegros: list[schemas.ReintegroDetalleItem] = []
    liq_actual = (
        db.query(models.Liquidacion)
        .filter(
            models.Liquidacion.profesional_id == profesional_id,
            models.Liquidacion.period == periodo,
        )
        .first()
    )
    if liq_actual:
        reintegros_total = sum(r.importe for r in liq_actual.reintegros)
        detalle_reintegros = [
            schemas.ReintegroDetalleItem(
                reintegro_id=r.id,
                concepto=r.concepto,
                importe=r.importe,
            )
            for r in liq_actual.reintegros
        ]

    # ── Total a cobrar ────────────────────────────────────────────────────────
    total_a_cobrar = round(
        honorarios_brutos - adelantos_cobrados + saldo_anterior + reintegros_total, 2
    )

    return schemas.LiquidacionPreviewOut(
        profesional_id=profesional_id,
        profesional_nombre=prof.nombre,
        periodo=periodo,
        honorarios_brutos=round(honorarios_brutos, 2),
        adelantos_cobrados=round(adelantos_cobrados, 2),
        saldo_anterior=saldo_anterior,
        reintegros_total=round(reintegros_total, 2),
        total_a_cobrar=total_a_cobrar,
        detalle_honorarios=detalle_honorarios,
        detalle_adelantos=detalle_adelantos,
        detalle_reintegros=detalle_reintegros,
        cerrada=liq_actual.cerrada if liq_actual else False,
    )
