# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Larrañaga is a web platform for the **AGEP accounting firm** to manage clients, tasks, IVA records, invoices, retenciones/percepciones, and AFIP/ARCA automation. It is a FastAPI + React 18 + SQLite monorepo.

## Commands

### Backend

```bash
# Windows one-shot (handles venv + deps)
start-backend.bat

# Manual
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

API: `http://localhost:8000` — Swagger UI: `http://localhost:8000/docs`

```bash
# AFIP SDK scripts (run from backend/)
python -m app.afip_sdk.bootstrap   # generate cert + register WSAuth
python -m app.afip_sdk.smoke_test  # validate AFIP WS connectivity
python -m app.afip_sdk.info        # list sales points, voucher types, etc.
```

### Frontend

```bash
# Windows one-shot
start-frontend.bat

# Manual
cd frontend
npm install
npm run dev    # http://localhost:5173
npm run build  # output → dist/
```

Vite proxies `/api/*` → `http://localhost:8000`.

### Tests

```bash
# Backend (from backend/)
pytest -v                  # all tests
pytest -v --afip-live      # include live AFIP SDK tests (require real credentials)
pytest -v tests/test_cruce.py  # single file

# Accounting agent (from larranaga-accounting-agent/)
pip install -r requirements.txt
pytest -v
```

No automated frontend tests; use manual testing against `http://localhost:5173`.

### Docker

```bash
docker compose up -d --build
```

Backend (port 8000) + nginx-served frontend on port 80.

## Architecture

### Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2.7, SQLite (→ PostgreSQL) |
| Auth | JWT HS256 (8h), bcrypt passwords, MultiFernet for clave fiscal |
| Frontend | React 18 + Vite 5, Tailwind CSS, Recharts, Axios, React Router 6 |
| AFIP | afip.py 1.2.0 → app.afipsdk.com; WSFE + automations (ARCA scraping) |

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app, CORS, router registration, auto-create + seed DB on startup
- **`database.py`** — SQLAlchemy engine/session, `get_db` dependency
- **`models.py`** — All 10 ORM tables (see schema below)
- **`schemas.py`** — All Pydantic request/response models
- **`security.py`** — `create_access_token`, `get_current_user`, `get_password_hash`, `encrypt_clave_fiscal`/`decrypt_clave_fiscal` (MultiFernet)
- **`mock_data.py`** — Seeds 3 admins + 8 collaborators + 10 clients + IVA/tasks/invoices on first startup
- **`routers/`** — One file per domain: `auth`, `clients`, `collaborators`, `tasks`, `iva`, `facturas`, `dashboard`, `retenciones`, `comprobantes`, `herramientas`, `cuentas_corrientes`
- **`afip_sdk/`** — AFIP SDK integration: `bootstrap.py`, `smoke_test.py`, `info.py`, `automations.py` (retenciones + comprobantes sync via scraping)

### Frontend (`frontend/src/`)

- **`App.jsx`** — React Router with protected routes; unauthenticated → redirect `/login`
- **`context/AuthContext.jsx`** — Global auth state, token in `localStorage`, user/role
- **`utils/api.js`** — All Axios calls; Bearer token injected via interceptor
- **`utils/helpers.js`** — Currency/date formatters, badge configs, Holistor color maps
- **`pages/`** — One file per route: Dashboard, Clientes, ClientDetail, Colaboradores, Tareas, IVA, Facturas, Retenciones, Herramientas, CuentasCorrientes
- **`components/`** — Layout/Sidebar, Badge, StatCard, PageHeader, LoadingSpinner, RetencionesPanel, CrucePanel

### Key Data Model Relationships

```
users ──< client_collaborators >── clients ──< iva_records
  │                                         ├─< invoices
  └──< tasks >── subtasks                   ├─< retenciones_percepciones >── comprobantes_recibidos
       │                                    └─< action_logs
       └──< action_logs
```

### Auth & Access Control

- **Roles**: `admin` (full access) vs `collaborator` (only assigned clients via `client_collaborators`)
- Token payload: `{ sub: user_id, role }` — role check is done per-endpoint with `Depends(get_current_user)`
- `clave_fiscal` stored encrypted with MultiFernet; access logged to `action_logs`

### AFIP SDK Integration

Two modes per endpoint:
1. **Web Service** (certificate) — used for invoice issuance (WSFE/CAE)
2. **Automation** (clave fiscal scraping) — used for Mis Retenciones + Mis Comprobantes Recibidos via app.afipsdk.com

Retenciones sync is **idempotent** — duplicate check by `(client_id, cuit_agente, tipo, monto, periodo)`.  
Comprobantes sync is **idempotent** — duplicate check by `(client_id, tipo, numero_desde, nro_doc_emisor, fecha)`.

After sync, **cruce** (matching) runs automatically: retenciones ↔ comprobantes by CUIT + date (±5 days). Results exported to Holistor CSV (`codigo_holistor` column AB, UTF-8-BOM).

### Database

SQLite in development (`backend/larranaga.db`). To switch to PostgreSQL:
1. `pip install psycopg2-binary`
2. Set `DATABASE_URL=postgresql://user:pass@host:5432/larranaga` in `backend/.env`
3. Restart backend — SQLAlchemy creates the schema automatically.

Tables auto-created and seeded on first startup via `main.py`. No migration system is in place yet.

### Environment Variables (`backend/.env`)

```
SECRET_KEY=...          # JWT signing key
ENCRYPTION_KEY=...      # MultiFernet key for clave fiscal (newest)
ENCRYPTION_KEYS=...     # CSV of all keys for rotation (newest first)
DATABASE_URL=...        # defaults to sqlite:///./larranaga.db
AFIP_SDK_API_KEY=...    # app.afipsdk.com API key
```

### Accounting Agent (`larranaga-accounting-agent/`)

Standalone Python module for Excel transformations. R-01 (`src/transformaciones/limpieza_inicial.py`) cleans raw "Libro IVA Compras" exports. Has its own `requirements.txt` and pytest suite.
