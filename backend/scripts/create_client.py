"""
CLI para crear un cliente llamando al endpoint POST /clients/ del backend.

Uso rápido:
    python -m scripts.create_client \\
        --name "Agropecuaria El Alba S.R.L." \\
        --cuit 23-31134894-9 \\
        --clave-fiscal "MiClaveAFIP" \\
        --fiscal-condition "Responsable Inscripto"

Credenciales admin por defecto: admin1@larranaga.com / admin123
(Se pueden sobreescribir con --email / --password o env LARRANAGA_ADMIN_EMAIL / LARRANAGA_ADMIN_PASSWORD)

Backend por defecto: http://localhost:8000  (override con --base-url o LARRANAGA_API)
"""
import argparse
import json
import os
import sys
from urllib import request, error


def _post(url: str, payload: dict, token: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} en {url}: {body}") from None
    except error.URLError as e:
        raise SystemExit(f"No pude conectar con {url}: {e.reason}") from None


def login(base_url: str, email: str, password: str) -> str:
    resp = _post(f"{base_url}/auth/login", {"email": email, "password": password})
    return resp["access_token"]


def create_client(base_url: str, token: str, payload: dict) -> dict:
    return _post(f"{base_url}/clients/", payload, token=token)


def main() -> None:
    p = argparse.ArgumentParser(description="Crear un cliente vía API")
    p.add_argument("--name", required=True)
    p.add_argument("--business-name", dest="business_name")
    p.add_argument("--cuit")
    p.add_argument("--clave-fiscal", dest="clave_fiscal")
    p.add_argument("--address")
    p.add_argument("--phone")
    p.add_argument("--email-client", dest="email_client", help="Email del cliente")
    p.add_argument("--category")
    p.add_argument("--fiscal-condition", dest="fiscal_condition")
    p.add_argument("--activity-code", dest="activity_code")
    p.add_argument("--notes")

    p.add_argument("--base-url", default=os.getenv("LARRANAGA_API", "http://localhost:8000"))
    p.add_argument("--email", default=os.getenv("LARRANAGA_ADMIN_EMAIL", "admin1@larranaga.com"),
                   help="Email admin para autenticar")
    p.add_argument("--password", default=os.getenv("LARRANAGA_ADMIN_PASSWORD", "admin123"),
                   help="Password admin para autenticar")

    args = p.parse_args()

    payload = {
        "name": args.name,
        "business_name": args.business_name,
        "cuit": args.cuit,
        "clave_fiscal": args.clave_fiscal,
        "address": args.address,
        "phone": args.phone,
        "email": args.email_client,
        "category": args.category,
        "fiscal_condition": args.fiscal_condition,
        "activity_code": args.activity_code,
        "notes": args.notes,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    print(f"-> Login como {args.email} en {args.base_url}...")
    token = login(args.base_url, args.email, args.password)

    print(f"-> Creando cliente: {args.name}")
    created = create_client(args.base_url, token, payload)

    print("[OK] Cliente creado:")
    print(json.dumps(
        {k: created.get(k) for k in ("id", "name", "cuit", "fiscal_condition", "is_active")},
        indent=2, ensure_ascii=False
    ))
    sys.exit(0)


if __name__ == "__main__":
    main()
