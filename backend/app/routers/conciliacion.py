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

# Hacemos disponible larranaga-accounting-agent como import path.
# Busca el agent en dos ubicaciones (igual que herramientas.py):
#   1) Dev local: <repo_root>/larranaga-accounting-agent  (parents[3])
#   2) Producción Docker: backend/larranaga-accounting-agent (parents[2] = /app)
_HERE = Path(__file__).resolve()
for _candidate in (
    _HERE.parents[3] / "larranaga-accounting-agent",  # dev local
    _HERE.parents[2] / "larranaga-accounting-agent",  # docker / vendor
):
    if _candidate.is_dir() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
        break

# Import defensivo: si el agente no está disponible (p. ej. vendor incompleto),
# degradamos en vez de tumbar TODA la app al importar este router (causó un 502
# global en producción). Los endpoints responden 400 con la lista vacía de bancos.
try:
    from src.bancos import PARSERS, get_parser  # type: ignore  # noqa: E402
except ImportError:  # pragma: no cover
    PARSERS = {}
    get_parser = None


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


# ─── F3-06: POST /conciliacion/{extracto_id}/run-matching ────────────────────

from ..services import conciliacion as matching_service  # noqa: E402


@router.post("/{extracto_id}/run-matching", response_model=schemas.MatchingRunOut)
def run_matching(
    extracto_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Ejecuta el algoritmo de matching automático sobre el extracto.

    Marca los movimientos matcheados como conciliados y actualiza los contadores.
    """
    try:
        result = matching_service.correr_matching(db, extracto_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


# ─── F3-07: POST /conciliacion/movimiento/{id}/match-manual ──────────────────

@router.post("/movimiento/{movimiento_id}/match-manual", response_model=schemas.MovimientoBancarioOut)
def match_manual(
    movimiento_id: int,
    data: schemas.MatchManualIn,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """El operador asigna manualmente un movimiento bancario a un pago existente."""
    mov = db.get(models.MovimientoBancario, movimiento_id)
    if not mov:
        raise HTTPException(404, "Movimiento bancario no encontrado")

    pago = db.get(models.Pago, data.pago_id)
    if not pago:
        raise HTTPException(404, "Pago no encontrado")

    # Verificar que el pago no esté ya matcheado a otro movimiento
    otro = db.query(models.MovimientoBancario).filter(
        models.MovimientoBancario.pago_id == data.pago_id,
        models.MovimientoBancario.id != movimiento_id,
        models.MovimientoBancario.conciliado.is_(True),
    ).first()
    if otro:
        raise HTTPException(409, f"Ese pago ya está conciliado con el movimiento {otro.id}")

    mov.pago_id = data.pago_id
    mov.conciliado = True
    mov.notas = data.nota or "match manual"

    # Actualizar contadores del extracto
    extracto = db.get(models.ExtractoBancario, mov.extracto_id)
    if extracto:
        extracto.n_conciliados = (
            db.query(models.MovimientoBancario)
            .filter_by(extracto_id=mov.extracto_id, conciliado=True)
            .count()
        )
        extracto.n_pendientes = extracto.n_movimientos - extracto.n_conciliados

    db.commit()
    db.refresh(mov)
    return mov


# ─── GET /conciliacion/movimiento/{id}/sugerencias ───────────────────────────

@router.get("/movimiento/{movimiento_id}/sugerencias", response_model=list[schemas.CandidatoSugerido])
def sugerencias(
    movimiento_id: int,
    top_n: int = Query(3, ge=1, le=10),
    use_ai: bool = Query(False, description="Si True y ANTHROPIC_API_KEY está seteada, refina con Claude"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Devuelve top N pagos candidatos para conciliar manualmente este movimiento."""
    mov = db.get(models.MovimientoBancario, movimiento_id)
    if not mov:
        raise HTTPException(404, "Movimiento no encontrado")
    if use_ai:
        from ..services import conciliacion_ai
        return conciliacion_ai.sugerir_con_ai(db, movimiento_id, top_n)
    return matching_service.sugerir_candidatos(db, movimiento_id, top_n)


# ─── POST /conciliacion/movimiento/{id}/desconciliar ─────────────────────────

@router.post("/movimiento/{movimiento_id}/desconciliar", response_model=schemas.MovimientoBancarioOut)
def desconciliar(
    movimiento_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Revierte una conciliación (libera el pago para volver a matchear)."""
    mov = db.get(models.MovimientoBancario, movimiento_id)
    if not mov:
        raise HTTPException(404, "Movimiento no encontrado")
    mov.pago_id = None
    mov.conciliado = False
    mov.notas = "desconciliado manual"
    extracto = db.get(models.ExtractoBancario, mov.extracto_id)
    if extracto:
        extracto.n_conciliados = max(0, extracto.n_conciliados - 1)
        extracto.n_pendientes = extracto.n_movimientos - extracto.n_conciliados
    db.commit()
    db.refresh(mov)
    return mov
