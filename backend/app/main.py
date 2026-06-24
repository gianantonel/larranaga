from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import engine
from . import models
from .sync import register_sync_events, start_periodic_sync

from .routers import (
    auth, clients, collaborators, tasks, iva, facturas, dashboard,
    retenciones, comprobantes, herramientas, cuentas_corrientes,
    honorarios, profesionales_adm, users, bulk, billetes, pagos, imputacion,
    insforge, retiros, flujo_fondos, feature_flags, empleados, liquidacion_personal,
)
from .mock_data import seed_database, seed_profesionales_y_productos, seed_feature_flags, seed_empleados


def _migrate_sqlite():
    """Migración liviana de schema: añade columnas nuevas y recrea tablas con schema
    incorrecto. Cross-dialect (SQLite + PostgreSQL): usa el inspector de SQLAlchemy
    en vez de `PRAGMA table_info` (que es exclusivo de SQLite y rompía el arranque
    en producción sobre Postgres con `syntax error at or near "PRAGMA"`)."""
    from sqlalchemy import inspect as sa_inspect

    new_client_cols = [
        ("tipo_honorario",   "VARCHAR(20)"),
        ("importe_honorario","FLOAT"),
        ("producto_ref_id",  "INTEGER"),
        ("cantidad_unidades","FLOAT"),
        ("profesional_id",   "INTEGER"),
    ]
    new_user_cols = [
        ("last_name", "VARCHAR(100)"),
        ("cuit",      "VARCHAR(13)"),
        ("status",    "VARCHAR(10) DEFAULT 'active'"),
    ]
    new_movimiento_cols = [
        ("periodo_honorario", "VARCHAR(7)"),
        ("forma_pago",        "VARCHAR(20)"),
        ("profesional_id",    "INTEGER"),
    ]

    insp = sa_inspect(engine)
    tables = set(insp.get_table_names())

    def _cols(table):
        """Columnas existentes de una tabla (vacío si la tabla no existe)."""
        return {c["name"] for c in insp.get_columns(table)} if table in tables else set()

    with engine.connect() as conn:
        # 1. Columnas nuevas en clients
        existing_cols = _cols("clients")
        for col, col_type in new_client_cols:
            if existing_cols and col not in existing_cols:
                conn.execute(text(f"ALTER TABLE clients ADD COLUMN {col} {col_type}"))

        # 2. Columnas nuevas en users (sistema de roles v2)
        existing_user_cols = _cols("users")
        for col, col_type in new_user_cols:
            if existing_user_cols and col not in existing_user_cols:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))

        # 2b. Columnas nuevas en movimientos_cc (R-03/R-04 — vínculo con honorarios y pagos)
        existing_mov_cols = _cols("movimientos_cc")
        if existing_mov_cols:
            for col, col_type in new_movimiento_cols:
                if col not in existing_mov_cols:
                    conn.execute(text(f"ALTER TABLE movimientos_cc ADD COLUMN {col} {col_type}"))

        # 3. Si honorarios existe con schema viejo (columna 'amount' en lugar de 'importe'), la borramos
        #    para que create_all la recree correctamente.
        hon_cols = _cols("honorarios")
        if hon_cols and "importe" not in hon_cols:
            conn.execute(text("DROP TABLE honorarios"))

        conn.commit()


def _add_missing_columns():
    """Agrega columnas que existen en el modelo pero faltan en la base. InsForge
    importó algunas tablas sin todas las columnas (p. ej. `limpiezas_iva` quedó sin
    `archivo_corregido`/BYTEA), y `create_all` NO altera tablas existentes → cualquier
    SELECT de esa tabla falla con `UndefinedColumn` → 500.

    Cross-dialect: compila el tipo de cada columna según el dialecto activo
    (LargeBinary→BYTEA en Postgres, etc.). Las columnas se agregan SIN NOT NULL ni
    default para no fallar si la tabla ya tiene filas; la app igual valida el not-null
    al insertar. Cada ALTER va en su propia transacción + try/except. Idempotente."""
    from sqlalchemy import inspect as sa_inspect

    insp = sa_inspect(engine)
    db_tables = set(insp.get_table_names())
    dialect = engine.dialect

    for table_name, table in models.Base.metadata.tables.items():
        if table_name not in db_tables:
            continue  # create_all ya crea las tablas nuevas completas
        existing = {c["name"] for c in insp.get_columns(table_name)}
        for col in table.columns:
            if col.name in existing:
                continue
            try:
                col_type = col.type.compile(dialect=dialect)
                with engine.begin() as conn:
                    conn.execute(
                        text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col_type}')
                    )
                print(f"[migrate] columna agregada: {table_name}.{col.name} {col_type}")
            except Exception as e:  # noqa: BLE001 — no debe romper el arranque
                print(f"[migrate] WARN no se pudo agregar {table_name}.{col.name}: {e}")


