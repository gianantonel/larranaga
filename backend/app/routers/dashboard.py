from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, case
from typing import List
from datetime import datetime, date
from collections import defaultdict
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    now = datetime.utcnow()
    month_start = date(now.year, now.month, 1)

    return schemas.DashboardStats(
        total_clients=db.query(models.Client).count(),
        active_clients=db.query(models.Client).filter(models.Client.is_active == True).count(),
        total_collaborators=db.query(models.User).filter(models.User.role == models.UserRole.colaborador).count(),
        total_tasks=db.query(models.Task).count(),
        pending_tasks=db.query(models.Task).filter(models.Task.status == models.TaskStatus.pendiente).count(),
        in_progress_tasks=db.query(models.Task).filter(models.Task.status == models.TaskStatus.en_curso).count(),
        completed_tasks=db.query(models.Task).filter(models.Task.status == models.TaskStatus.terminada).count(),
        blocked_tasks=db.query(models.Task).filter(models.Task.status == models.TaskStatus.bloqueada).count(),
        tasks_this_month=db.query(models.Task).filter(
            func.date(models.Task.created_at) >= month_start
        ).count(),
        iva_pendientes=db.query(models.IVARecord).filter(models.IVARecord.filed == False).count(),
        iva_presentados_mes=db.query(models.IVARecord).filter(
            models.IVARecord.filed == True,
            func.date(models.IVARecord.filed_at) >= month_start
        ).count()
    )


@router.get("/collaborator-stats", response_model=List[schemas.CollaboratorStats])
def get_all_collaborator_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    collaborators = db.query(models.User).filter(
        models.User.role == models.UserRole.colaborador,
        models.User.is_active == True
    ).all()

    if not collaborators:
        return []

    # Single query for all collaborator tasks instead of N queries
    collab_ids = [c.id for c in collaborators]
    all_tasks = db.query(
        models.Task.collaborator_id,
        models.Task.status,
        models.Task.client_id,
    ).filter(models.Task.collaborator_id.in_(collab_ids)).all()

    # Group in Python — zero extra queries
    tasks_by_collab: dict = defaultdict(list)
    for t in all_tasks:
        tasks_by_collab[t.collaborator_id].append(t)

    result = []
    for collab in collaborators:
        tasks = tasks_by_collab.get(collab.id, [])
        clients_count = len({t.client_id for t in tasks})
        result.append(schemas.CollaboratorStats(
            collaborator_id=collab.id,
            collaborator_name=collab.name,
            total_tasks=len(tasks),
            completed=sum(1 for t in tasks if t.status == models.TaskStatus.terminada),
            pending=sum(1 for t in tasks if t.status == models.TaskStatus.pendiente),
            in_progress=sum(1 for t in tasks if t.status == models.TaskStatus.en_curso),
            blocked=sum(1 for t in tasks if t.status == models.TaskStatus.bloqueada),
            clients_count=clients_count
        ))
    return result


@router.get("/timeline")
def get_timeline(
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # selectinload eliminates the 200×2 = 400 lazy-load queries
    logs = db.query(models.ActionLog).options(
        selectinload(models.ActionLog.user),
        selectinload(models.ActionLog.client),
    ).order_by(models.ActionLog.created_at.desc()).limit(50).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user.name if log.user else "Desconocido",
            "client_id": log.client_id,
            "client_name": log.client.name if log.client else None,
            "task_id": log.task_id,
            "action_type": log.action_type,
            "description": log.description,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/iva-overview")
def get_iva_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    clients = db.query(models.Client).filter(models.Client.is_active == True).all()
    if not clients:
        return []

    client_ids = [c.id for c in clients]

    # Single query for all IVA records instead of N queries
    all_records = db.query(models.IVARecord).filter(
        models.IVARecord.client_id.in_(client_ids)
    ).order_by(models.IVARecord.period.desc()).all()

    # Group in Python
    records_by_client: dict = defaultdict(list)
    for r in all_records:
        if len(records_by_client[r.client_id]) < 12:
            records_by_client[r.client_id].append(r)

    return [
        {
            "client_id": c.id,
            "client_name": c.name,
            "cuit": c.cuit,
            "records": [
                {
                    "period": r.period,
                    "debito_fiscal": r.debito_fiscal,
                    "credito_fiscal": r.credito_fiscal,
                    "saldo": r.saldo,
                    "filed": r.filed,
                }
                for r in records_by_client.get(c.id, [])
            ],
            "pending_count": sum(1 for r in records_by_client.get(c.id, []) if not r.filed),
        }
        for c in clients
    ]


@router.get("/tasks-by-type")
def get_tasks_by_type(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    results = db.query(
        models.Task.task_type,
        models.Task.status,
        func.count(models.Task.id).label("count")
    ).group_by(models.Task.task_type, models.Task.status).all()

    data = {}
    for task_type, task_status, count in results:
        if task_type not in data:
            data[task_type] = {}
        data[task_type][task_status] = count
    return data


@router.get("/monthly-activity")
def get_monthly_activity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Use SQL aggregation instead of loading all rows into Python
    invoice_agg = db.query(
        func.strftime("%Y-%m", models.Invoice.date).label("period"),
        func.count(models.Invoice.id).label("facturas"),
        func.sum(models.Invoice.total).label("monto_facturas"),
    ).group_by(func.strftime("%Y-%m", models.Invoice.date)).all()

    iva_agg = db.query(
        models.IVARecord.period,
        func.count(models.IVARecord.id).label("iva_presentados"),
    ).filter(models.IVARecord.filed == True).group_by(models.IVARecord.period).all()

    task_agg = db.query(
        func.strftime("%Y-%m", models.Task.created_at).label("period"),
        func.count(models.Task.id).label("tareas"),
    ).filter(models.Task.created_at.isnot(None)).group_by(
        func.strftime("%Y-%m", models.Task.created_at)
    ).all()

    monthly: dict = {}

    for row in invoice_agg:
        if row.period:
            monthly.setdefault(row.period, {"facturas": 0, "monto_facturas": 0, "iva_presentados": 0, "tareas": 0})
            monthly[row.period]["facturas"] = row.facturas
            monthly[row.period]["monto_facturas"] = round(row.monto_facturas or 0, 2)

    for row in iva_agg:
        if row.period:
            monthly.setdefault(row.period, {"facturas": 0, "monto_facturas": 0, "iva_presentados": 0, "tareas": 0})
            monthly[row.period]["iva_presentados"] = row.iva_presentados

    for row in task_agg:
        if row.period:
            monthly.setdefault(row.period, {"facturas": 0, "monto_facturas": 0, "iva_presentados": 0, "tareas": 0})
            monthly[row.period]["tareas"] = row.tareas

    return [{"period": k, **monthly[k]} for k in sorted(monthly)]
