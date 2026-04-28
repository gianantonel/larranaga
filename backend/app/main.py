from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .sync import register_sync_events, sync_now

from .routers import auth, clients, collaborators, tasks, iva, facturas, dashboard, retenciones, comprobantes, herramientas, users, cuentas_corrientes, bulk, profesionales, honorarios
from .mock_data import seed_database

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
app.include_router(profesionales.router)
app.include_router(honorarios.router)


@app.on_event("startup")
async def startup_event():
    # Registrar event listeners para sincronización automática con InsForge
    register_sync_events(engine)
    seed_database()


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


@app.post("/admin/sync-insforge")
def manual_sync_insforge():
    """Dispara una sincronización manual a InsForge (endpoint admin)."""
    success = sync_now()
    return {
        "status": "success" if success else "failed",
        "message": "Sincronización completada" if success else "Error durante sincronización (ver logs)"
    }
