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
├── start-backend.bat             # Inicia backend con venv automático
├── start-frontend.bat            # Inicia frontend con npm install automático
└── .gitignore
```

---

## Cómo iniciar el proyecto

### Requisitos previos
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
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

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
SECRET_KEY=           # Clave para firmar JWT (cambiar en producción)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
ENCRYPTION_KEY=       # Clave Fernet base64 para cifrar credenciales ARCA
DATABASE_URL=sqlite:///./larranaga.db
```

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

## Migración a PostgreSQL (cuando sea necesario)

1. Instalar driver: `pip install psycopg2-binary`
2. Cambiar en `.env`:
   ```
   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/larranaga
   ```
3. Crear la base de datos en PostgreSQL
4. Reiniciar el backend — SQLAlchemy creará las tablas automáticamente

PostgreSQL aporta: cifrado a nivel columna nativo, row-level security, mejores índices para reportes, y soporte para múltiples conexiones concurrentes.
