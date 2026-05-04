"""
Pull/Import desde InsForge -> SQLite local.

Lee registros desde la API REST de InsForge (PostgREST-style)
y los hace upsert en la base de datos local.

API endpoint descubierto: GET /api/database/records/{table}
"""

import logging
import os
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime

from .insforge_sync import INSFORGE_API_KEY, INSFORGE_API_URL

logger = logging.getLogger(__name__)

INSFORGE_RECORDS_BASE = f"{INSFORGE_API_URL}/api/database/records"

# Tablas a sincronizar desde InsForge (orden importa por foreign keys)
PULLABLE_TABLES = [
    "users",
    "clients",
    "client_collaborators",
    "tasks",
    "subtasks",
    "iva_records",
    "invoices",
    "ingresos_brutos",
    "movimientos_cc",
    "comprobantes_recibidos",
    "retenciones_percepciones",
    "limpiezas_iva",
    "action_logs",
]

# Columnas booleanas que vienen como bool desde InsForge (PostgreSQL)
# pero deben guardarse como int en SQLite
BOOLEAN_COLUMNS = {
    "users": ["is_active"],
    "clients": ["is_active"],
    "iva_records": ["filed"],
    "ingresos_brutos": ["filed"],
}

# Campos que NO se traen desde InsForge (encrypted con otra key, binarios, etc.)
EXCLUDED_FIELDS = {
    "clients": ["clave_fiscal_encrypted"],   # encriptado con la key de InsForge, no se puede desencriptar acá
    "limpiezas_iva": ["archivo_corregido"],  # binario
}


