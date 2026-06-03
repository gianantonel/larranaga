"""
Event listeners y scheduler periódico para sincronización con InsForge.

- register_sync_events: hook de SQLAlchemy (placeholder, no dispara sync por commit
  porque InsForge sync es caro — 1+ MB SQL upload)
- start_periodic_sync: timer que cada N segundos dispara un sync en background
- sync_now: trigger sincrónico (usado por endpoints REST)
"""

import logging
import os
import threading
from sqlalchemy import event
from sqlalchemy.orm import Session
from .insforge_sync import sync_to_insforge, export_database_to_sql, get_db_path

logger = logging.getLogger(__name__)

# Flag para evitar sincronizaciones simultáneas
_pending_sync = False
_sync_lock = threading.Lock()

# Timer de auto-sync periódico
_periodic_timer: threading.Timer | None = None
_periodic_stop = threading.Event()


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


def start_periodic_sync(interval_seconds: int = 0) -> bool:
    """
    Arranca un timer en background que dispara sync_to_insforge() cada
    `interval_seconds` segundos. Si interval_seconds <= 0, no hace nada
    (auto-sync deshabilitado).

    Lee la env var INSFORGE_AUTOSYNC_INTERVAL_SECONDS si interval_seconds=0.
    Retorna True si arrancó el timer, False si quedó deshabilitado.
    """
    global _periodic_timer

    if interval_seconds <= 0:
        try:
            interval_seconds = int(os.getenv("INSFORGE_AUTOSYNC_INTERVAL_SECONDS", "0"))
        except ValueError:
            interval_seconds = 0

    if interval_seconds <= 0:
        logger.info("Auto-sync InsForge deshabilitado (INSFORGE_AUTOSYNC_INTERVAL_SECONDS=0)")
        return False

    logger.info(f"Auto-sync InsForge habilitado: cada {interval_seconds}s")

    def _tick():
        if _periodic_stop.is_set():
            return
        try:
            _trigger_sync()
        except Exception as e:
            logger.error(f"Auto-sync tick error: {e}", exc_info=True)
        # Re-armar el timer
        if not _periodic_stop.is_set():
            global _periodic_timer
            _periodic_timer = threading.Timer(interval_seconds, _tick)
            _periodic_timer.daemon = True
            _periodic_timer.start()

    # Arrancar el primer tick (al intervalo, no inmediato)
    _periodic_timer = threading.Timer(interval_seconds, _tick)
    _periodic_timer.daemon = True
    _periodic_timer.start()
    return True


def stop_periodic_sync():
    """Frena el timer de auto-sync (útil en shutdown)."""
    global _periodic_timer
    _periodic_stop.set()
    if _periodic_timer is not None:
        _periodic_timer.cancel()
        _periodic_timer = None
    logger.info("Auto-sync InsForge detenido")


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
