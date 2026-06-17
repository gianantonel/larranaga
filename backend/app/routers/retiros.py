from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas
from ..database import get_db
from ..services import billetes as billetes_service
from .auth import get_current_user

router = APIRouter(prefix="/retiros", tags=["retiros"])


def _build_retiro_out(retiro: models.RetiroSocio) -> schemas.RetiroSocioOut:
    out = schemas.RetiroSocioOut.model_validate(retiro)
    out.profesional_nombre = retiro.profesional.nombre if retiro.profesional else None
    return out


def _total_retirado_anio(db: Session, profesional_id: int, anio: int) -> float:
    first = date(anio, 1, 1)
    last = date(anio, 12, 31)
    total = db.query(func.sum(models.RetiroSocio.importe)).filter(
        models.RetiroSocio.profesional_id == profesional_id,
        models.RetiroSocio.fecha >= first,
        models.RetiroSocio.fecha <= last,
    ).scalar()
    return round(total or 0.0, 2)


# ─── POST /retiros/ ───────────────────────────────────────────────────────────

@router.post("/", response_model=schemas.RetiroImpactoOut, status_code=201)
def crear_retiro(
    data: schemas.RetiroSocioCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Registra un retiro de un socio con impacto automático en tesorería y billetes.

    Efectos:
    - Crea MovimientoTesoreria egreso categoria=retiro_socio
    - Crea RetiroSocio con FK a la tesorería
    - Si forma_pago='efectivo' y se proveen billetes, valida suma y descuenta stock
    """
    # ── Validaciones ─────────────────────────────────────────────────────────
    profesional = db.get(models.Profesional, data.profesional_id)
    if not profesional:
        raise HTTPException(404, "Profesional no encontrado")
    if profesional.tipo != models.TipoProfesional.socio:
        raise HTTPException(
            status_code=400,
            detail=f"El profesional '{profesional.nombre}' no es socio (tipo={profesional.tipo.value}). Solo socios pueden registrar retiros.",
        )

    if data.forma_pago not in ("efectivo", "transferencia"):
        raise HTTPException(400, "forma_pago debe ser 'efectivo' o 'transferencia'")

    if data.importe <= 0:
        raise HTTPException(400, "El importe debe ser mayor a 0")

    # ── Validación de billetes (si efectivo) ──────────────────────────────────
    if data.forma_pago == "efectivo" and data.billetes:
        total_billetes = sum(int(denom) * qty for denom, qty in data.billetes.items())
        if abs(total_billetes - data.importe) > 1:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "La suma de billetes no coincide con el importe",
                    "total_billetes": total_billetes,
                    "importe": data.importe,
                    "diferencia": total_billetes - data.importe,
                },
            )

    fecha_retiro = data.fecha or date.today()
    concepto = f"Retiro socio — {profesional.nombre}"
    if data.notas:
        concepto += f" ({data.notas[:80]})"

    # ── Crear MovimientoTesoreria ─────────────────────────────────────────────
    mov_tes = models.MovimientoTesoreria(
        fecha=fecha_retiro,
        tipo=models.TipoMovTesoreria.egreso,
        categoria=models.CategoriaTesoreria.retiro_socio,
        importe=data.importe,
        forma_pago=models.FormaPago(data.forma_pago),
        banco=data.banco_origen if data.forma_pago == "transferencia" else None,
        concepto=concepto,
        profesional_id=profesional.id,
        notas=data.notas,
    )
    db.add(mov_tes)
    db.flush()

    # ── Crear RetiroSocio ─────────────────────────────────────────────────────
    retiro = models.RetiroSocio(
        profesional_id=profesional.id,
        fecha=fecha_retiro,
        importe=data.importe,
        forma_pago=models.FormaPago(data.forma_pago),
        banco_origen=data.banco_origen if data.forma_pago == "transferencia" else None,
        conciliado=False,
        movimiento_tesoreria_id=mov_tes.id,
        notas=data.notas,
    )
    db.add(retiro)
    db.flush()

    # ── Descontar billetes (si efectivo) ──────────────────────────────────────
    if data.forma_pago == "efectivo" and data.billetes:
        for denom_str, qty in data.billetes.items():
            if qty > 0:
                billetes_service.aplicar_movimiento(
                    db,
                    denominacion=int(denom_str),
                    delta=-qty,                          # salida
                    concepto=f"retiro_socio_{retiro.id}",
                    pago_id=None,
                )

    db.commit()
    db.refresh(retiro)
    db.refresh(mov_tes)

    total_anio = _total_retirado_anio(db, profesional.id, fecha_retiro.year)

    return schemas.RetiroImpactoOut(
        retiro=_build_retiro_out(retiro),
        movimiento_tesoreria_id=mov_tes.id,
        total_retirado_socio_anio=total_anio,
    )


# ─── GET /retiros/ ────────────────────────────────────────────────────────────

@router.get("/", response_model=list[schemas.RetiroSocioOut])
def listar_retiros(
    profesional_id: Optional[int] = Query(None),
    period: Optional[str] = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Lista retiros de socios. Filtra por profesional y/o período (YYYY-MM)."""
    import calendar
    q = db.query(models.RetiroSocio)
    if profesional_id:
        q = q.filter(models.RetiroSocio.profesional_id == profesional_id)
    if period:
        try:
            year, month = int(period[:4]), int(period[5:7])
            first = date(year, month, 1)
            last = date(year, month, calendar.monthrange(year, month)[1])
            q = q.filter(models.RetiroSocio.fecha >= first, models.RetiroSocio.fecha <= last)
        except (ValueError, IndexError):
            raise HTTPException(400, "Formato de period inválido (esperado YYYY-MM)")

    return [_build_retiro_out(r) for r in q.order_by(models.RetiroSocio.fecha.desc()).all()]


# ─── GET /retiros/{id} ────────────────────────────────────────────────────────

@router.get("/{retiro_id}", response_model=schemas.RetiroSocioOut)
def get_retiro(
    retiro_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    retiro = db.get(models.RetiroSocio, retiro_id)
    if not retiro:
        raise HTTPException(404, "Retiro no encontrado")
    return _build_retiro_out(retiro)
