# Larrañaga — Plataforma Contable y Legal

Sistema de gestión integral para el estudio contable y legal **Larrañaga**, orientado a la administración de clientes, colaboradores y todas las gestiones tributarias ante **ARCA (ex AFIP)** en Argentina.

---

## Tecnologías

| Capa | Stack |
|------|-------|
| **Backend** | Python 3.11+ · FastAPI · SQLAlchemy ORM · SQLite (→ PostgreSQL) |
| **Frontend** | React 18 · Vite · Tailwind CSS (dark theme) · Recharts |
| **Seguridad** | JWT (auth) · bcrypt (contraseñas) · Fernet (credenciales ARCA) |
| **Base de datos** | SQLite (desarrollo) → PostgreSQL (producción) |

---

## Estructura del repositorio

```
larranaga/
├── backend/
│   ├── app/
│   │   ├── main.py               # Entrypoint FastAPI + CORS + seed
│   │   ├── database.py           # SQLAlchemy engine + session
│   │   ├── models.py             # Modelos ORM (User, Client, Task, IVA, Invoice...)
│   │   ├── schemas.py            # Schemas Pydantic (request/response)
│   │   ├── security.py           # JWT, bcrypt, Fernet encrypt/decrypt
│   │   ├── mock_data.py          # Seed de datos de prueba (se ejecuta al arrancar)
│   │   └── routers/
│   │       ├── auth.py           # Login, token, /me
│   │       ├── clients.py        # CRUD clientes + asignación colaboradores
│   │       ├── collaborators.py  # CRUD colaboradores + stats
│   │       ├── tasks.py          # CRUD tareas + subtareas
│   │       ├── iva.py            # Balance IVA, presentación DDJJ
│   │       ├── facturas.py       # Comprobantes electrónicos
│   │       └── dashboard.py      # Stats, timeline, gráficos
│   │   └── afip_sdk/             # Integración AFIP vía app.afipsdk.com (afip.py)
│   │       ├── client.py         # load_context(): arma Afip() con cert/key persistido
│   │       ├── bootstrap.py      # createCert + createWSAuth por CUIT/entorno
│   │       ├── smoke_test.py     # FEDummy + último comprobante + detalle
│   │       └── info.py           # FEParamGet* (ptos de venta, tipos, alícuotas, etc.)
│   ├── scripts/
│   │   └── create_client.py      # Alta de clientes vía API desde CLI
│   ├── afip_certs/               # PEMs generados por CUIT+entorno (NO commitear)
│   ├── requirements.txt
│   └── .env                      # Variables de entorno (no commitear en prod)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Router principal + guards de autenticación
│   │   ├── index.css             # Tailwind + componentes globales (dark theme)
│   │   ├── context/
│   │   │   └── AuthContext.jsx   # Estado global de autenticación
│   │   ├── utils/
│   │   │   ├── api.js            # Axios + interceptors + todas las llamadas API
│   │   │   └── helpers.js        # Formateadores, configs de badges y colores
│   │   ├── components/
│   │   │   ├── Layout/           # Sidebar, Layout wrapper
│   │   │   └── UI/               # Badge, StatCard, PageHeader, LoadingSpinner
│   │   └── pages/
│   │       ├── Login.jsx
│   │       ├── Dashboard.jsx     # KPIs + 4 gráficos + tabla rendimiento
│   │       ├── Clients.jsx       # Listado + creación de clientes
│   │       ├── ClientDetail.jsx  # Detalle cliente: IVA, facturas, tareas, credenciales
│   │       ├── Collaborators.jsx # Cards con pie charts y stats por colaborador
│   │       ├── Tasks.jsx         # Tareas expandibles con subtareas tick-able
│   │       ├── IVA.jsx           # Balance IVA + gráfico + acción "Presentar"
│   │       └── Facturas.jsx      # Historial + emisión de comprobantes
│   ├── package.json
│   ├── vite.config.js            # Proxy /api → localhost:8000
│   └── tailwind.config.js
│
├── start-backend.bat             # Inicia backend (venv gestionado internamente, sin activar en la shell)
├── start-frontend.bat            # Inicia frontend con npm install automático
└── .gitignore
```

