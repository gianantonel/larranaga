"""Wrapper sobre afip.createAutomation (servicio app.afipsdk.com).

Las automatizaciones usan clave fiscal (scraping de portales AFIP/ARCA),
a diferencia de los Web Services que usan certificado/key.

Uso tipico:
    from .client import load_context
    from .automations import run_automation

    ctx = load_context(client_id=12, production=True)
    job = run_automation(ctx, "mis-retenciones",
                        {"periodo": "2022-03"}, wait=True)
    print(job["status"], job.get("data"))

Devuelve el dict crudo de app.afipsdk.com (con "status", "data", "id", etc.).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .client import ClientAfipContext


RAW_DIR = Path(__file__).resolve().parent.parent.parent / "afip_raw"


def run_automation(
    ctx: ClientAfipContext,
    automation: str,
    extra_params: dict[str, Any] | None = None,
    *,
    wait: bool = True,
    include_credentials: bool = True,
) -> dict:
    """Invoca una automatizacion y devuelve el response crudo.

    Por defecto inyecta cuit + clave_fiscal del contexto en los params.
    """
    params: dict[str, Any] = {}
    if include_credentials:
        params["cuit"] = str(ctx.cuit_int)
        if ctx.clave_fiscal:
            params["clave_fiscal"] = ctx.clave_fiscal
    if extra_params:
        params.update(extra_params)

    return ctx.afip.createAutomation(automation, params, wait)


def save_raw(
    ctx: ClientAfipContext,
    automation: str,
    period: str,
    payload: dict,
) -> Path:
    """Persiste el JSON crudo en afip_raw/{cuit}/{automation}/{period}.json."""
    out_dir = RAW_DIR / str(ctx.cuit_int) / automation
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{period}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
