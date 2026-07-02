"""Router de Feature Flags por Requisito (R-XX).

- GET  /feature-flags          → cualquier user logueado
- PUT  /feature-flags/{codigo} → admin o super_admin; toggle enabled
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


@router.get("", response_model=List[schemas.FeatureFlagOut])
def list_feature_flags(
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.FeatureFlag)
        .order_by(models.FeatureFlag.fase, models.FeatureFlag.codigo)
        .all()
    )


@router.put("/{codigo}", response_model=schemas.FeatureFlagOut)
def update_feature_flag(
    codigo: str,
    payload: schemas.FeatureFlagUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    flag = db.query(models.FeatureFlag).filter_by(codigo=codigo).first()
    if not flag:
        raise HTTPException(status_code=404, detail=f"Requisito {codigo} no existe")

    es_super = current_user.role == models.UserRole.super_admin
    cambios = []

    # Nivel ADMIN (qué ve el admin) — solo super_admin
    if payload.enabled_admin is not None:
        if not es_super:
            raise HTTPException(403, "Solo un super_admin puede cambiar la visibilidad del admin")
        flag.enabled_admin = payload.enabled_admin
        cambios.append(f"enabled_admin={payload.enabled_admin}")
        # Si el admin ya no puede ver la acción, tampoco el colaborador
        if not payload.enabled_admin:
            flag.enabled = False

    # Nivel COLABORADOR (qué ve el colaborador) — admin o super_admin
    if payload.enabled is not None:
        # El admin (no super) solo puede togglear dentro de lo que tiene habilitado
        if not es_super and not flag.enabled_admin:
            raise HTTPException(403, "Esta acción no está habilitada para vos por el super_admin")
        flag.enabled = payload.enabled
        cambios.append(f"enabled={payload.enabled}")

    if not cambios:
        raise HTTPException(400, "Nada para actualizar")

    flag.updated_by_id = current_user.id
    flag.updated_at = datetime.utcnow()
    db.add(models.ActionLog(
        user_id=current_user.id,
        action_type="feature_flag_toggle",
        description=f"{codigo} -> {', '.join(cambios)}",
    ))

    db.commit()
    db.refresh(flag)
    return flag
