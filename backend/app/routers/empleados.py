"""CRUD de empleados (nómina por empresa cliente).

Cada empleado pertenece a una empresa (client_id → clients). Endpoints:
  GET    /empleados/                  listado (filtros: client_id, activo, q)
  GET    /empleados/{id}              detalle
  POST   /empleados/                  alta (valida que la empresa exista)
  PUT    /empleados/{id}              edición parcial
  DELETE /empleados/{id}              baja física
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, require_admin
from ..access import assigned_client_ids, ensure_client_access

router = APIRouter(prefix="/empleados", tags=["empleados"])


def _to_out(emp: models.Empleado) -> schemas.EmpleadoOut:
    out = schemas.EmpleadoOut.model_validate(emp)
    out.client_name = emp.empresa.name if emp.empresa else None
    return out


@router.get("/", response_model=List[schemas.EmpleadoOut])
def list_empleados(
    client_id: Optional[int] = None,
    activo: Optional[bool] = None,
    q: Optional[str] = Query(default=None, description="Busca en nombre/apellido/CUIL"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Empleado)
    allowed = assigned_client_ids(db, current_user)
    if allowed is not None:
        query = query.filter(models.Empleado.client_id.in_(allowed))
    if client_id is not None:
        query = query.filter(models.Empleado.client_id == client_id)
    if activo is not None:
        query = query.filter(models.Empleado.activo == activo)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (models.Empleado.nombre.ilike(like))
            | (models.Empleado.apellido.ilike(like))
            | (models.Empleado.cuil.ilike(like))
        )
    empleados = query.order_by(
        models.Empleado.apellido, models.Empleado.nombre
    ).all()
    return [_to_out(e) for e in empleados]


@router.get("/{empleado_id}", response_model=schemas.EmpleadoOut)
def get_empleado(
    empleado_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    emp = db.get(models.Empleado, empleado_id)
    if not emp:
        raise HTTPException(404, "Empleado no encontrado")
    ensure_client_access(db, current_user, emp.client_id)
    return _to_out(emp)


@router.post("/", response_model=schemas.EmpleadoOut, status_code=status.HTTP_201_CREATED)
def create_empleado(
    data: schemas.EmpleadoCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    empresa = db.get(models.Client, data.client_id)
    if not empresa:
        raise HTTPException(400, f"Empresa (client_id={data.client_id}) no encontrada")

    emp = models.Empleado(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return _to_out(emp)


@router.put("/{empleado_id}", response_model=schemas.EmpleadoOut)
def update_empleado(
    empleado_id: int,
    data: schemas.EmpleadoUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    emp = db.get(models.Empleado, empleado_id)
    if not emp:
        raise HTTPException(404, "Empleado no encontrado")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(emp, field, val)

    db.commit()
    db.refresh(emp)
    return _to_out(emp)


@router.delete("/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_empleado(
    empleado_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    emp = db.get(models.Empleado, empleado_id)
    if not emp:
        raise HTTPException(404, "Empleado no encontrado")
    db.delete(emp)
    db.commit()
    return None
