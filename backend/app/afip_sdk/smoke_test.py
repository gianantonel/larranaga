"""Smoke test: FEDummy + FECompUltimoAutorizado + FECompConsultar."""
import argparse

from .client import load_context, env_label


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--client-id", type=int)
    p.add_argument("--cuit")
    p.add_argument("--prod", action="store_true")
    p.add_argument("--punto-venta", type=int, default=1)
    p.add_argument("--tipo-cbte", type=int, default=11,
                   help="1=FA A, 6=FA B, 11=FA C (default)")
    args = p.parse_args()

    ctx = load_context(client_id=args.client_id, cuit=args.cuit, production=args.prod)
    print(f"Ambiente: {env_label(ctx.production)}   CUIT: {ctx.cuit_int}   "
          f"cliente: {ctx.name}")

    eb = ctx.afip.ElectronicBilling

    print("\n[1/3] FEDummy (healthcheck)...")
    try:
        print("  ->", eb.getServerStatus())
    except Exception as e:
        raise SystemExit(f"FEDummy fallo: {e!r}")

    print(f"\n[2/3] FECompUltimoAutorizado (pto={args.punto_venta}, tipo={args.tipo_cbte})...")
    try:
        last = eb.getLastVoucher(args.punto_venta, args.tipo_cbte)
        print(f"  -> ultimo numero autorizado: {last}")
    except Exception as e:
        print(f"  (!) fallo: {e!s}")
        print("      Si dice 'Certificado/Key obligatorio' corré primero:")
        print(f"        python -m app.afip_sdk.bootstrap --client-id {ctx.client_id}"
              + (" --prod" if ctx.production else ""))
        return

    if not last:
        print("  (no hay comprobantes emitidos todavia para este pto/tipo)")
        return

    print(f"\n[3/3] FECompConsultar (numero={last})...")
    try:
        info = eb.getVoucherInfo(last, args.punto_venta, args.tipo_cbte)
        if not info:
            print("  (sin datos)")
        else:
            detail = info.get("ResultGet", info) if isinstance(info, dict) else info
            for k in ("CbteFch", "DocTipo", "DocNro", "ImpTotal", "ImpNeto",
                      "ImpIVA", "CodAutorizacion", "FchVto", "Resultado", "MonId"):
                if k in detail:
                    print(f"  {k}: {detail[k]}")
    except Exception as e:
        print(f"  (!) fallo: {e!s}")


if __name__ == "__main__":
    main()
