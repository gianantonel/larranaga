# Políticas del Proyecto Larrañaga

## 📋 Política #1: Documentación Obligatoria de Cambios

### ¿Por Qué?
- **Transparencia**: El equipo sabe qué cambios se hicieron
- **Trazabilidad**: Podemos rastrear cuándo y dónde se hizo cada cambio
- **Onboarding**: Los nuevos desarrolladores entienden la historia del proyecto
- **Debugging**: Facilita encontrar cuándo se introdujo un bug

### ¿Qué Es Obligatorio?
Cada **commit** (excepto merge commits) debe incluir una entrada en `actualizaciones-larranaga.md` que describe:
1. **QUÉ** se cambió (descripción)
2. **DÓNDE** se cambió (archivos/carpetas)
3. **POR QUÉ** se cambió (razón/contexto)
4. **HASH** del commit

### ¿Quién Debe Hacerlo?
**Todos los desarrolladores, sin excepción.**

### ¿Cuándo?
**Antes de hacer el commit**, actualizar el documento.

### ¿Cómo?
1. Lee `CONTRIBUTING.md` para instrucciones detalladas
2. Usa `PLANTILLA-CAMBIOS.txt` como base
3. Actualiza `actualizaciones-larranaga.md`
4. Haz commit que incluya el documento

### ¿Qué Pasa Si No Lo Haces?
- ❌ PR será rechazado por code review
- ❌ No será mergeado a dev
- ❌ Bloquea el deployment

---

## 📖 Política #2: Lectura de Cambios Recientes

### Obligación
Cada vez que **comienzes a trabajar**, debes leer `actualizaciones-larranaga.md` para:
- Entender qué cambios se hicieron recientemente
- Evitar duplicar trabajo
- Entender el contexto del código
- Prevenir conflictos de merge

### Comandos Rápidos
```bash
# Ver últimos cambios
head -100 actualizaciones-larranaga.md

# Buscar en tu área de trabajo
grep "frontend\|backend" actualizaciones-larranaga.md
```

---

## 🔄 Política #3: Sincronización de Ramas

### Branches Principales
- **dev**: Rama de integración (cambios estables)
- **fede**: Tu rama personal de trabajo

### Workflow
1. Comienza en **fede**
2. Haz cambios y actualiza documentación
3. Haz commit
4. Haz pull request a **dev** cuando esté listo
5. Sync fede ← dev regularmente

### Checklist Antes de PR
- [ ] Leí `actualizaciones-larranaga.md`
- [ ] Actualicé `actualizaciones-larranaga.md`
- [ ] Los cambios están en `actualizaciones-larranaga.md`
- [ ] El commit está listo para merge

---

## 🛠️ Herramientas Disponibles

| Archivo | Propósito |
|---------|-----------|
| `actualizaciones-larranaga.md` | Registro de todos los cambios |
| `CONTRIBUTING.md` | Guía detallada de contribución |
| `PLANTILLA-CAMBIOS.txt` | Template para documentar cambios |
| `README_POLITICAS.md` | Este documento |

---

## 📞 Preguntas?

Si tienes dudas sobre cómo documentar un cambio:
1. Lee `CONTRIBUTING.md`
2. Mira ejemplos en `actualizaciones-larranaga.md`
3. Usa `PLANTILLA-CAMBIOS.txt`

---

**Recordatorio:** Sin documentar cambios, tu código no será mergeado.

**Última Actualización:** 2026-04-27
