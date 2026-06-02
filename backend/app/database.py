from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./larranaga.db")

_is_sqlite = "sqlite" in DATABASE_URL

# Postgres en cloud (InsForge / Supabase / RDS) cierra conexiones idle por SSL
# timeout. pool_recycle fuerza re-conexión cada 5 min ANTES de que el server las
# mate; keepalives mantiene el socket vivo cuando hay tráfico bajo; pool_pre_ping
# valida la conexión antes de cada checkout (descarta zombies).
if _is_sqlite:
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "pool_pre_ping": True,
    }
else:
    _engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10,
        "connect_args": {
            "sslmode": "require",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "connect_timeout": 10,
        },
    }

engine = create_engine(DATABASE_URL, **_engine_kwargs)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _rec):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")       # concurrent reads/writes
        cur.execute("PRAGMA synchronous=NORMAL")     # safe + faster than FULL
        cur.execute("PRAGMA cache_size=-65536")      # 64 MB page cache
        cur.execute("PRAGMA temp_store=MEMORY")      # temp tables in RAM
        cur.execute("PRAGMA mmap_size=268435456")    # 256 MB memory-mapped I/O
        cur.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
