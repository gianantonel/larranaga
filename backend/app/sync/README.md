# Sistema de Sincronización InsForge

Módulo que sincroniza automáticamente la base de datos SQLite local con InsForge Cloud.

## Archivos

- `insforge_sync.py` — Script principal de sincronización
- `events.py` — Event listeners de SQLAlchemy para sincronización automática
- `__init__.py` — Exporta funciones del módulo
- `README.md` — Esta documentación

## Cómo Funciona

### Automático (Por defecto)

Cada vez que se modifica la base de datos:
1. SQLAlchemy detecta los cambios
2. Se dispara un evento `after_commit`
3. El módulo `events.py` ejecuta la sincronización en background
4. Los cambios se replican a InsForge automáticamente

### Manual

Si necesitas forzar una sincronización:

```bash
# Vía API
POST http://localhost:8000/admin/sync-insforge

# Vía CLI
python -m app.sync.insforge_sync
```

## Uso en Código

```python
from app.sync import sync_now, export_database_to_sql

# Sincronización manual
success = sync_now()

# Exportar BD a SQL
sql = export_database_to_sql('backend/larranaga.db')
```

## Configuración

Variables de entorno (opcional):

```bash
INSFORGE_API_KEY=tu_clave
INSFORGE_API_URL=tu_url
```

Por defecto usa las credenciales de tu instancia de InsForge.

## Logs

Se guardan en: `backend/logs/insforge_sync.log`

## Características

- ✓ Sincronización automática al guardar cambios
- ✓ Reintentos automáticos con backoff exponencial
- ✓ Ejecución en thread separado (no bloquea la aplicación)
- ✓ Conversión de tipos de datos SQLite → PostgreSQL
- ✓ Logging completo de todas las operaciones
- ✓ Endpoint admin para sincronización manual
- ✓ Manejo de errores robusto

## Próximas Mejoras

- [ ] Sincronización incremental (solo cambios)
- [ ] Dashboard de estado de sincronización
- [ ] Alertas para fallos de sincronización
- [ ] Sincronización bidireccional desde InsForge
