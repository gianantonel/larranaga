# Guía de Contribución - Larrañaga

## 📋 Obligación: Documentar Cambios en actualizaciones-larranaga.md

Cada commit que hagas **DEBE** incluir una entrada en `actualizaciones-larranaga.md`.

---

## ✅ Checklist Antes de Hacer Commit

- [ ] ¿Leíste `actualizaciones-larranaga.md` para ver cambios recientes?
- [ ] ¿Actualicé `actualizaciones-larranaga.md` con mis cambios?
- [ ] ¿Especifiqué QUÉ cambié?
- [ ] ¿Especifiqué DÓNDE cambié (archivos/carpetas)?
- [ ] ¿Incluí el commit hash en la entrada?

---

## 📝 Cómo Actualizar actualizaciones-larranaga.md

### Formato Requerido

Cada nueva sección de cambios debe tener:

```markdown
## YYYY-MM-DD — Descripción Breve de Cambios

### 🎯 Resumen
1-2 líneas explicando qué se hizo y por qué.

### ✨ Cambios Realizados

#### 1. **Nombre del Cambio**

**Archivos Modificados:**
- `ruta/archivo.ext` — Breve descripción

**Archivos Creados:**
- `ruta/archivo.ext` — Breve descripción

**Funcionalidad:**
- ✅ Punto 1
- ✅ Punto 2

**Commit:** `hash1234`

---
```

### Ejemplo Real

```markdown
## 2026-04-27 — Sistema de Sincronización InsForge + UI Improvements

### 🎯 Resumen
Integración automática de sincronización SQLite ↔ InsForge y reorganización de navegación.

### ✨ Cambios Realizados

#### 1. **Sistema de Sincronización Automática**

**Archivos Creados:**
- `backend/app/sync/insforge_sync.py` — Export DB a SQL
- `backend/app/sync/events.py` — Event listeners

**Archivos Modificados:**
- `backend/app/main.py` — Registra listeners en startup

**Funcionalidad:**
- ✅ Auto-sync en cambios de BD
- ✅ Endpoint manual POST /admin/sync-insforge

**Commit:** `c8d6d03`

---
```

---

## 🔍 Cómo Consultar Cambios Recientes

**Antes de comenzar a trabajar:**

```bash
# Ver últimos cambios
head -50 actualizaciones-larranaga.md

# Buscar cambios en área específica
grep -n "frontend\|backend\|sync" actualizaciones-larranaga.md

# Ver solo la fecha más reciente
grep "^## 20" actualizaciones-larranaga.md | head -1
```

---

## 🚫 Qué Pasa Si No Documentas

- ❌ Tu PR será rechazado
- ❌ El commit no será mergeable
- ❌ El equipo no sabrá qué hiciste

---

## 📊 Obligaciones por Tipo de Cambio

### Bug Fix
```
**Cambios:**
- ✅ Descripción breve del bug
- ✅ Cómo se fixeó
- ✅ Archivos afectados

**Commit:** `hash`
```

### Nueva Funcionalidad
```
**Archivos Creados:**
- `ruta/archivo.ext` — Descripción

**Archivos Modificados:**
- `ruta/archivo.ext` — Cambios

**Funcionalidad:**
- ✅ Feature 1
- ✅ Feature 2

**Commit:** `hash`
```

### Refactor
```
**Cambios:**
- ✅ Qué se refactorizó
- ✅ Por qué se refactorizó
- ✅ Archivos afectados

**Commit:** `hash`
```

---

## 🔗 Referencias Útiles

- **Archivo de Actualizaciones:** `actualizaciones-larranaga.md`
- **Branches Principales:** `dev` (integración), `fede` (trabajo)
- **Logs:** `backend/logs/insforge_sync.log`

---

## 📌 Workflow Recomendado

```bash
# 1. Leer cambios recientes
cat actualizaciones-larranaga.md | head -100

# 2. Hacer cambios

# 3. Actualizar actualizaciones-larranaga.md

# 4. Commit (incluirá el documento)
git add .
git commit -m "feat/fix/refactor: descripción"

# 5. Push
git push origin fede
```

---

## 🤔 Preguntas Frecuentes

**P: ¿Qué si solo cambié una línea?**
R: Documenta igual. Los cambios pequeños también cuentan.

**P: ¿Debo documentar antes o después del commit?**
R: Antes. El documento debe actualizar con tu commit.

**P: ¿Qué formato de commit uso?**
R: El que usa el equipo. Pero actualiza `actualizaciones-larranaga.md` también.

**P: ¿Y si mi cambio es muy pequeño?**
R: No existe "demasiado pequeño". Documenta.

---

**⚠️ OBLIGATORIO:** Sin actualizar `actualizaciones-larranaga.md`, tu PR no será mergeado.

---

**Última Actualización:** 2026-04-27
