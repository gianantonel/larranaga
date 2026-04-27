# Actualizaciones Larrañaga — Registro de Cambios

Documento de control de todas las actualizaciones realizadas en la plataforma Larrañaga.

---

## 2026-04-27 — Sistema de Sincronización InsForge + UI Improvements

### 📌 Resumen
Integración completa de sincronización automática SQLite ↔ InsForge Cloud y reorganización de la interfaz de usuario.

### ✨ Cambios Realizados

#### 1. **Sistema de Sincronización Automática InsForge**

**Archivos Creados:**
- `backend/app/sync/insforge_sync.py` — Script de exportación y sincronización
- `backend/app/sync/events.py` — Event listeners de SQLAlchemy (detección automática de cambios)
- `backend/app/sync/__init__.py` — Exporta funciones del módulo
- `backend/app/sync/README.md` — Documentación del módulo
- `backend/logs/.gitkeep` — Directorio para logs

**Archivos Modificados:**
- `backend/app/main.py` — Integra event listeners en startup + endpoint admin

**Funcionalidad:**
- ✅ Sincronización automática: Cada cambio en BD → InsForge (background thread)
- ✅ Sincronización manual: Endpoint `POST /admin/sync-insforge`
- ✅ Reintentos automáticos con backoff exponencial
- ✅ Logging completo en `backend/logs/insforge_sync.log`
- ✅ Conversión de tipos SQLite → PostgreSQL
- ✅ Exclusión de campos binarios

**Commits:**
- `c8d6d03` — feat(insforge): Sistema de sincronización SQLite <-> InsForge
- `1418507` — feat(insforge): Integración automática de sincronización

---

#### 2. **UI — Reorganización de Sidebar**

**Archivos Modificados:**
- `frontend/src/components/Layout/Sidebar.jsx` — Estructura árbol colapsable
- `frontend/src/index.css` — Estilos `.nav-group-header`, `.nav-link-child`
- `frontend/src/pages/Herramientas.jsx` — Renombrado descriptivo

**Cambios:**
- ✅ Sidebar con 3 grupos colapsables:
  - **Vistas** (Dashboard, Clientes, Colaboradores, Tareas)
  - **Acciones** (Cuentas Corrientes, Retenciones/IVA, Facturación, Retenciones Avanzadas, Tesorería)
  - **Otras Acciones** (Corrección B/C Holistor Columna L)
- ✅ ChevronRight con animación rotate-90 al abrir/cerrar
- ✅ Renombrado de R-01/R-02 → nombres descriptivos de funciones
- ✅ Item "Tesorería" como disabled con badge "Próx."

**Commits:**
- `4663e9e` — feat(UI): Reorganizar navegación en árbol colapsable y renombrar herramientas

---

#### 3. **Migración de BD a InsForge Cloud**

**Acción:**
- ✅ Exportación de `larranaga.db` (SQLite) a SQL PostgreSQL
- ✅ Importación exitosa a InsForge: **3,209 registros** en **13 tablas**

**Tablas Sincronizadas:**
| Tabla | Registros |
|---|---|
| users | 11 |
| clients | 12 |
| client_collaborators | 13 |
| tasks | 361 |
| iva_records | 120 |
| invoices | 994 |
| ingresos_brutos | 84 |
| subtasks | 1,440 |
| action_logs | 118 |
| comprobantes_recibidos | 45 |
| retenciones_percepciones | 7 |
| limpiezas_iva | 4 |
| movimientos_cc | 0 |

**Instancia InsForge:**
- URL: `https://vivnx98a.us-east.insforge.app`
- API Key: `ik_6e043a410661a9bfaed032bf81e065fd`

---

#### 4. **Sincronización de Ramas**

**Estado:**
- ✅ `dev` ← sincronizada con cambios
- ✅ `fede` ← sincronizada con dev
- ✅ PR #14 (dev → fede) mergeado

**Commits:**
- `71a535f` — merge: sincronizar fede con dev
- `a3b2d2d` — data: actualizar larranaga.db a versión más reciente de rama gian

---

### 🔍 Cómo Encontrar Cambios Específicos

#### Por Funcionalidad
- **Sincronización InsForge**: Buscar `backend/app/sync/`
- **UI Sidebar**: Buscar `frontend/src/components/Layout/Sidebar.jsx`
- **Estilos**: Buscar `frontend/src/index.css` (`.nav-group-header`, `.nav-link-child`)
- **Logs de Sincronización**: `backend/logs/insforge_sync.log`

#### Por Archivo
```
backend/app/sync/
├── insforge_sync.py      (exportación + API calls)
├── events.py             (event listeners SQLAlchemy)
├── __init__.py           (exports)
└── README.md             (documentación)

backend/app/main.py       (integración en startup + endpoint admin)

frontend/src/
├── components/Layout/Sidebar.jsx   (UI tree)
├── pages/Herramientas.jsx          (renombrado)
└── index.css                       (estilos nuevos)
```

#### Por Rama
```
git log --oneline dev | grep insforge
git log --oneline fede | grep insforge
```

---

### 📊 Estadísticas

- **Archivos Creados**: 7
- **Archivos Modificados**: 3
- **Registros Sincronizados**: 3,209
- **Tablas**: 13
- **Commits**: 4
- **Líneas Agregadas**: ~500

---

### 🔗 Referencias Rápidas

**Endpoints Nuevos:**
- `POST /admin/sync-insforge` — Sincronización manual

**Variables de Entorno:**
```bash
INSFORGE_API_KEY=ik_6e043a410661a9bfaed032bf81e065fd
INSFORGE_API_URL=https://vivnx98a.us-east.insforge.app
```

**Comandos Útiles:**
```bash
# Sincronización manual
python -m app.sync.insforge_sync

# Ver logs
tail -f backend/logs/insforge_sync.log

# Ver historial de cambios
git log --oneline | grep insforge
```

---

### ✅ Testing Realizado

- ✅ Exportación de BD a SQL (3,209 registros)
- ✅ Importación a InsForge (200 OK)
- ✅ Event listeners funcionando
- ✅ Endpoint admin respondiendo
- ✅ Sidebar colapsable funcionando
- ✅ Renombrado de items visible en UI

---

### 📝 Notas Adicionales

- Datos binarios (`archivo_corregido`) excluidos de sincronización
- Sincronización corre en thread separado (no bloquea la app)
- Reintentos automáticos si falla la sincronización
- Compatible con PostgreSQL/InsForge
- Logs guardados para auditoría

---

**Última Actualización:** 2026-04-27 23:45
**Responsable:** Claude Haiku 4.5
**Estado**: ✅ Completado y Pusheado a GitHub
