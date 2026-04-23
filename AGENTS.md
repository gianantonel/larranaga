
# AGENTS.md — Guía para agentes automatizados

Este archivo orienta a agentes (Claude Code, Codex, etc.) que operan sobre este repo. Mantener actualizado cuando cambien convenciones operativas o comandos repetibles.

---

## Resumen del proyecto

Plataforma contable/legal para el estudio **Larrañaga** (Argentina). Backend FastAPI + SQLAlchemy + SQLite; frontend React/Vite. Gestiona clientes, colaboradores, tareas, IVA, facturación e integración con AFIP (ARCA) vía `app.afipsdk.com`.

- **Raíz operativa:** `D:\Documents\Claude_Tests\Larranaga\larranaga\`
- **Arranque dev:** `start-backend.bat` + `start-frontend.bat` desde la raíz.
- **Shell del venv:** los ejecutables se llaman directo (`.venv\Scripts\python ...`). **No activar el venv** en la shell.
- **Fecha del sistema usada en seeds/memoria:** 2026 (ver `mock_data.py`).

---

## Convenciones al editar código

- **Trailing slash obligatorio** en endpoints de colección desde el frontend (`/clients/`, `/tasks/`, etc.). Sin slash → redirect 307 que dropea el header `Authorization` y pega 401.
- **Límites de paginación:** seed crea ~360 tareas y ~1080 facturas. Mantener `limit=500` en tasks y facturas.
- `ENCRYPTION_KEY` en `.env` es **singular**. Si se escribe `ENCRYPTION_KEYS`, `security.py` cae a Fernet random por proceso → credenciales cifradas quedan irrecuperables tras reiniciar.
- Windows rompe PEMs al escribirlos con `write_text` (CRLF → ASN.1 inválido). Para cualquier archivo de cert/key: `write_bytes` con contenido normalizado a LF. Ya resuelto en `app/afip_sdk/client.py`.

---

## Integración AFIP SDK — comandos repetibles

Documentación completa en [README.md § Integración AFIP SDK](README.md#integración-afip-sdk-appafipsdkcom). Resumen operativo:

### Requisitos
- `AFIP_SDK_ACCESS_TOKEN` configurado en `backend/.env` (token de la cuenta en app.afipsdk.com).
- Cliente en DB con `cuit` y `clave_fiscal_encrypted` válidos.
- `afip.py==1.2.0` en `requirements.txt`.

### Alta de cliente desde CLI

```powershell
cd backend
.venv\Scripts\python -m scripts.create_client `
  --name "Razón social" --cuit "XX-XXXXXXXX-X" `
  --clave-fiscal "..." --fiscal-condition "Responsable Inscripto"
