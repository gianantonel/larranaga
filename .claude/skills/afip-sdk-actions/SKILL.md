---
name: afip-sdk-actions
description: Usar este skill cuando el usuario pida integrar, usar o automatizar algo con AFIP / ARCA / AFIP SDK en el proyecto Larrañaga (estudio contable AGEP). Activar ante pedidos como "emitir factura electrónica", "consultar padrón de un CUIT", "descargar constancia de inscripción", "traer Mis Comprobantes", "Mis Retenciones", "SIPER", "libro IVA digital", "agregar acción AFIP al dashboard del colaborador", "crear endpoint FastAPI que llame a AFIP", "automatizar trámite ARCA con clave fiscal", "usar wsfe / ws_sr_constancia_inscripcion / padrón A4 A5 A13", o cualquier integración con https://app.afipsdk.com. También cuando se deba decidir entre Web Service (certificado) y Automatización (clave fiscal scraping).

version: 2.1.0
last_updated: 2026-04-22 (R-05 Mis Retenciones validado end-to-end con El Alba 2025-12)
---

> **Última actualización: 2026-04-22** — Se agregó wrapper genérico de Automatizaciones (`automations.py`) y CLI `retenciones.py` para R-05, validado con Agropecuaria El Alba período 2025-12 (7 percepciones IVA, agente 30500012516, total $8.045,13). Ver secciones **§ 0**, **§ 2.b**, **§ 9** y **§ 12**.

# AFIP SDK Actions — Integración en backend Larrañaga

Guía operativa para agregar acciones que consumen AFIP (ARCA) vía **app.afipsdk.com**. Refleja el estado actual del paquete `backend/app/afip_sdk/` y las convenciones validadas contra AFIP real (confirmado el 2026-04-21 con Agropecuaria El Alba, última Factura A Nro 41, CAE `86151427323266`; y el 2026-04-22 con la automation `mis-retenciones` del mismo CUIT).

Documentación complementaria: [`README.md` § Integración AFIP SDK](../../../README.md), [`AGENTS.md`](../../../AGENTS.md).

---

## 0. Qué ya existe vs qué falta construir

