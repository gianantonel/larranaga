"""
Event listeners para sincronización automática con InsForge.

Detecta cambios en la base de datos y dispara la sincronización.
"""

import logging
import threading
from sqlalchemy import event
from sqlalchemy.orm import Session
from .insforge_sync import sync_to_insforge, export_database_to_sql

logger = logging.getLogger(__name__)

# Flag para rastrear si hay cambios pendientes
_pending_sync = False
_sync_lock = threading.Lock()


def register_sync_events(engine):
    """
    Registra event listeners en el engine para detectar cambios.

    Debe llamarse después de crear el engine pero antes de usar la aplicación.
    """

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Evento al conectarse."""
        logger.debug("Conexión a BD establecida")

    logger.info("Event listeners de sincronización registrados")


def register_session_sync_events(session: Session):
    """
    Registra listeners en una sesión para detectar cambios antes del commit.

    Se debe llamar después de crear una sesión.
    """

    @event.listens_for(session, "after_commit")
    def receive_after_commit():
        """Disparado después de un commit exitoso."""
        logger.debug("Commit detectado en sesión")
        _trigger_sync()

    @event.listens_for(session, "after_flush")
    def receive_after_flush(session, flush_context):
        """Disparado después de flush."""
        if session.new or session.dirty or session.deleted:
            logger.debug(f"Cambios detectados: new={len(session.new)}, dirty={len(session.dirty)}, deleted={len(session.deleted)}")


def _trigger_sync():
    """Dispara la sincronización a InsForge de forma asincrónica."""

    global _pending_sync

    with _sync_lock:
        if _pending_sync:
            logger.debug("Sincronización ya está pendiente, ignorando")
            return

        _pending_sync = True

    # Ejecutar sincronización en thread separado para no bloquear la aplicación
    thread = threading.Thread(target=_do_sync, daemon=True)
    thread.start()


def _do_sync():
    """Ejecuta la sincronización."""

    global _pending_sync

    try:
        logger.info("Iniciando sincronización automática a InsForge...")

        # Obtener la ruta de la BD (por defecto larranaga.db)
        import os
        db_path = os.path.join(os.path.dirname(__file__), '../../..', 'backend', 'larranaga.db')

        # Exportar
        sql_content = export_database_to_sql(db_path)

        # Sincronizar
        success = sync_to_insforge(sql_content, retry_attempts=3)

        if success:
            logger.info("Sincronización automática completada exitosamente")
        else:
            logger.error("Sincronización automática falló (pero continuó la aplicación)")

    except Exception as e:
        logger.error(f"Error en sincronización automática: {e}", exc_info=True)

    finally:
        with _sync_lock:
            _pending_sync = False


def sync_now():
    """Dispara una sincronización inmediata (sincrónica)."""

    logger.info("Sincronización manual iniciada")

    try:
        import os
        db_path = os.path.join(os.path.dirname(__file__), '../../..', 'backend', 'larranaga.db')
        sql_content = export_database_to_sql(db_path)
        success = sync_to_insforge(sql_content, retry_attempts=3)

        if success:
            logger.info("Sincronización manual completada")
            return True
        else:
            logger.error("Sincronización manual falló")
            return False

    except Exception as e:
        logger.error(f"Error en sincronización manual: {e}", exc_info=True)
        return False