```

Credenciales admin por defecto: `admin1@larranaga.com / admin123`. Override con `--email` / `--password` o env `LARRANAGA_ADMIN_EMAIL` / `LARRANAGA_ADMIN_PASSWORD`.

### Bootstrap de certificado (una vez por CUIT+entorno)

```powershell
# Homologación
.venv\Scripts\python -m app.afip_sdk.bootstrap --client-id 12
# Producción
.venv\Scripts\python -m app.afip_sdk.bootstrap --client-id 12 --prod
```

Persiste en `backend/afip_certs/{CUIT}-{dev|prod}.(cert|key)`. **No commitear**.

### Smoke test

```powershell
.venv\Scripts\python -m app.afip_sdk.smoke_test --client-id 12                          # dev, PV=1, tipo=11
.venv\Scripts\python -m app.afip_sdk.smoke_test --client-id 12 --prod --punto-venta 6 --tipo-cbte 1
```

### Consultas informativas

```powershell
.venv\Scripts\python -m app.afip_sdk.info --client-id 12 --prod --what sales-points
```

`--what`: `sales-points | voucher-types | document-types | currencies | aliquots | concepts | taxes`.

### Automatizaciones (Mis Retenciones) — scraping con clave fiscal

Las *automatizaciones* de app.afipsdk.com usan la clave fiscal (no cert/key) para scrapear portales ARCA. Wrapper genérico en `backend/app/afip_sdk/automations.py` (`run_automation(ctx, name, params, wait)` + `save_raw(...)` → `backend/afip_raw/{cuit}/{automation}/{period}.json`).

CLI Mis Retenciones (R-05):

```powershell
.venv\Scripts\python -m app.afip_sdk.retenciones --client-id 12 --prod --period 2025-12 --impuesto 217 --descripcion-impuesto IVA
```

Parámetros documentados por app.afipsdk.com (`mis-retenciones`):

- `mode="filter"` requiere `filters.{descripcionImpuesto, fechaRetencionDesde, fechaRetencionHasta, impuestoRetenido, tipoImpuesto, percepciones, retenciones}`.
- `mode="preset"` con `preset` ∈ `{percepcion-ganancias, percepcion-bienes-personales, retencion-ganancias}` — **no cubre IVA** (consultarlo siempre por filter).
- `page` arranca en **0**, `size` recomendado 100.

Códigos AFIP relevantes (`impuestoRetenido`):

| Código | Impuesto | Mapeo Holistor (col AR) |
|---|---|---|
| 217 | IVA – Percepciones/Retenciones | `PIVC` |
| 11 | Ganancias – Retención | `PGAN` |
| 10 | Ganancias – Percepción | `PGAN` |
| 767 | Bienes Personales | `OTRO` |

Response: `data.rows[]` con `cuitAgenteRetencion, impuestoRetenido, codigoRegimen, fechaRetencion, importeRetenido, numeroComprobante, descripcionOperacion`.

**Nota El Alba**: sin movimientos de retenciones en 2021–2024. Demo actual: **período 2025-12** (7 percepciones IVA, agente 30500012516, total $8.045,13).

### Agregar un nuevo script de operación AFIP

1. Crear `backend/app/afip_sdk/<nombre>.py`.
2. Importar `from .client import load_context, env_label`.
3. `ctx = load_context(client_id=..., production=args.prod)` — devuelve un `Afip()` listo con cert+key.
4. Operar con `ctx.afip.ElectronicBilling.<método>(...)`.
5. Ejecutar con `python -m app.afip_sdk.<nombre>`.

Mantener los sub-módulos chicos y enfocados (un verbo por archivo): facilita encadenarlos desde el backend cuando se integren al router.

---

## Cliente de prueba en producción

Para validar end-to-end contra AFIP real:

- **Agropecuaria El Alba S.R.L.** — DB id=12, CUIT `23-31134894-9`
- Punto de venta habilitado en prod: **6** (único, CAE - RI IVA)
- Confirmado el 2026-04-21: última Factura A Nro 41, fecha 2026-04-13, CAE `86151427323266`, total $12.100.000.

---

## Testing manual (sin suite automatizada)

No hay tests automatizados aún. Para validar cambios:

1. Reiniciar backend (`start-backend.bat`) y ver `Application startup complete`.
2. Frontend en `http://localhost:5173` — login con `admin1@larranaga.com / admin123`.
3. API docs: `http://localhost:8000/docs`.
4. Para integración AFIP: correr bootstrap + smoke_test contra Agropecuaria El Alba (client-id 12) en homologación.

---

## Archivos que **no** deben commitearse

- `backend/afip_certs/**` — claves privadas X.509.
- `backend/.env` — secretos.
- `backend/larranaga.db*` — base SQLite con clave fiscal cifrada pero con la Fernet key correspondiente en `.env`.

---

## Referencias internas

- Modelos y esquemas: `backend/app/models.py`, `backend/app/schemas.py`
- Seguridad (JWT, Fernet, bcrypt): `backend/app/security.py`
- Endpoints de clientes (incluye `/clients/{id}/credentials`): `backend/app/routers/clients.py`
- Seed inicial: `backend/app/mock_data.py`
# AGENTS.md — Proyecto Larrañaga × Optimizar

Este archivo es la **guía de agentes de IA** (Claude Code, subagentes, agentes SDK) para el repo del proyecto Larrañaga. Léelo al iniciar cualquier tarea en este repo.

---

## Contexto del proyecto

