"""Helpers para resolver credenciales y construir una instancia Afip()."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from afip import Afip  # noqa: E402

from ..database import SessionLocal  # noqa: E402
from .. import models  # noqa: E402
from ..security import decrypt_credential  # noqa: E402


CERTS_DIR = Path(__file__).resolve().parent.parent.parent / "afip_certs"


def cert_paths(cuit_int: int, production: bool) -> tuple[Path, Path]:
    env = "prod" if production else "dev"
    base = CERTS_DIR / f"{cuit_int}-{env}"
    return base.with_suffix(".cert"), base.with_suffix(".key")


def _normalize_pem(s: str) -> str:
    # Ensure consistent LF endings regardless of what app.afipsdk.com returned (\n or \r\n).
    return s.replace("\r\n", "\n").replace("\r", "\n")


def save_cert_key(cuit_int: int, production: bool, cert_pem: str, key_pem: str) -> tuple[Path, Path]:
    CERTS_DIR.mkdir(parents=True, exist_ok=True)
    cert_p, key_p = cert_paths(cuit_int, production)
    # newline="" disables universal-newline translation on write so Windows doesn't
    # turn \n into \r\n (which corrupts the PEM as ASN.1).
    cert_p.write_bytes(_normalize_pem(cert_pem).encode("utf-8"))
    key_p.write_bytes(_normalize_pem(key_pem).encode("utf-8"))
    return cert_p, key_p


def load_cert_key(cuit_int: int, production: bool) -> tuple[str | None, str | None]:
    cert_p, key_p = cert_paths(cuit_int, production)
    if cert_p.exists() and key_p.exists():
        return cert_p.read_bytes().decode("utf-8"), key_p.read_bytes().decode("utf-8")
    return None, None


@dataclass
class ClientAfipContext:
    client_id: int
    name: str
    cuit_raw: str
    cuit_int: int
    clave_fiscal: str | None  # descifrada, None si no hay
    production: bool
    access_token: str
    afip: Afip


def _clean_cuit(cuit: str) -> int:
    digits = "".join(ch for ch in cuit if ch.isdigit())
    if len(digits) != 11:
        raise ValueError(f"CUIT invalido (esperaba 11 digitos): {cuit!r}")
    return int(digits)


def _require_token() -> str:
    token = os.getenv("AFIP_SDK_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Falta AFIP_SDK_ACCESS_TOKEN en el entorno/.env")
    return token


def load_context(
    client_id: int | None = None,
    cuit: str | None = None,
    production: bool = False,
) -> ClientAfipContext:
    """Resuelve el cliente por id o por CUIT, descifra la clave fiscal y arma el Afip()."""
    token = _require_token()

    db = SessionLocal()
    try:
        q = db.query(models.Client)
        if client_id is not None:
            client = q.filter(models.Client.id == client_id).first()
        elif cuit is not None:
            target = "".join(ch for ch in cuit if ch.isdigit())
            client = next(
                (c for c in q.filter(models.Client.cuit.isnot(None)).all()
                 if "".join(ch for ch in (c.cuit or "") if ch.isdigit()) == target),
                None,
            )
        else:
            raise SystemExit("Debe indicar --client-id o --cuit")

        if not client:
            raise SystemExit("Cliente no encontrado.")
        if not client.cuit:
            raise SystemExit(f"El cliente id={client.id} no tiene CUIT cargado.")

        cuit_int = _clean_cuit(client.cuit)
        clave = None
        if client.clave_fiscal_encrypted:
            try:
                clave = decrypt_credential(client.clave_fiscal_encrypted)
            except Exception as e:
                print(f"  (!) No pude descifrar la clave fiscal: {e!r}")

        cert_pem, key_pem = load_cert_key(cuit_int, production)
        opts = {
            "CUIT": cuit_int,
            "production": bool(production),
            "access_token": token,
        }
        if cert_pem and key_pem:
            opts["cert"] = cert_pem
            opts["key"] = key_pem
        afip = Afip(opts)

        return ClientAfipContext(
            client_id=client.id,
            name=client.name,
            cuit_raw=client.cuit,
            cuit_int=cuit_int,
            clave_fiscal=clave,
            production=bool(production),
            access_token=token,
            afip=afip,
        )
    finally:
        db.close()


def env_label(production: bool) -> str:
    return "PRODUCCION" if production else "HOMOLOGACION"
