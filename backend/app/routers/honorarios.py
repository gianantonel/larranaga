from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, require_admin
from .clients import _format_client_out

router = APIRouter(prefix="/honorarios", tags=["honorarios"])


# ─── Helper ───────────────────────────────────────────────────────────────────

def _calcular_importe(client: models.Client, db: Session) -> tuple[float, Optional[float]]:
    """Devuelve (importe, precio_producto_snapshot). Lanza 400 si no está configurado."""
    if not client.tipo_honorario:
        raise HTTPException(400, f"Cliente '{client.name}' no tiene tipo_honorario configurado")

    if client.tipo_honorario == models.TipoHonorario.fijo:
        if client.importe_honorario is None:
            raise HTTPException(400, f"Cliente '{client.name}': importe_honorario no configurado")
        return client.importe_honorario, None

    if client.tipo_honorario == models.TipoHonorario.producto:
        if not client.producto_ref_id or client.cantidad_unidades is None:
            raise HTTPException(400, f"Cliente '{client.name}': producto_ref_id o cantidad_unidades no configurados")
        prod = db.get(models.ProductoReferencia, client.producto_ref_id)
        if not prod:
            raise HTTPException(400, f"Producto de referencia id={client.producto_ref_id} no encontrado")
        return round(client.cantidad_unidades * prod.precio_vigente, 2), prod.precio_vigente

    raise HTTPException(400, f"tipo_honorario desconocido: {client.tipo_honorario}")


# ─── Productos de referencia ──────────────────────────────────────────────────

@router.get("/productos-referencia", response_model=List[schemas.ProductoReferenciaOut])
def list_productos(db: Session = Depends(get_db),
                   _: models.User = Depends(get_current_user)):
    return db.query(models.ProductoReferencia).order_by(models.ProductoReferencia.nombre).all()


@router.post("/productos-referencia", response_model=schemas.ProductoReferenciaOut, status_code=201)
def create_producto(data: schemas.ProductoReferenciaCreate, db: Session = Depends(get_db),
                    _: models.User = Depends(require_admin)):
    prod = models.ProductoReferencia(**data.model_dump())
    db.add(prod)
    db.flush()
    db.add(models.HistorialPrecioProducto(
        producto_id=prod.id, precio=prod.precio_vigente, vigente_desde=date.today()
    ))
    db.commit()
    db.refresh(prod)
    return prod


@router.put("/productos-referencia/{id}", response_model=schemas.ProductoReferenciaOut)
def update_producto(id: int, data: schemas.ProductoReferenciaUpdate, db: Session = Depends(get_db),
                    _: models.User = Depends(require_admin)):
    prod = db.get(models.ProductoReferencia, id)
    if not prod:
        raise HTTPException(404, "Producto no encontrado")

    if data.precio_vigente is not None and data.precio_vigente != prod.precio_vigente:
        db.add(models.HistorialPrecioProducto(
            producto_id=prod.id, precio=data.precio_vigente, vigente_desde=date.today()
        ))

    for field, val in data.model_dump(exclude_none=True).items():
        setattr(prod, field, val)

    db.commit()
    db.refresh(prod)
    return prod


# ─── Configuración de honorario por cliente ───────────────────────────────────

@router.put("/clientes/{client_id}/configurar", response_model=schemas.ClientOut)
def configurar_honorario(client_id: int, data: schemas.ClientHonorarioUpdate,
                         db: Session = Depends(get_db),
                         _: models.User = Depends(require_admin)):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    for field, val in data.model_dump(exclude_none=True).items():
        setattr(client, field, val)

    db.commit()
    db.refresh(client)

    return _format_client_out(client, db)


# ─── Honorarios calculados ────────────────────────────────────────────────────

@router.get("/", response_model=List[schemas.HonorarioOut])
def list_honorarios(client_id: Optional[int] = None, period: Optional[str] = None,
                    db: Session = Depends(get_db),
                    _: models.User = Depends(get_current_user)):
    q = db.query(models.Honorario)
    if client_id:
        q = q.filter(models.Honorario.client_id == client_id)
    if period:
        q = q.filter(models.Honorario.period == period)

    result = []
    for h in q.order_by(models.Honorario.period.desc(), models.Honorario.client_id).all():
        out = schemas.HonorarioOut.model_validate(h)
        out.client_name = h.client.name if h.client else None
        result.append(out)
    return result


