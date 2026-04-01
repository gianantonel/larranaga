from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/iva", tags=["iva"])


@router.get("/", response_model=List[schemas.IVARecordOut])
def list_iva_records(
    client_id: Optional[int] = None,
    period: Optional[str] = None,
    filed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.IVARecord)
    if client_id:
        query = query.filter(models.IVARecord.client_id == client_id)
    if period:
        query = query.filter(models.IVARecord.period == period)
    if filed is not None:
        query = query.filter(models.IVARecord.filed == filed)

    records = query.options(
        selectinload(models.IVARecord.client)
    ).order_by(models.IVARecord.period.desc()).all()
    return [_build_iva_out(r) for r in records]


@router.get("/{record_id}", response_model=schemas.IVARecordOut)
def get_iva_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    record = db.query(models.IVARecord).options(
        selectinload(models.IVARecord.client)
    ).filter(models.IVARecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro IVA no encontrado")
    return _build_iva_out(record)


@router.post("/", response_model=schemas.IVARecordOut, status_code=status.HTTP_201_CREATED)
def create_iva_record(
    data: schemas.IVARecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    existing = db.query(models.IVARecord).filter(
        models.IVARecord.client_id == data.client_id,
        models.IVARecord.period == data.period
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un registro IVA para ese cliente y período")

    saldo = (data.debito_fiscal - data.credito_fiscal) - data.saldo_a_favor_anterior
    record = models.IVARecord(
        **data.model_dump(),
        saldo=saldo
    )
    db.add(record)
    db.commit()
    record = db.query(models.IVARecord).options(
        selectinload(models.IVARecord.client)
    ).filter(models.IVARecord.id == record.id).one()
    return _build_iva_out(record)


@router.put("/{record_id}", response_model=schemas.IVARecordOut)
def update_iva_record(
    record_id: int,
    data: schemas.IVARecordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    record = db.query(models.IVARecord).filter(models.IVARecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro IVA no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(record, field, value)

    record.saldo = (record.debito_fiscal - record.credito_fiscal) - record.saldo_a_favor_anterior
    db.commit()
    record = db.query(models.IVARecord).options(
        selectinload(models.IVARecord.client)
    ).filter(models.IVARecord.id == record.id).one()
    return _build_iva_out(record)


@router.post("/{record_id}/file")
def file_iva(
    record_id: int,
    vep_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    record = db.query(models.IVARecord).filter(models.IVARecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro IVA no encontrado")

    record.filed = True
    record.filed_at = datetime.utcnow()
    if vep_number:
        record.vep_number = vep_number
    db.commit()

    db.add(models.ActionLog(
        user_id=current_user.id,
        client_id=record.client_id,
        action_type="iva_filed",
        description=f"DDJJ IVA presentada: período {record.period}" + (f" VEP: {vep_number}" if vep_number else "")
    ))
    db.commit()
    return {"message": "DDJJ IVA presentada correctamente"}


@router.get("/summary/{client_id}")
def get_iva_summary(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    records = db.query(models.IVARecord).options(
        selectinload(models.IVARecord.client)
    ).filter(
        models.IVARecord.client_id == client_id
    ).order_by(models.IVARecord.period).all()

    return {
        "client_id": client_id,
        "total_records": len(records),
        "filed_count": sum(1 for r in records if r.filed),
        "pending_count": sum(1 for r in records if not r.filed),
        "total_debito": sum(r.debito_fiscal for r in records),
        "total_credito": sum(r.credito_fiscal for r in records),
        "total_saldo": sum(r.saldo for r in records),
        "records": [_build_iva_out(r) for r in records]
    }


def _build_iva_out(record: models.IVARecord) -> schemas.IVARecordOut:
    out = schemas.IVARecordOut.model_validate(record)
    out.client_name = record.client.name if record.client else None
    return out