def _repair_numeric_columns():
    """Auto-reparación de tipos: InsForge (y otros BaaS que importan datos) crean
    columnas numéricas como TEXT. El ORM las mapea como Float y al leerlas psycopg
    falla con `InvalidRequestError: Unknown PG numeric type: 25` (25 = OID de text),
    devolviendo 500 en TODO endpoint que lea esas tablas (clients, iva, facturas,
    honorarios, etc.).

    Solo aplica en Postgres: recorre las columnas Float del modelo, y si en la base
    están como texto las convierte a `double precision` con un cast seguro
    (`NULLIF(btrim(...), '')`). Cada ALTER corre en su propia transacción y bajo
    try/except, de modo que una columna con datos no convertibles no aborte el resto
    ni rompa el arranque. Es idempotente: si ya es numérica, no hace nada."""
    from sqlalchemy import inspect as sa_inspect, types as sqltypes

    if engine.dialect.name == "sqlite":
        return

    insp = sa_inspect(engine)
    db_tables = set(insp.get_table_names())

    for table_name, table in models.Base.metadata.tables.items():
        if table_name not in db_tables:
            continue
        live_types = {c["name"]: c["type"] for c in insp.get_columns(table_name)}
        for col in table.columns:
            # Float es subclase de Numeric en SQLAlchemy
            if not isinstance(col.type, sqltypes.Numeric):
                continue
            live = live_types.get(col.name)
            # Solo reparar si en la base la columna está como texto
            if live is None or not isinstance(live, sqltypes.String):
                continue
            stmt = text(
                f'ALTER TABLE "{table_name}" '
                f'ALTER COLUMN "{col.name}" TYPE double precision '
                f'USING NULLIF(btrim("{col.name}"::text), \'\')::double precision'
            )
            try:
                with engine.begin() as conn:
                    conn.execute(stmt)
                print(f"[migrate] {table_name}.{col.name}: TEXT → double precision")
            except Exception as e:  # noqa: BLE001 — no debe romper el arranque
                print(f"[migrate] WARN no se pudo convertir {table_name}.{col.name}: {e}")


def _repair_boolean_columns():
    """Convierte a boolean las columnas Boolean del modelo que InsForge guardó como
    INTEGER o TEXT. Síntoma: queries como `liquidaciones.cerrada == True` generan
    `cerrada = true` y Postgres falla con
    `operator does not exist: integer = boolean` → 500.

    Solo Postgres. Por cada columna Boolean del modelo cuya columna real no sea
    boolean, hace DROP DEFAULT (evita conflicto de cast del default) y luego
    ALTER ... TYPE boolean USING (...). Integer→(col<>0); Text→(lower(col) in
    'true','t','1','yes','y'). Cada tabla en su transacción + try/except. Idempotente."""
    from sqlalchemy import inspect as sa_inspect, types as sqltypes

    if engine.dialect.name == "sqlite":
        return

    insp = sa_inspect(engine)
    db_tables = set(insp.get_table_names())

    for table_name, table in models.Base.metadata.tables.items():
        if table_name not in db_tables:
            continue
        live_types = {c["name"]: c["type"] for c in insp.get_columns(table_name)}
        for col in table.columns:
            if not isinstance(col.type, sqltypes.Boolean):
                continue
            live = live_types.get(col.name)
            if live is None or isinstance(live, sqltypes.Boolean):
                continue  # ya es boolean o no existe
            if isinstance(live, sqltypes.Integer):
                using = f'("{col.name}" <> 0)'
            else:  # texto u otro
                using = (
                    f"(lower(nullif(btrim(\"{col.name}\"::text), '')) "
                    f"IN ('true', 't', '1', 'yes', 'y'))"
                )
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" DROP DEFAULT'
                    ))
                    conn.execute(text(
                        f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" '
                        f'TYPE boolean USING {using}'
                    ))
                print(f"[migrate] {table_name}.{col.name}: → boolean")
            except Exception as e:  # noqa: BLE001 — no debe romper el arranque
                print(f"[migrate] WARN no se pudo convertir {table_name}.{col.name} a boolean: {e}")


