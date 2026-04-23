"""Endpoints para Retenciones y Percepciones (Mis Retenciones ARCA).

Consume la automatizacion `mis-retenciones` de AFIP SDK (via backend/app/afip_sdk/),
clasifica por impuestoRetenido -> codigo Holistor, persiste en DB y expone listado.
"""
from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..afip_sdk.client import load_context
from ..afip_sdk.automations import run_automation, save_raw
from ..afip_sdk.retenciones import IMPUESTO_TO_HOLISTOR, classify_regimen, extract_records


router = APIRouter(prefix="/retenciones", tags=["retenciones"])


def _parse_period(period: str) -> tuple[str, str]:
    """YYYY-MM -> (desde, hasta) en formato yyyy-mm-dd."""
    try:
        y, m = period.split("-")
        y_i, m_i = int(y), int(m)
        last = calendar.monthrange(y_i, m_i)[1]
        return f"{y_i:04d}-{m_i:02d}-01", f"{y_i:04d}-{m_i:02d}-{last:02d}"
    except Exception:
        raise HTTPException(status_code=400, detail=f"Periodo invalido: {period!r}. Esperado YYYY-MM.")


def _parse_afip_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "")).date()
    except Exception:
        return None


def _summarize(records: list[models.RetencionPercepcion]) -> dict:
    out: dict = {}
    for r in records:
        key = r.codigo_holistor or "OTRO"
        slot = out.setdefault(key, {"count": 0, "total": 0.0})
        slot["count"] += 1
        slot["total"] += float(r.importe or 0)
    return out


@router.post("/sync", response_model=schemas.RetencionSyncResponse, status_code=status.HTTP_200_OK)
def sync_retenciones(
    body: schemas.RetencionSyncRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Dispara la automation `mis-retenciones` para (client_id, period) y persiste los resultados.

    Idempotente: si ya hay registros para esa combinacion (client_id, period, numero_certificado),
    se saltean los duplicados.
    """
    client = db.query(models.Client).filter(models.Client.id == body.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not client.cuit:
        raise HTTPException(status_code=400, detail="El cliente no tiene CUIT cargado")
    if not client.clave_fiscal_encrypted:
        raise HTTPException(status_code=400, detail="El cliente no tiene clave fiscal cargada (requerida para Mis Retenciones)")

    try:
        ctx = load_context(client_id=body.client_id, production=True)
    except SystemExit as e:
        raise HTTPException(status_code=500, detail=str(e))

    desde, hasta = _parse_period(body.period)
    params = {
        "cuit": str(ctx.cuit_int),
        "username": str(ctx.cuit_int),
        "password": ctx.clave_fiscal,
        "mode": "filter",
        "page": 0,
        "size": 100,
        "filters": {
            "descripcionImpuesto": body.descripcion_impuesto,
            "fechaRetencionDesde": desde,
            "fechaRetencionHasta": hasta,
            "impuestoRetenido": body.impuesto_retenido,
            "tipoImpuesto": "IMP",
            "percepciones": body.incluir_percepciones,
            "retenciones": body.incluir_retenciones,
        },
    }

    try:
        payload = run_automation(ctx, "mis-retenciones", params,
                                 wait=True, include_credentials=False)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AFIP SDK fallo: {e!s}")

    if payload.get("status") == "error":
        raise HTTPException(status_code=502, detail=f"AFIP SDK error: {payload.get('data')}")

    save_raw(ctx, "mis-retenciones", body.period, payload)

    rows = extract_records(payload)
    sdk_job_id = payload.get("id")

    inserted = 0
    skipped = 0
    result_models: list[models.RetencionPercepcion] = []

    for row in rows:
        numero_cert = str(row.get("numeroCertificado") or "")
        numero_cbte = str(row.get("numeroComprobante") or "")
        fecha_ret = _parse_afip_date(row.get("fechaRetencion"))
        cuit_agente = str(row.get("cuitAgenteRetencion") or "")

        # Idempotencia: misma (client, period, certificado) o (client, period, cuit_agente, fecha, cbte)
        q = db.query(models.RetencionPercepcion).filter(
            models.RetencionPercepcion.client_id == body.client_id,
            models.RetencionPercepcion.period == body.period,
        )
        if numero_cert:
            existing = q.filter(models.RetencionPercepcion.numero_certificado == numero_cert).first()
        else:
            existing = q.filter(
                models.RetencionPercepcion.cuit_agente == cuit_agente,
                models.RetencionPercepcion.fecha_retencion == fecha_ret,
                models.RetencionPercepcion.numero_comprobante == numero_cbte,
            ).first()

        if existing:
            skipped += 1
            result_models.append(existing)
            continue

        rec = models.RetencionPercepcion(
            client_id=body.client_id,
            period=body.period,
            cuit_agente=cuit_agente,
            impuesto_retenido=row.get("impuestoRetenido"),
            codigo_regimen=row.get("codigoRegimen"),
            tipo_operacion=row.get("descripcionOperacion"),
            fecha_retencion=fecha_ret,
            fecha_comprobante=_parse_afip_date(row.get("fechaComprobante")),
            importe=float(row.get("importeRetenido") or 0),
            numero_certificado=numero_cert or None,
            numero_comprobante=numero_cbte or None,
            descripcion_comprobante=row.get("descripcionComprobante"),
            codigo_holistor=classify_regimen(row.get("impuestoRetenido")),
            sdk_job_id=sdk_job_id,
        )
        db.add(rec)
        inserted += 1
        result_models.append(rec)

    db.add(models.ActionLog(
        user_id=current_user.id,
        client_id=body.client_id,
        action_type="retenciones_sync",
        description=f"Mis Retenciones {body.period} impuesto={body.impuesto_retenido}: {len(rows)} registros ({inserted} nuevos, {skipped} duplicados)",
    ))
    db.commit()
    for r in result_models:
        db.refresh(r)

    return schemas.RetencionSyncResponse(
        client_id=body.client_id,
        period=body.period,
        sdk_job_id=sdk_job_id,
        status=payload.get("status", "complete"),
        total_records=len(rows),
        inserted=inserted,
        skipped_duplicates=skipped,
        summary_by_holistor=_summarize(result_models),
        records=[schemas.RetencionPercepcionOut.model_validate(r) for r in result_models],
    )


@router.get("/", response_model=List[schemas.RetencionPercepcionOut])
def list_retenciones(
    client_id: Optional[int] = None,
    period: Optional[str] = None,
    codigo_holistor: Optional[str] = None,
    limit: int = Query(default=500, le=5000),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.RetencionPercepcion)
    if client_id:
        q = q.filter(models.RetencionPercepcion.client_id == client_id)
    if period:
        q = q.filter(models.RetencionPercepcion.period == period)
    if codigo_holistor:
        q = q.filter(models.RetencionPercepcion.codigo_holistor == codigo_holistor)
    return q.order_by(models.RetencionPercepcion.fecha_retencion.desc()).limit(limit).all()


@router.get("/summary/{client_id}")
def summary(
    client_id: int,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.RetencionPercepcion).filter(models.RetencionPercepcion.client_id == client_id)
    if period:
        q = q.filter(models.RetencionPercepcion.period == period)
    records = q.all()
    return {
        "client_id": client_id,
        "period": period,
        "total_records": len(records),
        "total_amount": sum(float(r.importe or 0) for r in records),
        "by_holistor": _summarize(records),
    }


@router.delete("/{retencion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_retencion(
    retencion_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    rec = db.query(models.RetencionPercepcion).filter(models.RetencionPercepcion.id == retencion_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(rec)
    db.commit()
    return None
