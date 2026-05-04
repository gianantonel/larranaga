"""
Event listeners para sincronización automática con InsForge.

Detecta cambios en la base de datos y dispara la sincronización.
"""

import logging
import threading
from sqlalchemy import event
from sqlalchemy.orm import Session
from .insforge_sync import sync_to_insforge, export_database_to_sql, get_db_path

logger = logging.getLogger(__name__)

# Flag para evitar sincronizaciones simultáneas
_pending_sync = False
_sync_lock = threading.Lock()


def register_sync_events(engine):
    """
    Registra event listeners en el engine para detectar cambios.

    Debe llamarse después de crear el engine pero antes de usar la aplicación.
    """

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        logger.debug("Conexión a BD establecida")

    logger.info("Event listeners de sincronización InsForge registrados")


def register_session_sync_events(session: Session):
    """
    Registra listeners en una sesión para detectar cambios y disparar sync.

    Se debe llamar en el middleware o dependency de FastAPI si se quiere
    auto-sincronización por sesión.
    """

    @event.listens_for(session, "after_commit")
    def receive_after_commit():
        logger.debug("Commit detectado — disparando sync InsForge")
        _trigger_sync()

    @event.listens_for(session, "after_flush")
    def receive_after_flush(session, flush_context):
        if session.new or session.dirty or session.deleted:
            logger.debug(
                f"Cambios detectados: "
                f"new={len(session.new)}, dirty={len(session.dirty)}, deleted={len(session.deleted)}"
            )


def _trigger_sync():
    """Dispara la sincronización a InsForge de forma asincrónica (no bloquea)."""

    global _pending_sync

    with _sync_lock:
        if _pending_sync:
            logger.debug("Sincronización ya está en curso, ignorando")
            return
        _pending_sync = True

    thread = threading.Thread(target=_do_sync, daemon=True)
    thread.start()


def _do_sync():
    """Ejecuta la sincronización en un thread separado."""

    global _pending_sync

    try:
        logger.info("Iniciando sincronización automática a InsForge...")
        db_path = get_db_path()
        sql_content = export_database_to_sql(db_path)
        success = sync_to_insforge(sql_content, retry_attempts=3)

        if success:
            logger.info("Sincronización automática completada exitosamente")
        else:
            logger.error("Sincronización automática falló (aplicación continúa normalmente)")

    except Exception as e:
        logger.error(f"Error en sincronización automática: {e}", exc_info=True)

    finally:
        with _sync_lock:
            _pending_sync = False


def sync_now() -> bool:
    """Dispara una sincronización inmediata (sincrónica). Retorna True si fue exitosa."""

    logger.info("Sincronización manual InsForge iniciada")

    try:
        db_path = get_db_path()
        sql_content = export_database_to_sql(db_path)
        success = sync_to_insforge(sql_content, retry_attempts=3)

        if success:
            logger.info("Sincronización manual completada exitosamente")
        else:
            logger.error("Sincronización manual falló")

        return success

    except Exception as e:
        logger.error(f"Error en sincronización manual: {e}", exc_info=True)
        return False
