# AFIP SDK — Guía de uso en el proyecto Larrañaga

Resumen práctico de cómo integrar **AFIP SDK** (https://afipsdk.com) en el backend Python (FastAPI) del estudio para automatizar acciones que hoy se hacen manualmente en ARCA/AFIP. Los colaboradores dispararán estas acciones desde el frontend con un botón; el sistema tomará el **CUIT + Clave Fiscal** del cliente desde la DB y pedirá solo los datos puntuales.

Fuentes: `docs.afipsdk.com/integracion/python`, `.../integracion/api`, `.../siguientes-pasos/web-services/*`.

---

## 1. Conceptos clave

- **AFIP SDK** es un proxy/gateway que envuelve los Web Services SOAP de ARCA con una **API REST** moderna + SDKs por lenguaje. Maneja por nosotros: certificados, firma, cacheo y renovación del Ticket de Acceso (TA = `token` + `sign`).
- Autenticación a AFIP SDK: header `Authorization: Bearer <ACCESS_TOKEN>` (token del plan pago, ver `AFIP_SDK_ACCESS_TOKEN/Access_Token_Afip_SDK.txt`).
- Dos modos:
  - **`dev`** (homologación): no necesita certificado. Se usa el CUIT de prueba `20-40937847-2`.
  - **`prod`**: requiere certificado digital `.crt` + clave privada `.key` del cliente (subidos en la DB del estudio o montados como secretos).
- Todas las llamadas incluyen `environment: "dev" | "prod"` y el `tax_id` (CUIT del cliente).

---

## 2. Instalación (Python)

```bash
pip install afip.py
```

Agregar a `backend/requirements.txt`.

Recomendado: crear `backend/app/services/afip_client.py` que construya una instancia de `Afip` por cliente del estudio, leyendo CUIT / cert / key desde la tabla de clientes.

```python
from afip import Afip
from app.core.config import settings  # AFIP_SDK_ACCESS_TOKEN

def build_afip_for_client(client) -> Afip:
    cfg = {
        "CUIT": int(client.cuit),
        "access_token": settings.AFIP_SDK_ACCESS_TOKEN,
    }
    if settings.AFIP_ENV == "prod":
        cfg["cert"] = client.afip_cert  # string PEM desde DB
        cfg["key"]  = client.afip_key
    return Afip(cfg)
```

En **dev** solo se necesita el access_token + CUIT de prueba (20409378472). No se usa clave fiscal: el SDK maneja la autenticación de ARCA, no hay login web con clave fiscal para los web services oficiales.

> ⚠️ Nota sobre "Clave Fiscal": los **web services de ARCA** (facturación, padrón, etc.) no usan clave fiscal — usan **certificado digital**. La "clave fiscal" solo aparece en las **automatizaciones de scraping** (Mis Comprobantes, Mis Retenciones, descargar constancia PDF, SIPER, etc.), que sí requieren usuario + clave fiscal del contribuyente. Hay que almacenar ambos en la DB según qué acción se dispare.

---

## 3. API REST (alternativa al SDK)

Base: `https://app.afipsdk.com/api/v1`

Headers comunes:
```
Content-Type: application/json
Authorization: Bearer <ACCESS_TOKEN>
```

### 3.1 Endpoint de autenticación (obtener TA)

`POST /afip/auth`

```json
{
  "environment": "dev",
  "tax_id": "20409378472",
  "wsid": "wsfe",
  "force_create": false,
  "cert": "...PEM...",   // solo prod
  "key":  "...PEM..."    // solo prod
}
```
Respuesta:
```json
{ "expiration": "...", "token": "PD94bWw...", "sign": "kEaC..." }
```
El SDK cachea y renueva esto automáticamente.

### 3.2 Endpoint genérico para cualquier método SOAP

`POST /afip/requests`

```json
{
  "environment": "dev",
  "method": "getPersona_v2",
  "wsid": "ws_sr_constancia_inscripcion",
  "params": {
    "token": "{{token}}",
    "sign":  "{{sign}}",
    "cuitRepresentada": "20409378472",
    "idPersona": 20111111111
  }
}
```

Esto permite llamar **cualquier método** de **cualquier WS de ARCA** aunque el SDK no lo envuelva explícitamente — útil para padrones A4/A5/A13, constancia, etc.

---

## 4. Web Services cubiertos por el SDK

| Área | Clase SDK / `wsid` | Uso |
|------|--------------------|-----|
| Factura electrónica A/B/C | `afip.ElectronicBilling` / `wsfe` | Emitir comprobantes, consultar CAE, último número |
| Notas de crédito / débito | `afip.ElectronicBilling` | mismo WS, cambia `CbteTipo` |
| Factura MiPyME (FCE) | `afip.ElectronicBillingMiPyme` / `wsfecred` | FCE A/B/C |
| Factura de exportación | `afip.ElectronicBillingExport` / `wsfex` | Exportación |
| Padrón constancia inscripción | `afip.RegisterInscriptionProof` / `ws_sr_constancia_inscripcion` | `getTaxpayerDetails(cuit)` |
| Padrón A4 / A5 / A13 | `ws_sr_padron_a4`, `_a5`, `_a13` | Datos fiscales ampliados |
| Carta de Porte Electrónica | `afip.ElectronicCargoBill` / `wslpg` | Granos / transporte |

### 4.1 Factura electrónica — snippets

```python
# Emitir siguiente comprobante (auto-incrementa el número)
data = {
  "CantReg": 1, "PtoVta": 1, "CbteTipo": 6,   # 6 = Factura B
  "Concepto": 1, "DocTipo": 99, "DocNro": 0,
  "CbteFch": 20260419,
  "ImpTotal": 121, "ImpNeto": 100, "ImpIVA": 21,
  "ImpTotConc": 0, "ImpOpEx": 0, "ImpTrib": 0,
  "MonId": "PES", "MonCotiz": 1,
  "CondicionIVAReceptorId": 5,                # 5 = Consumidor Final
  "Iva": [{"Id": 5, "BaseImp": 100, "Importe": 21}],  # 5 = 21%
}
res = afip.ElectronicBilling.createNextVoucher(data)
# res["CAE"], res["CAEFchVto"], res["voucher_number"]

# Consultar comprobante ya emitido
afip.ElectronicBilling.getVoucherInfo(numero, pto_vta, tipo)

# Último número emitido
afip.ElectronicBilling.getLastVoucher(pto_vta, tipo)

# Catálogos
afip.ElectronicBilling.getVoucherTypes()
afip.ElectronicBilling.getAliquotTypes()
afip.ElectronicBilling.executeRequest('FEParamGetCondicionIvaReceptor')
```

### 4.2 Padrón — datos de un contribuyente

```python
details = afip.RegisterInscriptionProof.getTaxpayerDetails(20111111111)
# devuelve dict con razón social, domicilio, actividades, impuestos, categoría monotributo, etc.
# None si no existe.
```

Equivalente REST:
```json
POST /api/v1/afip/requests
{"environment":"dev","method":"getPersona_v2","wsid":"ws_sr_constancia_inscripcion",
 "params":{"token":"{{token}}","sign":"{{sign}}",
           "cuitRepresentada":"<cuit_del_cliente>","idPersona":20111111111}}
```

---

## 5. Automatizaciones (scraping de portales ARCA con clave fiscal)

Las **automatizaciones** son distintas de los web services: AFIP SDK loguea con **CUIT + clave fiscal** del contribuyente y scrapea los portales. Ideales para lo que ARCA no expone por WS. Se invocan vía la REST API del SDK (ver docs `app.afipsdk.com/dashboard` → Automatizaciones para el catálogo actualizado y los `endpoints` exactos). Usos típicos en el estudio:

- Descargar **Constancia de Inscripción** PDF
- **Mis Comprobantes** — emitidos y recibidos (listado + descarga PDF)
- **Mis Retenciones** sufridas
- **SIPER** (sistema de perfil de riesgo)
- **SIRE / SICORE** — regímenes de retención
- **Presentación de DDJJ** monotributo / recategorización
- Listado de empleados (**Simplificación Registral** / Mi Simplificación)
- **Libro IVA Digital** — descarga / presentación

Patrón genérico de invocación REST (confirmar nombre de endpoint exacto en dashboard):
```
POST https://app.afipsdk.com/api/v1/automations/<nombre-automatizacion>
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
  "tax_id": "<CUIT del cliente>",
  "password": "<Clave Fiscal del cliente>",
  "params": { ... específicos de cada automatización ... }
}
```

La mayoría son **asíncronas**: devuelven un `job_id` y se pollea `GET /api/v1/automations/jobs/<job_id>` hasta `status: "finished"`, con un `result` que incluye datos estructurados y/o URLs a archivos descargados.

---

## 6. Patrón recomendado para el backend Larrañaga

1. Tabla `clients` ya guarda CUIT y clave fiscal. Agregar columnas opcionales `afip_cert`, `afip_key` (PEM) para los que usan WS de facturación en prod.
2. Servicio `app/services/afip_client.py`: factory `build_afip_for_client(client)` + `call_automation(client, name, params)`.
3. Endpoint FastAPI `/api/afip/<accion>/{client_id}` por cada acción ofrecida al colaborador. El frontend renderiza un formulario con solo los params extra (ej. rango de fechas, punto de venta).
4. Jobs largos → `BackgroundTasks` o Celery, guardar `job_id` en DB y exponer `/api/afip/jobs/{id}` para el polling del frontend.
5. **Seguridad**: nunca loguear el access_token ni la clave fiscal. Cifrar la clave fiscal en DB (Fernet con `AFIP_CLAVE_FISCAL_KEY`).
6. **Entornos**: `AFIP_ENV=dev` por defecto en desarrollo; forzar `prod` solo por cliente en producción.

### Esqueleto de wrapper asíncrono

```python
# app/services/afip_automations.py
import httpx
from app.core.config import settings

BASE = "https://app.afipsdk.com/api/v1"
HEADERS = {"Authorization": f"Bearer {settings.AFIP_SDK_ACCESS_TOKEN}"}

async def run_automation(name: str, tax_id: str, password: str, params: dict) -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/automations/{name}",
                         headers=HEADERS,
                         json={"tax_id": tax_id, "password": password, "params": params})
        r.raise_for_status()
        return r.json()["job_id"]

async def wait_job(job_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as c:
        while True:
            r = await c.get(f"{BASE}/automations/jobs/{job_id}", headers=HEADERS)
            data = r.json()
            if data["status"] in ("finished", "failed"):
                return data
```

---

## 7. Credenciales de desarrollo

- CUIT de prueba: **20-40937847-2** (numérico: `20409378472`)
- No requiere certificado en `environment=dev`.
- El access_token real (plan pago) ya está en `AFIP_SDK_ACCESS_TOKEN/Access_Token_Afip_SDK.txt` — usar el mismo tanto en dev como en prod.

Ver `afip_dev_credentials.txt` para los datos de prueba en un archivo standalone.

---

## 8. Checklist para crear una nueva "acción" en el frontend

1. Identificar si es **Web Service** (certificado) o **Automatización** (clave fiscal).
2. Agregar método en `afip_client.py` / `afip_automations.py`.
3. Crear endpoint FastAPI bajo `/api/afip/...`.
4. Si es async: guardar `job_id` + poller en el frontend.
5. Botón en UI del cliente → modal con los params faltantes → llamada → mostrar resultado (JSON, PDF embedido, o Excel descargable).
6. Auditoría: loguear en tabla `afip_actions` quién, cuándo, qué acción, resultado (sin datos sensibles).

---

## 9. Referencias

- Integración Python: https://docs.afipsdk.com/integracion/python
- API REST: https://docs.afipsdk.com/integracion/api
- Factura electrónica: https://docs.afipsdk.com/siguientes-pasos/web-services/factura-electronica
- Padrón: https://docs.afipsdk.com/siguientes-pasos/web-services/padron-de-constancia-de-inscripcion
- Dashboard (access_token + automatizaciones): https://app.afipsdk.com
