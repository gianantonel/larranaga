"""
Herramientas IVA — R-01
POST /herramientas/limpiar-libro-iva
  Recibe: .xlsx de ARCA (Mis Comprobantes Recibidos)
  Devuelve: .xlsx corregido (tipo cambio formateado, B/C con neto/IVA en 0)
"""

import io
import sys
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse

# Agregar larranaga-accounting-agent al path para importar la logica de R-01
_ROOT = Path(__file__).resolve().parents[4]  # sube hasta el worktree
_AGENT = _ROOT / "larranaga-accounting-agent"
if str(_AGENT) not in sys.path:
    sys.path.insert(0, str(_AGENT))

try:
    from src.transformaciones.limpieza_inicial import (
        limpiar_comprobantes_desde_bytes,
    )
    _MODULO_OK = True
except ImportError:
    _MODULO_OK = False

from .auth import get_current_user
from .. import models

router = APIRouter(prefix="/herramientas", tags=["herramientas"])


@router.post("/limpiar-libro-iva")
async def limpiar_libro_iva(
    archivo: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    """
    Sube el Excel 'Mis Comprobantes Recibidos' de ARCA y devuelve
    el archivo corregido listo para importar en Holistor.
    """
    if not archivo.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "El archivo debe ser .xlsx o .xls")

    if not _MODULO_OK:
        raise HTTPException(
            503,
            "Modulo de limpieza no disponible. "
            "Verificar que larranaga-accounting-agent este instalado."
        )

    contenido = await archivo.read()
    if len(contenido) == 0:
        raise HTTPException(400, "El archivo esta vacio")

    try:
        xlsx_corregido = limpiar_comprobantes_desde_bytes(contenido)
    except Exception as e:
        raise HTTPException(422, f"Error al procesar el archivo: {str(e)}")

    nombre_salida = archivo.filename.replace(".xlsx", "_corregido.xlsx").replace(".xls", "_corregido.xlsx")

    return StreamingResponse(
        io.BytesIO(xlsx_corregido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_salida}"'},
    )
