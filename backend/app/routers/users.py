"""
/users — Gestión de usuarios (panel del admin / super-admin)

Reglas de asignación de rol:
  - Super-Admin puede asignar: admin, colaborador, invitado
  - Admin       puede asignar: colaborador, invitado
  - Nadie       puede asignar super_admin (solo via seed/migración)
  - Nadie       puede modificar a un super_admin (excepto otro super_admin)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_password_hash
from .auth import get_current_user, require_admin, require_super_admin


router = APIRouter(prefix="/users", tags=["users"])


# ─── Reglas de permisos ──────────────────────────────────────────────────────

def _can_assign(actor: models.User, target_role: models.UserRole) -> bool:
    """¿Puede `actor` asignar `target_role` a alguien?"""
    if actor.role == models.UserRole.super_admin:
        return target_role in (
            models.UserRole.admin,
            models.UserRole.colaborador,
            models.UserRole.invitado,
        )
    if actor.role == models.UserRole.admin:
        return target_role in (
            models.UserRole.colaborador,
            models.UserRole.invitado,
        )
    return False


def _can_modify_target(actor: models.User, target: models.User) -> bool:
    """¿Puede `actor` editar al usuario `target`?"""
    # Nadie puede modificar a un super_admin salvo otro super_admin
    if target.role == models.UserRole.super_admin and actor.role != models.UserRole.super_admin:
        return False
    # Un admin no puede modificar a otro admin (solo super_admin puede)
    if target.role == models.UserRole.admin and actor.role == models.UserRole.admin and actor.id != target.id:
        return False
    return True


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/", response_model=List[schemas.UserOut])
def listar_activos(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Listado de usuarios activos."""
    return (
        db.query(models.User)
        .filter(models.User.status == models.UserStatus.active)
        .order_by(models.User.role, models.User.name)
        .all()
    )


@router.get("/pending", response_model=List[schemas.UserOut])
def listar_pendientes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Listado de usuarios pendientes de aprobación."""
    return (
        db.query(models.User)
        .filter(models.User.status == models.UserStatus.pending)
        .order_by(models.User.created_at.desc())
        .all()
    )


@router.post("/invite", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def invitar_usuario(
    data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Crear usuario en estado pending (sólo invitación)."""
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(400, "Ya existe un usuario con ese email")

    if not _can_assign(current_user, data.role):
        raise HTTPException(403, f"No tenés permisos para asignar el rol '{data.role.value}'")

    initials = ((data.name or " ")[0] + (data.last_name or " ")[0]).strip().upper() or "??"

    user = models.User(
        name=data.name,
        last_name=data.last_name,
        cuit=data.cuit,
        email=data.email,
        password_hash=get_password_hash(data.password),
        role=data.role,
        status=models.UserStatus.pending,
        is_active=True,
        avatar_initials=initials[:3],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/role", response_model=schemas.UserOut)
def cambiar_rol(
    user_id: int,
    data: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Cambiar el rol de un usuario respetando jerarquía."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    if not _can_modify_target(current_user, user):
        raise HTTPException(403, "No tenés permisos para modificar este usuario")

    if not _can_assign(current_user, data.role):
        raise HTTPException(403, f"No tenés permisos para asignar el rol '{data.role.value}'")

    user.role = data.role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/approve", response_model=schemas.UserOut)
def aprobar_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Aprobar un usuario que está pending → active."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    if user.status != models.UserStatus.pending:
        raise HTTPException(400, "El usuario no está pendiente de aprobación")
    if not _can_modify_target(current_user, user):
        raise HTTPException(403, "No tenés permisos para aprobar este usuario")

    user.status = models.UserStatus.active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Soft-delete (is_active=False)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    if not _can_modify_target(current_user, user):
        raise HTTPException(403, "No tenés permisos para desactivar este usuario")
    if user.id == current_user.id:
        raise HTTPException(400, "No podés desactivarte a vos mismo")

    user.is_active = False
    db.commit()
