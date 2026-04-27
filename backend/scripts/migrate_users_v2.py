"""
Migración v2 — Modelo de usuarios con roles Super-Admin / Admin / Colaborador / Invitado.

Qué hace:
  1. Agrega columnas last_name, cuit, status a la tabla users (si no existen)
  2. Mapea valores antiguos de role:
       admin1/2/3   → admin
       collaborator → colaborador
  3. Garantiza que los 4 emails de super-admins estén creados con rol super_admin
  4. Marca todos los usuarios existentes con status=active

Uso:
  python -m scripts.migrate_users_v2
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text
from app.database import SessionLocal, engine
from app.models import User, UserRole, UserStatus
from app.security import get_password_hash


SUPER_ADMINS = [
    {"email": "optimizar.ai@gmail.com",      "name": "Optimizar", "last_name": "AI",       "initials": "OP"},
    {"email": "gianantonel@gmail.com",       "name": "Gian",      "last_name": "Antonel",  "initials": "GA"},
    {"email": "rodriguezfederico765@gmail.com", "name": "Federico","last_name": "Rodriguez","initials": "FR"},
    {"email": "gerogambuli2002@gmail.com",   "name": "Gero",      "last_name": "Gambuli",  "initials": "GG"},
]

DEFAULT_PASSWORD = "admin123"


def column_exists(conn, table, col) -> bool:
    insp = inspect(conn)
    return col in [c["name"] for c in insp.get_columns(table)]


def add_column_if_missing(conn, table, col, ddl):
    if not column_exists(conn, table, col):
        print(f"  + agregando columna {table}.{col}")
        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    else:
        print(f"  = columna {table}.{col} ya existe")


def main():
    print("=== Migración usuarios v2 ===")

    # 1) ALTER TABLE — agregar columnas nuevas (SQLite no soporta IF NOT EXISTS aquí)
    with engine.begin() as conn:
        add_column_if_missing(conn, "users", "last_name", "VARCHAR(100)")
        add_column_if_missing(conn, "users", "cuit",      "VARCHAR(13)")
        add_column_if_missing(conn, "users", "status",    "VARCHAR(20)")

    # 2) Remapeo de roles antiguos + status default
    db = SessionLocal()
    try:
        # Remap directo por SQL para evitar problemas de Enum cuando los valores viejos no existen en el enum nuevo
        db.execute(text("UPDATE users SET role='admin'       WHERE role IN ('admin1','admin2','admin3')"))
        db.execute(text("UPDATE users SET role='colaborador' WHERE role='collaborator'"))
        db.execute(text("UPDATE users SET status='active'    WHERE status IS NULL OR status=''"))
        db.commit()

        total = db.query(User).count()
        print(f"  · usuarios totales: {total}")

        # 3) Garantizar super-admins
        for sa in SUPER_ADMINS:
            user = db.query(User).filter(User.email == sa["email"]).first()
            if user:
                user.role = UserRole.super_admin
                user.status = UserStatus.active
                user.is_active = True
                if not user.last_name:
                    user.last_name = sa["last_name"]
                print(f"  · super-admin existente: {sa['email']}")
            else:
                user = User(
                    name=sa["name"],
                    last_name=sa["last_name"],
                    email=sa["email"],
                    password_hash=get_password_hash(DEFAULT_PASSWORD),
                    role=UserRole.super_admin,
                    status=UserStatus.active,
                    is_active=True,
                    avatar_initials=sa["initials"],
                )
                db.add(user)
                print(f"  + super-admin creado: {sa['email']} (password por defecto: {DEFAULT_PASSWORD})")
        db.commit()

        # Resumen
        print("\n=== Resumen final ===")
        for r in [UserRole.super_admin, UserRole.admin, UserRole.colaborador, UserRole.invitado]:
            n = db.query(User).filter(User.role == r).count()
            print(f"  {r.value:>14}: {n}")
        pendientes = db.query(User).filter(User.status == UserStatus.pending).count()
        print(f"  {'pendientes':>14}: {pendientes}")
    finally:
        db.close()

    print("\n[OK] Migración completa.")


if __name__ == "__main__":
    main()
