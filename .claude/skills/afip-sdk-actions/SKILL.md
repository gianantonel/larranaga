---
name: afip-sdk-actions
description: Usar este skill cuando el usuario pida integrar, usar o automatizar algo con AFIP / ARCA / AFIP SDK en el proyecto Larrañaga (estudio contable AGEP). Activar ante pedidos como "emitir factura electrónica", "consultar padrón de un CUIT", "descargar constancia de inscripción", "traer Mis Comprobantes", "Mis Retenciones", "SIPER", "libro IVA digital", "agregar acción AFIP al dashboard del colaborador", "crear endpoint FastAPI que llame a AFIP", "automatizar trámite ARCA con clave fiscal", "usar wsfe / ws_sr_constancia_inscripcion / padrón A4 A5 A13", o cualquier integración con https://app.afipsdk.com. También cuando se deba decidir entre Web Service (certificado) y Automatización (clave fiscal scraping).
version: 1.0.0
---

# AFIP SDK Actions — Integración en backend Larrañaga

Este skill indica **cómo implementar correcta y eficientemente** una acción que consume la API de AFIP SDK dentro del proyecto Larrañaga (FastAPI + React). El objetivo de cada acción: que un colaborador del estudio seleccione un cliente, apriete un botón, complete los pocos datos faltantes y el backend ejecute la operación en ARCA usando el **CUIT + certificado** o **CUIT + clave fiscal** que ya están en la DB.

Lectura de referencia del repo: `afip_sdk.md` y `afip_dev_credentials.txt` en la raíz.

---

## 0. Antes de escribir una sola línea: clasificar la acción

**Preguntar siempre:** ¿la acción está expuesta como **Web Service SOAP** por ARCA, o solo está en el **portal web** (requiere scraping)?

| Tipo | Autenticación | Cómo llamarla desde el SDK |
|------|---------------|---------------------------|
| **Web Service** (facturación, padrón, MiPyMe, exportación, carta de porte) | CUIT + **certificado digital** `.crt/.key` | Clase `afip.XXX` o `POST /api/v1/afip/requests` |
| **Automatización** (constancia PDF, Mis Comprobantes, Mis Retenciones, SIPER, SICORE, Mi Simplificación, DDJJ monotributo, Libro IVA Digital presentación) | CUIT + **clave fiscal** | `POST /api/v1/automations/<nombre>` (async, con `job_id`) |

Si no está clara la clasificación: consultar el dashboard en https://app.afipsdk.com y/o el sitemap `https://docs.afipsdk.com/sitemap.md` antes de codear.

---

## 1. Variables de entorno requeridas (`backend/.env`)

```
AFIP_SDK_ACCESS_TOKEN=<contenido de AFIP_SDK_ACCESS_TOKEN/Access_Token_Afip_SDK.txt>
AFIP_ENV=dev              # o "prod"
AFIP_CLAVE_FISCAL_KEY=<Fernet key base64 para cifrar clave fiscal en DB>
```

Nunca loguear estos valores. El token y la clave fiscal jamás deben salir del backend ni aparecer en respuestas al frontend.

---

## 2. Estructura de archivos a crear/usar

```
backend/app/services/
  afip_client.py         # factory de la clase Afip() por cliente (Web Services)
  afip_automations.py    # wrapper httpx para /automations/* (scraping)
  afip_crypto.py         # Fernet encrypt/decrypt de clave fiscal
backend/app/api/routes/
  afip.py                # endpoints /api/afip/<accion>/{client_id}
backend/app/models/
  afip_action_log.py     # auditoría (quién, cuándo, qué, ok/error)
```

---

## 3. Plantilla — Web Service (ej. emitir factura B)

