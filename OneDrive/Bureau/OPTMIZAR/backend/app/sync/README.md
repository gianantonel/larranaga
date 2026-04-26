# Sistema de Sincronización InsForge

Módulo que sincroniza automáticamente la base de datos SQLite local con InsForge Cloud.

## Archivos

- `insforge_sync.py` — Script principal de sincronización
- `__init__.py` — Exporta funciones del módulo

## Uso

### Sincronización Manual

```bash
cd backend
python -m app.sync.insforge_sync
```

### Importar en Otras Partes del Código

```python
from app.sync import sync_to_insforge, export_database_to_sql

# Exportar la BD a SQL
sql = export_database_to_sql('backend/larranaga.db')

# Sincronizar a InsForge
success = sync_to_insforge(sql)
```

## Configuración

Variables de entorno requeridas:

```bash
INSFORGE_API_KEY=ik_6e043a410661a9bfaed032bf81e065fd
INSFORGE_API_URL=https://vivnx98a.us-east.insforge.app
```

## Logs

Los logs se guardan en `backend/logs/insforge_sync.log`

## Próximas Mejoras

- Integración con eventos SQLAlchemy para sincronización automática
- Soporte para cambios incrementales (no todo el dump)
- API endpoint para disparar sincronización manualmente
- Dashboard de estado de sincronización
