"""Servicio de cálculo del flujo de fondos del estudio.

Convención de signos:
- saldo_cc > 0  → el cliente tiene saldo a favor (pagó más de lo devengado)
- saldo_cc < 0  → el cliente debe (deuda positiva)
- deuda = -saldo_cc (signada): número positivo = cliente debe; negativo = cliente tiene a favor.
"""
from datetime import date
import calendar
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from .. import models


def saldo_cc_a_fecha(db: Session, client_id: int, hasta: Optional[date] = None) -> float:
    """Saldo de la CC del cliente hasta (incluyendo) la fecha dada.

    saldo = sum(ingresos) − sum(egresos/honorarios/ajustes negativos).
    Si `hasta` es None, calcula el saldo total (todos los movimientos).
    """
    q = db.query(
        func.sum(
            case(
                (models.MovimientoCuentaCorriente.tipo == "ingreso",
                 models.MovimientoCuentaCorriente.monto),
                else_=-models.MovimientoCuentaCorriente.monto,
            )
        )
    ).filter(models.MovimientoCuentaCorriente.client_id == client_id)
    if hasta is not None:
        q = q.filter(models.MovimientoCuentaCorriente.fecha <= hasta)
    return round(q.scalar() or 0.0, 2)


def _r(x: float) -> float:
    """Redondea a 2 decimales y normaliza -0.0 a 0.0."""
    v = round(x, 2)
    return 0.0 if v == 0 else v


def _parse_periodo(periodo: str) -> tuple[date, date, date]:
    """Devuelve (primer_dia, dia_previo, ultimo_dia) del período YYYY-MM."""
    if len(periodo) != 7 or periodo[4] != "-":
        raise ValueError(f"Período inválido: {periodo!r} (esperado YYYY-MM)")
    year, month = int(periodo[:4]), int(periodo[5:7])
    primer_dia = date(year, month, 1)
    ultimo_dia = date(year, month, calendar.monthrange(year, month)[1])
    if month == 1:
        dia_previo = date(year - 1, 12, 31)
    else:
        last_prev = calendar.monthrange(year, month - 1)[1]
        dia_previo = date(year, month - 1, last_prev)
    return primer_dia, dia_previo, ultimo_dia


def flujo_fondos_mensual(db: Session, periodo: str, profesional_id: Optional[int] = None) -> dict:
    """Calcula flujo de fondos para todos los clientes del período YYYY-MM.

    Filtros opcionales:
      profesional_id: limita a clientes a cargo de ese profesional.
    """
    primer_dia, dia_previo, ultimo_dia = _parse_periodo(periodo)

    q = db.query(models.Client).filter(models.Client.is_active == True)  # noqa: E712
    if profesional_id is not None:
        q = q.filter(models.Client.profesional_id == profesional_id)
    clientes = q.order_by(models.Client.name).all()

    rows = []
    tot_di = tot_dev = tot_cob = tot_df = 0.0

    for cliente in clientes:
        saldo_inicio = saldo_cc_a_fecha(db, cliente.id, dia_previo)
        saldo_fin = saldo_cc_a_fecha(db, cliente.id, ultimo_dia)

        deuda_inicio = _r(-saldo_inicio)
        deuda_fin = _r(-saldo_fin)

        devengado = db.query(func.sum(models.Honorario.importe)).filter(
            models.Honorario.client_id == cliente.id,
            models.Honorario.period == periodo,
        ).scalar() or 0.0

        cobrado = db.query(func.sum(models.Pago.importe)).filter(
            models.Pago.client_id == cliente.id,
            models.Pago.fecha >= primer_dia,
            models.Pago.fecha <= ultimo_dia,
        ).scalar() or 0.0

        rows.append({
            "cliente_id": cliente.id,
            "cliente_nombre": cliente.name,
            "deuda_inicio": deuda_inicio,
            "honorario_devengado": _r(devengado),
            "cobrado": _r(cobrado),
            "deuda_fin": deuda_fin,
        })
        tot_di += deuda_inicio
        tot_dev += devengado
        tot_cob += cobrado
        tot_df += deuda_fin

    return {
        "periodo": periodo,
        "rows": rows,
        "total": {
            "deuda_inicio": _r(tot_di),
            "honorario_devengado": _r(tot_dev),
            "cobrado": _r(tot_cob),
            "deuda_fin": _r(tot_df),
        },
    }


