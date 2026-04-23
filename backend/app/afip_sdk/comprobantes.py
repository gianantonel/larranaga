"""CLI para descargar Mis Comprobantes (emitidos o recibidos).

Uso:
    # Comprobantes RECIBIDOS diciembre 2025
    python -m app.afip_sdk.comprobantes --client-id 12 --prod --period 2025-12 --t R

    # Comprobantes EMITIDOS rango libre
    python -m app.afip_sdk.comprobantes --client-id 12 --prod --desde 01/06/2025 --hasta 30/06/2025 --t E

Schema oficial: https://afipsdk.com/docs/automations/mis-comprobantes/nodejs/
Automation name: mis-comprobantes
Filtro fecha: "dd/mm/yyyy - dd/mm/yyyy"
Response: data = array plano con claves en español (sin 'rows').
"""
from __future__ import annotations

import argparse
import calendar
import json
from datetime import date

from .automations import run_automation, save_raw
from .client import load_context, env_label


def period_to_fechas(period: str) -> tuple[str, str]:
    """'YYYY-MM' → ('dd/mm/yyyy', 'dd/mm/yyyy') para el filtro fechaEmision."""
    y, m = period.split("-")
    last = calendar.monthrange(int(y), int(m))[1]
    return f"01/{m}/{y}", f"{last:02d}/{m}/{y}"