def _repair_datetime_columns():
    """Convierte a timestamp/date las columnas DateTime/Date del modelo que InsForge
    guardó como TEXT. Cuando se importa desde el dump SQLite, las fechas quedan como
    texto ISO; el ORM las mapea como DateTime/Date y al leerlas el dialecto psycopg
    falla → 500 en TODO endpoint que lea esas tablas (p. ej. honorarios /
    productos_referencia, cuyas columnas `actualizado_en`, `created_at`, `vigente_desde`
    quedaron como texto). Complementa a `_repair_numeric_columns` y
    `_repair_boolean_columns`.

    Solo Postgres. Por cada columna DateTime/Date del modelo cuya columna real sea
    texto, hace ALTER ... TYPE timestamptz/timestamp/date con un cast seguro
    (`NULLIF(btrim(...), '')`). DROP DEFAULT previo para evitar conflictos de cast.
    Cada tabla en su transacción + try/except. Idempotente: si ya es del tipo correcto,
    no hace nada."""
    from sqlalchemy import inspect as sa_inspect, types as sqltypes

    if engine.dialect.name == "sqlite":
        return

    insp = sa_inspect(engine)
    db_tables = set(insp.get_table_names())

    for table_name, table in models.Base.metadata.tables.items():
        if table_name not in db_tables:
            continue
        live_types = {c["name"]: c["type"] for c in insp.get_columns(table_name)}
        for col in table.columns:
            is_dt = isinstance(col.type, sqltypes.DateTime)
            is_date = isinstance(col.type, sqltypes.Date) and not is_dt
            if not (is_dt or is_date):
                continue
            live = live_types.get(col.name)
            # Solo reparar si en la base la columna está como texto
            if live is None or not isinstance(live, sqltypes.String):
                continue
            if is_dt:
                target = "timestamptz" if getattr(col.type, "timezone", False) else "timestamp"
            else:
                target = "date"
            using = f'NULLIF(btrim("{col.name}"::text), \'\')::{target}'
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" DROP DEFAULT'
                    ))
                    conn.execute(text(
                        f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" '
                        f'TYPE {target} USING {using}'
                    ))
                print(f"[migrate] {table_name}.{col.name}: TEXT → {target}")
            except Exception as e:  # noqa: BLE001 — no debe romper el arranque
                print(f"[migrate] WARN no se pudo convertir {table_name}.{col.name} a {target}: {e}")


def _backfill_datetime_defaults():
    """Rellena las columnas DateTime con server_default que quedaron en NULL y les
    fija el DEFAULT now() en Postgres.

    Causa: `_add_missing_columns` agrega columnas faltantes SIN default, así que las
    columnas tipo `created_at`/`actualizado_en` (que en el modelo tienen
    server_default=now()) quedan sin default en la base y los INSERT las dejan en NULL.
    Como muchos schemas de salida declaran `created_at: datetime` (requerido), al
    serializar una fila con NULL Pydantic lanza ValidationError → 500 en TODO endpoint
    que lea esa tabla (p. ej. GET/POST productos_referencia, cálculo de honorarios).

    Solo Postgres. Por cada columna DateTime del modelo con server_default: fija
    `DEFAULT now()` y backfillea las filas en NULL con now(). Cada tabla en su
    transacción + try/except. Idempotente."""
    from sqlalchemy import inspect as sa_inspect, types as sqltypes

    if engine.dialect.name == "sqlite":
        return

    insp = sa_inspect(engine)
    db_tables = set(insp.get_table_names())

    for table_name, table in models.Base.metadata.tables.items():
        if table_name not in db_tables:
            continue
        live_cols = {c["name"] for c in insp.get_columns(table_name)}
        for col in table.columns:
            if not isinstance(col.type, sqltypes.DateTime):
                continue
            if col.server_default is None or col.name not in live_cols:
                continue
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" SET DEFAULT now()'
                    ))
                    res = conn.execute(text(
                        f'UPDATE "{table_name}" SET "{col.name}" = now() '
                        f'WHERE "{col.name}" IS NULL'
                    ))
                n = res.rowcount if res.rowcount is not None else 0
                print(f"[migrate] {table_name}.{col.name}: default now() + backfill {n} NULL")
            except Exception as e:  # noqa: BLE001 — no debe romper el arranque
                print(f"[migrate] WARN no se pudo backfillear {table_name}.{col.name}: {e}")


