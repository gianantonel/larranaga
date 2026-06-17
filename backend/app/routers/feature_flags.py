"""Router de Feature Flags por Requisito (R-XX).

- GET  /feature-flags          → cualquier user logueado
- PUT  /feature-flags/{codigo} → solo super_admin; toggle enabled
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, require_super_admin

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
    current_user: models.User = Depends(require_super_admin),
):
    flag = db.query(models.FeatureFlag).filter_by(codigo=codigo).first()
    if not flag:
        raise HTTPException(status_code=404, detail=f"Requisito {codigo} no existe")

    flag.enabled = payload.enabled
    flag.updated_by_id = current_user.id
    flag.updated_at = datetime.utcnow()

    db.add(models.ActionLog(
        user_id=current_user.id,
        action_type="feature_flag_toggle",
        description=f"{codigo} -> enabled={payload.enabled}",
    ))

    db.commit()
    db.refresh(flag)
    return flag
