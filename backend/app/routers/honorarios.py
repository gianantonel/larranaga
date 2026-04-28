"""R-03 — Gestión de Productos de Referencia y cálculo de Honorarios."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from .. import models, schemas
from ..database import get_db
from ..routers.auth import get_current_user

router = APIRouter(prefix="/honorarios", tags=["honorarios"])


# ─── Productos de Referencia ──────────────────────────────────────────────────

@router.get("/productos", response_model=List[schemas.ProductoReferenciaOut])
def list_productos(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    q = db.query(models.ProductoReferencia)
    if activo is not None:
        q = q.filter(models.ProductoReferencia.activo == activo)
    return q.order_by(models.ProductoReferencia.nombre).all()


@router.post("/productos", response_model=schemas.ProductoReferenciaOut, status_code=status.HTTP_201_CREATED)
def create_producto(
    data: schemas.ProductoReferenciaCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    prod = models.ProductoReferencia(**data.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@router.patch("/productos/{prod_id}", response_model=schemas.ProductoReferenciaOut)
def update_producto(
    prod_id: int,
    data: schemas.ProductoReferenciaUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    prod = db.query(models.ProductoReferencia).filter(models.ProductoReferencia.id == prod_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(prod, k, v)
    db.commit()
    db.refresh(prod)
    return prod


# ─── Configuración de honorario por cliente ───────────────────────────────────

@router.patch("/clientes/{client_id}/config", response_model=schemas.HonorarioOut)
def update_client_honorario_config(
    client_id: int,
    data: schemas.ClientHonorarioUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Actualiza el tipo y parámetros de honorario de un cliente."""
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(client, k, v)
    db.commit()
    db.refresh(client)
    # Return a synthetic HonorarioOut showing current config
    importe = _calcular_importe(client, db)
    return schemas.HonorarioOut(
        id=0,
        client_id=client.id,
        client_name=client.name,
        periodo="config",
        importe=importe,
        estado="config",
        created_at=client.created_at,
    )


def _calcular_importe(client: models.Client, db: Session) -> float:
    """Calcula el importe de honorario según el tipo configurado en el cliente."""
    if client.tipo_honorario == "fijo":
        return client.importe_honorario or 0.0
    if client.tipo_honorario == "producto" and client.producto_ref_id:
        prod = db.query(models.ProductoReferencia).filter(
            models.ProductoReferencia.id == client.producto_ref_id
        ).first()
        if prod:
            return (client.cantidad_unidades or 0) * prod.precio_vigente
    return 0.0


# ─── Calcular / Generar honorarios por período ────────────────────────────────

@router.post("/calcular/{periodo}", response_model=List[schemas.HonorarioOut])
def calcular_honorarios_periodo(
    periodo: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Genera (o actualiza) los registros de Honorario para todos los clientes activos
    con honorario configurado en el período indicado (YYYY-MM).
    Si ya existe para un cliente/período, lo actualiza (re-calcula).
    """
    if current_user.role not in (models.UserRole.super_admin, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="Solo administradores")

    clientes = db.query(models.Client).filter(models.Client.is_active == True).all()
    resultado = []

    for client in clientes:
        if not client.tipo_honorario or (client.importe_honorario == 0 and client.tipo_honorario == "fijo"):
            continue  # Sin honorario configurado
        importe = _calcular_importe(client, db)
        if importe == 0:
            continue

        existing = (
            db.query(models.Honorario)
            .filter(models.Honorario.client_id == client.id, models.Honorario.periodo == periodo)
            .first()
        )
        if existing:
            existing.importe = importe
            db.flush()
            resultado.append(existing)
        else:
            hon = models.Honorario(client_id=client.id, periodo=periodo, importe=importe)
            db.add(hon)
            db.flush()
            resultado.append(hon)

        # Registrar movimiento en CC si no existe ya el cargo de honorarios para ese período
        cc_existing = (
            db.query(models.MovimientoCuentaCorriente)
            .filter(
                models.MovimientoCuentaCorriente.client_id == client.id,
                models.MovimientoCuentaCorriente.tipo == "honorario",
                models.MovimientoCuentaCorriente.periodo_honorario == periodo,
            )
            .first()
        )
        if not cc_existing:
            year, month = periodo.split("-")
            from datetime import date
            fecha = date(int(year), int(month), 1)
            mov = models.MovimientoCuentaCorriente(
                client_id=client.id,
                tipo="honorario",
                monto=importe,
                concepto=f"HONORARIOS {periodo}",
                fecha=fecha,
                periodo_honorario=periodo,
            )
            db.add(mov)

    db.commit()

    # Refresh y devolver
    for h in resultado:
        db.refresh(h)

    out = []
    for h in resultado:
        item = schemas.HonorarioOut.model_validate(h)
        if h.client:
            item.client_name = h.client.name
        out.append(item)
    return out


@router.get("/periodo/{periodo}", response_model=List[schemas.HonorarioOut])
def get_honorarios_periodo(
    periodo: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    hons = (
        db.query(models.Honorario)
        .filter(models.Honorario.periodo == periodo)
        .all()
    )
    out = []
    for h in hons:
        item = schemas.HonorarioOut.model_validate(h)
        if h.client:
            item.client_name = h.client.name
        out.append(item)
    return out


@router.get("/cliente/{client_id}", response_model=List[schemas.HonorarioOut])
def get_honorarios_cliente(
    client_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    hons = (
        db.query(models.Honorario)
        .filter(models.Honorario.client_id == client_id)
        .order_by(models.Honorario.periodo.desc())
        .all()
    )
    out = []
    for h in hons:
        item = schemas.HonorarioOut.model_validate(h)
        item.client_name = client.name
        out.append(item)
    return out


@router.get("/resumen/clientes", response_model=List[dict])
def get_resumen_clientes(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Lista todos los clientes activos con su configuración de honorario actual."""
    clientes = db.query(models.Client).filter(models.Client.is_active == True).all()
    result = []
    for c in clientes:
        importe = _calcular_importe(c, db)
        prod_nombre = None
        if c.producto_ref_id and c.tipo_honorario == "producto":
            prod = db.query(models.ProductoReferencia).filter(
                models.ProductoReferencia.id == c.producto_ref_id
            ).first()
            if prod:
                prod_nombre = prod.nombre
        prof_nombre = None
        if c.profesional_id:
            prof = db.query(models.Profesional).filter(
                models.Profesional.id == c.profesional_id
            ).first()
            if prof:
                prof_nombre = f"{prof.nombre} {prof.apellido or ''}".strip()
        result.append({
            "client_id": c.id,
            "client_name": c.name,
            "cuit": c.cuit,
            "tipo_honorario": c.tipo_honorario,
            "importe_honorario": c.importe_honorario,
            "cantidad_unidades": c.cantidad_unidades,
            "producto_ref_id": c.producto_ref_id,
            "producto_nombre": prod_nombre,
            "importe_calculado": importe,
            "profesional_id": c.profesional_id,
            "profesional_nombre": prof_nombre,
        })
    return result