@router.post("/calcular/{client_id}/{period}", response_model=schemas.HonorarioOut, status_code=201)
def calcular_honorario(client_id: int, period: str, db: Session = Depends(get_db),
                       _: models.User = Depends(require_admin)):
    """Genera (o regenera) el honorario de un cliente para el período YYYY-MM."""
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    importe, precio_snapshot = _calcular_importe(client, db)

    existing = db.query(models.Honorario).filter(
        models.Honorario.client_id == client_id,
        models.Honorario.period == period
    ).first()
    if existing:
        db.delete(existing)
        db.flush()

    h = models.Honorario(
        client_id=client_id,
        period=period,
        importe=importe,
        tipo=client.tipo_honorario.value,
        precio_producto_snapshot=precio_snapshot,
    )
    db.add(h)
    db.commit()
    db.refresh(h)

    out = schemas.HonorarioOut.model_validate(h)
    out.client_name = client.name
    return out


@router.post("/calcular-periodo/{period}", response_model=List[schemas.HonorarioOut])
def calcular_periodo(period: str, db: Session = Depends(get_db),
                     _: models.User = Depends(require_admin)):
    """Genera honorarios de todos los clientes activos configurados para el período."""
    clientes = db.query(models.Client).filter(
        models.Client.is_active == True,
        models.Client.tipo_honorario.isnot(None),
    ).all()

    generados = []
    for client in clientes:
        try:
            importe, precio_snapshot = _calcular_importe(client, db)
        except HTTPException:
            continue

        existing = db.query(models.Honorario).filter(
            models.Honorario.client_id == client.id,
            models.Honorario.period == period,
        ).first()
        if existing:
            db.delete(existing)
            db.flush()

        h = models.Honorario(
            client_id=client.id,
            period=period,
            importe=importe,
            tipo=client.tipo_honorario.value,
            precio_producto_snapshot=precio_snapshot,
        )
        db.add(h)
        db.flush()
        generados.append((h, client.name))

    db.commit()

    result = []
    for h, client_name in generados:
        db.refresh(h)
        out = schemas.HonorarioOut.model_validate(h)
        out.client_name = client_name
        result.append(out)
    return result


# ─── Actualización cuatrimestral ─────────────────────────────────────────────

@router.get("/actualizacion-cuatrimestral/preview",
            response_model=schemas.ActualizacionCuatrimestralPreview)
def preview_actualizacion(indice_pct: float = Query(..., gt=0, description="Índice en %, ej: 10 para +10%"),
                          db: Session = Depends(get_db),
                          _: models.User = Depends(require_admin)):
    clientes = db.query(models.Client).filter(
        models.Client.is_active == True,
        models.Client.tipo_honorario.isnot(None),
    ).order_by(models.Client.name).all()

    items = []
    for c in clientes:
        if c.tipo_honorario == models.TipoHonorario.fijo:
            actual = c.importe_honorario or 0.0
            propuesto = round(actual * (1 + indice_pct / 100), 2)
            items.append(schemas.ClienteActualizacionItem(
                client_id=c.id, client_name=c.name,
                tipo_honorario="fijo",
                importe_actual=actual, importe_propuesto=propuesto,
                delta_pct=indice_pct, aplica_indice=True,
            ))
        else:
            items.append(schemas.ClienteActualizacionItem(
                client_id=c.id, client_name=c.name,
                tipo_honorario="producto",
                aplica_indice=False,
            ))

    return schemas.ActualizacionCuatrimestralPreview(indice_pct=indice_pct, clientes=items)


@router.post("/actualizacion-cuatrimestral/aplicar")
def aplicar_actualizacion(data: schemas.ActualizacionCuatrimestralApply,
                          db: Session = Depends(get_db),
                          _: models.User = Depends(require_admin)):
    """Aplica la actualización cuatrimestral a los clientes confirmados."""
    actualizados = []
    for item in data.actualizaciones:
        if not item.confirmar:
            continue
        client = db.get(models.Client, item.client_id)
        if not client or client.tipo_honorario != models.TipoHonorario.fijo:
            continue
        anterior = client.importe_honorario
        client.importe_honorario = item.nuevo_importe
        actualizados.append({
            "client_id": item.client_id,
            "client_name": client.name,
            "importe_anterior": anterior,
            "importe_nuevo": item.nuevo_importe,
        })

    db.commit()
    return {
        "indice_pct": data.indice_pct,
        "vigente_desde": data.vigente_desde,
        "actualizados": len(actualizados),
        "detalle": actualizados,
    }