def _resync_sequences():
    """Resincroniza las secuencias de `id` en Postgres. Cuando se importan datos con
    `id` explícito (como hace InsForge desde el dump SQLite), la secuencia SERIAL/IDENTITY
    NO se avanza, así que el próximo INSERT genera un id que ya existe →
    `UniqueViolation: duplicate key ... _pkey`. Esto rompe TODO INSERT en tablas
    importadas (crear cliente, tarea, factura, asignar colaborador, etc.).

    Solo aplica en Postgres: por cada tabla con PK simple `id` con secuencia asociada,
    hace `setval(seq, max(id)+1, false)`. Idempotente y seguro de correr en cada arranque.
    No-op en SQLite local. Cada tabla va en su propia transacción + try/except."""
    from sqlalchemy import inspect as sa_inspect

    if engine.dialect.name == "sqlite":
        return

    insp = sa_inspect(engine)
    db_tables = set(insp.get_table_names())

    for table_name, table in models.Base.metadata.tables.items():
        if table_name not in db_tables:
            continue
        pk_cols = [c.name for c in table.primary_key.columns]
        if pk_cols != ["id"]:
            continue
        try:
            with engine.begin() as conn:
                seq = conn.execute(
                    text("SELECT pg_get_serial_sequence(:t, 'id')"),
                    {"t": table_name},
                ).scalar()
                if not seq:
                    continue  # id sin secuencia (no autoincrement) → nada que resync
                conn.execute(
                    text(
                        f"SELECT setval('{seq}', "
                        f'COALESCE((SELECT MAX(id) FROM "{table_name}"), 0) + 1, false)'
                    )
                )
            print(f"[migrate] secuencia resync: {table_name}")
        except Exception as e:  # noqa: BLE001 — no debe romper el arranque
            print(f"[migrate] WARN no se pudo resync secuencia de {table_name}: {e}")


# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Larrañaga — Plataforma Contable y Legal",
    description="Sistema de gestión para estudio contable y legal. Facturación, IVA, DDJJ y más.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(collaborators.router)
app.include_router(tasks.router)
app.include_router(iva.router)
app.include_router(facturas.router)
app.include_router(dashboard.router)
app.include_router(retenciones.router)
app.include_router(comprobantes.router)
app.include_router(herramientas.router)
app.include_router(cuentas_corrientes.router)
app.include_router(honorarios.router)
app.include_router(profesionales_adm.router)
app.include_router(bulk.router)
app.include_router(billetes.router)
app.include_router(pagos.router)
app.include_router(imputacion.router)
app.include_router(retiros.router)
app.include_router(flujo_fondos.router)
app.include_router(insforge.router)
app.include_router(feature_flags.router)
app.include_router(empleados.router)
app.include_router(liquidacion_personal.router)

# Fase 3 — R-15 conciliación bancaria
from .routers import conciliacion  # noqa: E402
app.include_router(conciliacion.router)


def _seed_billetes():
    """Inicializa stock de billetes en 0 para las 5 denominaciones (idempotente)."""
    from .database import SessionLocal
    from .services.billetes import DENOMINACIONES
    db = SessionLocal()
    try:
        for denom in DENOMINACIONES:
            if not db.query(models.ControlBillete).filter_by(denominacion=denom).first():
                db.add(models.ControlBillete(denominacion=denom, cantidad=0))
        db.commit()
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    _migrate_sqlite()
    _add_missing_columns()
    _repair_numeric_columns()
    _repair_boolean_columns()
    _repair_datetime_columns()
    _backfill_datetime_defaults()
    _resync_sequences()
    register_sync_events(engine)
    seed_database()
    seed_profesionales_y_productos()
    _seed_billetes()
    seed_feature_flags()
    seed_empleados()
    # Auto-sync periódico a InsForge (controlado por env var
    # INSFORGE_AUTOSYNC_INTERVAL_SECONDS, 0 o sin definir = deshabilitado)
    start_periodic_sync()


@app.get("/")
def root():
    return {
        "app": "Larrañaga — Plataforma Contable y Legal",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