```python
# backend/app/services/afip_client.py
from afip import Afip
from app.core.config import settings

def build_afip(client) -> Afip:
    cfg = {"CUIT": int(client.cuit), "access_token": settings.AFIP_SDK_ACCESS_TOKEN}
    if settings.AFIP_ENV == "prod":
        if not (client.afip_cert and client.afip_key):
            raise ValueError(f"Cliente {client.id} sin certificado AFIP cargado")
        cfg["cert"] = client.afip_cert
        cfg["key"]  = client.afip_key
    return Afip(cfg)
```

```python
# backend/app/api/routes/afip.py
@router.post("/factura/{client_id}")
def emitir_factura(client_id: int, payload: FacturaIn, db=Depends(get_db), user=Depends(current_user)):
    client = get_client_or_404(db, client_id)
    afip = build_afip(client)
    data = payload.to_wsfe_dict()               # mapear DTO del frontend al formato WSFE
    try:
        res = afip.ElectronicBilling.createNextVoucher(data)
    except Exception as e:
        log_afip_action(db, user, client, "emitir_factura", ok=False, error=str(e))
        raise HTTPException(502, f"AFIP SDK: {e}")
    log_afip_action(db, user, client, "emitir_factura", ok=True, meta={"voucher": res["voucher_number"]})
    return {"cae": res["CAE"], "cae_vto": res["CAEFchVto"], "numero": res["voucher_number"]}
```

Puntos importantes:
- **Nunca** pedir al colaborador CUIT/cert/key: se arman desde `client`.
- Mapear el DTO del frontend a los campos exactos de WSFE (`CbteTipo`, `Concepto`, `Iva[]`, `CondicionIVAReceptorId`). Usar enums en el backend, no strings libres.
- En dev usar CUIT `20409378472` (override por flag de testing, no por cliente real).

---

## 4. Plantilla — Automatización (ej. descargar constancia de inscripción)

Las automatizaciones son **asíncronas**: devuelven `job_id`. Nunca bloquear el request HTTP del colaborador esperando el `finished`.

```python
# backend/app/services/afip_automations.py
import httpx
from app.core.config import settings

BASE = "https://app.afipsdk.com/api/v1"

async def start_automation(name: str, tax_id: str, password: str, params: dict) -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"{BASE}/automations/{name}",
            headers={"Authorization": f"Bearer {settings.AFIP_SDK_ACCESS_TOKEN}"},
            json={"tax_id": tax_id, "password": password, "params": params},
        )
        r.raise_for_status()
        return r.json()["job_id"]

async def get_job(job_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            f"{BASE}/automations/jobs/{job_id}",
            headers={"Authorization": f"Bearer {settings.AFIP_SDK_ACCESS_TOKEN}"},
        )
        r.raise_for_status()
        return r.json()   # {status: queued|running|finished|failed, result: {...}}
```

```python
# backend/app/api/routes/afip.py
@router.post("/constancia/{client_id}")
async def iniciar_constancia(client_id: int, db=Depends(get_db), user=Depends(current_user)):
    client = get_client_or_404(db, client_id)
    clave = decrypt_clave_fiscal(client.clave_fiscal_enc)   # Fernet
    job_id = await start_automation("constancia-inscripcion",
                                    tax_id=client.cuit, password=clave, params={})
    save_job(db, user, client, "constancia", job_id)
    return {"job_id": job_id, "status": "queued"}

@router.get("/jobs/{job_id}")
async def poll_job(job_id: str, user=Depends(current_user)):
    data = await get_job(job_id)
    return data   # frontend hace polling cada 3–5 s
```

El frontend muestra un spinner y al `finished` redirige al `result.pdf_url` o descarga el archivo.

---

## 5. Nombres de automatizaciones más usadas en el estudio

Confirmar el slug exacto en el dashboard de AFIP SDK (`app.afipsdk.com`) antes de usar. Nombres orientativos:

- `constancia-inscripcion` — PDF de constancia
- `mis-comprobantes-emitidos` / `mis-comprobantes-recibidos` — listado + PDFs
- `mis-retenciones` — retenciones sufridas
- `siper` — perfil de riesgo
- `libro-iva-digital` — generar/presentar
- `monotributo-recategorizacion`
- `mi-simplificacion` — empleados

