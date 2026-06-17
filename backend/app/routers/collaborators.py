from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..security import get_password_hash
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/collaborators", tags=["collaborators"])


@router.get("/", response_model=List[schemas.UserOut])
def list_collaborators(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    users = db.query(models.User).filter(
        models.User.role == models.UserRole.colaborador,
        models.User.is_active == True
    ).all()
    return users


@router.get("/all", response_model=List[schemas.UserOut])
def list_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    return db.query(models.User).all()


@router.post("/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_collaborator(
    data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")

    initials = "".join(w[0].upper() for w in data.name.split()[:2])
    user = models.User(
        name=data.name,
        email=data.email,
        password_hash=get_password_hash(data.password),
        role=data.role,
        avatar_initials=initials
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_collaborator(
    user_id: int,
    data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = data.model_dump(exclude_none=True)
    if "password" in update_data:
        user.password_hash = get_password_hash(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_collaborator(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.is_active = False
    db.commit()


@router.get("/{user_id}/stats", response_model=schemas.CollaboratorStats)
def get_collaborator_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    tasks = db.query(models.Task).filter(models.Task.collaborator_id == user_id).all()
    clients_count = len(set(t.client_id for t in tasks))

    return schemas.CollaboratorStats(
        collaborator_id=user.id,
        collaborator_name=user.name,
        total_tasks=len(tasks),
        completed=sum(1 for t in tasks if t.status == models.TaskStatus.terminada),
        pending=sum(1 for t in tasks if t.status == models.TaskStatus.pendiente),
        in_progress=sum(1 for t in tasks if t.status == models.TaskStatus.en_curso),
        blocked=sum(1 for t in tasks if t.status == models.TaskStatus.bloqueada),
        clients_count=clients_count
    )
