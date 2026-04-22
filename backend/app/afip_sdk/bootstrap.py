"""One-time bootstrap: crea certificado + WSAuth para un CUIT en app.afipsdk.com.

Esto deja al CUIT habilitado para operar webservices (wsfe, etc.) en el entorno
elegido. Requiere que el cliente tenga la clave fiscal cargada en la DB
(se descifra al vuelo y se envia a app.afipsdk.com para que genere/asocie el cert).

Uso:
    python -m app.afip_sdk.bootstrap --client-id 12
    python -m app.afip_sdk.bootstrap --client-id 12 --prod
    python -m app.afip_sdk.bootstrap --client-id 12 --wsid wsfe --alias larranaga
    python -m app.afip_sdk.bootstrap --client-id 12 --skip-cert         # solo WSAuth
"""
import argparse
import json

from .client import load_context, env_label, save_cert_key


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--client-id", type=int)
    p.add_argument("--cuit")
    p.add_argument("--prod", action="store_true")
    p.add_argument("--alias", default="larranaga",
                   help="Alias del certificado en app.afipsdk.com (default: larranaga)")
    p.add_argument("--wsid", default="wsfe",
                   help="Webservice a habilitar (default: wsfe = factura electronica)")
    p.add_argument("--skip-cert", action="store_true",
                   help="Saltear createCert (util si ya existe y solo falta WSAuth)")
    p.add_argument("--skip-wsauth", action="store_true",
                   help="Saltear createWSAuth")
    args = p.parse_args()

    ctx = load_context(client_id=args.client_id, cuit=args.cuit, production=args.prod)
    print(f"Ambiente: {env_label(ctx.production)}")
    print(f"Cliente:  id={ctx.client_id} name={ctx.name} cuit={ctx.cuit_raw}")

    if not ctx.clave_fiscal:
        raise SystemExit(
            "Este cliente no tiene clave fiscal cargada (o no se pudo descifrar). "
            "Cargala primero con: PUT /clients/{id}  { clave_fiscal: '...' }"
        )

    username = str(ctx.cuit_int)

    if not args.skip_cert:
        print(f"\n[1/2] createCert alias={args.alias}...")
        try:
            result = ctx.afip.createCert(username, ctx.clave_fiscal, args.alias)
            cert_pem = result.get("cert")
            key_pem = result.get("key")
            if cert_pem and key_pem:
                cert_p, key_p = save_cert_key(ctx.cuit_int, ctx.production, cert_pem, key_pem)
                print(f"  OK — cert guardado en {cert_p}")
                print(f"       key  guardada en {key_p}")
                # Reinyectar en la instancia en memoria para que [2/2] y llamadas siguientes funcionen sin recargar
                ctx.afip.cert = cert_pem
                ctx.afip.key = key_pem
            else:
                print("  (!) la respuesta no trajo cert/key — no se persistio nada")
                print("  respuesta:", json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            msg = str(e)
            if "ya existe" in msg.lower() or "already exists" in msg.lower():
                print(f"  (info) el cert alias={args.alias} ya existia: {msg}")
            else:
                raise SystemExit(f"createCert fallo: {msg}")

    if not args.skip_wsauth:
        print(f"\n[2/2] createWSAuth wsid={args.wsid} alias={args.alias}...")
        try:
            result = ctx.afip.createWSAuth(username, ctx.clave_fiscal, args.alias, args.wsid)
            print("  OK")
            print("  respuesta:", json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            raise SystemExit(f"createWSAuth fallo: {e!s}")

    print("\nListo. Ahora corré:")
    print(f"  python -m app.afip_sdk.smoke_test --client-id {ctx.client_id}"
          + (" --prod" if ctx.production else ""))


if __name__ == "__main__":
    main()
