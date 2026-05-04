"""
Router de sincronización InsForge.

Expone endpoints para gestionar la sincronización de la base de datos
local (SQLite) con InsForge Cloud.
"""

import os
import requests
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from .. import models
from ..sync.insforge_sync import (
    sync_to_insforge,
    export_database_to_sql,
    get_db_path,
    INSFORGE_API_URL,
    INSFORGE_IMPORT_ENDPOINT,
    INSFORGE_API_KEY,
)
from ..sync.events import sync_now, _trigger_sync
from .auth import require_admin, get_current_user

router = APIRouter(prefix="/insforge", tags=["insforge"])

# Estado de la última sincronización (en memoria)
_last_sync: dict = {
    "timestamp": None,
    "status": "never",
    "message": "Sin sincronizaciones todavía",
}


@router.get("/status")
def get_status(current_user: models.User = Depends(require_admin)):
    """
    Devuelve el estado de la integración InsForge:
    - Si la API es alcanzable
    - Si la API key está configurada
    - Ruta y existencia de la base de datos
    - Última sincronización
    """
    # Verificar alcanzabilidad de InsForge
    insforge_reachable = False
    insforge_status_code = None
    try:
        resp = requests.get(f"{INSFORGE_API_URL}/health", timeout=5)
        insforge_status_code = resp.status_code
        insforge_reachable = resp.status_code < 500
    except requests.exceptions.ConnectionError:
        insforge_status_code = None
    except requests.exceptions.Timeout:
        insforge_status_code = "timeout"
    except Exception:
        pass

    # Info de la BD
    try:
        db_path = get_db_path()
        db_exists = os.path.exists(db_path)
        db_size_mb = round(os.path.getsize(db_path) / 1024 / 1024, 2) if db_exists else 0
    except ValueError as e:
        db_path = str(e)
        db_exists = False
        db_size_mb = 0

    api_key_configured = bool(os.getenv('INSFORGE_API_KEY'))
    api_key_preview = f"{INSFORGE_API_KEY[:8]}..." if INSFORGE_API_KEY else None

    return {
        "insforge_url": INSFORGE_API_URL,
        "insforge_reachable": insforge_reachable,
        "insforge_status_code": insforge_status_code,
        "api_key_configured": api_key_configured,
        "api_key_preview": api_key_preview,
        "db_path": db_path,
        "db_exists": db_exists,
        "db_size_mb": db_size_mb,
        "last_sync": _last_sync,
    }


@router.post("/sync")
def trigger_sync_manual(current_user: models.User = Depends(require_admin)):
    """
    Dispara una sincronización completa de la BD local a InsForge (sincrónico).
    Puede tardar varios segundos dependiendo del tamaño de la BD.
    """
    global _last_sync

    started_at = datetime.utcnow().isoformat()

    success = sync_now()

    _last_sync = {
        "timestamp": started_at,
        "status": "success" if success else "failed",
        "triggered_by": current_user.email,
        "message": "Sincronización completada exitosamente" if success
                   else "Error durante sincronización (revisar logs del servidor)",
    }

    if not success:
        raise HTTPException(
            status_code=502,
            detail="La sincronización con InsForge falló. Verificar logs del servidor y disponibilidad de InsForge."
        )

    return _last_sync


@router.post("/sync-background")
def trigger_sync_background(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(require_admin)
):
    """
    Dispara una sincronización en segundo plano (no bloquea la respuesta).
    Útil cuando la BD es grande y no se quiere esperar.
    """
    global _last_sync

    _last_sync = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "in_progress",
        "triggered_by": current_user.email,
        "message": "Sincronización en curso...",
    }

    def _bg_sync():
        global _last_sync
        success = sync_now()
        _last_sync["status"] = "success" if success else "failed"
        _last_sync["message"] = (
            "Sincronización completada exitosamente" if success
            else "Error durante sincronización (revisar logs)"
        )

    background_tasks.add_task(_bg_sync)

    return {
        "status": "queued",
        "message": "Sincronización iniciada en segundo plano. Consultá /insforge/status para ver el resultado.",
        "timestamp": _last_sync["timestamp"],
    }


@router.get("/preview-sql")
def preview_sql(
    limit_rows: int = 10,
    current_user: models.User = Depends(require_admin)
):
    """
    Devuelve una preview del SQL que se exportaría a InsForge.
    Solo las primeras `limit_rows` líneas de INSERT.
    """
    try:
        db_path = get_db_path()
        sql_content = export_database_to_sql(db_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando BD: {e}")

    lines = sql_content.split('\n')
    insert_lines = [l for l in lines if l.startswith('INSERT')]
    header_lines = [l for l in lines if not l.startswith('INSERT')]

    return {
        "total_insert_rows": len(insert_lines),
        "total_sql_bytes": len(sql_content),
        "preview_inserts": insert_lines[:limit_rows],
        "header": '\n'.join(header_lines[:20]),
    }