def verificar_consistencia(db: Session, periodo: str, tolerancia: float = 0.10) -> dict:
    """Verifica que para cada cliente, el saldo de CC al cierre coincida con
    la proyección calculada (deuda_inicio + devengado − cobrado).

    Si difieren más de `tolerancia` pesos, lo reporta como inconsistencia.
    Esto detecta honorarios devengados que no se reflejaron en CC, pagos
    sin imputar, o ajustes manuales no documentados.
    """
    primer_dia, dia_previo, ultimo_dia = _parse_periodo(periodo)

    clientes = db.query(models.Client).filter(models.Client.is_active == True).all()  # noqa: E712

    inconsistencias = []
    for cliente in clientes:
        saldo_inicio = saldo_cc_a_fecha(db, cliente.id, dia_previo)
        saldo_fin_real = saldo_cc_a_fecha(db, cliente.id, ultimo_dia)

        deuda_inicio = -saldo_inicio
        deuda_fin_real = -saldo_fin_real

        devengado = db.query(func.sum(models.Honorario.importe)).filter(
            models.Honorario.client_id == cliente.id,
            models.Honorario.period == periodo,
        ).scalar() or 0.0

        cobrado = db.query(func.sum(models.Pago.importe)).filter(
            models.Pago.client_id == cliente.id,
            models.Pago.fecha >= primer_dia,
            models.Pago.fecha <= ultimo_dia,
        ).scalar() or 0.0

        # deuda_fin esperada según flujo: deuda_inicio + devengado − cobrado
        deuda_fin_calculada = deuda_inicio + devengado - cobrado
        diferencia = round(deuda_fin_calculada - deuda_fin_real, 2)

        if abs(diferencia) > tolerancia:
            inconsistencias.append({
                "cliente_id": cliente.id,
                "cliente_nombre": cliente.name,
                "saldo_cc": _r(saldo_fin_real),
                "deuda_fin_real": _r(deuda_fin_real),
                "deuda_fin_calculada": _r(deuda_fin_calculada),
                "diferencia": _r(diferencia),
                "devengado": _r(devengado),
                "cobrado": _r(cobrado),
            })

    return {
        "periodo": periodo,
        "ok": len(inconsistencias) == 0,
        "tolerancia": tolerancia,
        "n_clientes": len(clientes),
        "n_inconsistencias": len(inconsistencias),
        "inconsistencias": inconsistencias,
    }


def flujo_fondos_anual(db: Session, year: int, profesional_id: Optional[int] = None) -> dict:
    """Calcula flujo de fondos anual pivoteado: una fila por cliente, columnas Ene-Dic.

    Cada celda tiene {devengado, cobrado, deuda_fin}.
    Devuelve totales por mes y total general.
    """
    if year < 1900 or year > 2100:
        raise ValueError(f"Año inválido: {year}")

    q = db.query(models.Client).filter(models.Client.is_active == True)  # noqa: E712
    if profesional_id is not None:
        q = q.filter(models.Client.profesional_id == profesional_id)
    clientes = q.order_by(models.Client.name).all()

    # Inicializar totales por mes (12 celdas)
    total_meses = [{"devengado": 0.0, "cobrado": 0.0, "deuda_fin": 0.0} for _ in range(12)]
    total_devengado = 0.0
    total_cobrado = 0.0

    rows = []

    for cliente in clientes:
        # Devengado por mes (un query por cliente)
        dev_por_periodo = dict(
            db.query(models.Honorario.period, func.sum(models.Honorario.importe))
            .filter(
                models.Honorario.client_id == cliente.id,
                models.Honorario.period.like(f"{year}-%"),
            )
            .group_by(models.Honorario.period)
            .all()
        )
        # Cobrado por mes — en SQLite uso strftime
        cob_por_mes = dict(
            db.query(
                func.strftime("%m", models.Pago.fecha),
                func.sum(models.Pago.importe),
            )
            .filter(
                models.Pago.client_id == cliente.id,
                func.strftime("%Y", models.Pago.fecha) == str(year),
            )
            .group_by(func.strftime("%m", models.Pago.fecha))
            .all()
        )

        meses = []
        cli_total_dev = 0.0
        cli_total_cob = 0.0
        for m in range(1, 13):
            mm = f"{m:02d}"
            periodo_str = f"{year}-{mm}"
            ultimo_dia = date(year, m, calendar.monthrange(year, m)[1])

            dev = float(dev_por_periodo.get(periodo_str, 0.0))
            cob = float(cob_por_mes.get(mm, 0.0))
            saldo_fin = saldo_cc_a_fecha(db, cliente.id, ultimo_dia)
            deuda_fin = _r(-saldo_fin)

            celda = {"devengado": _r(dev), "cobrado": _r(cob), "deuda_fin": deuda_fin}
            meses.append(celda)

            cli_total_dev += dev
            cli_total_cob += cob

            total_meses[m - 1]["devengado"] += dev
            total_meses[m - 1]["cobrado"] += cob
            total_meses[m - 1]["deuda_fin"] += deuda_fin

        rows.append({
            "cliente_id": cliente.id,
            "cliente_nombre": cliente.name,
            "meses": meses,
            "total_devengado": _r(cli_total_dev),
            "total_cobrado": _r(cli_total_cob),
            "deuda_fin": meses[-1]["deuda_fin"],
        })
        total_devengado += cli_total_dev
        total_cobrado += cli_total_cob

    total_meses_r = [
        {k: _r(v) for k, v in c.items()} for c in total_meses
    ]

    return {
        "year": year,
        "rows": rows,
        "total": {
            "meses": total_meses_r,
            "total_devengado": _r(total_devengado),
            "total_cobrado": _r(total_cobrado),
        },
    }
