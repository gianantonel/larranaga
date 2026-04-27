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
- `backend/app/sync/events.py` — Event listeners de SQLAlchemy (detección automática)
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
- ✅ 3 grupos colapsables (Vistas, Acciones, Otras Acciones)
- ✅ Animación ChevronRight rotate-90
- ✅ Renombrado R-01/R-02 → nombres descriptivos
- ✅ Item "Tesorería" disabled con badge "Próx."

**Commits:**
- `4663e9e` — feat(UI): Reorganizar navegación en árbol colapsable

---

#### 3. **Migración de BD a InsForge Cloud**

- ✅ Exportación de `larranaga.db` → SQL PostgreSQL
- ✅ Importación: **3,209 registros** en **13 tablas**
- ✅ URL: `https://vivnx98a.us-east.insforge.app`

---

### 🔍 Cómo Encontrar Cambios Específicos

**Por Funcionalidad:**
- Sincronización InsForge → `backend/app/sync/`
- UI Sidebar → `frontend/src/components/Layout/Sidebar.jsx`
- Estilos → `frontend/src/index.css`

**Por Rama:**
```bash
git log --oneline dev | grep insforge
git log --oneline fede | grep insforge
```

---

### 🔗 Referencias Rápidas

**Endpoint Nuevo:**
- `POST /admin/sync-insforge` — Sincronización manual

**Comando Útil:**
```bash
python -m app.sync.insforge_sync    # Sincronización manual
tail -f backend/logs/insforge_sync.log  # Ver logs
```

---

**Última Actualización:** 2026-04-27
**Estado:** ✅ Completado y Pusheado a GitHub
