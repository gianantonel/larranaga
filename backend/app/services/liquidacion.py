import calendar
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas


# Formas de pago no-efectivo que el profesional "recibe" → cuentan como adelanto
_FORMAS_ADELANTO = ("transferencia", "cheque", "deposito")


def _mov_ars(m) -> float:
    """Importe del movimiento convertido a ARS (USD × cotización; ARS tal cual)."""
    if (m.moneda or "ARS").upper() == "USD" and m.cotizacion:
        return float(m.monto) * float(m.cotizacion)
    return float(m.monto)


def _adelantos_r07(db: Session, profesional_id: int, periodo: str) -> list:
    """Adelantos cargados directo en R-07 (Cuentas Corrientes): movimientos de
    `ingreso` no-efectivo (transferencia/cheque/depósito) a este profesional,
    imputados al `periodo` (campo periodo_honorario = "mes que se cobra"). Se
    excluyen los que provienen de un Pago (`pago_id` no nulo), porque ésos ya se
    cuentan vía la tabla `pagos`."""
    return (
        db.query(models.MovimientoCuentaCorriente)
        .filter(
            models.MovimientoCuentaCorriente.profesional_id == profesional_id,
            func.lower(models.MovimientoCuentaCorriente.tipo) == "ingreso",
            func.lower(models.MovimientoCuentaCorriente.forma_pago).in_(_FORMAS_ADELANTO),
            models.MovimientoCuentaCorriente.periodo_honorario == periodo,
            models.MovimientoCuentaCorriente.pago_id.is_(None),
        )
        .all()
    )


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

    # ── Adelantos cargados directo en R-07 (CC, transferencia al profesional) ──
    movs_r07 = _adelantos_r07(db, profesional_id, periodo)
    adelantos_cobrados += sum(_mov_ars(m) for m in movs_r07)
    detalle_adelantos += [
        schemas.AdelantoDetalleItem(
            pago_id=None,
            fecha=m.fecha,
            importe=_mov_ars(m),
            forma_pago=m.forma_pago or "transferencia",
            fuente_pago=m.concepto,
            cliente_nombre=m.client.name if m.client else "",
        )
        for m in movs_r07
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
            db.query(func.sum(models.Pago.importe))
            .filter(
                models.Pago.profesional_destinatario_id == profesional_id,
                models.Pago.fecha >= prev_first,
                models.Pago.fecha <= prev_last,
            )
            .scalar() or 0.0
        )
        # Adelantos cargados directo en R-07 del mes anterior (imputados por período)
        prev_adelantos += sum(_mov_ars(m) for m in _adelantos_r07(db, profesional_id, liq_prev.period))
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

    # ── Estado de pago (paralelo a la nómina de empleados) ────────────────────
    liquidacion_id = None
    medio_pago = "transferencia"
    pagado = 0.0
    pagos_out: list[schemas.PagoProfesionalOut] = []
    if liq_actual:
        liquidacion_id = liq_actual.id
        medio_pago = liq_actual.medio_pago or "transferencia"
        pagado = round(sum(p.monto for p in liq_actual.pagos), 2)
        pagos_out = [schemas.PagoProfesionalOut.model_validate(p) for p in liq_actual.pagos]

    restante = round(max(0.0, total_a_cobrar - pagado), 2)
    if pagado <= 0.005:
        estado = "sin_liquidar"
    elif pagado < total_a_cobrar - 0.005:
        estado = "parcial"
    else:
        estado = "pagado"

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
        liquidacion_id=liquidacion_id,
        medio_pago=medio_pago,
        pagado=pagado,
        restante=restante,
        estado=estado,
        pagos=pagos_out,
    )
