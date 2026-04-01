from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from typing import List, Optional
from collections import defaultdict
from .. import models, schemas
from ..database import get_db
from ..security import encrypt_credential, decrypt_credential
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=List[schemas.ClientOut])
def list_clients(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Client).options(
        selectinload(models.Client.collaborators).selectinload(models.ClientCollaborator.collaborator),
    )
    if active_only:
        query = query.filter(models.Client.is_active == True)

    # Collaborators only see their assigned clients — use a subquery to avoid
    # lazy-loading client_assignments on the user object
    if current_user.role == models.UserRole.collaborator:
        assigned_subq = (
            db.query(models.ClientCollaborator.client_id)
            .filter(models.ClientCollaborator.collaborator_id == current_user.id)
            .subquery()
        )
        query = query.filter(models.Client.id.in_(assigned_subq))

    clients = query.all()

    # Fetch task counts in a single lightweight query (only client_id + status)
    # instead of loading full Task objects via selectinload.
    client_ids = [c.id for c in clients]
    task_counts = defaultdict(int)
    pending_counts = defaultdict(int)
    if client_ids:
        rows = (
            db.query(models.Task.client_id, models.Task.status)
            .filter(models.Task.client_id.in_(client_ids))
            .all()
        )
        for row in rows:
            task_counts[row.client_id] += 1
            if row.status == models.TaskStatus.pendiente:
                pending_counts[row.client_id] += 1

    result = []
    for client in clients:
        client_dict = {
            col.key: getattr(client, col.key)
            for col in models.Client.__mapper__.column_attrs
        }
        client_dict['collaborators'] = [
            schemas.CollaboratorBrief.model_validate(cc.collaborator)
            for cc in client.collaborators
        ]
        client_dict['task_count'] = task_counts.get(client.id, 0)
        client_dict['pending_tasks'] = pending_counts.get(client.id, 0)
        result.append(schemas.ClientOut.model_validate(client_dict))
    return result


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    client = db.query(models.Client).options(
        selectinload(models.Client.collaborators).selectinload(models.ClientCollaborator.collaborator),
        selectinload(models.Client.tasks),
    ).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if current_user.role == models.UserRole.collaborator:
        assigned_ids = [ca.client_id for ca in current_user.client_assignments]
        if client_id not in assigned_ids:
            raise HTTPException(status_code=403, detail="Sin acceso a este cliente")

    out = schemas.ClientOut.model_validate(client)
    out.collaborators = [
        schemas.CollaboratorBrief.model_validate(cc.collaborator)
        for cc in client.collaborators
    ]
    out.task_count = len(client.tasks)
    out.pending_tasks = sum(1 for t in client.tasks if t.status == models.TaskStatus.pendiente)
    return out


@router.post("/", response_model=schemas.ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    data: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    existing = db.query(models.Client).filter(models.Client.cuit == data.cuit).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese CUIT")

    encrypted = None
    if data.clave_fiscal:
        encrypted = encrypt_credential(data.clave_fiscal)

    client = models.Client(
        name=data.name,
        business_name=data.business_name,
        cuit=data.cuit,
        clave_fiscal_encrypted=encrypted,
        address=data.address,
        phone=data.phone,
        email=data.email,
        category=data.category,
        fiscal_condition=data.fiscal_condition,
        activity_code=data.activity_code,
        notes=data.notes,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return schemas.ClientOut.model_validate(client)


@router.put("/{client_id}", response_model=schemas.ClientOut)
def update_client(
    client_id: int,
    data: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        if field == "clave_fiscal":
            client.clave_fiscal_encrypted = encrypt_credential(value)
        else:
            setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return schemas.ClientOut.model_validate(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(client)
    db.commit()


@router.post("/{client_id}/collaborators", status_code=status.HTTP_201_CREATED)
def assign_collaborator(
    client_id: int,
    data: schemas.AssignCollaborator,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    collaborator = db.query(models.User).filter(models.User.id == data.collaborator_id).first()
    if not collaborator:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")

    exists = db.query(models.ClientCollaborator).filter(
        models.ClientCollaborator.client_id == client_id,
        models.ClientCollaborator.collaborator_id == data.collaborator_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="El colaborador ya está asignado a este cliente")

    cc = models.ClientCollaborator(
        client_id=client_id,
        collaborator_id=data.collaborator_id,
        assigned_by_id=current_user.id
    )
    db.add(cc)
    db.commit()
    return {"message": "Colaborador asignado correctamente"}


@router.delete("/{client_id}/collaborators/{collaborator_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_collaborator(
    client_id: int,
    collaborator_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    cc = db.query(models.ClientCollaborator).filter(
        models.ClientCollaborator.client_id == client_id,
        models.ClientCollaborator.collaborator_id == collaborator_id
    ).first()
    if not cc:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    db.delete(cc)
    db.commit()


@router.get("/{client_id}/credentials", response_model=schemas.ClientCredentials)
def get_credentials(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    clave = None
    if client.clave_fiscal_encrypted:
        try:
            clave = decrypt_credential(client.clave_fiscal_encrypted)
        except Exception:
            clave = None

    return schemas.ClientCredentials(cuit=client.cuit, clave_fiscal=clave)