**Hecho y funcionando:**
- Paquete CLI `backend/app/afip_sdk/` con `client.py` (factory), `bootstrap.py` (alta de cert+WSAuth), `smoke_test.py`, `info.py`.
- **Wrapper de Automatizaciones** (`automations.py`) + **CLI Mis Retenciones** (`retenciones.py`) — usa clave fiscal, persiste JSON crudo en `backend/afip_raw/{cuit}/{automation}/{period}.json`.
- Alta de clientes vía CLI (`backend/scripts/create_client.py`) sin pasar por la UI.
- Persistencia de cert+key en `backend/afip_certs/{CUIT}-{env}.(cert|key)` (gitignoreado).
- Validación end-to-end en producción contra un CUIT real (Agropecuaria El Alba, CUIT `23311348949`, pto vta 6) — **WS** (Factura A #41, CAE 86151427323266) y **Automatización** (`mis-retenciones` período 2025-12, 7 percepciones IVA).

**Pendiente (construir cuando se pida):**
- Endpoints FastAPI bajo `/api/afip/...` y `/api/retenciones/...` que expongan las operaciones al frontend.
- Modelo SQLAlchemy `RetencionPercepcion` + migración (persistir resultados de `mis-retenciones` para cruzar con Mis Comprobantes).
- Cruce automático Col AB (Otros Tributos) de Mis Comprobantes Recibidos → código Holistor (PIVC/PIBA/PGAN) vía match `(cuit_emisor, fecha, importe)`.
- Más automatizaciones: `mis-comprobantes`, constancias, SIPER, Libro IVA Digital.
- Tabla `afip_action_log` para auditoría.
- Catálogos cacheados en DB (voucher_types, alícuotas, condición IVA receptor, etc.).
- UI por cliente con botones de acción + polling para jobs async.

---

## 1. Clasificar la acción antes de codear

**Pregunta siempre:** ¿la acción está expuesta como **Web Service SOAP** por ARCA, o solo está en el **portal web** (requiere scraping)?

| Tipo | Autenticación | Cómo se invoca |
|------|---------------|----------------|
| **Web Service** (facturación, padrón, MiPyMe, exportación, carta de porte) | CUIT + **cert/key X.509** | Usar el paquete `app.afip_sdk` (via `load_context` → `ctx.afip.ElectronicBilling.*` u otros `ctx.afip.*`) |
| **Automatización** (constancia PDF, Mis Comprobantes, Mis Retenciones, SIPER, SICORE, Mi Simplificación, DDJJ monotributo, presentación Libro IVA Digital) | CUIT + **clave fiscal** | `afip.createAutomation(...)` (sync o async con `job_id`) o POST REST a `/api/v1/automations` |

Si no está clara la clasificación: dashboard de app.afipsdk.com y/o `https://docs.afipsdk.com/sitemap.md`.

---

## 2. Variables de entorno (`backend/.env`)

```env
AFIP_SDK_ACCESS_TOKEN=...       # Token de la cuenta en app.afipsdk.com (identifica la cuenta, no un CUIT)
ENCRYPTION_KEY=...              # Fernet key (singular) para clients.clave_fiscal_encrypted
```

⚠️ **La variable se llama `ENCRYPTION_KEY` (singular).** Si se escribe `ENCRYPTION_KEYS`, `backend/app/security.py` cae a una Fernet key random por proceso y rompe las credenciales cifradas al reiniciar. Bug histórico ya corregido pero fácil de reintroducir.

El entorno (dev/prod) **no** es una variable global — se pasa por flag `--prod` o argumento `production=True`. Permite que el mismo proceso opere contra homologación y producción según el caso.

Nunca loguear el `AFIP_SDK_ACCESS_TOKEN` ni la clave fiscal. No deben salir del backend ni aparecer en respuestas HTTP.

---

## 3. Estructura actual del paquete

```
backend/
├── app/
│   ├── afip_sdk/
│   │   ├── __init__.py
│   │   ├── client.py        # load_context() — factory + persist cert/key
│   │   ├── bootstrap.py     # CLI: createCert + createWSAuth
│   │   ├── smoke_test.py    # CLI: FEDummy + último comprobante + detalle
│   │   └── info.py          # CLI: FEParamGet* paramétrico
│   ├── models.py            # Client.clave_fiscal_encrypted (Text, Fernet)
│   ├── security.py          # encrypt_credential / decrypt_credential
│   └── routers/
│       └── clients.py       # POST/PUT /clients/ acepta clave_fiscal plaintext y cifra
├── afip_certs/              # {CUIT}-{dev|prod}.cert / .key — NO commitear
└── scripts/
    └── create_client.py     # Alta de cliente via API (CLI)
```

Cuando se agreguen endpoints HTTP de AFIP, el lugar es `backend/app/routers/afip.py` (seguir la convención de los routers existentes, no inventar `app/api/routes/`).

---

## 4. Comandos listos para usar

```powershell
cd backend

# Alta de cliente con clave fiscal cifrada
.venv\Scripts\python -m scripts.create_client --name "Razón social" --cuit "XX-XXXXXXXX-X" `
  --clave-fiscal "..." --fiscal-condition "Responsable Inscripto"

# Bootstrap (one-time por CUIT+entorno). Genera cert X.509 y registra WSAuth wsfe.
.venv\Scripts\python -m app.afip_sdk.bootstrap --client-id 12          # homologación
.venv\Scripts\python -m app.afip_sdk.bootstrap --client-id 12 --prod   # producción

# Smoke test — FEDummy + último comprobante + detalle
.venv\Scripts\python -m app.afip_sdk.smoke_test --client-id 12 --prod --punto-venta 6 --tipo-cbte 1

# Información paramétrica (sales-points | voucher-types | document-types | currencies | aliquots | concepts | taxes)
.venv\Scripts\python -m app.afip_sdk.info --client-id 12 --prod --what sales-points
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


## 5. Agregar una operación WSFE nueva — patrón

`load_context()` devuelve un `Afip()` ya inicializado con cert+key descifrados y cargados. No reinventar el factory.

```python
# backend/app/afip_sdk/emitir_factura.py (nuevo, ejemplo)
import argparse
from .client import load_context, env_label


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--client-id", type=int, required=True)
    p.add_argument("--prod", action="store_true")
    p.add_argument("--pto-venta", type=int, required=True)
    p.add_argument("--tipo-cbte", type=int, required=True)
    # ... resto de flags de la factura
    args = p.parse_args()

    ctx = load_context(client_id=args.client_id, production=args.prod)
    eb = ctx.afip.ElectronicBilling

    data = {
        "CantReg": 1, "PtoVta": args.pto_venta, "CbteTipo": args.tipo_cbte,
        "Concepto": 1, "DocTipo": 80, "DocNro": 30708552654,
        "CbteDesde": 1, "CbteHasta": 1,
        # ... ImpTotal, ImpNeto, Iva[], CondicionIVAReceptorId, MonId, MonCotiz, etc.
    }
    res = eb.createNextVoucher(data)
    print(res)  # {'CAE': '...', 'CAEFchVto': '...', 'voucher_number': N}
```

Cuando se expone como endpoint HTTP, la firma es:

```python
# backend/app/routers/afip.py (cuando exista)
from fastapi import APIRouter, Depends, HTTPException
from ..afip_sdk.client import load_context
from .auth import get_current_user
from .. import schemas

router = APIRouter(prefix="/afip", tags=["afip"])


@router.post("/factura/{client_id}")
def emitir_factura(client_id: int, payload: schemas.FacturaIn, user=Depends(get_current_user)):
    ctx = load_context(client_id=client_id, production=True)
    try:
        res = ctx.afip.ElectronicBilling.createNextVoucher(payload.to_wsfe_dict())
    except Exception as e:
        raise HTTPException(502, f"AFIP SDK: {e}")
    # TODO: auditar en afip_action_log
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

- El colaborador **nunca** envía CUIT / cert / key / clave fiscal: todo se resuelve desde `client_id`.
- Validar permisos sobre el cliente antes de operar (colaborador solo sus asignados — patrón ya implementado en `routers/clients.py`, replicarlo).
- Mapear DTO del frontend a WSFE exacto (`CbteTipo`, `Concepto`, `Iva[]`, `CondicionIVAReceptorId`). Usar enums en backend, no strings libres.
- **`createNextVoucher`**: nunca reintentar a ciegas — puede haberse emitido. Antes de reintentar, llamar `getLastVoucher(pto, tipo)` para ver si avanzó la numeración.

---

## 6. Flow completo de alta de un CUIT nuevo en producción

El caso típico "onboarding de un cliente nuevo para facturar":

1. Alta del cliente con clave fiscal:
   ```
   python -m scripts.create_client --name "..." --cuit "..." --clave-fiscal "..."
   ```
2. Bootstrap en **producción** (usa la clave fiscal descifrada para que app.afipsdk.com genere el cert):
   ```
   python -m app.afip_sdk.bootstrap --client-id N --prod
   ```
3. Consultar qué ptos de venta tiene habilitados en AFIP:
   ```
   python -m app.afip_sdk.info --client-id N --prod --what sales-points
   ```
4. Smoke test con un pto de venta válido:
   ```
   python -m app.afip_sdk.smoke_test --client-id N --prod --punto-venta X --tipo-cbte 1
   ```

Si [1/3] (FEDummy) falla → problema de conectividad o `AFIP_SDK_ACCESS_TOKEN` inválido.
Si [2/3] falla con `11002` → pto de venta no está habilitado en AFIP para ese CUIT/WS (verificar con `info`).
Si [2/3] falla con `Certificado/Key obligatorio` → falta correr `bootstrap` (o se borró el archivo en `afip_certs/`).
Si [2/3] falla con `Too few bytes to read ASN.1` → el PEM está con CRLF; `client.py` ya normaliza a LF, rebootstrap.

---

## 7. Automatizaciones — wrapper implementado, catálogo por expandir

Las automatizaciones de app.afipsdk.com usan **clave fiscal** (scraping de portales ARCA), a diferencia de los WS que usan cert/key. Implementación viva: `backend/app/afip_sdk/automations.py`.

```python
from .client import load_context
from .automations import run_automation, save_raw

ctx = load_context(client_id=12, production=True)
payload = run_automation(ctx, "mis-retenciones", {
    "cuit": str(ctx.cuit_int),
    "username": str(ctx.cuit_int),
    "password": ctx.clave_fiscal,
    "mode": "filter",
    "page": 0, "size": 100,
    "filters": {
        "descripcionImpuesto": "IVA",
        "fechaRetencionDesde": "2025-12-01",
        "fechaRetencionHasta": "2025-12-31",
        "impuestoRetenido": 217,
        "tipoImpuesto": "IMP",
        "percepciones": True, "retenciones": True,
    },
}, wait=True, include_credentials=False)
save_raw(ctx, "mis-retenciones", "2025-12", payload)
```

Convenciones:

- **Async** — `wait=True` deja que el SDK haga polling (~2 min máx). Para UI, usar `wait=False` + `GET /afip/jobs/{id}` + polling cliente 3–5 s.
- Los credenciales van **dentro de `params`** (`username`, `password`, `cuit`), no como header. Por eso `run_automation(..., include_credentials=False)` y se arman a mano cuando la automation lo requiere.
- JSON crudo siempre a `backend/afip_raw/{cuit}/{automation}/{period}.json` — sirve como cache y para debugging.

### 7.a `mis-retenciones` — schema oficial

Doc fuente: https://afipsdk.com/docs/automations/mis-retenciones/nodejs

| Param | Tipo | Notas |
|---|---|---|
| `cuit` | string | CUIT a consultar |
| `username` | string | CUIT con el que se loguea (mismo que `cuit` salvo delegación) |
| `password` | string | Clave fiscal |
| `mode` | string | **`"filter"`** o **`"preset"`** (los únicos valores válidos) |
| `page` | int | **Arranca en 0** (no 1) |
| `size` | int | Default recomendado: 100 |

**Cuando `mode="filter"`** todos requeridos dentro de `filters`:
`descripcionImpuesto`, `fechaRetencionDesde` (yyyy-mm-dd), `fechaRetencionHasta`, `impuestoRetenido` (int), `tipoImpuesto` (usar `"IMP"`), `percepciones` (bool), `retenciones` (bool).

**Cuando `mode="preset"`** usar `preset` ∈ `{percepcion-ganancias, percepcion-bienes-personales, retencion-ganancias}`. **No cubre IVA** — para IVA siempre `filter` con `impuestoRetenido=217`.

Códigos AFIP `impuestoRetenido` conocidos: **217=IVA**, **11=Ganancias (ret)**, **10=Ganancias (perc)**, **767=Bienes Personales**.

Response: `data.rows[]` con `cuitAgenteRetencion, impuestoRetenido, codigoRegimen, fechaRetencion, importeRetenido, numeroComprobante, descripcionOperacion, fechaComprobante`.

Mapa a código Holistor (col AR en HWCRARCA): 217→`PIVC`, 10/11→`PGAN`, 767→`OTRO`. Definido en `retenciones.py:IMPUESTO_TO_HOLISTOR`.

### 7.b Otras automatizaciones candidatas (por implementar)

Al sumar una nueva automation: antes de codear, leer la doc oficial (`https://afipsdk.com/docs/automations/<slug>/nodejs`) para capturar params exactos — probing a ciegas quema el cupo mensual de automatizaciones (100/mes en el plan actual).

- `constancia-inscripcion` — PDF
- `mis-comprobantes-emitidos` / `mis-comprobantes-recibidos` (clave para el cruce de R-05)
- `siper` — perfil de riesgo
- `libro-iva-digital`
- `monotributo-recategorizacion`
- `mi-simplificacion` — empleados

Mantener un catálogo en `backend/app/afip_sdk/catalog.py` (slug, nombre visible, params requeridos, tipo WS/automation) cuando haya ≥3 automatizaciones implementadas.

---

## 8. Web Services cheat sheet

```python
# --- Healthcheck
eb.getServerStatus()

# --- Facturación
eb.getLastVoucher(pto_vta, tipo)
eb.getVoucherInfo(nro, pto_vta, tipo)     # respuesta anidada bajo "ResultGet"
eb.createNextVoucher(data)                 # emite y devuelve CAE
eb.getVoucherTypes()
eb.getAliquotTypes()
eb.executeRequest('FEParamGetCondicionIvaReceptor')

# --- Padrón
afip.RegisterInscriptionProof.getTaxpayerDetails(20111111111)
# Padrón ampliado: wsid = ws_sr_padron_a4 | ws_sr_padron_a5 | ws_sr_padron_a13
#                  method = getPersona_v2 / getPersonaList_v2

# Catálogos a cachear en DB (cambian muy poco):
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


### Tipos de comprobante más usados

| Código | Tipo |
|---|---|
| 1  | Factura A |
| 6  | Factura B |
| 11 | Factura C |
| 51 | Factura M |
| 19 | Factura E (exportación) |

---

## 9. Gotchas observados en este repo

Estos errores nos mordieron durante la integración — prevenir antes que depurar:

| Síntoma | Causa | Remedio |
|---|---|---|
| `InvalidToken` al descifrar clave fiscal | `.env` dice `ENCRYPTION_KEYS` en vez de `ENCRYPTION_KEY`; `security.py` cae a Fernet random | Fixear `.env`, reiniciar backend, **recargar** la clave fiscal (`PUT /clients/{id}`) |
| `El campo Certificado es obligatorio` post-bootstrap | `afip.py` **no persiste** cert/key retornados por `createCert`; hay que guardarlos y reinyectarlos en cada `Afip()` | `client.py` ya lo hace con `save_cert_key`/`load_cert_key`. Si fallara, rebootstrap con `--skip-wsauth` |
| `Too few bytes to read ASN.1 value` | PEMs escritos con `write_text` en Windows → CRLF dobles | `client.py` escribe en binario normalizando a LF. No usar `Path.write_text` para PEMs |
| `(11002) Punto de venta no habilitado` | El PV pasado no está declarado para el WS del CUIT en AFIP | `info --what sales-points` para listar los válidos |
| `createCert` → `already exists` | El alias ya está tomado en app.afipsdk.com | `--alias <otro>` o `--skip-cert` si el PEM ya está en disco |

---

## 10. Seguridad — checklist por acción HTTP nueva

- [ ] Requiere `get_current_user` (colaborador autenticado)
- [ ] Verifica que el colaborador tenga permiso sobre `client_id` (asignación en `client_collaborators`)
- [ ] Clave fiscal se descifra solo en memoria, nunca loguear ni devolver en response
- [ ] `AFIP_SDK_ACCESS_TOKEN` solo en backend
- [ ] Log en `afip_action_log` (cuando exista la tabla) con metadata, sin payloads sensibles
- [ ] Errores al frontend: mensaje en castellano, sin stacktrace
- [ ] Tests: mockear `Afip` y `httpx`, **nunca** golpear AFIP desde CI

---

## 11. Cliente real para validación en prod

**Agropecuaria El Alba S.R.L.** — CUIT `23-31134894-9`, `client_id=12` en la DB.

- Único pto de venta habilitado en WSFE producción: **6** (EmisionTipo: CAE - RI IVA).
- Última Factura A conocida: Nro 41, fecha 2026-04-13, total $12.100.000, CAE `86151427323266`, receptor CUIT 30708552654.
- Usarlo para smoke tests y para validar cualquier operación nueva de consulta antes de habilitarla para todos los clientes.

Para desarrollo de WSFE en homologación (dev): CUIT genérico de prueba `20409378472` (sin ligar a ningún cliente real).
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