def parse_importe(s: str | None) -> float:
    """'1.234,56' → 1234.56."""
    if not s:
        return 0.0
    try:
        return float(s.replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0


def extract_records(payload: dict) -> list[dict]:
    """Response: data es array plano (a diferencia de mis-retenciones que tiene data.rows)."""
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    return []


def _get(row: dict, *keys: str, default="") -> str:
    """Busca la primera key que exista en el dict (manejo de encoding variante)."""
    for k in keys:
        v = row.get(k)
        if v is not None:
            return str(v)
    # fallback: búsqueda parcial insensible a acentos/encoding
    for rk, rv in row.items():
        for k in keys:
            # compara solo caracteres ASCII del key buscado
            ascii_k = "".join(c for c in k if ord(c) < 128)
            ascii_rk = "".join(c for c in rk if ord(c) < 128)
            if ascii_k and ascii_k in ascii_rk:
                return str(rv) if rv is not None else default
    return default


def normalize_record(row: dict) -> dict:
    """Normaliza un registro crudo a nombres de campo snake_case.

    El response REAL tiene Nro. Doc. Emisor + Nro. Doc. Receptor por separado
    (los docs de afipsdk muestran solo Receptor). El emisor es quien aplica
    la percepcion (= cuit_agente en mis-retenciones).
    El IVA viene desglosado por alicuota; usamos 'Total IVA' como resumen.
    """
    # IVA total: preferir 'Total IVA', sino sumar columnas individuales
    iva_total = parse_importe(_get(row, "Total IVA"))
    if not iva_total:
        for k in ["IVA 2,5%", "IVA 5%", "IVA 10,5%", "IVA 21%", "IVA 27%", "IVA"]:
            iva_total += parse_importe(row.get(k))

    return {
        "fecha_emision":         _get(row, "Fecha de Emisión", "Fecha de Emision"),
        "tipo_comprobante":      _get(row, "Tipo de Comprobante"),
        "punto_venta":           _get(row, "Punto de Venta"),
        "numero_desde":          _get(row, "Número Desde", "Numero Desde"),
        "numero_hasta":          _get(row, "Número Hasta", "Numero Hasta"),
        "cod_autorizacion":      _get(row, "Cód. Autorización", "Cod. Autorizacion"),
        # Emisor = quien emite la factura y aplica la percepción (= cuit_agente en ret.)
        "tipo_doc_emisor":       _get(row, "Tipo Doc. Emisor"),
        "nro_doc_emisor":        _get(row, "Nro. Doc. Emisor").strip(),
        "denominacion_emisor":   _get(row, "Denominación Emisor", "Denominacion Emisor"),
        # Receptor = nuestro cliente (El Alba)
        "tipo_doc_receptor":     _get(row, "Tipo Doc. Receptor"),
        "nro_doc_receptor":      _get(row, "Nro. Doc. Receptor").strip(),
        "moneda":                _get(row, "Moneda") or "PES",
        "tipo_cambio":           parse_importe(_get(row, "Tipo Cambio")) or 1.0,
        "imp_neto_gravado":      parse_importe(_get(row, "Imp. Neto Gravado Total", "Imp. Neto Gravado")),
        "imp_neto_no_gravado":   parse_importe(_get(row, "Imp. Neto No Gravado")),
        "imp_op_exentas":        parse_importe(_get(row, "Imp. Op. Exentas")),
        "otros_tributos":        parse_importe(_get(row, "Otros Tributos")),
        "iva":                   iva_total,
        "imp_total":             parse_importe(_get(row, "Imp. Total")),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Descarga Mis Comprobantes via AFIP SDK")
    p.add_argument("--client-id", type=int)
    p.add_argument("--cuit")
    p.add_argument("--prod", action="store_true")
    p.add_argument("--period", help="Período YYYY-MM (define fechaEmision automáticamente)")
    p.add_argument("--desde", help="Fecha desde dd/mm/yyyy (override --period)")
    p.add_argument("--hasta", help="Fecha hasta dd/mm/yyyy (override --period)")
    p.add_argument("--t", default="R", choices=["E", "R"],
                   help="E=Emitidos, R=Recibidos (default: R)")
    p.add_argument("--tipos", nargs="*", type=int,
                   help="Tipos de comprobante (ej: 1 6 11)")
    p.add_argument("--no-wait", action="store_true")
    args = p.parse_args()

    if not args.period and not (args.desde and args.hasta):
        raise SystemExit("Requerido: --period YYYY-MM o --desde/--hasta dd/mm/yyyy")

    ctx = load_context(client_id=args.client_id, cuit=args.cuit, production=args.prod)
    if not ctx.clave_fiscal:
        raise SystemExit("El cliente no tiene clave fiscal cargada.")

    print(f"Ambiente: {env_label(ctx.production)}  CUIT: {ctx.cuit_int}  cliente: {ctx.name}")

    if args.period:
        desde_str, hasta_str = period_to_fechas(args.period)
        period_label = args.period
    else:
        desde_str, hasta_str = args.desde, args.hasta
        period_label = f"{args.desde}-{args.hasta}"

    fecha_emision = f"{desde_str} - {hasta_str}"
    print(f"mis-comprobantes  t={args.t}  fechaEmision={fecha_emision!r}")

    filters: dict = {"t": args.t, "fechaEmision": fecha_emision}
    if args.tipos:
        filters["tiposComprobantes"] = args.tipos

    params = {
        "cuit":     str(ctx.cuit_int),
        "username": str(ctx.cuit_int),
        "password": ctx.clave_fiscal,
        "filters":  filters,
    }

    print("  -> invocando...")
    try:
        payload = run_automation(ctx, "mis-comprobantes", params,
                                 wait=not args.no_wait,
                                 include_credentials=False)
    except Exception as e:
        raise SystemExit(f"Fallo la automatizacion: {e!s}")

    print(f"  -> status: {payload.get('status')}  id: {payload.get('id')}")
    out = save_raw(ctx, "mis-comprobantes", period_label, payload)
    print(f"  -> JSON crudo guardado en: {out}")

    records = extract_records(payload)
    print(f"\nComprobantes recibidos: {len(records)}")
    if not records:
        print("  (sin registros o estructura inesperada)")
        print("  Preview:")
        print(json.dumps(payload, indent=2, ensure_ascii=False)[:1500])
        return

    total = sum(parse_importe(r.get("Imp. Total")) for r in records)
    otros = sum(parse_importe(r.get("Otros Tributos")) for r in records)
    print(f"  Imp. Total acumulado : ${total:>15,.2f}")
    print(f"  Otros Tributos total : ${otros:>15,.2f}")
    print("\nPrimeros 5 registros:")
    for r in records[:5]:
        n = normalize_record(r)
        print(f"  {n['fecha_emision']}  CUIT={n['nro_doc_receptor']:13s}  "
              f"tipo={n['tipo_comprobante']:3s}  total=${n['imp_total']:>12,.2f}  "
              f"otros=${n['otros_tributos']:>10,.2f}")


if __name__ == "__main__":
    main()
