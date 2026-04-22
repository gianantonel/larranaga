"""Scripts y helpers para operar con AFIP vía app.afipsdk.com.

Sub-modulos:
    client       helper para construir una instancia Afip() a partir de un cliente de la DB
    bootstrap    alta de certificado + WSAuth para un CUIT (one-time per CUIT/entorno)
    smoke_test   FEDummy + FECompUltimoAutorizado + FECompConsultar

Uso:
    python -m app.afip_sdk.bootstrap   --client-id 12
    python -m app.afip_sdk.smoke_test  --client-id 12
"""
