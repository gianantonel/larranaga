"""F3-04 (R-15): Endpoint de import de extractos bancarios."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

# Hacemos disponible larranaga-accounting-agent como import path
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ACCOUNTING_PKG = _REPO_ROOT / "larranaga-accounting-agent"
if str(_ACCOUNTING_PKG) not in sys.path:
    sys.path.insert(0, str(_ACCOUNTING_PKG))

from src.bancos import PARSERS, get_parser  # type: ignore  # noqa: E402


router = APIRouter(prefix="/conciliacion", tags=["conciliacion"])


VALID_BANCOS = set(PARSERS.keys())


# ─── POST /conciliacion/import-extracto ──────────────────────────────────────

@router.post("/import-extracto", response_model=schemas.ImportExtractoStats, status_code=201)
async def import_extracto(
    banco: str = Form(...),
    periodo: str = Form(..., description="YYYY-MM"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Importa un extracto bancario, parsea sus movimientos y persiste todo."""
    banco_lc = banco.strip().lower()
    if banco_lc not in VALID_BANCOS:
        raise HTTPException(400, f"Banco inválido. Opciones: {sorted(VALID_BANCOS)}")

    if len(periodo) != 7 or periodo[4] != "-":
        raise HTTPException(400, "Periodo debe tener formato YYYY-MM")

    # Persistir el archivo en /tmp para que el parser lo lea
    suffix = Path(file.filename or "extracto.xlsx").suffix or ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        parser = get_parser(banco_lc)
        movs = parser.parse(tmp_path)
    except Exception as e:
        raise HTTPException(422, f"Error parseando extracto: {e}")
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    if not movs:
        raise HTTPException(422, "El extracto no contiene movimientos válidos")

    # Crear cabecera + filas
    extracto = models.ExtractoBancario(
        banco=banco_lc,
        periodo=periodo,
        archivo_nombre=file.filename,
        n_movimientos=len(movs),
        n_conciliados=0,
        n_pendientes=len(movs),
    )
    db.add(extracto)
    db.flush()

    for m in movs:
        db.add(models.MovimientoBancario(
            extracto_id=extracto.id,
            banco=m["banco"],
            fecha=m["fecha"],
            descripcion=m["descripcion"],
            importe=m["importe"],
            tipo=m["tipo"],
            saldo=m.get("saldo"),
            cuit_detectado=m.get("cuit_detectado"),
            conciliado=False,
        ))

    db.commit()
    db.refresh(extracto)

    n_creditos = sum(1 for m in movs if m["tipo"] == "C")
    n_debitos = sum(1 for m in movs if m["tipo"] == "D")
    imp_creditos = sum(m["importe"] for m in movs if m["tipo"] == "C")
    imp_debitos = sum(m["importe"] for m in movs if m["tipo"] == "D")

    return schemas.ImportExtractoStats(
        extracto=schemas.ExtractoBancarioOut.model_validate(extracto),
        n_creditos=n_creditos,
        n_debitos=n_debitos,
        importe_total_creditos=round(imp_creditos, 2),
        importe_total_debitos=round(imp_debitos, 2),
    )


# ─── GET /conciliacion/extractos ─────────────────────────────────────────────

@router.get("/extractos", response_model=list[schemas.ExtractoBancarioOut])
def listar_extractos(
    banco: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    q = db.query(models.ExtractoBancario)
    if banco:
        q = q.filter(models.ExtractoBancario.banco == banco.lower())
    if periodo:
        q = q.filter(models.ExtractoBancario.periodo == periodo)
    return q.order_by(models.ExtractoBancario.fecha_importacion.desc()).all()


# ─── GET /conciliacion/extracto/{id}/movimientos ─────────────────────────────

@router.get("/extracto/{extracto_id}/movimientos", response_model=list[schemas.MovimientoBancarioOut])
def listar_movimientos(
    extracto_id: int,
    solo_pendientes: bool = Query(False),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    extracto = db.get(models.ExtractoBancario, extracto_id)
    if not extracto:
        raise HTTPException(404, "Extracto no encontrado")

    q = db.query(models.MovimientoBancario).filter_by(extracto_id=extracto_id)
    if solo_pendientes:
        q = q.filter(models.MovimientoBancario.conciliado.is_(False))
    return q.order_by(models.MovimientoBancario.fecha).all()
