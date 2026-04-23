"""Endpoints para Comprobantes Recibidos y cruce con Retenciones (R-05).

Automation: mis-comprobantes (t=R) via AFIP SDK.
Cruce: RetencionPercepcion ↔ ComprobanteRecibido por cuit_agente == nro_doc_receptor + fecha.
Export: CSV formato Holistor (col AB = codigo_holistor de la retencion cruzada).
"""
from __future__ import annotations

import calendar
import csv
import io
from datetime import date, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..afip_sdk.client import load_context
from ..afip_sdk.automations import run_automation, save_raw
from ..afip_sdk.comprobantes import extract_records, normalize_record, period_to_fechas

router = APIRouter(prefix="/comprobantes", tags=["comprobantes"])


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ─── Sync Comprobantes Recibidos ─────────────────────────────────────────────

@router.post("/sync", response_model=schemas.ComprobanteSyncResponse, status_code=200)
def sync_comprobantes(
    body: schemas.ComprobanteSyncRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Descarga Mis Comprobantes Recibidos (t=R) para (client_id, period) y persiste.

    Idempotente por (client_id, period, cod_autorizacion) o
    (client_id, period, tipo, numero_desde, nro_doc_receptor).
    """
    client = db.query(models.Client).filter(models.Client.id == body.client_id).first()
    if not client:
        raise HTTPException(404, "Cliente no encontrado")
    if not client.cuit:
        raise HTTPException(400, "El cliente no tiene CUIT cargado")
    if not client.clave_fiscal_encrypted:
        raise HTTPException(400, "El cliente no tiene clave fiscal cargada")

    try:
        ctx = load_context(client_id=body.client_id, production=True)
    except SystemExit as e:
        raise HTTPException(500, str(e))

    desde_str, hasta_str = period_to_fechas(body.period)
    fecha_emision = f"{desde_str} - {hasta_str}"

    filters: dict = {"t": "R", "fechaEmision": fecha_emision}
    if body.tipos_comprobantes:
        filters["tiposComprobantes"] = body.tipos_comprobantes

    params = {
        "cuit":     str(ctx.cuit_int),
        "username": str(ctx.cuit_int),
        "password": ctx.clave_fiscal,
        "filters":  filters,
    }

    try:
        payload = run_automation(ctx, "mis-comprobantes", params,
                                 wait=True, include_credentials=False)
    except Exception as e:
        raise HTTPException(502, f"AFIP SDK fallo: {e!s}")

    if payload.get("status") == "error":
        raise HTTPException(502, f"AFIP SDK error: {payload.get('data')}")

    save_raw(ctx, "mis-comprobantes", body.period, payload)

    raw_records = extract_records(payload)
    sdk_job_id = payload.get("id")
    inserted = skipped = 0
    result_models: list[models.ComprobanteRecibido] = []

    for row in raw_records:
        n = normalize_record(row)
        fecha = _parse_date(n["fecha_emision"])
        if fecha is None:
            continue

        q = db.query(models.ComprobanteRecibido).filter(
            models.ComprobanteRecibido.client_id == body.client_id,
            models.ComprobanteRecibido.period == body.period,
        )
        if n["cod_autorizacion"]:
            existing = q.filter(
                models.ComprobanteRecibido.cod_autorizacion == n["cod_autorizacion"]
            ).first()
        else:
            existing = q.filter(
                models.ComprobanteRecibido.tipo_comprobante == n["tipo_comprobante"],
                models.ComprobanteRecibido.numero_desde == n["numero_desde"],
                models.ComprobanteRecibido.nro_doc_emisor == n["nro_doc_emisor"],
            ).first()

        if existing:
            skipped += 1
            result_models.append(existing)
            continue

        rec = models.ComprobanteRecibido(
            client_id=body.client_id,
            period=body.period,
            fecha_emision=fecha,
            tipo_comprobante=n["tipo_comprobante"],
            punto_venta=n["punto_venta"],
            numero_desde=n["numero_desde"],
            numero_hasta=n["numero_hasta"],
            cod_autorizacion=n["cod_autorizacion"],
            tipo_doc_emisor=n["tipo_doc_emisor"],
            nro_doc_emisor=n["nro_doc_emisor"],
            denominacion_emisor=n["denominacion_emisor"],
            tipo_doc_receptor=n["tipo_doc_receptor"],
            nro_doc_receptor=n["nro_doc_receptor"],
            moneda=n["moneda"],
            tipo_cambio=n["tipo_cambio"],
            imp_neto_gravado=n["imp_neto_gravado"],
            imp_neto_no_gravado=n["imp_neto_no_gravado"],
            imp_op_exentas=n["imp_op_exentas"],
            otros_tributos=n["otros_tributos"],
            iva=n["iva"],
            imp_total=n["imp_total"],
            sdk_job_id=sdk_job_id,
        )
        db.add(rec)
        inserted += 1
        result_models.append(rec)

    db.add(models.ActionLog(
        user_id=current_user.id,
        client_id=body.client_id,
        action_type="comprobantes_sync",
        description=(
            f"Mis Comprobantes Recibidos {body.period}: "
            f"{len(raw_records)} registros ({inserted} nuevos, {skipped} duplicados)"
        ),
    ))
    db.commit()
    for r in result_models:
        db.refresh(r)

    return schemas.ComprobanteSyncResponse(
        client_id=body.client_id,
        period=body.period,
        sdk_job_id=sdk_job_id,
        status=payload.get("status", "complete"),
        total_records=len(raw_records),
        inserted=inserted,
        skipped_duplicates=skipped,
        records=[schemas.ComprobanteRecibidoOut.model_validate(r) for r in result_models],
    )


@router.get("/", response_model=List[schemas.ComprobanteRecibidoOut])
def list_comprobantes(
    client_id: Optional[int] = None,
    period: Optional[str] = None,
    limit: int = Query(default=500, le=5000),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.ComprobanteRecibido)
    if client_id:
        q = q.filter(models.ComprobanteRecibido.client_id == client_id)
    if period:
        q = q.filter(models.ComprobanteRecibido.period == period)
    return q.order_by(models.ComprobanteRecibido.fecha_emision.desc()).limit(limit).all()


# ─── Cruce Retenciones ↔ Comprobantes ────────────────────────────────────────

def _match_score(ret: models.RetencionPercepcion,
                 cbte: models.ComprobanteRecibido) -> str:
    """Clasifica la calidad del match entre una retencion y un comprobante.

    El agente de percepcion (cuit_agente en Mis Retenciones) es el EMISOR
    del comprobante recibido (nro_doc_emisor). El receptor es nuestro cliente.

    Niveles:
    - exact  : mismo cuit_agente == nro_doc_emisor Y misma fecha (±0 días)
    - approx : mismo cuit_agente Y fecha dentro de ±5 días
    - none   : sin match
    """
    if not cbte:
        return "none"
    cuit_ret = (ret.cuit_agente or "").strip().replace("-", "")
    cuit_cbte = (cbte.nro_doc_emisor or "").strip().replace("-", "")
    if not cuit_ret or cuit_ret != cuit_cbte:
        return "none"
    if not (ret.fecha_retencion and cbte.fecha_emision):
        return "approx"
    delta = abs((ret.fecha_retencion - cbte.fecha_emision).days)
    if delta == 0:
        return "exact"
    if delta <= 5:
        return "approx"
    return "none"


@router.get("/cruce", response_model=schemas.CruceResponse)
def cruce_retenciones(
    client_id: int,
    period: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Cruza RetencionPercepcion con ComprobanteRecibido por cuit_agente + fecha.

    Para cada retencion busca el comprobante con mejor score (exact > approx).
    Actualiza la FK comprobante_id en la retencion y devuelve el resultado.
    """
    retenciones = (
        db.query(models.RetencionPercepcion)
        .filter(
            models.RetencionPercepcion.client_id == client_id,
            models.RetencionPercepcion.period == period,
        )
        .all()
    )
    if not retenciones:
        raise HTTPException(404, f"Sin retenciones para client_id={client_id} period={period}")

    comprobantes = (
        db.query(models.ComprobanteRecibido)
        .filter(
            models.ComprobanteRecibido.client_id == client_id,
            models.ComprobanteRecibido.period == period,
        )
        .all()
    )

    items: list[schemas.CruceItem] = []
    matched = 0

    for ret in retenciones:
        best_cbte = None
        best_score = "none"

        for cbte in comprobantes:
            score = _match_score(ret, cbte)
            if score == "exact":
                best_cbte, best_score = cbte, score
                break
            if score == "approx" and best_score == "none":
                best_cbte, best_score = cbte, score

        # Persistir FK si hay match
        if best_cbte and best_score != "none":
            ret.comprobante_id = best_cbte.id
            matched += 1

        items.append(schemas.CruceItem(
            retencion_id=ret.id,
            comprobante_id=best_cbte.id if best_cbte else None,
            client_id=client_id,
            period=period,
            fecha_retencion=ret.fecha_retencion,
            cuit_agente=ret.cuit_agente,
            importe_retencion=float(ret.importe or 0),
            codigo_holistor=ret.codigo_holistor,
            fecha_emision=best_cbte.fecha_emision if best_cbte else None,
            tipo_comprobante=best_cbte.tipo_comprobante if best_cbte else None,
            numero_desde=best_cbte.numero_desde if best_cbte else None,
            denominacion_receptor=best_cbte.denominacion_receptor if best_cbte else None,
            imp_total=float(best_cbte.imp_total or 0) if best_cbte else None,
            otros_tributos_comprobante=float(best_cbte.otros_tributos or 0) if best_cbte else None,
            match_score=best_score,
        ))

    db.commit()

    return schemas.CruceResponse(
        client_id=client_id,
        period=period,
        total_retenciones=len(retenciones),
        matched=matched,
        unmatched=len(retenciones) - matched,
        items=items,
    )


# ─── Export CSV Holistor ──────────────────────────────────────────────────────

@router.get("/export-holistor")
def export_holistor(
    client_id: int,
    period: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Genera CSV compatible con Holistor para la col. AB (Otros Tributos).

    Columnas: Fecha Emisión, Tipo Cbte, Nro, CUIT Emisor, Denominación,
              Imp Total, Otros Tributos, Código Holistor, Match Score.
    """
    comprobantes = (
        db.query(models.ComprobanteRecibido)
        .filter(
            models.ComprobanteRecibido.client_id == client_id,
            models.ComprobanteRecibido.period == period,
        )
        .order_by(models.ComprobanteRecibido.fecha_emision)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "Fecha Emisión", "Tipo Cbte", "Punto Venta", "Número",
        "CAE", "CUIT Emisor", "Denominación",
        "Neto Gravado", "IVA", "Otros Tributos", "Total",
        "Cód. Holistor", "Match",
    ])

    for cbte in comprobantes:
        # Buscar retenciones cruzadas a este comprobante
        rets = [r for r in cbte.retenciones] if cbte.retenciones else []
        holistor_codes = ",".join(sorted({r.codigo_holistor or "OTRO" for r in rets})) if rets else ""
        match = "matched" if rets else "unmatched"

        writer.writerow([
            cbte.fecha_emision.isoformat() if cbte.fecha_emision else "",
            cbte.tipo_comprobante or "",
            cbte.punto_venta or "",
            cbte.numero_desde or "",
            cbte.cod_autorizacion or "",
            cbte.nro_doc_emisor or "",
            cbte.denominacion_emisor or "",
            f"{cbte.imp_neto_gravado:.2f}".replace(".", ","),
            f"{cbte.iva:.2f}".replace(".", ","),
            f"{cbte.otros_tributos:.2f}".replace(".", ","),
            f"{cbte.imp_total:.2f}".replace(".", ","),
            holistor_codes,
            match,
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM para Excel
    filename = f"holistor_{client_id}_{period}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{comprobante_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comprobante(
    comprobante_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    rec = db.query(models.ComprobanteRecibido).filter(
        models.ComprobanteRecibido.id == comprobante_id
    ).first()
    if not rec:
        raise HTTPException(404, "Comprobante no encontrado")
    db.delete(rec)
    db.commit()
