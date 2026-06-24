"""Liquidación de honorarios por empleado (nómina de cada cliente).

Vista Honorarios rediseñada: cliente → nómina → liquidar.
  GET  /liquidacion-personal/{client_id}?period=YYYY-MM
       Devuelve los empleados activos del cliente con su monto SUGERIDO:
       - si ya hay liquidación para (empleado, período) → ese monto (ya_liquidado)
       - si no, el monto del período anterior del empleado
       - si es nuevo (sin período previo) → base de la config del cliente (fijo/producto)
  POST /liquidacion-personal/{client_id}/liquidar
       Liquida (upsert idempotente) los empleados seleccionados para el período.

Control de acceso: un colaborador solo opera sobre sus clientes asignados.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..access import ensure_client_access

router = APIRouter(prefix="/liquidacion-personal", tags=["liquidacion_personal"])


def _validar_period(period: str) -> str:
    if not period or len(period) != 7 or period[4] != "-":
        raise HTTPException(400, f"period inválido: {period!r} (esperado YYYY-MM)")
    try:
        int(period[:4]); int(period[5:7])
    except ValueError:
        raise HTTPException(400, f"period inválido: {period!r}")
    return period


def _base_config(client: models.Client, db: Session) -> float:
    """Monto base según la config de honorario del cliente. 0 si no está configurada."""
    if client.tipo_honorario == models.TipoHonorario.fijo:
        return float(client.importe_honorario or 0.0)
    if client.tipo_honorario == models.TipoHonorario.producto:
        if client.producto_ref_id and client.cantidad_unidades:
            prod = db.get(models.ProductoReferencia, client.producto_ref_id)
            if prod:
                return round(float(client.cantidad_unidades) * float(prod.precio_vigente), 2)
    return 0.0


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

    base = _base_config(client, db)

    empleados = (
        db.query(models.Empleado)
        .filter(models.Empleado.client_id == client_id, models.Empleado.activo == True)  # noqa: E712
        .order_by(models.Empleado.apellido, models.Empleado.nombre)
        .all()
    )

    rows = []
    for e in empleados:
        existing = (
            db.query(models.LiquidacionEmpleado)
            .filter(
                models.LiquidacionEmpleado.empleado_id == e.id,
                models.LiquidacionEmpleado.period == period,
            )
            .first()
        )
        if existing:
            rows.append(schemas.NominaEmpleadoRow(
                empleado_id=e.id, nombre=e.nombre, apellido=e.apellido, cuil=e.cuil,
                monto_sugerido=existing.monto, ya_liquidado=True,
                monto_liquidado=existing.monto, origen_sugerido="liquidado",
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
                empleado_id=e.id, nombre=e.nombre, apellido=e.apellido, cuil=e.cuil,
                monto_sugerido=prev.monto, ya_liquidado=False,
                origen_sugerido="periodo_anterior",
            ))
        else:
            rows.append(schemas.NominaEmpleadoRow(
                empleado_id=e.id, nombre=e.nombre, apellido=e.apellido, cuil=e.cuil,
                monto_sugerido=base, ya_liquidado=False,
                origen_sugerido="config_cliente",
            ))

    return schemas.NominaOut(
        client_id=client.id,
        client_name=client.name,
        period=period,
        tipo_honorario=client.tipo_honorario.value if client.tipo_honorario else None,
        empleados=rows,
    )


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
            raise HTTPException(
                400, f"Empleado {item.empleado_id} no pertenece a este cliente")

        existing = (
            db.query(models.LiquidacionEmpleado)
            .filter(
                models.LiquidacionEmpleado.empleado_id == item.empleado_id,
                models.LiquidacionEmpleado.period == body.period,
            )
            .first()
        )
        if existing:
            existing.monto = item.monto
            db.flush()
            detalle.append(existing)
        else:
            liq = models.LiquidacionEmpleado(
                empleado_id=item.empleado_id,
                client_id=client_id,
                period=body.period,
                monto=item.monto,
            )
            db.add(liq)
            db.flush()
            detalle.append(liq)

    db.add(models.ActionLog(
        user_id=current_user.id,
        client_id=client_id,
        action_type="liquidacion_personal",
        description=f"Liquidó {len(detalle)} empleado(s) para {body.period} "
                    f"(total ${sum(d.monto for d in detalle):,.2f})",
    ))
    db.commit()

    for d in detalle:
        db.refresh(d)

    return schemas.LiquidarResponse(
        client_id=client_id,
        period=body.period,
        liquidados=len(detalle),
        total=round(sum(d.monto for d in detalle), 2),
        detalle=[schemas.LiquidacionEmpleadoOut.model_validate(d) for d in detalle],
    )
