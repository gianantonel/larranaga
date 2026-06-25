"""Liquidación de honorarios por empleado (nómina de cada cliente).

Vista Honorarios: cliente → nómina → liquidar (total o parcial).
  GET  /liquidacion-personal/{client_id}?period=YYYY-MM
       Empleados activos con su config (medio de pago, fijo/producto), el monto
       sugerido (período anterior; si es nuevo, base de la config del empleado) y el
       estado de pago del período (pendiente/parcial/pagado, pagado, restante, pagos).
  POST /liquidacion-personal/{client_id}/liquidar
       Fija la obligación de los empleados seleccionados. Si modo='total' registra el
       pago completo; si modo='parcial' deja la obligación para cargar pagos en el modal.
  POST /liquidacion-personal/pago        registra un pago parcial.
  DELETE /liquidacion-personal/pago/{id} elimina un pago parcial.

Control de acceso: un colaborador solo opera sobre sus clientes asignados.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..access import ensure_client_access

router = APIRouter(prefix="/liquidacion-personal", tags=["liquidacion_personal"])

_EPS = 0.005


def _validar_period(period: str) -> str:
    if not period or len(period) != 7 or period[4] != "-":
        raise HTTPException(400, f"period inválido: {period!r} (esperado YYYY-MM)")
    try:
        int(period[:4]); int(period[5:7])
    except ValueError:
        raise HTTPException(400, f"period inválido: {period!r}")
    return period


def _base_empleado(emp: models.Empleado, db: Session) -> float:
    """Monto base según la config de honorario DEL EMPLEADO. 0 si no está configurada."""
    if emp.tipo_honorario == models.TipoHonorario.fijo:
        return float(emp.importe_fijo or 0.0)
    if emp.tipo_honorario == models.TipoHonorario.producto:
        if emp.producto_ref_id and emp.cantidad_unidades:
            prod = db.get(models.ProductoReferencia, emp.producto_ref_id)
            if prod:
                return round(float(emp.cantidad_unidades) * float(prod.precio_vigente), 2)
    return 0.0


def _pago_info(liq: models.LiquidacionEmpleado):
    """(pagado, restante, estado) de una liquidación según sus pagos."""
    pagado = round(sum(p.monto for p in liq.pagos), 2)
    restante = round(max(0.0, liq.monto - pagado), 2)
    if pagado <= _EPS:
        estado = "pendiente"
    elif pagado < liq.monto - _EPS:
        estado = "parcial"
    else:
        estado = "pagado"
    return pagado, restante, estado


def _liq_out(liq: models.LiquidacionEmpleado) -> schemas.LiquidacionEmpleadoOut:
    pagado, restante, estado = _pago_info(liq)
    return schemas.LiquidacionEmpleadoOut(
        id=liq.id, empleado_id=liq.empleado_id, client_id=liq.client_id,
        period=liq.period, monto=liq.monto, medio_pago=liq.medio_pago,
        pagado=pagado, restante=restante, estado=estado,
        pagos=[schemas.PagoEmpleadoOut.model_validate(p) for p in liq.pagos],
    )


def _tipo(emp: models.Empleado) -> Optional[str]:
    return emp.tipo_honorario.value if emp.tipo_honorario else None


@router.get("/{client_id}", response_model=schemas.NominaOut)
def get_nomina(
    client_id: int,
    period: str = Query(..., description="Período YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _validar_period(period)
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")
    ensure_client_access(db, current_user, client_id)

    empleados = (
        db.query(models.Empleado)
        .filter(models.Empleado.client_id == client_id, models.Empleado.activo == True)  # noqa: E712
        .order_by(models.Empleado.apellido, models.Empleado.nombre)
        .all()
    )

    rows = []
    for e in empleados:
        prod_nombre = None
        if e.producto_ref_id:
            prod = db.get(models.ProductoReferencia, e.producto_ref_id)
            prod_nombre = prod.nombre if prod else None

        existing = (
            db.query(models.LiquidacionEmpleado)
            .filter(
                models.LiquidacionEmpleado.empleado_id == e.id,
                models.LiquidacionEmpleado.period == period,
            )
            .first()
        )

        base = dict(
            empleado_id=e.id, nombre=e.nombre, apellido=e.apellido, cuil=e.cuil,
            medio_pago=e.medio_pago or "transferencia",
            tipo_honorario=_tipo(e), importe_fijo=e.importe_fijo,
            producto_ref_id=e.producto_ref_id, cantidad_unidades=e.cantidad_unidades,
            producto_nombre=prod_nombre,
        )

        if existing:
            pagado, restante, estado = _pago_info(existing)
            rows.append(schemas.NominaEmpleadoRow(
                **base,
                monto_sugerido=existing.monto, origen_sugerido="liquidado",
                liquidacion_id=existing.id, monto_a_pagar=existing.monto,
                pagado=pagado, restante=restante, estado=estado,
                pagos=[schemas.PagoEmpleadoOut.model_validate(p) for p in existing.pagos],
            ))
            continue

        prev = (
            db.query(models.LiquidacionEmpleado)
            .filter(
                models.LiquidacionEmpleado.empleado_id == e.id,
                models.LiquidacionEmpleado.period < period,
            )
            .order_by(models.LiquidacionEmpleado.period.desc())
            .first()
        )
        if prev:
            rows.append(schemas.NominaEmpleadoRow(
                **base, monto_sugerido=prev.monto, origen_sugerido="periodo_anterior",
            ))
        else:
            rows.append(schemas.NominaEmpleadoRow(
                **base, monto_sugerido=_base_empleado(e, db), origen_sugerido="config_empleado",
            ))

    return schemas.NominaOut(client_id=client.id, client_name=client.name, period=period, empleados=rows)


@router.post("/{client_id}/liquidar", response_model=schemas.LiquidarResponse)
def liquidar(
    client_id: int,
    body: schemas.LiquidarRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _validar_period(body.period)
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")
    ensure_client_access(db, current_user, client_id)
    if not body.items:
        raise HTTPException(400, "No se seleccionó ningún empleado para liquidar")

    detalle = []
    for item in body.items:
        emp = db.get(models.Empleado, item.empleado_id)
        if not emp or emp.client_id != client_id:
            raise HTTPException(400, f"Empleado {item.empleado_id} no pertenece a este cliente")

        liq = (
            db.query(models.LiquidacionEmpleado)
            .filter(
                models.LiquidacionEmpleado.empleado_id == item.empleado_id,
                models.LiquidacionEmpleado.period == body.period,
            )
            .first()
        )
        if liq:
            liq.monto = item.monto
            liq.medio_pago = item.medio_pago
        else:
            liq = models.LiquidacionEmpleado(
                empleado_id=item.empleado_id, client_id=client_id,
                period=body.period, monto=item.monto, medio_pago=item.medio_pago,
            )
            db.add(liq)
        db.flush()

        if item.modo == "total":
            # pago completo: reemplaza pagos previos por uno solo por el total
            for p in list(liq.pagos):
                db.delete(p)
            db.flush()
            db.add(models.PagoEmpleado(
                liquidacion_id=liq.id, monto=item.monto,
                medio_pago=item.medio_pago, fecha=date.today(),
            ))
        # modo 'parcial': se deja la obligación; los pagos se cargan con POST /pago
        db.flush()
        detalle.append(liq)

    db.add(models.ActionLog(
        user_id=current_user.id, client_id=client_id,
        action_type="liquidacion_personal",
        description=f"Liquidó {len(detalle)} empleado(s) para {body.period} "
                    f"(total ${sum(d.monto for d in detalle):,.2f})",
    ))
    db.commit()
    for d in detalle:
        db.refresh(d)

    return schemas.LiquidarResponse(
        client_id=client_id, period=body.period, liquidados=len(detalle),
        total=round(sum(d.monto for d in detalle), 2),
        detalle=[_liq_out(d) for d in detalle],
    )


@router.post("/pago", response_model=schemas.LiquidacionEmpleadoOut)
def registrar_pago(
    body: schemas.PagoEmpleadoCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Registra un pago parcial contra la liquidación de (empleado, período)."""
    _validar_period(body.period)
    liq = (
        db.query(models.LiquidacionEmpleado)
        .filter(
            models.LiquidacionEmpleado.empleado_id == body.empleado_id,
            models.LiquidacionEmpleado.period == body.period,
        )
        .first()
    )
    if not liq:
        raise HTTPException(400, "El empleado no tiene una liquidación para ese período. "
                                 "Liquidá primero (modo parcial) para fijar el importe.")
    ensure_client_access(db, current_user, liq.client_id)

    pagado, restante, _ = _pago_info(liq)
    if body.monto > restante + 0.01:
        raise HTTPException(422, {
            "error": "El pago supera el restante a pagar",
            "restante": restante, "intento": body.monto,
        })

    db.add(models.PagoEmpleado(
        liquidacion_id=liq.id, monto=body.monto,
        medio_pago=body.medio_pago, fecha=body.fecha or date.today(),
    ))
    db.commit()
    db.refresh(liq)
    return _liq_out(liq)


@router.delete("/pago/{pago_id}", response_model=schemas.LiquidacionEmpleadoOut)
def eliminar_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    pago = db.get(models.PagoEmpleado, pago_id)
    if not pago:
        raise HTTPException(404, "Pago no encontrado")
    liq = pago.liquidacion
    ensure_client_access(db, current_user, liq.client_id)
    db.delete(pago)
    db.commit()
    db.refresh(liq)
    return _liq_out(liq)
