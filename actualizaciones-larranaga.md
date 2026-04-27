# Actualizaciones Larrañaga — Registro de Cambios

Documento de control de todas las actualizaciones realizadas en la plataforma Larrañaga.

---

## 2026-04-27 — Sistema de Sincronización InsForge + UI Improvements

### 📌 Resumen Ejecutivo
✅ Sistema de sincronización automática SQLite ↔ InsForge integrado
✅ UI sidebar reorganizado en árbol colapsable
✅ 3,209 registros migrados a InsForge Cloud

---

### ✨ Cambios Realizados

#### 1. **Sistema de Sincronización Automática**

**Archivos Creados:**
- `backend/app/sync/insforge_sync.py` — Export + API calls
- `backend/app/sync/events.py` — SQLAlchemy listeners
- `backend/app/sync/__init__.py` — Module exports
- `backend/logs/.gitkeep` — Log directory

**Archivos Modificados:**
- `backend/app/main.py` — Register sync events + endpoint admin

**Features:**
- ✅ Auto-sync on DB changes (background thread)
- ✅ Manual endpoint: POST /admin/sync-insforge
- ✅ Auto-retry con backoff exponencial
- ✅ Logs en backend/logs/insforge_sync.log

**Commits:**
- `c8d6d03` / `1418507`

---

#### 2. **UI — Reorganización Sidebar**

**Archivos Modificados:**
- `frontend/src/components/Layout/Sidebar.jsx` — Tree structure
- `frontend/src/index.css` — New styles
- `frontend/src/pages/Herramientas.jsx` — Renamed

**Cambios:**
- ✅ 3 collapsible groups (Vistas, Acciones, Otras Acciones)
- ✅ ChevronRight animation
- ✅ Renamed R-01/R-02 → function names
- ✅ "Tesorería" disabled badge

**Commit:** `4663e9e`

---

#### 3. **Migración BD a InsForge**

- ✅ 3,209 registros × 13 tablas
- ✅ URL: https://vivnx98a.us-east.insforge.app
- ✅ API Key: ik_6e043a410661a9bfaed032bf81e065fd

---

### 🔍 Búsqueda Rápida

**Por Funcionalidad:**
- InsForge sync → `backend/app/sync/`
- UI sidebar → `frontend/src/components/Layout/Sidebar.jsx`
- Styles → `frontend/src/index.css`

**Comandos:**
```bash
git log --oneline | grep insforge
python -m app.sync.insforge_sync
tail -f backend/logs/insforge_sync.log
```

---

**Última Actualización:** 2026-04-27
**Estado:** ✅ Completado y Pusheado a GitHub
