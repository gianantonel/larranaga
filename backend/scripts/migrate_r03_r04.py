"""
Migración idempotente para R-03 + R-04:
  - Crea tablas: productos_referencia, profesionales, honorarios, liquidaciones, reintegros_gasto
  - Agrega columnas a clients: tipo_honorario, importe_honorario, cantidad_unidades, producto_ref_id, profesional_id
  - Agrega columnas a movimientos_cc: periodo_honorario, forma_pago, profesional_id
  - Inserta profesionales del estudio Larrañaga (seed inicial)

Uso: python -m app.scripts.migrate_r03_r04
  o:  python backend/scripts/migrate_r03_r04.py (desde raíz del proyecto)
"""
import sqlite3
import os
from pathlib import Path
from datetime import date

# Ruta a la BD — está en backend/larranaga.db
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DB_PATH = BASE_DIR / "larranaga.db"

PROFESIONALES_SEED = [
    ("Rodrigo", "Larrañaga", "rodrigo@larranaga.com", "socio"),
    ("Silvana", "Larrañaga", "silvana@larranaga.com", "socio"),
    ("Stefi", "Vicente", "stefi@larranaga.com", "profesional"),
    ("Marisol", "Borrego", "marisol.larranagayasociados@gmail.com", "socio"),
    ("Mariana", "", "mariana@larranaga.com", "profesional"),
]


def run():
    if not DB_PATH.exists():
        print(f"[ERROR] Base de datos no encontrada: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # ─── 1. Tabla productos_referencia ────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS productos_referencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            unidad VARCHAR(30) DEFAULT 'unidad',
            precio_vigente REAL NOT NULL,
            fecha_actualizacion DATE NOT NULL,
            activo BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Tabla productos_referencia")

    # ─── 2. Tabla profesionales ───────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profesionales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100),
            email VARCHAR(100),
            tipo VARCHAR(20) DEFAULT 'profesional',
            activo BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Tabla profesionales")

    # ─── 3. Tabla honorarios ──────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS honorarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            periodo VARCHAR(7) NOT NULL,
            importe REAL NOT NULL,
            estado VARCHAR(20) DEFAULT 'pendiente',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(client_id, periodo)
        )
    """)
    print("[OK] Tabla honorarios")

    # ─── 4. Tabla liquidaciones ───────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS liquidaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profesional_id INTEGER NOT NULL REFERENCES profesionales(id),
            periodo VARCHAR(7) NOT NULL,
            honorarios_totales REAL DEFAULT 0,
            adelantos_percibidos REAL DEFAULT 0,
            saldo_anterior REAL DEFAULT 0,
            reintegro_gastos REAL DEFAULT 0,
            total_a_cobrar REAL DEFAULT 0,
            forma_cobro VARCHAR(50),
            monto_cobrado REAL DEFAULT 0,
            saldo_siguiente REAL DEFAULT 0,
            cerrada BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(profesional_id, periodo)
        )
    """)
    print("[OK] Tabla liquidaciones")

    # ─── 5. Tabla reintegros_gasto ────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reintegros_gasto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liquidacion_id INTEGER NOT NULL REFERENCES liquidaciones(id) ON DELETE CASCADE,
            concepto VARCHAR(100) NOT NULL,
            importe REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Tabla reintegros_gasto")

    # ─── 6. Columnas nuevas en clients ────────────────────────────────────────
    clients_cols = {col[1] for col in cur.execute("PRAGMA table_info(clients)").fetchall()}
    new_client_cols = [
        ("tipo_honorario", "VARCHAR(10) DEFAULT 'fijo'"),
        ("importe_honorario", "REAL DEFAULT 0"),
        ("cantidad_unidades", "REAL DEFAULT 0"),
        ("producto_ref_id", "INTEGER REFERENCES productos_referencia(id)"),
        ("profesional_id", "INTEGER REFERENCES profesionales(id)"),
    ]
    for col_name, col_def in new_client_cols:
        if col_name not in clients_cols:
            cur.execute(f"ALTER TABLE clients ADD COLUMN {col_name} {col_def}")
            print(f"[OK] clients.{col_name} agregada")
        else:
            print(f"[SKIP] clients.{col_name} ya existe")

    # ─── 7. Columnas nuevas en movimientos_cc ─────────────────────────────────
    cc_cols = {col[1] for col in cur.execute("PRAGMA table_info(movimientos_cc)").fetchall()}
    new_cc_cols = [
        ("periodo_honorario", "VARCHAR(7)"),
        ("forma_pago", "VARCHAR(20)"),
        ("profesional_id", "INTEGER REFERENCES profesionales(id)"),
    ]
    for col_name, col_def in new_cc_cols:
        if col_name not in cc_cols:
            cur.execute(f"ALTER TABLE movimientos_cc ADD COLUMN {col_name} {col_def}")
            print(f"[OK] movimientos_cc.{col_name} agregada")
        else:
            print(f"[SKIP] movimientos_cc.{col_name} ya existe")

    # ─── 8. Seed de profesionales ─────────────────────────────────────────────
    for nombre, apellido, email, tipo in PROFESIONALES_SEED:
        existing = cur.execute(
            "SELECT id FROM profesionales WHERE nombre = ? AND apellido = ?", (nombre, apellido)
        ).fetchone()
        if not existing:
            cur.execute(
                "INSERT INTO profesionales (nombre, apellido, email, tipo) VALUES (?, ?, ?, ?)",
                (nombre, apellido, email, tipo),
            )
            print(f"[OK] Profesional insertado: {nombre} {apellido}")
        else:
            print(f"[SKIP] Profesional ya existe: {nombre} {apellido}")

    conn.commit()
    conn.close()
    print("\n[DONE] Migracion R-03/R-04 completada exitosamente.")


if __name__ == "__main__":
    run()