---

## Cómo iniciar el proyecto

### Opción A — Docker (VPS / producción)

Requisitos: tener Docker y Docker Compose instalados.

```bash
git clone https://github.com/gianantonel/larranaga.git
cd larranaga

# Crear el archivo de variables de entorno a partir del ejemplo
cp backend/.env.example backend/.env
# Editar backend/.env con las claves reales antes de continuar

# Construir imágenes y levantar ambos servicios en segundo plano
docker compose up -d --build
```

- App disponible en: `http://<IP-del-VPS>`
- Para detener: `docker compose down`
- Para ver logs: `docker compose logs -f`

> El backend (FastAPI) y el frontend (React + nginx) se levantan juntos con ese único comando. No hace falta iniciarlos por separado.

---

### Opción B — Local (desarrollo en Windows)

#### Requisitos previos
- Python 3.11 o superior
- Node.js 18 o superior
- npm

### Backend

```bat
start-backend.bat
```

O manualmente:
```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

> **Nota:** el venv se usa para aislar dependencias pero **no se activa** en la shell (se llaman sus ejecutables directamente). Esto evita que el prefijo `(venv)` persista en terminales nuevas.

- API disponible en: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs
- La base de datos SQLite (`larranaga.db`) se crea y se popula automáticamente al primer arranque.

### Frontend

```bat
start-frontend.bat
```

O manualmente:
```bash
cd frontend
npm install
npm run dev
```

- Aplicación en: http://localhost:5173

---

## Estado y notas de desarrollo

| # | Ítem | Estado |
|---|------|--------|
| 1 | **Landing page pública** (`/`) | ⚠️ **Oculta hasta nuevo aviso** — la ruta raíz redirige directamente a `/login`. El componente `Landing.jsx` está intacto. Para rehabilitarla, ver comentario en `frontend/src/App.jsx` línea ~41. |

---

## Usuarios de prueba

| Rol | Email | Contraseña | Nombre |
|-----|-------|------------|--------|
| Administrador 1 | admin1@larranaga.com | admin123 | Administrador 1 |
| Administrador 2 | admin2@larranaga.com | admin123 | Administrador 2 |
| Administrador 3 | admin3@larranaga.com | admin123 | Administrador 3 |
| Colaboradora | mgonzalez@larranaga.com | colab123 | María González |
| Colaborador | crodriguez@larranaga.com | colab123 | Carlos Rodríguez |
| Colaboradora | amartinez@larranaga.com | colab123 | Ana Martínez |
| Colaborador | dfernandez@larranaga.com | colab123 | Diego Fernández |
| Colaboradora | lsanchez@larranaga.com | colab123 | Laura Sánchez |
| Colaborador | rgomez@larranaga.com | colab123 | Roberto Gómez |
| Colaboradora | ptorres@larranaga.com | colab123 | Patricia Torres |
| Colaborador | smorales@larranaga.com | colab123 | Sebastián Morales |

---

## Módulos implementados

### Autenticación y roles
- Login con email y contraseña
- JWT con expiración de 8 horas
- Tres roles de administrador (`admin1`, `admin2`, `admin3`) con permisos plenos
- Rol `collaborator`: solo ve sus clientes asignados y sus tareas
- Guards de rutas en frontend

### Dashboard
- KPIs: clientes activos, colaboradores, tareas del mes, total tareas
- Desglose por estado: terminadas, en curso, pendientes, bloqueadas
- Alertas IVA: declaraciones pendientes vs presentadas en el mes
- **Gráfico de líneas**: evolución de facturación mensual
- **Gráfico de torta**: distribución de tareas por tipo
- **Barras apiladas**: tareas por colaborador (terminadas / en curso / pendientes / bloqueadas)
- **Barras agrupadas**: actividad mensual (tareas, facturas, IVA presentados)
- **Tabla de rendimiento**: % completado por colaborador con barra visual

### Clientes
- Listado con búsqueda por nombre, CUIT o categoría
- Ficha completa: razón social, CUIT, condición fiscal (RI, Monotributo, Exento), categoría, dirección, teléfono, email
- Creación por administradores con validación de CUIT duplicado
- **Credenciales ARCA**: CUIT y clave fiscal almacenados con cifrado Fernet, visibles solo con acción explícita
- Asignación y desasignación de colaboradores (solo admins)
- Vista detalle con tabs: IVA, Facturas, Tareas
- Gráfico de líneas de evolución IVA en la ficha del cliente

### Colaboradores
- Cards individuales con avatar, email y rol
- Mini gráfico de torta con distribución de estados de tareas
- Barra de progreso con % de completado (verde/amarillo/rojo según umbral)
- Conteo de clientes asignados
- Creación de nuevos colaboradores/administradores (solo admins)

### Tareas
- Filtros simultáneos: cliente, colaborador, estado, tipo
- Tipos: Facturación, Comprobantes en línea, DDJJ IVA, DDJJ Ganancias, DDJJ Bienes Personales, Ingresos Brutos, Legal, Otros
- Estados: Pendiente, En curso, Terminada, Bloqueada, Postergada
- Subtareas con check individual y cambio de estado en un click
- Campo de comentario de bloqueo con alerta visual en rojo
- Cambio de estado inline desde la tabla
- Creación de subtareas desde la misma vista expandida
- Log automático de acciones en la base de datos

### Balance IVA *(módulo principal)*
- Tabla por cliente y período: ventas gravadas, débito fiscal, compras gravadas, crédito fiscal, saldo
- Saldo en rojo (a pagar) o verde (a favor)
- Gráfico de barras mensual agregado de todos los clientes
- Filtros por cliente, estado de presentación y período
- Acción **"Presentar DDJJ"** con número de VEP opcional
- Fecha de vencimiento y fecha efectiva de presentación
- Marcado automático con fecha y hora en la base de datos
- Alerta visual en filas pendientes

### Facturación
- Historial completo con tipo (A, B, C, M, E), número con formato `XXXXX-XXXXXXXX`, fecha, receptor, neto, IVA y total
- CAE generado (mock, listo para reemplazar con AFIP SDK)
- Emisión de nuevos comprobantes con cálculo automático IVA 21%
- Gráfico de barras de facturación mensual por monto y cantidad
- Filtros por cliente y tipo de comprobante
- Trazabilidad: cada factura registra qué colaborador la emitió

### Seguridad
- **Contraseñas**: hasheadas con bcrypt (sin posibilidad de reversión)
- **Clave fiscal ARCA**: cifrada con Fernet (AES 128 en modo CBC), clave maestra en `.env`
- **JWT**: firmado con HS256, payload con `user_id` y `role`
- **Control de acceso**: colaboradores solo acceden a sus clientes; endpoints destructivos requieren rol admin
- La clave fiscal nunca se expone en listados ni en logs

---

## Datos de prueba (mock)

La base de datos se puebla automáticamente al primer arranque con:

| Entidad | Cantidad |
|---------|----------|
| Administradores | 3 |
| Colaboradores | 5 |
| Clientes | 10 (sectores variados: gastronomía, farmacia, tech, hotel, etc.) |
| Registros IVA | 12 meses × 10 clientes = 120 períodos |
| Facturas | ~3–15 por mes por cliente (aprox. 700 facturas) |
| Ingresos Brutos | 12 meses × 7 clientes = 84 períodos |
| Tareas | ~360 tareas con subtareas detalladas |
| Logs de acciones | 100 eventos históricos |

---

## Variables de entorno (backend/.env)

```env
SECRET_KEY=                     # Clave para firmar JWT (cambiar en producción)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
ENCRYPTION_KEY=                 # Clave Fernet base64 para cifrar credenciales ARCA
DATABASE_URL=sqlite:///./larranaga.db
AFIP_SDK_ACCESS_TOKEN=          # Token de la cuenta en app.afipsdk.com (ver sección AFIP SDK)
```

> ⚠️ La variable **debe llamarse `ENCRYPTION_KEY`** (singular). Si se escribe `ENCRYPTION_KEYS`, `app/security.py` no la encuentra y cae a una clave Fernet random en cada arranque, rompiendo las credenciales ya cifradas.

Para generar una clave Fernet nueva:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

---

## API — Endpoints principales

```
POST  /auth/login              → Login, retorna JWT
GET   /auth/me                 → Usuario actual

