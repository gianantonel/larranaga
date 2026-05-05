from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from .. import models, schemas
from ..database import get_db
from ..services import flujo_fondos as ff_service
from .auth import get_current_user

router = APIRouter(prefix="/flujo-fondos", tags=["flujo-fondos"])


@router.get("/verificar-consistencia", response_model=schemas.ConsistenciaOut)
def verificar_consistencia(
    periodo: str = Query(..., description="Período YYYY-MM", min_length=7, max_length=7),
    tolerancia: float = Query(0.10, ge=0, description="Tolerancia en pesos (default 0.10)"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Verifica que el saldo CC al cierre coincida con la proyección
    (deuda_inicio + devengado - cobrado) para cada cliente.
    """
    try:
        return ff_service.verificar_consistencia(db, periodo, tolerancia=tolerancia)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/anual", response_model=schemas.FlujoFondosAnualOut)
def get_flujo_fondos_anual(
    year: int = Query(..., description="Año YYYY", ge=1900, le=2100),
    profesional_id: Optional[int] = Query(None, description="Filtrar clientes por profesional a cargo"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Flujo de fondos anual pivoteado: una fila por cliente con columnas Ene-Dic.

    Cada celda devuelve devengado, cobrado y deuda_fin del mes.
    """
    try:
        return ff_service.flujo_fondos_anual(db, year, profesional_id=profesional_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/", response_model=schemas.FlujoFondosMensualOut)
def get_flujo_fondos_mensual(
    periodo: str = Query(..., description="Período YYYY-MM", min_length=7, max_length=7),
    profesional_id: Optional[int] = Query(None, description="Filtrar clientes por profesional a cargo"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Flujo de fondos del estudio para el período YYYY-MM.

    Por cliente devuelve: deuda_inicio, honorario_devengado, cobrado, deuda_fin.
    Convención: deuda > 0 = cliente debe; deuda < 0 = cliente tiene saldo a favor.
    """
    try:
        return ff_service.flujo_fondos_mensual(db, periodo, profesional_id=profesional_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
