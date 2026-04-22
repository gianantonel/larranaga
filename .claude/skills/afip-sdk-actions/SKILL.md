---
name: afip-sdk-actions
description: Usar este skill cuando el usuario pida integrar, usar o automatizar algo con AFIP / ARCA / AFIP SDK en el proyecto Larrañaga (estudio contable AGEP). Activar ante pedidos como "emitir factura electrónica", "consultar padrón de un CUIT", "descargar constancia de inscripción", "traer Mis Comprobantes", "Mis Retenciones", "SIPER", "libro IVA digital", "agregar acción AFIP al dashboard del colaborador", "crear endpoint FastAPI que llame a AFIP", "automatizar trámite ARCA con clave fiscal", "usar wsfe / ws_sr_constancia_inscripcion / padrón A4 A5 A13", o cualquier integración con https://app.afipsdk.com. También cuando se deba decidir entre Web Service (certificado) y Automatización (clave fiscal scraping).
version: 2.0.0
---

# AFIP SDK Actions — Integración en backend Larrañaga

Guía operativa para agregar acciones que consumen AFIP (ARCA) vía **app.afipsdk.com**. Refleja el estado actual del paquete `backend/app/afip_sdk/` y las convenciones validadas contra AFIP real (confirmado el 2026-04-21 con Agropecuaria El Alba, última Factura A Nro 41, CAE `86151427323266`).

Documentación complementaria: [`README.md` § Integración AFIP SDK](../../../README.md), [`AGENTS.md`](../../../AGENTS.md).

---

## 0. Qué ya existe vs qué falta construir

**Hecho y funcionando:**
- Paquete CLI `backend/app/afip_sdk/` con `client.py` (factory), `bootstrap.py` (alta de cert+WSAuth), `smoke_test.py`, `info.py`.
- Alta de clientes vía CLI (`backend/scripts/create_client.py`) sin pasar por la UI.
- Persistencia de cert+key en `backend/afip_certs/{CUIT}-{env}.(cert|key)` (gitignoreado).
- Validación end-to-end en producción contra un CUIT real (Agropecuaria El Alba, CUIT `23311348949`, pto vta 6).

**Pendiente (construir cuando se pida):**
- Endpoints FastAPI bajo `/api/afip/...` que expongan las operaciones al frontend.
- Wrapper de automatizaciones (`/api/v1/automations/*` de app.afipsdk.com) — scraping con clave fiscal para constancias, Mis Comprobantes, SIPER, Libro IVA Digital, etc.
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

## 7. Automatizaciones (aún no implementadas en este repo)

Cuando se pida una acción que no tiene Web Service (constancias PDF, Mis Comprobantes, SIPER, Libro IVA Digital presentación, etc.), la ruta es `afip.createAutomation(name, params, wait=False)`.

- Son **asíncronas**. No bloquear el request HTTP esperando `finished`.
- Patrón async: endpoint `POST` devuelve `job_id`, endpoint `GET /afip/jobs/{job_id}` hace polling, frontend hace polling cada 3–5 s.
- Requieren la clave fiscal descifrada — `ctx.clave_fiscal` ya viene disponible en `ClientAfipContext`.
- Cuando se implemente el wrapper, vivirá como `backend/app/afip_sdk/automations.py` (consistente con el resto del paquete, no en `services/`).

Nombres de automatizaciones candidatas a implementar primero (confirmar slug exacto en el panel de app.afipsdk.com):

- `constancia-inscripcion` — PDF de constancia
- `mis-comprobantes-emitidos` / `mis-comprobantes-recibidos`
- `mis-retenciones`
- `siper` — perfil de riesgo
- `libro-iva-digital`
- `monotributo-recategorizacion`
- `mi-simplificacion` — empleados

Cada una tiene **params propios** (rango de fechas, punto de venta, período). Mantener un catálogo en `backend/app/afip_sdk/catalog.py` (slug, nombre visible, params requeridos, tipo WS/automation).

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
