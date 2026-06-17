"""R-09: Maestro de Proveedores + Resolución de Imputación Contable por CUIT.

Pipeline de 3 niveles para GET /imputacion/cuit/{cuit}:
  1. Busca en maestro_proveedores (caché local) → retorna si encontrado.
  2. Si no, consulta padrón ARCA (ws_sr_padron_a4) → guarda y retorna.
  3. Si ARCA no devuelve cuenta contable → retorna cuenta_contable=null
     para asignación manual.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/imputacion", tags=["imputacion"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _consultar_padron_arca(cuit: str) -> dict | None:
    """Consulta el padrón ARCA (ws_sr_padron_a4) para obtener la razón social.

    TODO: integrar con afip_sdk cuando los certificados estén disponibles.
    Por ahora retorna None (sin datos de padrón) para no bloquear el pipeline.
    La función está preparada para recibir el resultado del SDK y mapearlo
    al formato esperado: {"razon_social": str, "cuenta_contable": str | None}.
    """
    try:
        # Placeholder — activar cuando haya certificados de padrón configurados
        # from ..afip_sdk.client import get_afip_instance_for_studio
        # afip = get_afip_instance_for_studio()
        # result = afip.PersonaServiceA4.getPersona(int(cuit.replace("-", "")))
        # return {
        #     "razon_social": result.get("razonSocial") or result.get("apellido"),
        #     "cuenta_contable": None,  # El padrón no devuelve cuenta contable
        # }
        return None
    except Exception as exc:
        logger.warning("ARCA padrón no disponible para CUIT %s: %s", cuit, exc)
        return None


# ─── Resolución de imputación (pipeline 3 niveles) ───────────────────────────

@router.get("/cuit/{cuit}", response_model=schemas.ImputacionCuitResponse)
def resolver_imputacion(
    cuit: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Resuelve la cuenta contable para un CUIT dado.

    Nivel 1 — caché local: si el CUIT ya está en maestro_proveedores, retorna.
    Nivel 2 — padrón ARCA: si no está en caché, consulta ARCA y guarda el resultado.
    Nivel 3 — sin datos: si ARCA tampoco tiene info, retorna cuenta_contable=null.
    """
    cuit_clean = cuit.strip().replace("-", "").replace(" ", "")

    # Nivel 1: caché local
    proveedor = (
        db.query(models.MaestroProveedor)
        .filter(models.MaestroProveedor.cuit == cuit_clean)
        .first()
    )
    if proveedor:
        return schemas.ImputacionCuitResponse(
            cuit=proveedor.cuit,
            razon_social=proveedor.razon_social,
            cuenta_contable=proveedor.cuenta_contable,
            fuente="cache",
            guardado=False,
        )

    # Nivel 2: consulta padrón ARCA
    padron_data = _consultar_padron_arca(cuit_clean)
    if padron_data:
        nuevo = models.MaestroProveedor(
            cuit=cuit_clean,
            razon_social=padron_data.get("razon_social"),
            cuenta_contable=padron_data.get("cuenta_contable"),
            fuente=models.FuenteMaestro.padron,
            activo=True,
        )
        db.add(nuevo)
        db.commit()
        return schemas.ImputacionCuitResponse(
            cuit=cuit_clean,
            razon_social=nuevo.razon_social,
            cuenta_contable=nuevo.cuenta_contable,
            fuente="padron",
            guardado=True,
        )

    # Nivel 3: sin datos — retorna shell para asignación manual
    return schemas.ImputacionCuitResponse(
        cuit=cuit_clean,
        razon_social=None,
        cuenta_contable=None,
        fuente="no_encontrado",
        guardado=False,
    )


# ─── CRUD Maestro de Proveedores ─────────────────────────────────────────────

@router.get("/proveedores", response_model=List[schemas.MaestroProveedorOut])
def listar_proveedores(
    q: Optional[str] = None,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Lista todos los proveedores del maestro. Soporta búsqueda por CUIT o razón social."""
    query = db.query(models.MaestroProveedor)
    if activo is not None:
        query = query.filter(models.MaestroProveedor.activo == activo)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            models.MaestroProveedor.cuit.like(like)
            | models.MaestroProveedor.razon_social.ilike(like)
        )
    return query.order_by(models.MaestroProveedor.razon_social).all()


@router.post(
    "/proveedores",
    response_model=schemas.MaestroProveedorOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_proveedor(
    data: schemas.MaestroProveedorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Crea un proveedor en el maestro (alta manual)."""
    cuit_clean = data.cuit.strip().replace("-", "").replace(" ", "")
    existente = (
        db.query(models.MaestroProveedor)
        .filter(models.MaestroProveedor.cuit == cuit_clean)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un proveedor con CUIT {cuit_clean}",
        )
    proveedor = models.MaestroProveedor(
        **{**data.model_dump(), "cuit": cuit_clean}
    )
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.put("/proveedores/{proveedor_id}", response_model=schemas.MaestroProveedorOut)
def actualizar_proveedor(
    proveedor_id: int,
    data: schemas.MaestroProveedorUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Actualiza razón social, cuenta contable, fuente o activo de un proveedor."""
    proveedor = db.query(models.MaestroProveedor).filter(
        models.MaestroProveedor.id == proveedor_id
    ).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(proveedor, field, value)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.delete("/proveedores/{proveedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Elimina (baja física) un proveedor del maestro."""
    proveedor = db.query(models.MaestroProveedor).filter(
        models.MaestroProveedor.id == proveedor_id
    ).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    db.delete(proveedor)
    db.commit()
