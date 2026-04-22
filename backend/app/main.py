from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import auth, clients, collaborators, tasks, iva, facturas, dashboard, herramientas
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
app.include_router(clients.router)
app.include_router(collaborators.router)
app.include_router(tasks.router)
app.include_router(iva.router)
app.include_router(facturas.router)
app.include_router(dashboard.router)
app.include_router(herramientas.router)


@app.on_event("startup")
async def startup_event():
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
