"""Seed de pagos que coinciden con el extracto sintético, para que el matching tenga match.

Ejecutar ANTES del QA: python scripts/qa_fase3_seed_pagos.py
"""
import requests

BASE = "http://127.0.0.1:8001"
EMAIL = "rodriguezfederico765@gmail.com"
PASS = "admin123"


def main():
    # Login
    r = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASS})
    r.raise_for_status()
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # Clientes
    r = requests.get(f"{BASE}/clients/?is_active=true", headers=h)
    clientes = r.json()

    # Mapping CUIT del extracto → cliente real (vamos a actualizar el CUIT del cliente)
    # El extracto tiene: 30709212083 (BUTALO), 20123456789 (Gesualdo), 30716234561 (Gaucho), 27987654321 (Farmacia)
    # Tomamos los primeros 4 clientes y actualizamos su CUIT en DB para que matchee
    cuits_extracto = ["30709212083", "20123456789", "30716234561", "27987654321"]
    importes_fechas = [
        (150000.0, "2026-02-01"),
        (300000.0, "2026-02-03"),
        (8500.0, "2026-02-08"),
        (25000.0, "2026-02-27"),
    ]

    pagos_creados = []
    for i, (cuit_target, (importe, fecha)) in enumerate(zip(cuits_extracto, importes_fechas)):
        cliente = clientes[i]
        # Actualizar CUIT del cliente para que matchee con el extracto
        # (no hay endpoint público — saltamos esto, pero podemos crear pagos por importe + fecha)
        # El matching de _match_credito_a_pago busca PRIMERO por CUIT y SI NO hay match, busca por importe+fecha exacta
        # Crear pago por importe + fecha
        r = requests.post(f"{BASE}/pagos/", json={
            "cliente_id": cliente["id"],
            "importe": importe,
            "forma_pago": "transferencia",
            "fecha": fecha,
            "fuente_pago": f"QA test {i+1}",
        }, headers=h)
        if r.status_code == 201:
            pago = r.json()["pago"]
            pagos_creados.append(pago)
            print(f"  OK Pago #{pago['id']} cliente={cliente['name']} importe=${importe} fecha={fecha}")
        else:
            print(f"  FAIL {r.status_code} {r.text[:120]}")

    print(f"\nTotal: {len(pagos_creados)} pagos creados, listos para matching por importe+fecha exacta.")


if __name__ == "__main__":
    main()
