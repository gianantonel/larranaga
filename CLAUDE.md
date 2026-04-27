# Instrucciones para Claude (IA) — Proyecto Larrañaga

## 📋 REGLA OBLIGATORIA: Documentar Todos los Cambios

**Cada vez que hagas cambios en el proyecto, DEBES actualizar `actualizaciones-larranaga.md`.**

Esta es una regla para ti (Claude), no opcional.

---

## ✅ Checklist ANTES de Hacer Commit

- [ ] ¿Hice cambios en el proyecto?
- [ ] ¿Actualicé `actualizaciones-larranaga.md` con los cambios?
- [ ] ¿Especifiqué QUÉ cambié?
- [ ] ¿Especifiqué DÓNDE cambié (archivos/carpetas)?
- [ ] ¿Incluí el commit hash en la entrada?
- [ ] ¿Hice commit que incluye el documento actualizado?

---

## 📝 Formato Obligatorio para Documentar

```markdown
## YYYY-MM-DD — [Descripción Breve]

### 🎯 Resumen
[1-2 líneas de QUÉ y POR QUÉ]

### ✨ Cambios Realizados

#### 1. **[Nombre del Cambio]**

**Archivos Creados:**
- `ruta/archivo.ext` — Descripción

**Archivos Modificados:**
- `ruta/archivo.ext` — Cambio realizado

**Funcionalidad:**
- ✅ Punto 1
- ✅ Punto 2

**Commits:** `hash1`, `hash2`

---
```

---

## 🚫 Lo que NO debes hacer

- ❌ Hacer commit sin actualizar `actualizaciones-larranaga.md`
- ❌ Dejar cambios sin documentar
- ❌ Hacer merge a dev sin documentación
- ❌ Crear PRs sin actualizar el documento

---

## 🔄 Workflow Claude

1. **Leer Cambios Recientes**
   ```
   Revisar actualizaciones-larranaga.md para ver trabajo anterior
   ```

2. **Hacer Cambios**
   ```
   Implementar features/fixes según instrucciones del usuario
   ```

3. **Documentar en actualizaciones-larranaga.md**
   ```
   Agregar entrada detallada de los cambios
   ```

4. **Hacer Commit**
   ```
   git add actualizaciones-larranaga.md
   git commit -m "feat/fix: descripción"
   ```

5. **Push**
   ```
   git push origin fede
   ```

---

## 📚 Archivos de Referencia

- **actualizaciones-larranaga.md** — Documento principal de cambios
- **PLANTILLA-CAMBIOS.txt** — Template para copiar
- **CONTRIBUTING.md** — Guía para humanos (informativo)
- **README_POLITICAS.md** — Políticas del proyecto

---

## ⚠️ REGLA FINAL

**OBLIGATORIO:** Cada cambio que hagas debe estar documentado antes de hacer commit.

Sin excepción. Sin negociación. Esta es la regla para ti como IA.

---

**Vigente desde:** 2026-04-27
**Aplica a:** Todos los cambios realizados por Claude
