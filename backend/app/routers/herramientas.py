"""
Herramientas IVA — R-01
POST /herramientas/limpiar-libro-iva
  Recibe: client_id + .xlsx de ARCA
  Procesa: corrige tipo B/C y columna L
  Guarda: registro + archivo en tabla limpiezas_iva
  Devuelve: .xlsx corregido como descarga

GET /herramientas/limpiar-libro-iva/historial?client_id=X
  Devuelve: historial de limpiezas del cliente

GET /herramientas/limpiar-libro-iva/{limpieza_id}/descargar
  Devuelve: archivo corregido guardado en BD
"""

import io
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from .auth import get_current_user

# ── Importar módulo R-01 ────────────────────────────────────────────────────
# parents[3] = raíz del repo larranaga (larranaga-accounting-agent vive ahí dentro)
_ROOT  = Path(__file__).resolve().parents[3]
_AGENT = _ROOT / "larranaga-accounting-agent"
if str(_AGENT) not in sys.path:
    sys.path.insert(0, str(_AGENT))

try:
    from src.transformaciones.limpieza_inicial import limpiar_comprobantes_desde_bytes
    _MODULO_OK = True
except ImportError:
    _MODULO_OK = False

router = APIRouter(prefix="/herramientas", tags=["herramientas"])


# ── Schemas de respuesta ────────────────────────────────────────────────────

class LimpiezaOut(BaseModel):
    id:                  int
    client_id:           int
    client_name:         Optional[str]
    user_id:             int
    user_name:           Optional[str]
    nombre_original:     str
    nombre_corregido:    str
    total_filas:         int
    filas_bc_corregidas: int
    created_at:          str

    model_config = {"from_attributes": True}


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/limpiar-libro-iva", response_model=LimpiezaOut)
async def limpiar_libro_iva(
    client_id: int      = Form(...),
    archivo:   UploadFile = File(...),
    db:        Session  = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Procesa el Excel de ARCA y guarda el resultado en la BD."""
    if not _MODULO_OK:
        raise HTTPException(503, "Módulo de limpieza no disponible.")

    # Validar cliente
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    if not archivo.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(400, "El archivo debe ser .xlsx o .xls")

    contenido = await archivo.read()
    if not contenido:
        raise HTTPException(400, "El archivo está vacío")

    # Procesar
    try:
        xlsx_corregido, stats = limpiar_comprobantes_desde_bytes_con_stats(contenido)
    except Exception as e:
        raise HTTPException(422, f"Error al procesar el archivo: {str(e)}")

    stem           = Path(archivo.filename).stem
    nombre_corregido = f"{stem}_corregido.xlsx"

    # Guardar en BD
    limpieza = models.LimpiezaIVA(
        client_id           = client_id,
        user_id             = current_user.id,
        nombre_original     = archivo.filename,
        nombre_corregido    = nombre_corregido,
        archivo_corregido   = xlsx_corregido,
        total_filas         = stats["total"],
        filas_bc_corregidas = stats["tipo_bc"],
    )
    db.add(limpieza)
    db.commit()
    db.refresh(limpieza)

    # Log de acción
    db.add(models.ActionLog(
        user_id     = current_user.id,
        client_id   = client_id,
        action_type = "limpieza_iva",
        description = (
            f"R-01 Limpieza IVA: {archivo.filename} → "
            f"{stats['total']} filas, {stats['tipo_bc']} B/C corregidas"
        ),
    ))
    db.commit()

    return _build_out(limpieza)


@router.get("/limpiar-libro-iva/historial", response_model=List[LimpiezaOut])
def historial_limpiezas(
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Devuelve el historial de archivos procesados (opcionalmente filtrado por cliente)."""
    q = db.query(models.LimpiezaIVA).order_by(models.LimpiezaIVA.created_at.desc())
    if client_id:
        q = q.filter(models.LimpiezaIVA.client_id == client_id)
    return [_build_out(l) for l in q.limit(50).all()]


@router.get("/limpiar-libro-iva/{limpieza_id}/descargar")
def descargar_limpieza(
    limpieza_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Descarga el archivo corregido guardado en la BD."""
    limpieza = db.query(models.LimpiezaIVA).filter(models.LimpiezaIVA.id == limpieza_id).first()
    if not limpieza:
        raise HTTPException(404, "Registro no encontrado")

    return StreamingResponse(
        io.BytesIO(limpieza.archivo_corregido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{limpieza.nombre_corregido}"'},
    )


# ── Helpers ─────────────────────────────────────────────────────────────────

def limpiar_comprobantes_desde_bytes_con_stats(contenido: bytes):
    """Llama al módulo R-01 y devuelve (xlsx_bytes, stats_dict)."""
    import io
    import re
    import pandas as pd
    from src.transformaciones.limpieza_inicial import (
        corregir_tipo_bc, corregir_columna_L, TIPOS_BC,
    )

    df = pd.read_excel(io.BytesIO(contenido), header=1, dtype=str)

    def cod(v):
        m = re.match(r'^\s*(\d+)\s*-', str(v))
        return m.group(1) if m else None

    total      = len(df)
    tipo_bc    = int(df["Tipo"].map(cod).isin(TIPOS_BC).sum()) if "Tipo" in df.columns else 0

    df = corregir_tipo_bc(df)
    df = corregir_columna_L(df)

    out = io.BytesIO()
    df.to_excel(out, index=False)

    return out.getvalue(), {"total": total, "tipo_bc": tipo_bc}


def _build_out(l: models.LimpiezaIVA) -> LimpiezaOut:
    return LimpiezaOut(
        id                  = l.id,
        client_id           = l.client_id,
        client_name         = l.client.name if l.client else None,
        user_id             = l.user_id,
        user_name           = l.user.name if l.user else None,
        nombre_original     = l.nombre_original,
        nombre_corregido    = l.nombre_corregido,
        total_filas         = l.total_filas,
        filas_bc_corregidas = l.filas_bc_corregidas,
        created_at          = l.created_at.isoformat() if l.created_at else "",
    )
