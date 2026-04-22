"""Consultas informativas contra AFIP: puntos de venta, tipos de comprobante, etc.

Uso:
    python -m app.afip_sdk.info --client-id 12 --what sales-points
    python -m app.afip_sdk.info --client-id 12 --what voucher-types
    python -m app.afip_sdk.info --client-id 12 --what document-types
    python -m app.afip_sdk.info --client-id 12 --prod --what sales-points
"""
import argparse
import json

from .client import load_context, env_label


QUERIES = {
    "sales-points":   ("getSalesPoints",   "Puntos de venta habilitados (FEParamGetPtosVenta)"),
    "voucher-types":  ("getVoucherTypes",  "Tipos de comprobante"),
    "document-types": ("getDocumentTypes", "Tipos de documento del receptor"),
    "currencies":     ("getCurrenciesTypes", "Monedas aceptadas"),
    "aliquots":       ("getAliquotTypes",  "Alícuotas de IVA"),
    "concepts":       ("getConceptTypes",  "Tipos de concepto (productos/servicios)"),
    "taxes":          ("getTaxTypes",      "Tipos de tributo"),
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--client-id", type=int)
    p.add_argument("--cuit")
    p.add_argument("--prod", action="store_true")
    p.add_argument("--what", choices=sorted(QUERIES.keys()), default="sales-points")
    args = p.parse_args()

    ctx = load_context(client_id=args.client_id, cuit=args.cuit, production=args.prod)
    method, desc = QUERIES[args.what]

    print(f"Ambiente: {env_label(ctx.production)}   CUIT: {ctx.cuit_int}   cliente: {ctx.name}")
    print(f"Consulta: {args.what}  ({desc})\n")

    eb = ctx.afip.ElectronicBilling
    try:
        result = getattr(eb, method)()
    except Exception as e:
        raise SystemExit(f"{method} fallo: {e!s}")

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