- **Cliente:** Estudio Larrañaga y Asociados — Santa Rosa, La Pampa.
- **Empresa desarrolladora:** **Optimizar** (nosotros).
- **Objetivo:** automatizar el estudio contable en dos frentes:
  - **Módulo IVA / Contabilidad:** preparación de IVA Compras/Ventas, HWCRARCA para Holistor/Onvio, reportes IVA-MES, VEPs.
  - **Módulo Administración / Tesorería:** cuentas corrientes, tesorería, conciliación bancaria, liquidación profesionales, flujo de fondos, retiros socios.
- **Principio rector:** **"Carga única — impacto automático en todos los módulos"**.

## Documentos de referencia (leer antes de codear)

| Archivo | Para qué |
|---------|----------|
| `Requerimiento Técnico Admin y Tesorería Larrañaga.md` | Requerimiento del cliente para el módulo ADM |
| `Requerimiento Técnico IVA Larrañaga.md` | Requerimiento del cliente para el módulo IVA Compras |
| `Plan_Maestro_de_Implementacion_Integral_Optimizar_para_Larrañaga.md` | **Plan de fases y tareas oficiales de Optimizar** — leer siempre antes de elegir qué hacer |
| `afip_sdk.md` | Cómo usar AFIP SDK (REST + Python) en el proyecto |
| `afip_dev_credentials.txt` | CUIT de prueba 20-40937847-2 para dev |
| `.claude/skills/afip-sdk-actions/SKILL.md` | Skill Claude Code con patrones de integración AFIP SDK |

## Stack tecnológico