Cada una tiene **params propios** (rango de fechas, punto de venta, período). El frontend debe renderizar un form dinámico a partir de un catálogo mantenido en `backend/app/services/afip_catalog.py`.

---

## 6. Web Services más usados — cheat sheet Python

```python
# Padrón — datos fiscales completos de un CUIT
afip.RegisterInscriptionProof.getTaxpayerDetails(20111111111)

# Padrón ampliado (A4/A5/A13) vía endpoint genérico REST
# wsid = ws_sr_padron_a4 | ws_sr_padron_a5 | ws_sr_padron_a13
# method = getPersona_v2 / getPersonaList_v2

# Facturación
afip.ElectronicBilling.getServerStatus()
afip.ElectronicBilling.getLastVoucher(pto_vta, tipo)
afip.ElectronicBilling.getVoucherInfo(nro, pto_vta, tipo)
afip.ElectronicBilling.createNextVoucher(data)   # emite y devuelve CAE
afip.ElectronicBilling.getVoucherTypes()
afip.ElectronicBilling.getAliquotTypes()
afip.ElectronicBilling.executeRequest('FEParamGetCondicionIvaReceptor')

# Catálogos que conviene cachear en DB (cambian muy poco):
#   voucher_types, aliquot_types, condicion_iva_receptor, puntos_venta,
#   monedas (FEParamGetTiposMonedas), conceptos, doc_tipos.
```

---

## 7. Errores y reintentos

- AFIP SDK devuelve errores con estructura `{error: {code, message}}`. Capturar y **mapear a mensajes en castellano** para el colaborador (ej. "Cliente sin punto de venta habilitado").
- El TA se renueva automáticamente; si aparece `Token no válido`, reintentar una vez con `force_create: true` en `/afip/auth` (solo para el wrapper REST, el SDK Python lo hace solo).
- Para `createNextVoucher`: **nunca** reintentar a ciegas si la respuesta no llegó — puede haberse emitido el comprobante. Consultar `getLastVoucher` antes de reintentar para evitar saltos de numeración.
- Rate limit del SDK: serializar llamadas por cliente (lock en Redis o similar) si hay ráfagas.

---

## 8. Seguridad — checklist por acción nueva

- [ ] Usa `current_user` (solo colaboradores autenticados)
- [ ] Verifica que el colaborador tenga permiso sobre `client_id` (asignación en DB)
- [ ] Clave fiscal se desencripta solo dentro del request y no se loguea
- [ ] `access_token` solo en backend, nunca enviado al frontend
- [ ] Registro en `afip_action_log` (sin payloads sensibles, solo metadata)
- [ ] Errores no exponen stacktrace al frontend

---

## 9. Modo desarrollo

- `AFIP_ENV=dev` + CUIT `20409378472` en las pruebas de WS.
- Para automatizaciones no hay clave fiscal de prueba genérica: usar un cliente real marcado como `sandbox` con consentimiento.
- Tests unitarios: mockear `httpx` / la clase `Afip` — nunca golpear AFIP desde CI.

---

## 10. Agregar una acción nueva — workflow

1. Identificar si es WS o automatización (sección 0).
2. Si es WS: ¿el SDK Python la envuelve? Sí → usar la clase. No → `executeRequest` o REST `/afip/requests`.
3. Crear servicio en `services/`, endpoint en `api/routes/afip.py`, DTO en `schemas/`.
4. Registrar en el catálogo `afip_catalog.py` (slug, nombre visible, params requeridos, tipo).
5. En el frontend: agregar la acción al panel del cliente — botón + modal con form generado desde el catálogo.
6. Si es async: UI con estados `queued → running → finished/failed` + descarga del resultado.
7. Auditoría + tests (mock).
8. Probar en `dev` con CUIT 20409378472 antes de habilitar en `prod`.
