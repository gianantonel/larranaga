# Actualizaciones Larrañaga — Registro de Cambios

Documento de control de todas las actualizaciones realizadas en la plataforma Larrañaga.

---

## 2026-04-27 — Panel de Gestión de Usuarios + Refactor de Roles

### 📌 Resumen
Nuevo sistema de roles (Super-Admin / Admin / Colaborador / Invitado), header global con dropdown, y página `/usuarios` con flujo de invitación-aprobación.

### ✨ Cambios Realizados

#### 1. **Refactor del modelo de usuarios**

**Archivos modificados:**
- `backend/app/models.py` — Enum `UserRole` con 4 roles claros (`super_admin`, `admin`, `colaborador`, `invitado`); nuevo enum `UserStatus` (`active`, `pending`); columnas `last_name`, `cuit`, `status` en tabla `users`
- `backend/app/schemas.py` — `UserCreate`, `UserUpdate`, `UserOut` actualizados; nuevo `UserRoleUpdate`
- `backend/app/mock_data.py` — Seed de 4 super-admins + colaboradores con apellido separado

**Archivos creados:**
- `backend/scripts/migrate_users_v2.py` — Script idempotente que: agrega columnas faltantes, mapea `admin1/2/3 → admin`, `collaborator → colaborador`, garantiza los 4 super-admins, marca todo como `active`

#### 2. **Endpoints `/users` (nuevo router)**

**Archivo creado:** `backend/app/routers/users.py`

**Endpoints:**
- `GET /users/` — Lista activos (admin+)
- `GET /users/pending` — Pendientes de aprobación
- `POST /users/invite` — Invitación (queda en `pending`)
- `PATCH /users/{id}/role` — Cambiar rol (con jerarquía)
- `PATCH /users/{id}/approve` — Aprobar pendiente
- `DELETE /users/{id}` — Soft-delete

**Reglas de permisos (enforced server-side):**
- Super-Admin puede asignar: `admin`, `colaborador`, `invitado`
- Admin puede asignar: `colaborador`, `invitado`
- Nadie puede asignar `super_admin` (solo via seed/migración)
- Nadie puede modificar a un super-admin salvo otro super-admin
- Un admin no puede modificar a otro admin

**Helpers en `auth.py`:** `require_admin` (super_admin + admin), nuevo `require_super_admin`.

#### 3. **Frontend — Header global + Dropdown**

**Archivos creados:** `frontend/src/components/Layout/Header.jsx`

**Archivos modificados:**
- `frontend/src/components/Layout/Layout.jsx` — Integra Header arriba del Outlet
- `frontend/src/components/Layout/Sidebar.jsx` — Removido el botón Logout (migrado al dropdown)

**Funcionalidad:**
- Esquina superior derecha: nombre + apellido + rol + flecha
- Dropdown: email del usuario, "Gestión de Usuarios" (solo admins) y "Cerrar sesión"
- Cierra al click outside

#### 4. **Página `/usuarios`**

**Archivo creado:** `frontend/src/pages/Usuarios.jsx`

**Archivos modificados:**
- `frontend/src/App.jsx` — Ruta `/usuarios` registrada
- `frontend/src/context/AuthContext.jsx` — `isSuperAdmin`, `assignableRoles`, `canAssignRole`; `isAdmin` limpiado de roles obsoletos

**Funcionalidad:**
- Tabla **Activos**: nombre, apellido, CUIT/CUIL, email, rol (badge por rol) + lápiz para editar rol
- Tabla **Pendientes**: misma cabecera + selector de rol inicial + botón aprobar
- Botón **Invitar usuario** (modal con form completo: nombre/apellido/CUIT/email/contraseña/rol)
- Modal de edición de rol restringido por jerarquía
- Las opciones del selector se filtran por `assignableRoles` del usuario actual

### 🔬 Validación end-to-end
- ✅ Login super-admin
- ✅ Invitar usuario → queda `pending`
- ✅ Aprobar pendiente → pasa a `active`
- ✅ Backend rechaza intento de asignar `super_admin` (`403: No tenés permisos para asignar el rol 'super_admin'`)
- ✅ Migración corre sobre BD existente sin perder datos: 4 super-admins, 3 admins, 8 colaboradores

### 🔑 Credenciales de los 4 Super-Admins
| Email | Password (default) |
|---|---|
| optimizar.ai@gmail.com | admin123 |
| gianantonel@gmail.com | admin123 |
| rodriguezfederico765@gmail.com | admin123 |
| gerogambuli2002@gmail.com | admin123 |

> Recordá cambiar las contraseñas en producción.

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