- **Backend:** Python 3.12 + FastAPI.
- **Base de datos:** Supabase (PostgreSQL) con Row Level Security.
- **Frontend:** React + TypeScript.
- **Procesamiento:** pandas + openpyxl (IVA, extractos), reportlab (PDF).
- **IA clasificación:** Claude API Sonnet (imputación contable, categorización de movimientos bancarios no identificados).
- **AFIP:** AFIP SDK (https://app.afipsdk.com) — web services + automatizaciones.
- **Orquestación:** n8n para schedules, triggers de Drive y envío de mails.
- **Archivos:** Google Drive.
- **Credenciales de clientes:** tabla cifrada Supabase (Fernet) — nunca en logs ni código.

## Repositorios del proyecto (5)

| Repo | Responsable | Contenido |
|------|-------------|-----------|
| `larranaga-core` | Dev 1 | Schema Supabase, RPCs, libs compartidas, CI/CD |
| `larranaga-arca-agent` | Dev 1 | Integración AFIP SDK — retenciones, comprobantes, padrón, VEPs |
| `larranaga-accounting-agent` | Dev 2 | Transformaciones IVA (B/C, alícuotas), imputación, HWCRARCA |
| `larranaga-admin-agent` | Dev 2 + Dev 3 | Backend FastAPI + frontend React del módulo ADM completo |
| `larranaga-banking-agent` | Dev 3 | Parsers bancarios (Pampa, Santander, MP) + algoritmo de conciliación |
| `larranaga-n8n-flows` | Dev 1 | Workflows n8n (schedules, triggers, mails) |
| `larranaga-reports` | Dev 2 | Generación de informes Excel/PDF y Google Docs IVA-MES |

## Plan por fases (oficial Optimizar)

Cada fase dura **3–4 semanas** y combina requerimientos de IVA **y** ADM. El cliente recibe valor visible en cada entrega.

### Fase 1 — Infra + Quick wins (sem 1–3)
- **R-01 + R-02** Corrección B/C + División alícuotas (Dev 2, Python puro)
- **R-05** Separación retenciones IVA vs IIBB (Dev 1, SDK)
- **R-07** Cuentas corrientes — base de datos (Dev 2, Supabase)
- **R-03 + R-04** Cálculo honorarios + Liquidación profesionales (Dev 2, Python puro)
- **Demo:** procesar IVA de BUTALO SRL Feb 2026 de punta a punta + registrar honorario de Juan Pérez con saldo en tiempo real.

### Fase 2 — Pipeline IVA + Tesorería (sem 4–6)
- **R-06** Conciliación IVA — posición mensual (Dev 1, SDK)
- **R-09 + R-10** Imputación CUIT + HWCRARCA completo (Dev 2, Python + Claude API)
- **R-08** Tesorería con impacto automático (Dev 2, Supabase) — `registrar_cobro()` operativo
- **R-14** Control de billetes / caja efectivo (Dev 3, Supabase)

### Fase 3 — Conciliación bancaria + Flujo de fondos (sem 7–10)
- **R-15** Conciliación bancaria — parsers Pampa/Santander/MP + matching (Dev 3, Python + Claude Vision)
- **R-11** Flujo de fondos — real vs proyectado (Dev 2, Supabase)
- **R-12** Retiros de socios (Dev 2, Supabase)
- **R-13** Actualización cuatrimestral de honorarios con pantalla de validación (Dev 3, Python + React)

### Fase 4 — Reportes, IVA-MES e integración total (sem 11–15)
- **R-16 + R-19** Reportes IVA-MES automáticos + Consulta ARCA (Dev 1, SDK)
- **R-17** Informes de gestión — todos los reportes ADM (Dev 2, Python + React)
- **R-20** Migración histórica Excel → Supabase (todos, Python + pandas)
- **R-18** MVP liquidación de impuestos + VEPs (Dev 1, SDK)

## Subagentes Claude Code disponibles

| Subagente | Repo | Función |
|-----------|------|---------|
| `agente-retenciones` | arca-agent | Clasifica percepciones/retenciones ARCA por régimen |
| `agente-conciliacion-iva` | arca-agent | Calcula posición IVA del mes |
| `agente-iva-mes` | arca-agent | Descarga comprobantes mensuales y genera reporte |
| `agente-veps` | arca-agent | Genera VEPs desde DDJJ |
| `agente-hwcrarca` | accounting-agent | Genera archivo HWCRARCA con validación Debe=Haber |
| `agente-honorarios` | admin-agent | Calcula honorarios fijo/producto + actualización cuatrimestral |
| `agente-tesoreria` | admin-agent | Registra cobros verificando los 5 impactos automáticos |
| `agente-liquidacion-prof` | admin-agent | Calcula liquidación mensual de cada profesional |
| `agente-parsers-bancos` | banking-agent | Parsea extractos de Pampa/Santander/MP |
| `agente-conciliacion-bancaria` | banking-agent | Matching entre extracto y movimientos registrados |
| `agente-migracion` | core | Migra datos históricos desde Excel |

## Reglas de oro para agentes

1. **Carga única — impacto automático.** Un cobro de honorarios SIEMPRE impacta: CC cliente + tesorería + liquidación profesional + control billetes (si efectivo) + cola conciliación (si transferencia). Si uno falla → **rollback completo**.
2. **Consistencia CC ↔ flujo de fondos.** `saldo_cuenta_corriente_cliente == deuda_en_flujo_fondos`. Si difieren >$0.10 → alerta inmediata, no continuar.
3. **Credenciales.** Nunca loguear AFIP access token ni clave fiscal del cliente. Se desencriptan solo en runtime dentro del request.
4. **Tipo B.** Los comprobantes tipo **B no se toman en IVA** (los C sí, con Neto+IVA=0 y total en AD).
5. **HWCRARCA.** Antes de escribir al disco, validar **Debe = Haber** contable.
6. **Actualización cuatrimestral.** Nunca masiva/automática — siempre con pantalla de validación individual por cliente.
7. **Dev por defecto.** `AFIP_ENV=dev` + CUIT `20409378472` para pruebas. `prod` solo por cliente real con certificado cargado.
8. **Tests mockean AFIP.** Ningún test de CI debe golpear el SDK real.

## Flujo de trabajo

1. **Antes de empezar una tarea**: identificar a qué requerimiento (R-XX) pertenece en el Plan Maestro y qué fase es.
2. **Leer** el requerimiento técnico del cliente correspondiente al módulo.
3. **Consultar** `afip_sdk.md` si la tarea toca AFIP.
4. **Activar el subagente apropiado** o el skill `afip-sdk-actions` si aplica.
5. **Escribir código + tests** en el repo correspondiente.
6. **Validar consistencia** antes de mergear (regla 2).
7. **Actualizar el todo list** y marcar tareas completadas una a una, no en batch.

---

*Equipo Optimizar — Proyecto Larrañaga y Asociados — Abril 2026.*