GET   /clients                 → Listado de clientes
POST  /clients                 → Crear cliente (admin)
GET   /clients/{id}            → Detalle cliente
POST  /clients/{id}/collaborators  → Asignar colaborador
GET   /clients/{id}/credentials    → Ver clave fiscal (decrypt)

GET   /collaborators           → Colaboradores activos
POST  /collaborators           → Crear colaborador (admin)
GET   /collaborators/{id}/stats → Estadísticas de un colaborador

GET   /tasks                   → Listar tareas (con filtros)
POST  /tasks                   → Crear tarea
PUT   /tasks/{id}              → Actualizar estado/datos
POST  /tasks/{id}/subtasks     → Agregar subtarea
PUT   /tasks/{id}/subtasks/{sid} → Actualizar subtarea

GET   /iva                     → Registros IVA (con filtros)
POST  /iva                     → Crear registro IVA
PUT   /iva/{id}                → Actualizar registro
POST  /iva/{id}/file           → Marcar como presentado
GET   /iva/summary/{client_id} → Resumen IVA de un cliente

GET   /facturas                → Listado facturas (con filtros)
POST  /facturas                → Emitir comprobante

GET   /dashboard/stats         → KPIs generales
GET   /dashboard/collaborator-stats → Stats por colaborador
GET   /dashboard/timeline      → Log de acciones recientes
GET   /dashboard/monthly-activity  → Actividad mensual agregada
GET   /dashboard/tasks-by-type     → Tareas agrupadas por tipo
GET   /dashboard/iva-overview      → Resumen IVA por cliente
```

---

## Integración AFIP SDK (`app.afipsdk.com`)

El backend se conecta a AFIP (ARCA) a través del servicio externo **app.afipsdk.com**, que gestiona el ciclo de vida del certificado X.509 de cada CUIT. Se usa la librería `afip.py==1.2.0`. Alternativa no implementada: WSAA directo con cert propio.

### 1. Login / obtener access token

1. Crear cuenta en https://app.afipsdk.com
2. En el panel, sección *Access Tokens*, generar un token. Identifica a **tu cuenta** (no a un CUIT puntual).
3. Guardarlo en `backend/.env`:

```env
AFIP_SDK_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Alta del CUIT en el sistema

