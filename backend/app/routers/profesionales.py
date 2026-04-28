"""R-04 — Gestión de Profesionales y Liquidaciones mensuales."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from .. import models, schemas
from ..database import get_db
from ..routers.auth import get_current_user

router = APIRouter(prefix="/profesionales", tags=["profesionales"])


# ─── CRUD Profesionales ───────────────────────────────────────────────────────

@router.get("/", response_model=List[schemas.ProfesionalOut])
def list_profesionales(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    q = db.query(models.Profesional)
    if activo is not None:
        q = q.filter(models.Profesional.activo == activo)
    return q.order_by(models.Profesional.apellido, models.Profesional.nombre).all()


@router.post("/", response_model=schemas.ProfesionalOut, status_code=status.HTTP_201_CREATED)
def create_profesional(
    data: schemas.ProfesionalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear profesionales")
    prof = models.Profesional(**data.model_dump())
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof


@router.get("/{prof_id}", response_model=schemas.ProfesionalOut)
def get_profesional(prof_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    prof = db.query(models.Profesional).filter(models.Profesional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profesional no encontrado")
    return prof


@router.patch("/{prof_id}", response_model=schemas.ProfesionalOut)
def update_profesional(
    prof_id: int,
    data: schemas.ProfesionalUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    prof = db.query(models.Profesional).filter(models.Profesional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profesional no encontrado")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(prof, k, v)
    db.commit()
    db.refresh(prof)
    return prof


# ─── CRUD Liquidaciones ───────────────────────────────────────────────────────

def _recalculate(liq: models.Liquidacion, db: Session) -> None:
    """Recalcular total_a_cobrar y saldo_siguiente en base a los datos actuales."""
    reintegro_total = sum(r.importe for r in liq.reintegros)
    liq.reintegro_gastos = reintegro_total
    # Total honorarios - adelantos + saldo anterior
    base = liq.honorarios_totales - liq.adelantos_percibidos + liq.saldo_anterior
    liq.total_a_cobrar = base + reintegro_total
    # El saldo que queda para el siguiente mes
    liq.saldo_siguiente = liq.total_a_cobrar - liq.monto_cobrado


@router.get("/liquidaciones/periodo/{periodo}", response_model=List[schemas.LiquidacionOut])
def list_liquidaciones_periodo(
    periodo: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    liqs = (
        db.query(models.Liquidacion)
        .filter(models.Liquidacion.periodo == periodo)
        .all()
    )
    result = []
    for liq in liqs:
        d = schemas.LiquidacionOut.model_validate(liq)
        if liq.profesional:
            d.profesional_nombre = f"{liq.profesional.nombre} {liq.profesional.apellido or ''}".strip()
        result.append(d)
    return result


@router.get("/{prof_id}/liquidaciones", response_model=List[schemas.LiquidacionOut])
def list_liquidaciones_profesional(
    prof_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    liqs = (
        db.query(models.Liquidacion)
        .filter(models.Liquidacion.profesional_id == prof_id)
        .order_by(models.Liquidacion.periodo.desc())
        .all()
    )
    result = []
    for liq in liqs:
        d = schemas.LiquidacionOut.model_validate(liq)
        if liq.profesional:
            d.profesional_nombre = f"{liq.profesional.nombre} {liq.profesional.apellido or ''}".strip()
        result.append(d)
    return result


@router.post("/{prof_id}/liquidaciones", response_model=schemas.LiquidacionOut, status_code=status.HTTP_201_CREATED)
def create_liquidacion(
    prof_id: int,
    data: schemas.LiquidacionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    prof = db.query(models.Profesional).filter(models.Profesional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profesional no encontrado")
    existing = (
        db.query(models.Liquidacion)
        .filter(models.Liquidacion.profesional_id == prof_id, models.Liquidacion.periodo == data.periodo)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe una liquidación para {data.periodo}")

    # Calcular adelantos del período automáticamente desde movimientos CC
    adelantos = (
        db.query(models.MovimientoCuentaCorriente)
        .filter(
            models.MovimientoCuentaCorriente.profesional_id == prof_id,
            models.MovimientoCuentaCorriente.periodo_honorario == data.periodo,
            models.MovimientoCuentaCorriente.tipo == "pago",
        )
        .all()
    )
    adelantos_total = sum(m.monto for m in adelantos)

    liq = models.Liquidacion(
        profesional_id=prof_id,
        periodo=data.periodo,
        honorarios_totales=data.honorarios_totales,
        adelantos_percibidos=adelantos_total,
        saldo_anterior=data.saldo_anterior,
    )
    db.add(liq)
    db.flush()
    _recalculate(liq, db)
    db.commit()
    db.refresh(liq)
    out = schemas.LiquidacionOut.model_validate(liq)
    out.profesional_nombre = f"{prof.nombre} {prof.apellido or ''}".strip()
    return out


@router.patch("/liquidaciones/{liq_id}", response_model=schemas.LiquidacionOut)
def update_liquidacion(
    liq_id: int,
    data: schemas.LiquidacionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    liq = db.query(models.Liquidacion).filter(models.Liquidacion.id == liq_id).first()
    if not liq:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(liq, k, v)
    _recalculate(liq, db)
    db.commit()
    db.refresh(liq)
    out = schemas.LiquidacionOut.model_validate(liq)
    if liq.profesional:
        out.profesional_nombre = f"{liq.profesional.nombre} {liq.profesional.apellido or ''}".strip()
    return out


# ─── Reintegros de Gastos ─────────────────────────────────────────────────────

@router.post("/liquidaciones/{liq_id}/reintegros", response_model=schemas.ReintegroGastoOut, status_code=201)
def add_reintegro(
    liq_id: int,
    data: schemas.ReintegroGastoCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    liq = db.query(models.Liquidacion).filter(models.Liquidacion.id == liq_id).first()
    if not liq:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    reintegro = models.ReintegroGasto(liquidacion_id=liq_id, **data.model_dump())
    db.add(reintegro)
    db.flush()
    _recalculate(liq, db)
    db.commit()
    db.refresh(reintegro)
    return reintegro


@router.delete("/liquidaciones/{liq_id}/reintegros/{reintegro_id}", status_code=204)
def delete_reintegro(
    liq_id: int,
    reintegro_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    reintegro = db.query(models.ReintegroGasto).filter(
        models.ReintegroGasto.id == reintegro_id,
        models.ReintegroGasto.liquidacion_id == liq_id,
    ).first()
    if not reintegro:
        raise HTTPException(status_code=404, detail="Reintegro no encontrado")
    liq = reintegro.liquidacion
    db.delete(reintegro)
    db.flush()
    _recalculate(liq, db)
    db.commit()


# ─── Actualizar adelantos automáticamente desde CC ───────────────────────────

@router.post("/liquidaciones/{liq_id}/sincronizar-adelantos", response_model=schemas.LiquidacionOut)
def sincronizar_adelantos(
    liq_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Re-calcula los adelantos percibidos leyendo movimientos CC del período."""
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    liq = db.query(models.Liquidacion).filter(models.Liquidacion.id == liq_id).first()
    if not liq:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")

    adelantos = (
        db.query(models.MovimientoCuentaCorriente)
        .filter(
            models.MovimientoCuentaCorriente.profesional_id == liq.profesional_id,
            models.MovimientoCuentaCorriente.periodo_honorario == liq.periodo,
            models.MovimientoCuentaCorriente.tipo == "pago",
        )
        .all()
    )
    liq.adelantos_percibidos = sum(m.monto for m in adelantos)
    _recalculate(liq, db)
    db.commit()
    db.refresh(liq)
    out = schemas.LiquidacionOut.model_validate(liq)
    if liq.profesional:
        out.profesional_nombre = f"{liq.profesional.nombre} {liq.profesional.apellido or ''}".strip()
    return out
