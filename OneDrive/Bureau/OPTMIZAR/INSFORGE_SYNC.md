# Sincronización con InsForge

## Descripción
Este documento describe el sistema de sincronización bidireccional entre la base de datos SQLite local (larranaga.db) y InsForge Cloud.

## Arquitectura

```
SQLite (Backend Local)
        ↓
    Cambios en BD
        ↓
    Hook de Sincronización
        ↓
    InsForge Cloud
```

## Funcionamiento

### 1. Sincronización Automática al Guardar Cambios

Cuando se realizan cambios en la base de datos del backend:
- `INSERT`, `UPDATE`, `DELETE` en cualquier tabla
- Se ejecuta automáticamente el script de sincronización
- Los cambios se replican a InsForge en tiempo real

### 2. Ubicación del Script

```
backend/app/sync/insforge_sync.py
```

Este script:
- Se ejecuta después de cada operación en la BD
- Exporta cambios desde SQLite
- Los importa a InsForge vía API REST

### 3. Credenciales

Las credenciales de InsForge se almacenan en variables de entorno:

```bash
INSFORGE_API_KEY=ik_6e043a410661a9bfaed032bf81e065fd
INSFORGE_API_URL=https://vivnx98a.us-east.insforge.app
```

### 4. Tablas Sincronizadas

Todas las tablas se sincronizan automáticamente:
- ✓ users
- ✓ clients
- ✓ client_collaborators
- ✓ tasks
- ✓ subtasks
- ✓ iva_records
- ✓ invoices
- ✓ ingresos_brutos
- ✓ action_logs
- ✓ comprobantes_recibidos
- ✓ retenciones_percepciones
- ✓ limpiezas_iva
- ✓ movimientos_cc

### 5. Campos Excluidos

Los siguientes campos no se sincronizan (datos binarios):
- `limpiezas_iva.archivo_corregido` (BLOB)

### 6. Flujo de Sincronización

```
1. Usuario/Sistema modifica BD local
   ↓
2. SQLAlchemy guarda en SQLite
   ↓
3. Event listener captura el cambio
   ↓
4. Script insforge_sync.py se ejecuta
   ↓
5. Exporta datos relevantes
   ↓
6. API POST /api/database/advance/import en InsForge
   ↓
7. Sincronización completada
```

### 7. Monitoreo

Se registran todos los eventos de sincronización en:
```
backend/logs/insforge_sync.log
```

### 8. Manejo de Errores

Si la sincronización falla:
- Se registra en el log
- Se reintenta automáticamente (máximo 3 intentos)
- Si persiste, se notifica al administrador
- Los cambios locales se mantienen intactos

### 9. Configuración

Para habilitar/deshabilitar sincronización, editar:
```
backend/config.py

INSFORGE_SYNC_ENABLED = True  # o False para deshabilitar
INSFORGE_SYNC_RETRY_ATTEMPTS = 3
INSFORGE_SYNC_TIMEOUT = 120  # segundos
```

## Uso

### Sincronización Manual (si es necesario)

```bash
cd backend
python -m app.sync.insforge_sync --full-export
```

### Ver Estado de Sincronización

```bash
python -m app.sync.insforge_sync --status
```

## Próximos Pasos

- [ ] Implementar sincronización desde InsForge hacia backend
- [ ] Agregar UI para ver estado de sincronización
- [ ] Dashboard con métricas de sincronización
- [ ] Alertas en tiempo real para fallos de sincronización

---

**Última actualización:** 2026-04-25
**Estado:** Implementación Inicial
