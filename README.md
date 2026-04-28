# Larrañaga — Plataforma Contable y Legal

Plataforma integral para estudios contables y legales. Automatización de facturación, IVA, DDJJ, retenciones y más.

---

## 🚀 Quick Start

```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

---

## 📋 Política de Documentación (⚠️ OBLIGATORIO)

**Cada cambio que hagas debe estar documentado en `actualizaciones-larranaga.md`**

### Antes de Comenzar a Trabajar
```bash
# Lee los cambios recientes
head -100 actualizaciones-larranaga.md
```

### Antes de Hacer Commit
```bash
# 1. Lee la guía
cat CONTRIBUTING.md

# 2. Actualiza la documentación usando la plantilla
cat PLANTILLA-CAMBIOS.txt

# 3. Pega tu cambio en actualizaciones-larranaga.md

# 4. Haz commit (incluye el documento)
git add actualizaciones-larranaga.md
git commit -m "feat: descripción de tu cambio"
```

### Sin Documentación = PR Rechazado
- ❌ Tu código no será mergeado
- ❌ El equipo no sabrá qué hiciste
- ❌ Bloquea deployments

---

## 📚 Documentos Obligatorios

| Documento | Propósito |
|-----------|-----------|
| **actualizaciones-larranaga.md** | Registro de cambios del proyecto |
| **CONTRIBUTING.md** | Guía detallada de cómo documentar |
| **PLANTILLA-CAMBIOS.txt** | Template para copiar/pegar |
| **README_POLITICAS.md** | Políticas del proyecto |

---

## 🏗️ Arquitectura

### Backend (FastAPI)
- `backend/app/main.py` — Punto de entrada
- `backend/app/routers/` — Endpoints por módulo
- `backend/app/sync/` — Sincronización InsForge
- `backend/logs/` — Logs de aplicación

### Frontend (React)
- `frontend/src/pages/` — Páginas principales
- `frontend/src/components/` — Componentes reutilizables
- `frontend/src/utils/` — Utilidades

### Base de Datos
- `backend/larranaga.db` — SQLite local
- **InsForge Cloud** — Backup en nube

---

## 🔄 Workflow de Ramas

```
fede (tu rama)
  ↓ PR cuando esté listo
dev (integración)
  ↓
origin (GitHub)
```

---

## 📦 Sincronización InsForge

Cada cambio en la BD se sincroniza automáticamente a InsForge Cloud.

```bash
# Manual sync
POST http://localhost:8000/admin/sync-insforge

# Ver logs
tail -f backend/logs/insforge_sync.log
```

---

## 🛠️ Tecnologías

| Stack | Tecnología |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, SQLite |
| Frontend | React, Vite, Tailwind CSS |
| Cloud | InsForge (PostgreSQL) |
| Auth | JWT |

---

## 📞 Soporte

- Documentación: Ver `CONTRIBUTING.md`
- Cambios recientes: Ver `actualizaciones-larranaga.md`
- Políticas: Ver `README_POLITICAS.md`

---

## ⚠️ IMPORTANTE

**Política Obligatoria:** Todos los cambios deben estar documentados en `actualizaciones-larranaga.md`. 

Sin documentación:
- ❌ Tu PR será rechazado
- ❌ El equipo no sabrá qué hiciste
- ❌ Bloquea cualquier merge a dev

---

**Última Actualización:** 2026-04-27
