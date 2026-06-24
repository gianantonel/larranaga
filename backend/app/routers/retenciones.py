"""Endpoints para Retenciones y Percepciones (Mis Retenciones ARCA).

POST /retenciones/sync   → crea un RetencionSyncJob (status=pending), encola
                           BackgroundTask, devuelve {job_id} en <1s. El
                           scraping AFIP tarda 1-3 min — supera Cloudflare ~100s.
GET  /retenciones/sync/{job_id} → estado del job (polling cada ~3s desde el
                           frontend hasta status in {done, error}).
GET  /retenciones/        → listado de registros ya sincronizados.
"""
from __future__ import annotations

import calendar
import json
import logging
from datetime import date, datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import SessionLocal, get_db
from .auth import get_current_user
from ..access import assigned_client_ids, ensure_client_access
from ..afip_sdk.client import load_context
from ..afip_sdk.automations import run_automation, save_raw
from ..afip_sdk.retenciones import IMPUESTO_TO_HOLISTOR, classify_regimen, extract_records


logger = logging.getLogger(__name__)

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


def _run_sync_job(job_id: int) -> None:
    """Worker que corre en BackgroundTasks. Abre su propia sesión de DB."""
    db: Session = SessionLocal()
    try:
        job = db.query(models.RetencionSyncJob).filter(models.RetencionSyncJob.id == job_id).first()
        if not job:
            logger.error("RetencionSyncJob %s no existe", job_id)
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        try:
            client = db.query(models.Client).filter(models.Client.id == job.client_id).first()
            if not client or not client.cuit or not client.clave_fiscal_encrypted:
                raise RuntimeError("Cliente sin CUIT o clave fiscal")

            ctx = load_context(client_id=job.client_id, production=True)
            desde, hasta = _parse_period(job.period)
            params = {
                "cuit": str(ctx.cuit_int),
                "username": str(ctx.cuit_int),
                "password": ctx.clave_fiscal,
                "mode": "filter",
                "page": 0,
                "size": 100,
                "filters": {
                    "descripcionImpuesto": job.descripcion_impuesto,
                    "fechaRetencionDesde": desde,
                    "fechaRetencionHasta": hasta,
                    "impuestoRetenido": job.impuesto_retenido,
                    "tipoImpuesto": "IMP",
                    "percepciones": job.incluir_percepciones,
                    "retenciones": job.incluir_retenciones,
                },
            }

            payload = run_automation(ctx, "mis-retenciones", params,
                                     wait=True, include_credentials=False)

            if payload.get("status") == "error":
                raise RuntimeError(f"AFIP SDK error: {payload.get('data')}")

            save_raw(ctx, "mis-retenciones", job.period, payload)

            rows = extract_records(payload)
            sdk_job_id = payload.get("id")

            inserted = 0
            skipped = 0
            persisted: list[models.RetencionPercepcion] = []

            for row in rows:
                numero_cert = str(row.get("numeroCertificado") or "")
                numero_cbte = str(row.get("numeroComprobante") or "")
                fecha_ret = _parse_afip_date(row.get("fechaRetencion"))
                cuit_agente = str(row.get("cuitAgenteRetencion") or "")

                q = db.query(models.RetencionPercepcion).filter(
                    models.RetencionPercepcion.client_id == job.client_id,
                    models.RetencionPercepcion.period == job.period,
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
                    persisted.append(existing)
                    continue

                rec = models.RetencionPercepcion(
                    client_id=job.client_id,
                    period=job.period,
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
                persisted.append(rec)

            db.add(models.ActionLog(
                user_id=job.user_id,
                client_id=job.client_id,
                action_type="retenciones_sync",
                description=(
                    f"Mis Retenciones {job.period} impuesto={job.impuesto_retenido}: "
                    f"{len(rows)} registros ({inserted} nuevos, {skipped} duplicados)"
                ),
            ))

            job.status = "done"
            job.sdk_job_id = sdk_job_id
            job.total_records = len(rows)
            job.inserted = inserted
            job.skipped_duplicates = skipped
            job.summary_by_holistor = json.dumps(_summarize(persisted))
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as e:
            db.rollback()
            logger.exception("RetencionSyncJob %s falló", job_id)
            # re-fetch (post-rollback) y marcar error
            j = db.query(models.RetencionSyncJob).filter(models.RetencionSyncJob.id == job_id).first()
            if j is not None:
                j.status = "error"
                j.error = str(e)[:2000]
                j.completed_at = datetime.now(timezone.utc)
                db.commit()
    finally:
        db.close()


@router.post("/sync", response_model=schemas.RetencionSyncJobAccepted, status_code=status.HTTP_202_ACCEPTED)
def sync_retenciones(
    body: schemas.RetencionSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Encola un job de scraping de Mis Retenciones y retorna `job_id` inmediatamente.

    El cliente debe polear `GET /retenciones/sync/{job_id}` hasta status in {done,error}.
    El scraping completo en AFIP SDK suele tardar 1–3 minutos.
    """
    ensure_client_access(db, current_user, body.client_id)
    client = db.query(models.Client).filter(models.Client.id == body.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not client.cuit:
        raise HTTPException(status_code=400, detail="El cliente no tiene CUIT cargado")
    if not client.clave_fiscal_encrypted:
        raise HTTPException(status_code=400, detail="El cliente no tiene clave fiscal cargada (requerida para Mis Retenciones)")

    job = models.RetencionSyncJob(
        client_id=body.client_id,
        user_id=current_user.id,
        period=body.period,
        impuesto_retenido=body.impuesto_retenido,
        descripcion_impuesto=body.descripcion_impuesto,
        incluir_percepciones=body.incluir_percepciones,
        incluir_retenciones=body.incluir_retenciones,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_sync_job, job.id)
    return schemas.RetencionSyncJobAccepted(job_id=job.id, status="pending")


@router.get("/sync/{job_id}", response_model=schemas.RetencionSyncJobOut)
def get_sync_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = db.query(models.RetencionSyncJob).filter(models.RetencionSyncJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    ensure_client_access(db, current_user, job.client_id)
    summary = None
    if job.summary_by_holistor:
        try:
            summary = json.loads(job.summary_by_holistor)
        except Exception:
            summary = None
    return schemas.RetencionSyncJobOut(
        id=job.id,
        client_id=job.client_id,
        period=job.period,
        status=job.status,
        impuesto_retenido=job.impuesto_retenido,
        sdk_job_id=job.sdk_job_id,
        total_records=job.total_records,
        inserted=job.inserted,
        skipped_duplicates=job.skipped_duplicates,
        summary_by_holistor=summary,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
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
    allowed = assigned_client_ids(db, current_user)
    if allowed is not None:
        q = q.filter(models.RetencionPercepcion.client_id.in_(allowed))
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
    ensure_client_access(db, current_user, client_id)
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
    ensure_client_access(db, current_user, rec.client_id)
    db.delete(rec)
    db.commit()
    return None
