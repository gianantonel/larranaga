"""Helpers de control de acceso por cliente.

Regla de negocio: admin/super_admin ven TODOS los clientes; un `colaborador`
solo puede ver/modificar datos de los clientes que tiene asignados vía la tabla
`client_collaborators`. Estos helpers centralizan ese filtro para usarlo en
todos los routers que exponen datos por cliente.
"""
from typing import Optional, Set

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models


def assigned_client_ids(db: Session, user: models.User) -> Optional[Set[int]]:
    """IDs de clientes que el usuario puede ver.

    Devuelve `None` si el usuario NO tiene restricción (admin/super_admin) —
    o sea, ve todos. Para un `colaborador`, devuelve el set de client_id que
    tiene asignados (puede ser vacío si no tiene ninguno).
    """
    if user.role == models.UserRole.colaborador:
        rows = (
            db.query(models.ClientCollaborator.client_id)
            .filter(models.ClientCollaborator.collaborator_id == user.id)
            .all()
        )
        return {r[0] for r in rows}
    return None


def ensure_client_access(db: Session, user: models.User, client_id: int) -> None:
    """Lanza 403 si el usuario es colaborador y `client_id` no está asignado.

    No-op para admin/super_admin. Usar en endpoints que reciben/operan sobre un
    client_id puntual (path, query o body), o sobre una entidad con FK client_id.
    """
    ids = assigned_client_ids(db, user)
    if ids is not None and client_id not in ids:
        raise HTTPException(status_code=403, detail="No tenés acceso a este cliente")
