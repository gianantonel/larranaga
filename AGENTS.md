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
