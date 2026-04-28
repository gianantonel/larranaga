from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[schemas.TaskOut])
def list_tasks(
    client_id: Optional[int] = None,
    collaborator_id: Optional[int] = None,
    task_status: Optional[str] = Query(None, alias="status"),
    task_type: Optional[str] = Query(None, alias="type"),
    period: Optional[str] = None,
    limit: int = Query(default=500, le=1000),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Task).options(
        selectinload(models.Task.client),
        selectinload(models.Task.collaborator),
        selectinload(models.Task.subtasks),
    )

    if current_user.role == models.UserRole.colaborador:
        query = query.filter(models.Task.collaborator_id == current_user.id)

    if client_id:
        query = query.filter(models.Task.client_id == client_id)
    if collaborator_id:
        query = query.filter(models.Task.collaborator_id == collaborator_id)
    if task_status:
        query = query.filter(models.Task.status == task_status)
    if task_type:
        query = query.filter(models.Task.task_type == task_type)
    if period:
        query = query.filter(models.Task.period == period)

    tasks = query.order_by(models.Task.created_at.desc()).limit(limit).all()
    return [_build_task_out(t) for t in tasks]


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).options(
        selectinload(models.Task.client),
        selectinload(models.Task.collaborator),
        selectinload(models.Task.subtasks),
    ).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return _build_task_out(task)


@router.post("/", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    client = db.query(models.Client).filter(models.Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    task = models.Task(**data.model_dump())
    db.add(task)
    db.commit()

    db.add(models.ActionLog(
        user_id=current_user.id,
        client_id=data.client_id,
        task_id=task.id,
        action_type="task_created",
        description=f"Tarea creada: {data.title}"
    ))
    db.commit()

    return _build_task_out(_reload_task(db, task.id))


@router.put("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    data: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    update_data = data.model_dump(exclude_none=True)
    old_status = task.status

    for field, value in update_data.items():
        setattr(task, field, value)

    if data.status == models.TaskStatus.terminada and old_status != models.TaskStatus.terminada:
        task.completed_at = datetime.utcnow()

    task.updated_at = datetime.utcnow()
    db.commit()

    db.add(models.ActionLog(
        user_id=current_user.id,
        client_id=task.client_id,
        task_id=task.id,
        action_type="task_updated",
        description=f"Tarea actualizada: {task.title} → {task.status}"
    ))
    db.commit()

    return _build_task_out(_reload_task(db, task.id))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    db.delete(task)
    db.commit()


# ─── Subtasks ─────────────────────────────────────────────────────────────────

@router.get("/{task_id}/subtasks", response_model=List[schemas.SubtaskOut])
def list_subtasks(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Subtask).filter(models.Subtask.task_id == task_id).all()


@router.post("/{task_id}/subtasks", response_model=schemas.SubtaskOut, status_code=status.HTTP_201_CREATED)
def create_subtask(
    task_id: int,
    data: schemas.SubtaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    subtask = models.Subtask(task_id=task_id, **data.model_dump())
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


@router.put("/{task_id}/subtasks/{subtask_id}", response_model=schemas.SubtaskOut)
def update_subtask(
    task_id: int,
    subtask_id: int,
    data: schemas.SubtaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    subtask = db.query(models.Subtask).filter(
        models.Subtask.id == subtask_id,
        models.Subtask.task_id == task_id
    ).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtarea no encontrada")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(subtask, field, value)
    subtask.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(subtask)
    return subtask


@router.delete("/{task_id}/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subtask(
    task_id: int,
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    subtask = db.query(models.Subtask).filter(
        models.Subtask.id == subtask_id,
        models.Subtask.task_id == task_id
    ).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtarea no encontrada")
    db.delete(subtask)
    db.commit()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _reload_task(db: Session, task_id: int) -> models.Task:
    """Reload a task with all relationships eagerly loaded."""
    return db.query(models.Task).options(
        selectinload(models.Task.client),
        selectinload(models.Task.collaborator),
        selectinload(models.Task.subtasks),
    ).filter(models.Task.id == task_id).one()


def _build_task_out(task: models.Task) -> schemas.TaskOut:
    out = schemas.TaskOut.model_validate(task)
    out.client_name = task.client.name if task.client else None
    out.collaborator_name = task.collaborator.name if task.collaborator else None
    out.subtasks = [schemas.SubtaskOut.model_validate(s) for s in task.subtasks]
    return out
