from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/facturas", tags=["facturas"])


@router.get("/", response_model=List[schemas.InvoiceOut])
def list_invoices(
    client_id: Optional[int] = None,
    invoice_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=500, le=2000),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Invoice)
    if client_id:
        query = query.filter(models.Invoice.client_id == client_id)
    if invoice_type:
        query = query.filter(models.Invoice.invoice_type == invoice_type)
    if from_date:
        query = query.filter(models.Invoice.date >= from_date)
    if to_date:
        query = query.filter(models.Invoice.date <= to_date)

    invoices = query.order_by(models.Invoice.date.desc()).limit(limit).all()

    # Batch load clients and collaborators — 2 queries total instead of 2×N
    client_ids = {inv.client_id for inv in invoices}
    collab_ids = {inv.collaborator_id for inv in invoices if inv.collaborator_id}

    clients_map = {
        c.id: c for c in db.query(models.Client).filter(models.Client.id.in_(client_ids)).all()
    } if client_ids else {}
    collabs_map = {
        u.id: u for u in db.query(models.User).filter(models.User.id.in_(collab_ids)).all()
    } if collab_ids else {}

    return [_build_invoice_out(inv, clients_map, collabs_map) for inv in invoices]


@router.get("/{invoice_id}", response_model=schemas.InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    inv = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    clients_map = {}
    collabs_map = {}
    if inv.client_id:
        c = db.query(models.Client).filter(models.Client.id == inv.client_id).first()
        if c:
            clients_map[c.id] = c
    if inv.collaborator_id:
        u = db.query(models.User).filter(models.User.id == inv.collaborator_id).first()
        if u:
            collabs_map[u.id] = u
    return _build_invoice_out(inv, clients_map, collabs_map)


@router.post("/", response_model=schemas.InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: schemas.InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Auto-increment number for that client+tipo+punto_venta
    last = db.query(models.Invoice).filter(
        models.Invoice.client_id == data.client_id,
        models.Invoice.invoice_type == data.invoice_type,
        models.Invoice.punto_venta == data.punto_venta
    ).order_by(models.Invoice.number.desc()).first()
    next_number = (last.number + 1) if last else 1

    import random, string
    cae = "".join(random.choices(string.digits, k=14))

    invoice = models.Invoice(
        **data.model_dump(),
        number=next_number,
        collaborator_id=current_user.id,
        cae=cae,
        status="emitida"
    )
    db.add(invoice)
    db.commit()

    db.add(models.ActionLog(
        user_id=current_user.id,
        client_id=data.client_id,
        action_type="invoice_created",
        description=f"Factura {data.invoice_type} {data.punto_venta:05d}-{next_number:08d} emitida. Total: ${data.total:,.2f}"
    ))
    db.commit()

    clients_map = {}
    collabs_map = {}
    c = db.query(models.Client).filter(models.Client.id == data.client_id).first()
    if c:
        clients_map[c.id] = c
    collabs_map[current_user.id] = current_user

    return _build_invoice_out(invoice, clients_map, collabs_map)


@router.get("/summary/{client_id}")
def get_invoice_summary(
    client_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Invoice).filter(models.Invoice.client_id == client_id)
    if year:
        query = query.filter(models.Invoice.date >= date(year, 1, 1), models.Invoice.date <= date(year, 12, 31))
    invoices = query.all()

    monthly = {}
    for inv in invoices:
        month_key = inv.date.strftime("%Y-%m")
        if month_key not in monthly:
            monthly[month_key] = {"total": 0, "count": 0, "iva": 0}
        monthly[month_key]["total"] += inv.total
        monthly[month_key]["count"] += 1
        monthly[month_key]["iva"] += inv.iva_21 + inv.iva_105

    return {
        "client_id": client_id,
        "total_invoices": len(invoices),
        "total_amount": sum(i.total for i in invoices),
        "total_iva": sum(i.iva_21 + i.iva_105 for i in invoices),
        "by_type": {
            t.value: {"count": sum(1 for i in invoices if i.invoice_type == t),
                       "total": sum(i.total for i in invoices if i.invoice_type == t)}
            for t in models.InvoiceType
        },
        "by_month": monthly
    }


def _build_invoice_out(
    inv: models.Invoice,
    clients_map: dict,
    collabs_map: dict,
) -> schemas.InvoiceOut:
    out = schemas.InvoiceOut.model_validate(inv)
    client = clients_map.get(inv.client_id)
    out.client_name = client.name if client else None
    if inv.collaborator_id:
        collab = collabs_map.get(inv.collaborator_id)
        out.collaborator_name = collab.name if collab else None
    return out