Para que el SDK pueda generar un certificado necesita la **clave fiscal** del CUIT (AFIP la valida contra `auth.afip.gob.ar`).

```bash
cd backend

# Crear cliente (usa POST /clients/ con login admin)
.venv\Scripts\python -m scripts.create_client ^
  --name "Agropecuaria El Alba S.R.L." ^
  --cuit "23-31134894-9" ^
  --clave-fiscal "MI_CLAVE_FISCAL" ^
  --fiscal-condition "Responsable Inscripto"
```

La clave queda cifrada con Fernet en la columna `clients.clave_fiscal_encrypted`. También se puede cargar/actualizar por `PUT /clients/{id}` con `{"clave_fiscal": "..."}`.

### 3. Bootstrap: certificado + autorización de web service

One-time por cada **(CUIT, entorno)**. Homologación y producción son independientes.

```bash
# Homologación
.venv\Scripts\python -m app.afip_sdk.bootstrap --client-id 12

# Producción
.venv\Scripts\python -m app.afip_sdk.bootstrap --client-id 12 --prod
```

Qué hace:
1. `createCert` en app.afipsdk.com → genera cert X.509 y clave privada para ese CUIT.
2. Guarda los PEMs en `backend/afip_certs/{CUIT}-{dev|prod}.(cert|key)` (en binario con LF para evitar corrupción ASN.1 en Windows).
3. `createWSAuth` → registra el WSID `wsfe` (factura electrónica) contra ese cert.

