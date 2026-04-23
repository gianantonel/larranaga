"""CLI para descargar Mis Retenciones (percepciones/retenciones sufridas).

Uso:
    python -m app.afip_sdk.retenciones --client-id 12 --prod --period 2022-03

Probar distintos nombres de automatizacion (la doc publica no lista el catalogo):
    python -m app.afip_sdk.retenciones --client-id 12 --prod --period 2022-03 \
        --automation mis-retenciones-sufridas

Output:
    - JSON crudo en backend/afip_raw/{cuit}/{automation}/{period}.json
    - Resumen por regimen (IV / IB / IG / otros) en stdout
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict

from .automations import run_automation, save_raw
from .client import load_context, env_label


# Mapa codigo AFIP "impuestoRetenido" -> codigo Holistor (col AR).
# Ref AFIP F.2003: 217=IVA percep/reten, 11/10=Ganancias, 767=Bienes Personales.
# Ampliar a medida que aparezcan nuevos codigos en los datos reales.
IMPUESTO_TO_HOLISTOR = {
    217: "PIVC",  # IVA - Percepciones / Retenciones
    216: "PIVC",
    11:  "PGAN",  # Ganancias - Retencion
    10:  "PGAN",  # Ganancias - Percepcion
    767: "OTRO",  # Bienes Personales (no tiene codigo Holistor directo)
}


def classify_regimen(impuesto: int | str | None) -> str:
    try:
        code = int(impuesto) if impuesto is not None else None
    except (TypeError, ValueError):
        return "OTRO"
    return IMPUESTO_TO_HOLISTOR.get(code, "OTRO")


def summarize(records: list[dict]) -> dict:
    """Agrupa por codigo Holistor y cuenta/total."""
    groups: dict[str, dict] = defaultdict(lambda: {"count": 0, "total": 0.0})
    for r in records:
        holistor = classify_regimen(r.get("impuestoRetenido"))
        try:
            importe = float(r.get("importeRetenido") or 0)
        except (TypeError, ValueError):
            importe = 0.0
        groups[holistor]["count"] += 1
        groups[holistor]["total"] += importe
    return dict(groups)


def extract_records(payload: dict) -> list[dict]:
    """Response documentado: {'data': {'rows': [...], 'page': {...}, 'total': N}}."""
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    if isinstance(data, list):
        return data
    return []


def main() -> None:
    p = argparse.ArgumentParser(description="Descarga Mis Retenciones via AFIP SDK")
    p.add_argument("--client-id", type=int)
    p.add_argument("--cuit")
    p.add_argument("--prod", action="store_true")
    p.add_argument("--period", required=True,
                   help="Periodo YYYY-MM (ej: 2022-03)")
    p.add_argument("--automation", default="mis-retenciones",
                   help="Nombre de la automatizacion (default: mis-retenciones)")
    p.add_argument("--no-wait", action="store_true",
                   help="No esperar el polling (devuelve job id)")
    p.add_argument("--desde", help="Fecha desde YYYY-MM-DD (override de --period)")
    p.add_argument("--hasta", help="Fecha hasta YYYY-MM-DD (override de --period)")
    p.add_argument("--mode", default="filter",
                   choices=["filter", "preset"],
                   help="filter (default) o preset")
    p.add_argument("--preset",
                   choices=["percepcion-ganancias",
                            "percepcion-bienes-personales",
                            "retencion-ganancias"],
                   help="Requerido si --mode preset")
    p.add_argument("--page", type=int, default=0)
    p.add_argument("--size", type=int, default=100)
    p.add_argument("--only-percepciones", action="store_true")
    p.add_argument("--only-retenciones", action="store_true")
    p.add_argument("--impuesto", type=int, default=217,
                   help="Codigo AFIP impuestoRetenido (217=IVA, 11=Ganancias, 767=Bienes Pers)")
    p.add_argument("--descripcion-impuesto", default="IVA",
                   help="descripcionImpuesto (default: IVA)")
    p.add_argument("--tipo-impuesto", default="IMP")
    args = p.parse_args()

    ctx = load_context(client_id=args.client_id, cuit=args.cuit, production=args.prod)
    if not ctx.clave_fiscal:
        raise SystemExit("El cliente no tiene clave fiscal cargada (requerida para automatizaciones).")

    print(f"Ambiente: {env_label(ctx.production)}   CUIT: {ctx.cuit_int}   cliente: {ctx.name}")
    print(f"Automation: {args.automation}   periodo: {args.period}")

    # Derivar desde/hasta del periodo si no se pasan explicitos
    if args.desde and args.hasta:
        desde, hasta = args.desde, args.hasta
    else:
        y, m = args.period.split("-")
        import calendar
        last = calendar.monthrange(int(y), int(m))[1]
        desde = f"{y}-{m}-01"
        hasta = f"{y}-{m}-{last:02d}"

    params: dict = {
        "cuit": str(ctx.cuit_int),
        "username": str(ctx.cuit_int),
        "password": ctx.clave_fiscal,
        "mode": args.mode,
        "page": args.page,
        "size": args.size,
    }
    if args.mode == "filter":
        incluir_per = not args.only_retenciones
        incluir_ret = not args.only_percepciones
        params["filters"] = {
            "descripcionImpuesto": args.descripcion_impuesto,
            "fechaRetencionDesde": desde,
            "fechaRetencionHasta": hasta,
            "impuestoRetenido": args.impuesto,
            "tipoImpuesto": args.tipo_impuesto,
            "percepciones": incluir_per,
            "retenciones": incluir_ret,
        }
    elif args.mode == "preset":
        if not args.preset:
            raise SystemExit("--mode preset requiere --preset")
        params["preset"] = args.preset

    print(f"  -> invocando (wait={not args.no_wait})...")
    try:
        payload = run_automation(ctx, args.automation, params,
                                 wait=not args.no_wait,
                                 include_credentials=False)
    except Exception as e:
        raise SystemExit(f"Fallo la automatizacion: {e!s}")

    print(f"  -> status: {payload.get('status')}   id: {payload.get('id')}")
    out = save_raw(ctx, args.automation, args.period, payload)
    print(f"  -> JSON crudo guardado en: {out}")

    records = extract_records(payload)
    print(f"\nRegistros recibidos: {len(records)}")
    if not records:
        print("  (sin registros o la estructura del response es distinta a la esperada)")
        print("  Preview del payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False)[:1500])
        return

    print("\nResumen por regimen (-> codigo Holistor):")
    for holistor, stats in summarize(records).items():
        print(f"  {holistor:6s}  count={stats['count']:4d}  total=${stats['total']:>15,.2f}")


if __name__ == "__main__":
    main()