def fetch_records(table: str, limit: int = 1000) -> List[Dict[str, Any]]:
    """Lee todos los registros de una tabla desde InsForge."""
    url = f"{INSFORGE_RECORDS_BASE}/{table}"
    headers = {"Authorization": f"Bearer {INSFORGE_API_KEY}"}
    params = {"limit": limit}

    logger.info(f"GET {url}")
    resp = requests.get(url, headers=headers, params=params, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    # InsForge puede retornar directamente la lista o envuelta en {data: [...]}
    if isinstance(data, dict) and "data" in data:
        records = data["data"]
    elif isinstance(data, list):
        records = data
    else:
        logger.warning(f"Formato inesperado de respuesta para {table}: {type(data)}")
        records = []

    logger.info(f"  {table}: {len(records)} registros recibidos")
    return records


# Sufijos de columnas que vienen como strings ISO desde InsForge y deben convertirse a datetime
DATETIME_SUFFIXES = ("_at", "_date")
DATE_FIELDS = ("date", "due_date", "fecha", "fecha_emision", "fecha_retencion",
               "fecha_comprobante", "cae_vto")


def _parse_datetime(value: str):
    """Convierte string ISO a datetime. Acepta formatos con/sin TZ."""
    if not value or not isinstance(value, str):
        return value
    from datetime import datetime, date
    # Quitar 'Z' final si existe
    s = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        try:
            return date.fromisoformat(s[:10])
        except Exception:
            return None


def _normalize_record(table: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte tipos de PostgreSQL/JSON a tipos compatibles con SQLite/SQLAlchemy."""
    excluded = EXCLUDED_FIELDS.get(table, [])
    bool_cols = BOOLEAN_COLUMNS.get(table, [])

    out = {}
    for k, v in record.items():
        if k in excluded:
            continue
        # bools → int (SQLite)
        if k in bool_cols and isinstance(v, bool):
            out[k] = 1 if v else 0
        elif isinstance(v, bool):
            out[k] = 1 if v else 0
        # ISO datetime/date strings → Python datetime/date
        elif isinstance(v, str) and (
            k.endswith(DATETIME_SUFFIXES) or k in DATE_FIELDS
        ):
            parsed = _parse_datetime(v)
            out[k] = parsed if parsed is not None else v
        else:
            out[k] = v
    return out


def upsert_table(db_session, model_cls, records: List[Dict[str, Any]], table_name: str) -> Dict[str, int]:
    """
    UPSERT por id (o cuit para clients) de la lista de records en el modelo dado.
    Retorna {inserted: N, updated: N, skipped: N}.
    """
    from sqlalchemy.exc import IntegrityError

    stats = {"inserted": 0, "updated": 0, "skipped": 0}

    # Para clients: usar cuit como key alternativa (es UNIQUE)
    use_cuit = (table_name == "clients")

    valid_columns = {col.key for col in model_cls.__mapper__.column_attrs}

    for raw in records:
        normalized = _normalize_record(table_name, raw)
        # Filtrar solo columnas que existen en el modelo
        clean = {k: v for k, v in normalized.items() if k in valid_columns}

        if not clean.get("id"):
            stats["skipped"] += 1
            continue

        # Buscar existente
        existing = None
        if use_cuit and clean.get("cuit"):
            existing = db_session.query(model_cls).filter(model_cls.cuit == clean["cuit"]).first()
        if not existing:
            existing = db_session.query(model_cls).filter(model_cls.id == clean["id"]).first()

        try:
            if existing:
                # UPDATE — solo campos no-None de InsForge
                for k, v in clean.items():
                    if k == "id":
                        continue
                    setattr(existing, k, v)
                stats["updated"] += 1
            else:
                # INSERT
                obj = model_cls(**clean)
                db_session.add(obj)
                stats["inserted"] += 1
        except (IntegrityError, TypeError) as e:
            logger.warning(f"  {table_name}: skip {clean.get('id')} ({e})")
            db_session.rollback()
            stats["skipped"] += 1

    return stats


def pull_from_insforge(db_session, tables: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Pull masivo desde InsForge a la BD local.

    tables: lista opcional de nombres de tabla. Si no se da, sincroniza todas las PULLABLE_TABLES.

    Retorna un dict con stats por tabla.
    """
    from .. import models

    # Mapeo de nombre de tabla -> modelo SQLAlchemy
    table_to_model = {
        "users": models.User,
        "clients": models.Client,
        "client_collaborators": models.ClientCollaborator,
        "tasks": models.Task,
        "subtasks": getattr(models, "Subtask", None),
        "iva_records": models.IVARecord,
        "invoices": models.Invoice,
        "ingresos_brutos": getattr(models, "IngresoBruto", None),
        "movimientos_cc": getattr(models, "MovimientoCuentaCorriente", None),
        "comprobantes_recibidos": getattr(models, "ComprobanteRecibido", None),
        "retenciones_percepciones": getattr(models, "RetencionPercepcion", None),
        "limpiezas_iva": getattr(models, "LimpiezaIVA", None),
        "action_logs": getattr(models, "ActionLog", None),
    }

    target_tables = tables or PULLABLE_TABLES
    overall_stats = {"started_at": datetime.utcnow().isoformat(), "tables": {}, "errors": []}

    for table in target_tables:
        model_cls = table_to_model.get(table)
        if model_cls is None:
            logger.warning(f"Tabla {table}: modelo no encontrado, salteando")
            overall_stats["tables"][table] = {"status": "no_model"}
            continue

        try:
            records = fetch_records(table)
            stats = upsert_table(db_session, model_cls, records, table)
            db_session.commit()
            overall_stats["tables"][table] = {"status": "ok", **stats, "fetched": len(records)}
            logger.info(f"  {table}: {stats}")
        except requests.exceptions.HTTPError as e:
            db_session.rollback()
            err = f"{table}: HTTP {e.response.status_code}"
            logger.error(err)
            overall_stats["tables"][table] = {"status": "http_error", "code": e.response.status_code}
            overall_stats["errors"].append(err)
        except Exception as e:
            db_session.rollback()
            err = f"{table}: {type(e).__name__}: {e}"
            logger.error(err, exc_info=True)
            overall_stats["tables"][table] = {"status": "error", "message": str(e)[:200]}
            overall_stats["errors"].append(err)

    overall_stats["finished_at"] = datetime.utcnow().isoformat()
    return overall_stats