Flags útiles:
- `--skip-cert` → solo registra WSAuth (si el cert ya existe)
- `--skip-wsauth` → solo genera cert (útil para re-persistir si se borró del disco)
- `--wsid wsmtxca` → registrar otro web service (default: `wsfe`)
- `--alias nombre` → etiqueta del cert en el panel de app.afipsdk.com (default: `larranaga`)

> ⚠️ **`backend/afip_certs/` contiene claves privadas.** Debe estar gitignoreado.

### 4. Smoke test

Valida FEDummy + FECompUltimoAutorizado + FECompConsultar de punta a punta.

```bash
# Homologación, pto vta 1, Factura C (default)
.venv\Scripts\python -m app.afip_sdk.smoke_test --client-id 12

# Producción, pto vta 6, Factura A
.venv\Scripts\python -m app.afip_sdk.smoke_test --client-id 12 --prod --punto-venta 6 --tipo-cbte 1
```

Salida esperada en producción con datos reales:
```
[1/3] FEDummy (healthcheck)...
  -> {'AppServer': 'OK', 'DbServer': 'OK', 'AuthServer': 'OK'}
[2/3] FECompUltimoAutorizado (pto=6, tipo=1)...
  -> ultimo numero autorizado: 41
[3/3] FECompConsultar (numero=41)...
  CbteFch: 20260413
  ImpTotal: 12100000
  CodAutorizacion: 86151427323266
  ...
```

### 5. Consultas informativas

Útil para averiguar qué puntos de venta tiene habilitados un CUIT, qué tipos de comprobante emite, etc.

```bash
.venv\Scripts\python -m app.afip_sdk.info --client-id 12 --prod --what sales-points
```

Valores de `--what`: `sales-points`, `voucher-types`, `document-types`, `currencies`, `aliquots`, `concepts`, `taxes`.

### Tipos de comprobante más usados

| Código | Tipo |
|---|---|
| 1 | Factura A |
| 6 | Factura B |
| 11 | Factura C |
| 51 | Factura M |
| 19 | Factura E (exportación) |

### Errores comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `El campo Certificado es obligatorio` | El cert no está en `afip_certs/` para ese CUIT+entorno | Correr `bootstrap` |
| `Too few bytes to read ASN.1 value` | PEM escrito con CRLF (Windows) | `client.py` ya lo normaliza a LF; re-correr bootstrap |
| `(11002) El punto de venta no se encuentra habilitado` | El PV que pasaste no está registrado en AFIP para ese CUIT/WS | `info --what sales-points` para ver los válidos |
| `createCert` da `already exists` | El alias ya está tomado en app.afipsdk.com | Usar `--alias otro` o saltear con `--skip-cert` |
| `InvalidToken` al descifrar clave fiscal | La Fernet key del `.env` cambió desde que se cifró | Re-cargar la clave fiscal con `PUT /clients/{id}` |

---

## Migración a PostgreSQL (cuando sea necesario)

1. Instalar driver: `pip install psycopg2-binary`
2. Cambiar en `.env`:
   ```
   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/larranaga
   ```
3. Crear la base de datos en PostgreSQL
4. Reiniciar el backend — SQLAlchemy creará las tablas automáticamente

PostgreSQL aporta: cifrado a nivel columna nativo, row-level security, mejores índices para reportes, y soporte para múltiples conexiones concurrentes.
