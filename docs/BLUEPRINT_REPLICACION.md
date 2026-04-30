# Larrañaga Platform — Architectural Blueprint for Client Replication

**Document Version:** 1.0  
**Date:** 2026-04-27  
**Purpose:** Complete structural guide for replicating the Larrañaga accounting platform for new clients

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Directory Structure](#directory-structure)
4. [Database Architecture](#database-architecture)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [Authentication & Authorization](#authentication--authorization)
8. [Common CRUD Patterns](#common-crud-patterns)
9. [External Integrations](#external-integrations)
10. [Data Processing Pipelines](#data-processing-pipelines)
11. [Development Workflow](#development-workflow)
12. [Deployment Guide](#deployment-guide)
13. [Step-by-Step Replication Guide](#step-by-step-replication-guide)

---

## Project Overview

### Purpose

Larrañaga is an **Argentine accounting platform** designed to streamline tax compliance, invoice management, and financial reporting for accounting firms and their clients. It integrates with:

- **AFIP** (Administración Federal de Ingresos Públicos) — Argentine tax authority
- **ARCA** (Sistema de Administración de Retenciones y Percepciones) — Withholding/perception records
- **Holistor** — Tax return filing system
- **InsForge Cloud** — Cloud database synchronization

### Key Features

- **User Management**: Multi-role system (Super-Admin, Admin, Colaborador, Invitado)
- **Client Management**: Store and manage client fiscal data
- **Task Management**: Track accounting work (invoicing, tax declarations, etc.)
- **Invoice Management**: Record and validate invoices with tax calculations
- **IVA & Tax Records**: Manage VAT, withholdings, perceptions, and gross income tax
- **Data Processing**: Excel import/processing pipelines (R-01 cleaning, R-02 splitting)
- **Audit Trail**: Log all actions for compliance

---

## Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.104+ |
| ORM | SQLAlchemy | 2.0+ |
| Database (Dev) | SQLite | 3.x |
| Database (Prod) | PostgreSQL | 14+ |
| Authentication | JWT + bcrypt | — |
| Validation | Pydantic | 2.0+ |
| HTTP Client | httpx | 0.25+ |
| Task Queue | Celery (optional) | 5.3+ |
| Logging | Python logging | built-in |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 18.x+ |
| Routing | React Router | 6.x+ |
| State Management | Context API | native |
| HTTP Client | Axios | 1.x+ |
| Styling | Tailwind CSS | 3.x+ |
| UI Icons | lucide-react | 0.x+ |
| Build Tool | Vite | 5.x+ |

### Development & DevOps

| Tool | Purpose |
|------|---------|
| Git | Version control |
| Python venv | Python environment isolation |
| pip | Python package management |
| npm | Node package management |
| Docker | Containerization (optional) |

---

## Directory Structure

### Backend (`backend/`)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── database.py             # SQLAlchemy engine, SessionLocal
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic validation schemas
│   ├── security.py             # JWT, password hashing, encryption
│   ├── routers/
│   │   ├── auth.py             # Authentication endpoints + helpers
│   │   ├── users.py            # User CRUD + role management
│   │   ├── clients.py          # Client CRUD
│   │   ├── tasks.py            # Task CRUD
│   │   ├── iva.py              # IVA record management
│   │   ├── facturas.py         # Invoice management
│   │   ├── retenciones.py      # Withholding/perception records
│   │   ├── comprobantes.py     # Received vouchers
│   │   ├── herramientas.py     # Data processing tools (R-01, R-02)
│   │   ├── cuentas_corrientes.py # Account balances
│   │   └── dashboard.py        # Dashboard metrics
│   ├── utils/
│   │   ├── resend.py           # Email notifications
│   │   └── afip_integration.py # AFIP API calls
│   ├── sync/
│   │   ├── insforge_sync.py    # Cloud database sync
│   │   └── events.py           # SQLAlchemy event listeners
│   └── logs/                   # Application logs
├── scripts/
│   ├── migrate_users_v2.py     # User migration script
│   └── seed_data.py            # Database seeding
├── requirements.txt
└── .env                        # Environment variables (git-ignored)
```

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── App.jsx                 # Route definitions
│   ├── main.jsx                # React entry point
│   ├── index.css               # Global styles
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Usuarios.jsx        # User management
│   │   ├── Clientes.jsx        # Client management
│   │   ├── Tareas.jsx          # Task management
│   │   ├── Facturas.jsx        # Invoice management
│   │   ├── IVA.jsx             # IVA management
│   │   ├── Retenciones.jsx     # Withholding records
│   │   ├── Comprobantes.jsx    # Received vouchers
│   │   ├── Herramientas.jsx    # Data processing tools
│   │   └── CuentasCorrientes.jsx
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Layout.jsx      # Main wrapper
│   │   │   ├── Header.jsx      # Top navbar
│   │   │   ├── Sidebar.jsx     # Left navigation
│   │   │   └── ProtectedRoute.jsx
│   │   ├── UI/
│   │   │   ├── PageHeader.jsx
│   │   │   ├── Modal.jsx
│   │   │   └── Table.jsx
│   │   └── Forms/
│   │       └── (form components)
│   ├── context/
│   │   └── AuthContext.jsx     # Global auth state
│   ├── utils/
│   │   └── api.js              # Axios instance
│   └── assets/
│       └── (images, icons)
├── package.json
└── vite.config.js
```

### Data Processing (`larranaga-accounting-agent/`)

```
larranaga-accounting-agent/
├── src/
│   └── transformaciones/
│       ├── limpieza_inicial.py     # R-01: ARCA cleaning
│       └── division_alicuotas.py   # R-02: Multi-rate splitting
└── tests/
    ├── test_limpieza_inicial.py
    └── test_division_alicuotas.py
```

---

## Database Architecture

### Core Models & Relationships

#### 1. **User Model** (Authentication & Authorization)

```python
class UserRole(str, Enum):
    super_admin = "super_admin"    # Full system access
    admin = "admin"                # Administrative access
    colaborador = "colaborador"    # Standard user
    invitado = "invitado"          # Limited guest access

class UserStatus(str, Enum):
    active = "active"              # User approved and active
    pending = "pending"            # Waiting for approval
    rejected = "rejected"          # Application rejected

class User(Base):
    __tablename__ = "users"
    
    id: int                         # PK
    name: str                       # First name
    last_name: str                  # Last name
    cuit: str                       # Argentine ID number
    email: str (unique)             # Login credential
    password_hash: str              # bcrypt hash
    role: UserRole                  # Hierarchical role
    status: UserStatus              # Approval status
    is_active: bool                 # Soft-delete flag
    avatar_initials: str            # Display initials
    created_at: DateTime            # Registration timestamp
    
    # Relationships
    tasks: Task[]                   # Work assigned to user
    client_assignments: ClientCollaborator[]
    action_logs: ActionLog[]
```

**Key Design Decision:** Soft-delete pattern (`is_active=False`) allows audit trail preservation without losing data.

#### 2. **Client Model** (Customer Management)

```python
class Client(Base):
    __tablename__ = "clients"
    
    id: int
    name: str                       # Display name
    business_name: str              # Official legal name
    cuit: str (unique)              # Tax ID
    clave_fiscal_encrypted: str     # AFIP credentials (encrypted)
    address: str
    phone: str
    email: str
    category: str                   # Business category
    fiscal_condition: str           # IVA condition (Responsable, No Responsable, etc)
    activity_code: str              # AFIP activity code
    is_active: bool
    notes: str
    created_at: DateTime
    
    # Relationships
    tasks: Task[]
    collaborators: ClientCollaborator[]   # Team assigned to this client
    iva_records: IVARecord[]
    invoices: Invoice[]
    ingresos_brutos: IngresosBrutos[]    # Gross income tax
    retenciones_percepciones: RetencionPercepcion[]
    comprobantes_recibidos: ComprobanteRecibido[]
    limpiezas_iva: LimpiezaIVA[]         # Audit trail of IVA cleaning
    movimientos_cc: MovimientoCuentaCorriente[]
```

**Key Design Decision:** `clave_fiscal_encrypted` stores AFIP credentials; encryption/decryption handled by security module.

#### 3. **Task Model** (Work Tracking)

```python
class TaskType(str, Enum):
    facturacion = "facturacion"
    comprobantes = "comprobantes"
    ddjj_iva = "ddjj_iva"
    ddjj_ganancias = "ddjj_ganancias"
    ddjj_bienes_personales = "ddjj_bienes_personales"
    ingresos_brutos = "ingresos_brutos"
    legal = "legal"
    otros = "otros"

class TaskStatus(str, Enum):
    pendiente = "pendiente"
    en_curso = "en_curso"
    terminada = "terminada"
    bloqueada = "bloqueada"
    postergada = "postergada"

class Task(Base):
    __tablename__ = "tasks"
    
    id: int
    title: str
    description: str
    task_type: TaskType             # Categorization
    status: TaskStatus              # State machine
    client_id: int (FK)             # Client this task serves
    collaborator_id: int (FK)       # Assigned user
    period: str                     # YYYY-MM format
    due_date: Date
    completed_at: DateTime
    blocker_comment: str            # Reason if blocked
    created_at: DateTime
    updated_at: DateTime
    
    # Relationships
    client: Client
    collaborator: User
    subtasks: Subtask[]
    action_logs: ActionLog[]
```

#### 4. **Invoice Model** (Tax Reporting)

```python
class InvoiceType(str, Enum):
    A = "A"     # Standard invoice (GST eligible)
    B = "B"     # Simplified invoice
    C = "C"     # Non-taxable invoice
    M = "M"     # Import invoice
    E = "E"     # Export invoice

class Invoice(Base):
    __tablename__ = "invoices"
    
    id: int
    client_id: int (FK)
    collaborator_id: int (FK)
    invoice_type: InvoiceType
    punto_venta: int                # Sales point
    number: int                     # Sequential number
    date: Date
    receptor_cuit: str              # Buyer CUIT
    receptor_name: str              # Buyer name
    concept: str
    neto_gravado: float             # Taxable amount
    neto_no_gravado: float          # Non-taxable amount
    exento: float                   # Exempt amount
    iva_21: float                   # 21% VAT
    iva_105: float                  # 10.5% VAT
    total: float
    cae: str                        # AFIP authorization code
    cae_vto: Date                   # CAE expiration
    status: str
    created_at: DateTime
    
    # Relationships
    client: Client
```

#### 5. **IVA Record Model** (Tax Declaration)

```python
class IVARecord(Base):
    __tablename__ = "iva_records"
    
    id: int
    client_id: int (FK)
    period: str                     # YYYY-MM
    
    # Sales (Ventas)
    ventas_gravadas: float
    ventas_exentas: float
    ventas_no_gravadas: float
    debito_fiscal: float            # Tax to pay
    
    # Purchases (Compras)
    compras_gravadas: float
    compras_exentas: float
    compras_no_gravadas: float
    credito_fiscal: float           # Tax credit
    
    # Balance
    saldo_a_favor_anterior: float   # Prior credit
    saldo: float                    # +ve = owe, -ve = credit
    
    # Filing
    filed: bool
    filed_at: DateTime
    due_date: Date
    vep_number: str                 # Payment reference
    created_at: DateTime
    
    # Relationships
    client: Client
```

#### 6. **ClientCollaborator (Many-to-Many)**

```python
class ClientCollaborator(Base):
    __tablename__ = "client_collaborators"
    
    id: int
    client_id: int (FK → clients.id)
    collaborator_id: int (FK → users.id)
    assigned_at: DateTime
    assigned_by_id: int (FK → users.id)
    
    # Relationships
    client: Client
    collaborator: User
```

**Purpose:** Maps which users work on which clients (many-to-many with audit trail).

#### 7. **LimpiezaIVA (Audit Trail for Data Processing)**

```python
class LimpiezaIVA(Base):
    __tablename__ = "limpiezas_iva"
    
    id: int
    client_id: int (FK)
    user_id: int (FK)               # Who processed it
    nombre_original: str            # Original filename
    nombre_corregido: str           # Output filename
    archivo_corregido: bytes        # Excel file as binary
    total_filas: int                # Input row count
    filas_bc_corregidas: int        # Corrected rows
    created_at: DateTime
    
    # Relationships
    client: Client
    user: User
```

**Purpose:** Maintains history of all data cleaning operations.

### Enum-Driven Type Safety

The architecture uses Python `Enum` classes to ensure type safety and prevent invalid state:

```python
from enum import Enum

class UserRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    # ... etc

# SQLAlchemy Column
role = Column(Enum(UserRole), nullable=False, default=UserRole.colaborador)

# Pydantic Schema
class UserRoleUpdate(BaseModel):
    role: UserRole  # Type-checked at validation
```

**Benefits:**
- Impossible to set invalid role (DB constraint + app validation)
- Frontend dropdown automatically reflects valid options
- API schema self-documents valid values

---

## Backend Architecture

### FastAPI Application Structure

#### Main Application (`app/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import event
from app.database import engine, Base
from app.routers import auth, users, clients, tasks, iva, facturas
from app.sync.events import setup_sync_listeners

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="Larrañaga API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(tasks.router)
app.include_router(iva.router)
app.include_router(facturas.router)

# Setup event listeners for sync
@app.on_event("startup")
def startup():
    setup_sync_listeners()

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}
```

### Router Pattern (User Management Example)

Each entity (User, Client, Task, etc.) follows a consistent pattern:

```python
# backend/app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from .auth import require_admin, require_super_admin

router = APIRouter(prefix="/users", tags=["users"])

# ─── Permission Helpers ──────────────────────────────────────────
def _can_assign(actor: models.User, target_role: models.UserRole) -> bool:
    """Validates if actor has permission to assign target_role."""
    if actor.role == models.UserRole.super_admin:
        return target_role in (
            models.UserRole.admin,
            models.UserRole.colaborador,
            models.UserRole.invitado,
        )
    if actor.role == models.UserRole.admin:
        return target_role in (
            models.UserRole.colaborador,
            models.UserRole.invitado,
        )
    return False

def _can_modify_target(actor: models.User, target: models.User) -> bool:
    """Validates if actor can edit target user."""
    # No one except super_admin can modify super_admin
    if target.role == models.UserRole.super_admin and actor.role != models.UserRole.super_admin:
        return False
    # Admin cannot modify other admins (only super_admin can)
    if target.role == models.UserRole.admin and actor.role == models.UserRole.admin and actor.id != target.id:
        return False
    return True

# ─── Endpoints ───────────────────────────────────────────────────

@router.get("/", response_model=List[schemas.UserOut])
def list_active_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """List all active users. Requires admin role."""
    return (
        db.query(models.User)
        .filter(models.User.status == models.UserStatus.active)
        .order_by(models.User.role, models.User.name)
        .all()
    )

@router.get("/pending", response_model=List[schemas.UserOut])
def list_pending_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """List users pending approval."""
    return (
        db.query(models.User)
        .filter(models.User.status == models.UserStatus.pending)
        .order_by(models.User.created_at.desc())
        .all()
    )

@router.post("/invite", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def invite_user(
    data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Create a new user in pending status (invitation workflow)."""
    # Check email uniqueness
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(400, "Usuario ya existe con ese email")
    
    # Check permission to assign target role
    if not _can_assign(current_user, data.role):
        raise HTTPException(403, f"No tenés permisos para asignar '{data.role.value}'")
    
    # Create user
    user = models.User(
        name=data.name,
        last_name=data.last_name,
        cuit=data.cuit,
        email=data.email,
        password_hash=get_password_hash(data.password),
        role=data.role,
        status=models.UserStatus.pending,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.patch("/{user_id}/role", response_model=schemas.UserOut)
def update_user_role(
    user_id: int,
    data: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Change a user's role (respects hierarchy)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    
    # Permission checks
    if not _can_modify_target(current_user, user):
        raise HTTPException(403, "No tenés permisos para modificar este usuario")
    
    if not _can_assign(current_user, data.role):
        raise HTTPException(403, f"No tenés permisos para asignar '{data.role.value}'")
    
    # Update
    user.role = data.role
    db.commit()
    db.refresh(user)
    return user

@router.patch("/{user_id}/approve", response_model=schemas.UserOut)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Approve a pending user (pending → active)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    
    if user.status != models.UserStatus.pending:
        raise HTTPException(400, "El usuario no está pendiente")
    
    if not _can_modify_target(current_user, user):
        raise HTTPException(403, "No tenés permisos para aprobar este usuario")
    
    # Approve
    user.status = models.UserStatus.active
    db.commit()
    db.refresh(user)
    
    # Send welcome email
    try:
        from app.utils.resend import send_welcome_email
        send_welcome_email(user.email, user.name, "/login")
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Soft-delete a user (is_active=False)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    
    if not _can_modify_target(current_user, user):
        raise HTTPException(403, "No tenés permisos para desactivar este usuario")
    
    if user.id == current_user.id:
        raise HTTPException(400, "No podés desactivarte a vos mismo")
    
    user.is_active = False
    db.commit()
```

**Key Patterns:**
1. **Permission Helpers** (`_can_assign`, `_can_modify_target`) validate hierarchy server-side
2. **Dependency Injection** (`Depends(require_admin)`) ensures authentication
3. **Status Codes** (201, 204, 400, 403, 404) follow HTTP standards
4. **Exception Handling** with clear detail messages

### Pydantic Schemas (Validation)

```python
# backend/app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from app.models import UserRole, UserStatus

class UserBase(BaseModel):
    """Shared fields for all User schemas."""
    name: str
    last_name: str | None = None
    cuit: str | None = None
    email: EmailStr

class UserCreate(UserBase):
    """Request body for creating users."""
    password: str = Field(min_length=6)
    role: UserRole

class UserUpdate(BaseModel):
    """Request body for updating users."""
    name: str | None = None
    last_name: str | None = None

class UserRoleUpdate(BaseModel):
    """Request body for role changes."""
    role: UserRole

class UserOut(UserBase):
    """Response body (never send password_hash)."""
    id: int
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allow ORM model → Pydantic conversion

class Token(BaseModel):
    """JWT response."""
    access_token: str
    token_type: str
    user: UserOut
```

**Key Concepts:**
- `BaseModel` inheritance reduces duplication
- `EmailStr` validates email format automatically
- `Field(min_length=6)` enforces password strength
- `from_attributes=True` converts SQLAlchemy models to Pydantic
- `UserOut` never includes `password_hash` (security)

---

## Frontend Architecture

### Context API for Global State

```javascript
// frontend/src/context/AuthContext.jsx

import { createContext, useContext, useState, useEffect } from 'react'
import api from '../utils/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load auth state on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    const token = localStorage.getItem('token')
    if (storedUser && token) {
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    const { access_token, user: userData } = res.data
    
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(userData))
    setUser(userData)
    
    return userData
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  // Computed properties based on role hierarchy
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin'
  const isSuperAdmin = user?.role === 'super_admin'
  
  // Roles this user can assign
  const assignableRoles = isSuperAdmin 
    ? ['admin', 'colaborador', 'invitado']
    : isAdmin 
    ? ['colaborador', 'invitado']
    : []

  const canAssignRole = (role) => assignableRoles.includes(role)

  const value = {
    user,
    loading,
    login,
    logout,
    isAdmin,
    isSuperAdmin,
    assignableRoles,
    canAssignRole,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
```

**Key Concepts:**
- `localStorage` persists token and user data across page reloads
- Computed properties (`isAdmin`, `assignableRoles`) prevent role logic duplication
- Custom hook `useAuth()` provides clean access throughout app

### Component Hierarchy

```
App.jsx
├── AuthProvider
│   └── BrowserRouter
│       └── Routes
│           ├── ProtectedRoute → Layout
│           │   ├── Header
│           │   │   └── UserDropdown (email, role, logout)
│           │   ├── Sidebar
│           │   │   └── NavLinks (role-based)
│           │   └── Outlet
│           │       └── Dashboard.jsx
│           │       └── Usuarios.jsx
│           │       └── Clientes.jsx
│           │       └── etc.
│           └── Route → Login.jsx
```

### Protected Routes

```javascript
// frontend/src/components/Layout/ProtectedRoute.jsx

import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function ProtectedRoute({ children, requiredRole = null }) {
  const { user, loading } = useAuth()

  if (loading) return <div>Cargando...</div>
  
  if (!user) return <Navigate to="/login" />
  
  if (requiredRole && !['admin', 'super_admin'].includes(user.role)) {
    return <Navigate to="/dashboard" />
  }

  return children
}

// Usage in App.jsx
<Routes>
  <Route 
    path="/usuarios" 
    element={
      <ProtectedRoute requiredRole="admin">
        <Layout><Usuarios /></Layout>
      </ProtectedRoute>
    } 
  />
  <Route path="/login" element={<Login />} />
</Routes>
```

### API Integration Pattern

```javascript
// frontend/src/utils/api.js

import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### Complex Component Example (Usuarios Page)

```javascript
// frontend/src/pages/Usuarios.jsx

import { useState, useEffect } from 'react'
import api from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { Check, Edit2, X, UserPlus, Loader2 } from 'lucide-react'

export default function Usuarios() {
  const [activos, setActivos] = useState([])
  const [pendientes, setPendientes] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)
  const [inviting, setInviting] = useState(false)
  const { user: currentUser, assignableRoles } = useAuth()

  // Load data on mount
  useEffect(() => { fetchUsers() }, [])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const [a, p] = await Promise.all([
        api.get('/users/'),
        api.get('/users/pending'),
      ])
      setActivos(a.data)
      setPendientes(p.data)
    } catch (e) {
      alert('Error al cargar usuarios')
    } finally {
      setLoading(false)
    }
  }

  const aprobar = async (id, role) => {
    try {
      await api.patch(`/users/${id}/role`, { role })
      await api.patch(`/users/${id}/approve`)
      fetchUsers()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al aprobar')
    }
  }

  const guardarRol = async (id, nuevoRol) => {
    try {
      await api.patch(`/users/${id}/role`, { role: nuevoRol })
      setEditing(null)
      fetchUsers()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al cambiar rol')
    }
  }

  const invitar = async (data) => {
    try {
      await api.post('/users/invite', data)
      setInviting(false)
      fetchUsers()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al invitar')
    }
  }

  const puedeEditar = (target) => {
    // Cannot edit super_admin unless you're super_admin
    if (target.role === 'super_admin' && currentUser.role !== 'super_admin') return false
    // Admin cannot edit other admins
    if (target.role === 'admin' && currentUser.role === 'admin' && target.id !== currentUser.id) return false
    return assignableRoles.length > 0
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-start justify-between">
        <h1>Gestión de Usuarios</h1>
        <button
          onClick={() => setInviting(true)}
          className="flex items-center gap-2 bg-violet-600 px-4 py-2 rounded-lg text-white"
        >
          <UserPlus size={16} /> Invitar usuario
        </button>
      </div>

      {/* Pending Users Table */}
      {pendientes.length > 0 && (
        <div className="card border border-amber-500/30">
          <h2 className="text-amber-400 font-semibold mb-3">
            Pendientes de aprobación ({pendientes.length})
          </h2>
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Email</th>
                <th>Rol</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {pendientes.map(u => (
                <tr key={u.id} className="border-b">
                  <td>{u.name}</td>
                  <td>{u.email}</td>
                  <td>
                    <select
                      defaultValue={u.role}
                      onChange={(e) => {
                        // Update role in form before approval
                      }}
                      className="bg-[#0f172a] border border-gray-600 rounded px-2 py-1"
                    >
                      {assignableRoles.map(r => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                  </td>
                  <td className="flex gap-2">
                    <button
                      onClick={() => aprobar(u.id, u.role)}
                      className="text-emerald-400 hover:text-emerald-300"
                    >
                      <Check size={20} />
                    </button>
                    <button
                      onClick={() => rechazar(u.id)}
                      className="text-rose-400 hover:text-rose-300"
                    >
                      <X size={20} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Active Users Table */}
      <div className="card">
        <h2 className="text-white font-semibold mb-3">
          Usuarios activos ({activos.length})
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left">Nombre</th>
              <th className="text-left">Email</th>
              <th className="text-left">Rol</th>
              <th className="text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {activos.map(u => (
              <tr key={u.id} className="border-b hover:bg-white/5">
                <td>{u.name} {u.last_name}</td>
                <td>{u.email}</td>
                <td>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    u.role === 'super_admin' ? 'bg-rose-500/20 text-rose-300'
                    : u.role === 'admin' ? 'bg-violet-500/20 text-violet-300'
                    : 'bg-emerald-500/20 text-emerald-300'
                  }`}>
                    {u.role}
                  </span>
                </td>
                <td className="text-right">
                  {puedeEditar(u) && (
                    <button
                      onClick={() => setEditing(u)}
                      className="text-gray-400 hover:text-violet-400"
                    >
                      <Edit2 size={16} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit Modal */}
      {editing && (
        <EditRoleModal
          user={editing}
          assignableRoles={assignableRoles}
          onClose={() => setEditing(null)}
          onSave={guardarRol}
        />
      )}

      {/* Invite Modal */}
      {inviting && (
        <InviteModal
          assignableRoles={assignableRoles}
          onClose={() => setInviting(false)}
          onSave={invitar}
        />
      )}
    </div>
  )
}

// Edit Role Modal (sub-component)
function EditRoleModal({ user, assignableRoles, onClose, onSave }) {
  const [rol, setRol] = useState(user.role)
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#1e293b] rounded-xl p-6 w-96 border border-gray-700">
        <h3 className="text-white font-semibold mb-4">Editar rol de usuario</h3>
        <p className="text-gray-400 mb-4">{user.name} {user.last_name}</p>
        
        <select
          value={rol}
          onChange={(e) => setRol(e.target.value)}
          className="w-full bg-[#0f172a] border border-gray-600 rounded px-3 py-2 text-white"
        >
          {assignableRoles.map(r => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        
        <div className="flex gap-2 mt-6">
          <button
            onClick={onClose}
            className="flex-1 py-2 rounded-lg text-gray-300 hover:bg-white/5"
          >
            Cancelar
          </button>
          <button
            onClick={() => onSave(user.id, rol)}
            className="flex-1 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-semibold"
          >
            Guardar
          </button>
        </div>
      </div>
    </div>
  )
}
```

---

## Authentication & Authorization

### JWT-Based Flow

```
1. User submits login form (email, password)
   ↓
2. Backend validates credentials
   - Query user by email
   - Compare password with bcrypt hash
   ↓
3. Create JWT token (if valid)
   - Payload: { sub: user.id, role: user.role }
   - Signed with SECRET_KEY
   - Expires in 24 hours
   ↓
4. Return token + user data to frontend
   ↓
5. Frontend stores in localStorage
   ↓
6. Every request includes: Authorization: Bearer <token>
   ↓
7. Backend verifies token in dependency
   - Decode JWT
   - Check expiration
   - Extract user_id
   - Query user from DB
```

### Implementation

```python
# backend/app/security.py

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"  # Store in .env
ALGORITHM = "HS256"

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare plain password with hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise JWTError()
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

```python
# backend/app/routers/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session
from app.security import verify_password, create_access_token, decode_access_token
from app.database import get_db
from app import models

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    """Extract and validate current user from JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = int(payload.get("sub"))
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Require admin or super_admin role."""
    if current_user.role not in (models.UserRole.admin, models.UserRole.super_admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

def require_super_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Require super_admin role."""
    if current_user.role != models.UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.post("/login", response_model=schemas.Token)
def login(
    credentials: schemas.LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user and return JWT token."""
    # Find user by email
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    user_out = schemas.UserOut.model_validate(user)
    return schemas.Token(access_token=access_token, token_type="bearer", user=user_out)
```

### Role Hierarchy Enforcement

```
Super-Admin
├── Can: assign admin, colaborador, invitado
├── Can: modify other super-admins
├── Can: modify admins
└── Can: modify any user

Admin
├── Can: assign colaborador, invitado
├── Cannot: assign admin
├── Cannot: modify other admins
└── Cannot: modify super-admin

Colaborador
├── Cannot: assign any role
└── Can: view/edit own data only

Invitado
├── Read-only access
└── Minimal privileges
```

**Backend Enforcement:**

Permission checks happen in two places:
1. **Router-level** (dependency injection): `Depends(require_admin)`
2. **Business logic** (helper functions): `_can_assign()`, `_can_modify_target()`

This "defense in depth" ensures invalid operations are blocked at multiple layers.

---

## Common CRUD Patterns

### The 5 Standard Endpoints

Every entity (User, Client, Task, Invoice, etc.) follows this pattern:

```
GET    /entity/                    # List all
GET    /entity/{id}                # Get single
POST   /entity/                    # Create
PATCH  /entity/{id}                # Update
DELETE /entity/{id}                # Delete (soft)
```

### Example: Task CRUD

```python
# backend/app/routers/tasks.py

@router.get("/", response_model=List[schemas.TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List tasks visible to current user (own + client assignments)."""
    tasks = db.query(models.Task)
    
    if current_user.role == "colaborador":
        # Colaboradores see only own tasks + clients they're assigned to
        client_ids = [
            cc.client_id for cc in current_user.client_assignments
        ]
        tasks = tasks.filter(
            (models.Task.collaborator_id == current_user.id) |
            (models.Task.client_id.in_(client_ids))
        )
    # Admins see all tasks
    
    return tasks.order_by(models.Task.due_date).all()

@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get single task."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Tarea no encontrada")
    
    # Visibility check (colaboradores can only see own or client-assigned)
    if current_user.role == "colaborador":
        can_view = (
            task.collaborator_id == current_user.id or
            task.client_id in [cc.client_id for cc in current_user.client_assignments]
        )
        if not can_view:
            raise HTTPException(403, "No tenés acceso a esta tarea")
    
    return task

@router.post("/", response_model=schemas.TaskOut, status_code=201)
def create_task(
    data: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Create new task."""
    task = models.Task(
        title=data.title,
        description=data.description,
        task_type=data.task_type,
        status=models.TaskStatus.pendiente,
        client_id=data.client_id,
        collaborator_id=data.collaborator_id,
        due_date=data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Log action
    log_action(db, current_user.id, client_id=data.client_id, task_id=task.id, action="create_task")
    
    return task

@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    data: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Update task."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Tarea no encontrada")
    
    # Update fields
    if data.title is not None:
        task.title = data.title
    if data.status is not None:
        task.status = data.status
    if data.due_date is not None:
        task.due_date = data.due_date
    
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Soft-delete task."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Tarea no encontrada")
    
    # In this case, we archive instead of hard-delete
    task.status = models.TaskStatus.postergada
    db.commit()
```

### Frontend CRUD Pattern

```javascript
// frontend/src/pages/Tareas.jsx

import { useState, useEffect } from 'react'
import api from '../utils/api'

export default function Tareas() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState(null)

  useEffect(() => { fetchTasks() }, [])

  const fetchTasks = async () => {
    try {
      const res = await api.get('/tasks/')
      setTasks(res.data)
    } catch (e) {
      alert('Error al cargar tareas')
    } finally {
      setLoading(false)
    }
  }

  const createTask = async (data) => {
    try {
      await api.post('/tasks/', data)
      fetchTasks()  // Refresh list
      setFormData(null)  // Close form
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al crear')
    }
  }

  const updateTask = async (id, data) => {
    try {
      await api.patch(`/tasks/${id}`, data)
      fetchTasks()
      setFormData(null)
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al actualizar')
    }
  }

  const deleteTask = async (id) => {
    if (!confirm('¿Confirmar eliminación?')) return
    try {
      await api.delete(`/tasks/${id}`)
      fetchTasks()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al eliminar')
    }
  }

  if (loading) return <div>Cargando...</div>

  return (
    <div className="space-y-6">
      <h1>Tareas</h1>
      <button onClick={() => setFormData({})}>+ Nueva tarea</button>

      {/* Task Form Modal */}
      {formData && (
        <TaskForm
          task={formData}
          onSave={(data) => {
            if (data.id) updateTask(data.id, data)
            else createTask(data)
          }}
          onClose={() => setFormData(null)}
        />
      )}

      {/* Task List */}
      <table className="w-full">
        <thead>
          <tr>
            <th>Título</th>
            <th>Estado</th>
            <th>Vencimiento</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map(task => (
            <tr key={task.id}>
              <td>{task.title}</td>
              <td>{task.status}</td>
              <td>{task.due_date}</td>
              <td>
                <button onClick={() => setFormData(task)}>Editar</button>
                <button onClick={() => deleteTask(task.id)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

---

## External Integrations

### 1. AFIP Integration (Pending)

```python
# backend/app/utils/afip_integration.py

"""
Integration with AFIP (Argentine Tax Authority) for:
- User authentication
- Certificate management
- Invoice validation
- Tax filing
"""

class AFIPClient:
    def __init__(self, cuit: str, cert_path: str, key_path: str):
        self.cuit = cuit
        self.cert_path = cert_path
        self.key_path = key_path
    
    def get_cuit_data(self, cuit: str):
        """Retrieve registered information for a CUIT."""
        # Implementation pending
        pass
    
    def validate_invoice(self, invoice_data: dict):
        """Validate invoice before submission."""
        # Implementation pending
        pass
    
    def submit_tax_return(self, tax_data: dict):
        """Submit tax declaration to AFIP."""
        # Implementation pending
        pass
```

### 2. ARCA Integration (Excel Import)

```python
# backend/app/routers/herramientas.py

"""
ARCA = Sistema de Administración de Retenciones y Percepciones
Exports contain: withholding records, perception records, invoice details

Process:
1. User uploads .xlsx exported from ARCA
2. R-01 cleans: corrects B/C types, normalizes exchange rates
3. R-02 divides: splits multi-alícuota rows for Holistor compatibility
4. Output: corrected .xlsx ready for tax filing
"""

@router.post("/limpiar-libro-iva")
def clean_iva_book(
    file: UploadFile,
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Process ARCA export: clean + divide by alícuota."""
    from larranaga_accounting_agent.src.transformaciones.limpieza_inicial import limpiar_comprobantes
    from larranaga_accounting_agent.src.transformaciones.division_alicuotas import aplicar_division_alicuotas
    
    try:
        # Read file into DataFrame
        contents = await file.read()
        df = pd.read_excel(contents, sheet_name="Comprobantes")
        
        # R-01: Clean
        df_limpiado, stats_r01 = limpiar_comprobantes(df)
        
        # R-02: Divide
        df_dividido, stats_r02 = aplicar_division_alicuotas(df_limpiado)
        
        # Save to database
        limpieza = models.LimpiezaIVA(
            client_id=client_id,
            user_id=current_user.id,
            nombre_original=file.filename,
            nombre_corregido=f"R-02_{file.filename}",
            archivo_corregido=save_to_bytes(df_dividido),
            total_filas=len(df),
            filas_bc_corregidas=stats_r01['filas_bc_corregidas'],
        )
        db.add(limpieza)
        db.commit()
        
        # Return download
        return {
            "filename": f"R-02_{file.filename}",
            "bytes": limpieza.archivo_corregido,
            "stats": {**stats_r01, **stats_r02},
        }
    except Exception as e:
        raise HTTPException(400, str(e))
```

### 3. Holistor Integration (PENDING)

```python
# backend/app/utils/holistor_integration.py

"""
Holistor = Tax return filing system
Receives "long" format (one row per alícuota)
R-02 output feeds directly into Holistor upload
"""

class HolistorUploader:
    def __init__(self, credentials: dict):
        self.api_key = credentials.get('api_key')
        self.base_url = "https://api.holistor.com"
    
    def upload_iva_book(self, df: pd.DataFrame, client_cuit: str):
        """Upload processed IVA book to Holistor."""
        payload = self._format_for_holistor(df)
        response = requests.post(
            f"{self.base_url}/upload",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        return response.json()
```

### 4. InsForge Cloud Sync

```python
# backend/app/sync/insforge_sync.py

"""
Automatic bidirectional sync: SQLite ↔ InsForge Cloud PostgreSQL
Triggered by:
1. Every database change (SQLAlchemy events)
2. Manual endpoint: POST /admin/sync-insforge
3. Scheduled job (if Celery configured)
"""

from sqlalchemy import event
from sqlalchemy.orm import Session
from app.database import Base

def sync_to_insforge(table_name: str, record_id: int, operation: str):
    """Push change to InsForge Cloud."""
    import requests
    
    try:
        payload = {
            "table": table_name,
            "record_id": record_id,
            "operation": operation,  # INSERT, UPDATE, DELETE
            "timestamp": datetime.utcnow().isoformat(),
        }
        response = requests.post(
            "https://vivnx98a.us-east.insforge.app/api/sync",
            json=payload,
            headers={"X-API-Key": os.getenv("INSFORGE_API_KEY")},
            timeout=5,
        )
        response.raise_for_status()
    except Exception as e:
        print(f"[InsForge Sync Error] {e}")

def setup_sync_listeners():
    """Register event listeners for automatic sync."""
    @event.listens_for(Base, "after_insert")
    def receive_after_insert(mapper, connection, target):
        table_name = target.__tablename__
        sync_to_insforge(table_name, target.id, "INSERT")
    
    @event.listens_for(Base, "after_update")
    def receive_after_update(mapper, connection, target):
        table_name = target.__tablename__
        sync_to_insforge(table_name, target.id, "UPDATE")
    
    @event.listens_for(Base, "after_delete")
    def receive_after_delete(mapper, connection, target):
        table_name = target.__tablename__
        sync_to_insforge(table_name, target.id, "DELETE")
```

---

## Data Processing Pipelines

### R-01: ARCA Cleaning (Limpieza Inicial)

**Problem:** ARCA exports contain errors:
- Type B/C rows marked as Type A with zeros
- Exchange rate variations across rows

**Solution:** Normalize the data

```python
# larranaga-accounting-agent/src/transformaciones/limpieza_inicial.py

def corregir_tipo_comprobante(row: pd.Series) -> str:
    """Correct voucher type based on neto values."""
    neto_gravado = parse_float(row['Neto Gravado'])
    # If neto=0, it's B or C type (non-taxable)
    return 'B' if neto_gravado == 0 else row['Tipo']

def normalizar_tipo_cambio(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize exchange rate to be consistent."""
    # Use first valid rate as baseline
    df['Tipo Cambio'] = df['Tipo Cambio'].fillna(1.0)
    return df

def limpiar_comprobantes(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Main cleaning function."""
    stats = {
        'filas_originales': len(df),
        'filas_bc_corregidas': 0,
    }
    
    # Apply corrections
    df['Tipo'] = df.apply(corregir_tipo_comprobante, axis=1)
    df = normalizar_tipo_cambio(df)
    
    stats['filas_bc_corregidas'] = len(df[df['Tipo'].isin(['B', 'C'])])
    
    return df, stats
```

### R-02: Multi-Alícuota Division

**Problem:** ARCA exports in "wide" format with multiple alícuota columns:

```
Row: Claro invoice
Neto 21%: 89.516,16   IVA 21%: 18.798,39
Neto 27%: 181.350,87  IVA 27%: 48.965,19
```

**Solution:** Split into separate rows for Holistor

```python
# larranaga-accounting-agent/src/transformaciones/division_alicuotas.py

ALICUOTAS = [0, 2.5, 5, 10.5, 21, 27]
NETO_COLS = [13, 15, 17, 19, 21, 23]   # Column indices
IVA_COLS = [14, 16, 18, 20, 22]        # Column indices

def detect_multi_alicuota_rows(df: pd.DataFrame) -> dict:
    """Find rows with 2+ alícuotas active."""
    multi = {}
    for idx, row in df.iterrows():
        active_rates = []
        for i, neto_col in enumerate(NETO_COLS):
            if parse_float(row.iloc[neto_col]) > 0:
                active_rates.append(ALICUOTAS[i])
        if len(active_rates) > 1:
            multi[idx] = active_rates
    return multi

def expand_multi_alicuota_row(row: pd.Series, rates: List[float], idx: int) -> List[pd.Series]:
    """Split 1 row into N rows (one per alícuota)."""
    rows = []
    original_otros_tributos = parse_float(row.iloc[27])  # Column AB
    
    for i, rate in enumerate(rates):
        new_row = row.copy()
        
        # Zero out all neto/iva except this rate
        for j, alicuota in enumerate(ALICUOTAS):
            new_row.iloc[NETO_COLS[j]] = 0 if alicuota != rate else row.iloc[NETO_COLS[j]]
            if j < len(IVA_COLS):
                new_row.iloc[IVA_COLS[j]] = 0 if alicuota != rate else row.iloc[IVA_COLS[j]]
        
        # Otros Tributos: 100% on primary rate (21% if present)
        if i == 0:  # First split gets all otros_tributos
            new_row.iloc[27] = original_otros_tributos
        else:
            new_row.iloc[27] = 0
        
        # Update row number with suffix (991 → 991/A, 991/B)
        num_col = new_row.iloc[8]  # Original row number
        new_row.iloc[8] = f"{num_col}/{chr(65 + i)}"
        
        rows.append(new_row)
    
    return rows

def aplicar_division_alicuotas(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Main division function."""
    multi = detect_multi_alicuota_rows(df)
    
    if not multi:
        # No multi-alícuota rows; return as-is
        return df, {'multi_alicuota_detected': 0, 'filas_totales': len(df)}
    
    # Expand multi-alícuota rows
    new_rows = []
    for idx, row in df.iterrows():
        if idx in multi:
            expanded = expand_multi_alicuota_row(row, multi[idx], idx)
            new_rows.extend(expanded)
        else:
            new_rows.append(row)
    
    df_expanded = pd.DataFrame(new_rows).reset_index(drop=True)
    
    return df_expanded, {
        'multi_alicuota_detected': len(multi),
        'filas_originales': len(df),
        'filas_totales': len(df_expanded),
    }
```

---

## Development Workflow

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/larrañaga.git
cd larrañaga

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=sqlite:///./larrañaga.db
SECRET_KEY=your-super-secret-key-change-in-production
AFIP_CERT_PATH=/path/to/cert.crt
AFIP_KEY_PATH=/path/to/key.key
INSFORGE_API_KEY=your-insforge-key
RESEND_API_KEY=your-email-service-key
EOF

# Run migrations
python scripts/migrate_users_v2.py
python scripts/seed_data.py

# Start backend
uvicorn app.main:app --reload --port 8000

# Frontend setup (in new terminal)
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

### 2. Git Workflow

```bash
# Branches
- main        # Production-ready
- dev         # Integration branch
- fede        # Feature: user management
- gero        # Feature: advanced tax calculations
- personal    # Individual feature branches

# Creating a feature
git checkout -b feature/my-feature dev
# ... make changes ...
git add .
git commit -m "feat(module): description"
git push origin feature/my-feature

# Create pull request on GitHub
# After review & CI passes → merge to dev → merge to main
```

### 3. Testing Strategy

```bash
# Backend tests
cd backend
pytest tests/ -v
pytest tests/test_users.py -v  # Specific file

# Frontend tests
cd frontend
npm test
npm test -- --watch

# Integration tests
# Run backend + frontend, manually test workflows

# E2E tests (with Playwright/Cypress)
npm run test:e2e
```

### 4. Code Style

**Backend (Python):**
- PEP 8 style guide
- Black formatter: `black app/`
- Type hints required
- Docstrings for public functions

**Frontend (JavaScript):**
- ESLint configured
- Prettier formatter
- Functional components + hooks only
- camelCase for variables

---

## Deployment Guide

### Development → Production Checklist

```
[ ] Update version in package.json + requirements.txt
[ ] Run full test suite locally
[ ] Build frontend: npm run build
[ ] Verify .env variables (SECRET_KEY, DB_URL, API_keys)
[ ] Database backups created
[ ] Security audit (no secrets in code)
[ ] Performance test (load testing)
[ ] SSL certificate configured
[ ] CORS origins updated
[ ] Rate limiting configured
[ ] Logging configured
[ ] Monitoring setup (Sentry, DataDog, etc.)
[ ] Deployment script tested
[ ] Rollback plan prepared
```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile.backend

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY scripts/ scripts/

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://user:pass@db:5432/larrañaga

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile.frontend

FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json .
RUN npm install

COPY . .
RUN npm run build

FROM node:18-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=build /app/dist dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

```yaml
# docker-compose.yml

version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: larrañaga
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@db:5432/larrañaga
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Deployment Commands

```bash
# Build
docker-compose build

# Deploy
docker-compose up -d

# View logs
docker-compose logs -f backend

# Database migrations
docker-compose exec backend python scripts/migrate_users_v2.py

# Rollback
docker-compose down
docker rmi larrañaga_backend larrañaga_frontend
```

---

## Step-by-Step Replication Guide

### For a New Accounting Firm Client

Follow this process to replicate Larrañaga for **ClientName**:

#### Phase 1: Project Setup (Day 1)

1. **Clone Larrañaga template**
   ```bash
   git clone https://github.com/your-org/larrañaga.git clientname-platform
   cd clientname-platform
   ```

2. **Rename project identifiers**
   - `backend/app/main.py`: Change `title="Larrañaga API"` → `title="ClientName API"`
   - `frontend/src/App.jsx`: Update brand name in layout/header
   - `package.json`: Change name to `clientname-platform`
   - Database filename: `larrañaga.db` → `clientname.db`

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with:
   # - CLIENT_NAME=ClientName
   # - DATABASE_URL=sqlite:///./clientname.db
   # - SECRET_KEY=<generate new>
   # - AFIP credentials (if applicable)
   # - Email service keys
   ```

#### Phase 2: Customize Database & Models (Days 2-3)

1. **Extend User model if needed**
   ```python
   # Example: Add department field
   class User(Base):
       # ... existing fields ...
       department = Column(String(100))  # New field
   ```

2. **Add custom enums for task types**
   ```python
   class TaskType(str, Enum):
       # Larrañaga defaults:
       facturacion = "facturacion"
       # ADD ClientName-specific types:
       # custom_task_type = "custom_task_type"
   ```

3. **Create migration for custom fields**
   ```bash
   # Database will auto-create on startup if using SQLite
   # For PostgreSQL, create migration scripts
   ```

#### Phase 3: Customize Routers & Business Logic (Days 4-5)

1. **Review permission rules** (in `routers/users.py`)
   - Are the 4 roles (super_admin, admin, colaborador, invitado) appropriate?
   - Or do you need custom roles?

2. **Extend with ClientName-specific endpoints**
   ```python
   # Example: Add expense tracking
   @router.post("/gastos/", response_model=schemas.GastoOut)
   def crear_gasto(data: schemas.GastoCreate, ...):
       # Implementation
       pass
   ```

3. **Customize email templates**
   - `backend/app/utils/resend.py`: Update email HTML/CSS

#### Phase 4: Customize Frontend (Days 6-7)

1. **Update branding**
   - Logo: `frontend/src/assets/logo.png`
   - Colors: `frontend/src/index.css` (Tailwind theme)
   - Font: Update in `frontend/index.html`

2. **Add ClientName-specific pages**
   ```javascript
   // Create frontend/src/pages/ClientNameDashboard.jsx
   export default function ClientNameDashboard() {
       // Custom widgets, metrics, etc.
   }
   ```

3. **Update sidebar navigation**
   - `frontend/src/components/Layout/Sidebar.jsx`: Add ClientName menu items

#### Phase 5: Setup AFIP & External Integrations (Days 8-9)

1. **AFIP Integration** (if client is Argentine)
   ```python
   # Populate in backend/app/utils/afip_integration.py
   # Requires: cert.crt, key.key, CUIT
   ```

2. **Holistor Setup** (if using)
   - Get credentials from Holistor
   - Store in `.env`: `HOLISTOR_API_KEY=...`

3. **Email Service** (Resend / SendGrid / etc.)
   - Setup account
   - Store credentials in `.env`: `RESEND_API_KEY=...`

#### Phase 6: Initialize Data (Day 10)

1. **Create super-admins**
   ```bash
   # Modify backend/scripts/seed_data.py
   # Add 2-4 super-admin accounts for ClientName team
   python scripts/seed_data.py
   ```

2. **Create initial clients** (if applicable)
   - Manually via API/UI
   - Or batch import if data available

#### Phase 7: Testing & QA (Days 11-12)

1. **Test all core flows**
   - User registration → approval workflow
   - Client creation
   - Task assignment
   - Data processing (R-01, R-02)
   - Invoice entry

2. **Load testing**
   - Use LoadRunner / k6 to simulate 50-100 concurrent users

3. **Security audit**
   - Check JWT token expiry
   - Verify permission checks
   - SQL injection / XSS testing
   - CORS configuration

#### Phase 8: Deployment (Day 13)

1. **Choose infrastructure**
   - Option A: EC2 + RDS (AWS)
   - Option B: DigitalOcean droplet + managed DB
   - Option C: Heroku
   - Option D: Docker + Kubernetes

2. **Deploy backend**
   ```bash
   git push production
   # CI/CD pipeline builds & deploys
   ```

3. **Deploy frontend**
   ```bash
   npm run build
   # Deploy dist/ to CDN or static host
   ```

4. **Enable HTTPS**
   - Get SSL certificate (Let's Encrypt)
   - Configure nginx/reverse proxy

5. **Setup monitoring**
   - Sentry for error tracking
   - DataDog / New Relic for performance
   - Uptime monitoring

#### Phase 9: Training & Handoff (Day 14)

1. **Document for ClientName**
   - Admin guide (user management, system settings)
   - User guide (how to use platform)
   - API documentation (if 3rd-party integrations)

2. **Train ClientName team**
   - Admin: User management, reporting
   - Users: Day-to-day operations

3. **Establish support plan**
   - Escalation contacts
   - SLA for incident response
   - Monthly review meetings

---

### Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Setup | 1 day | Running instance |
| 2. Database | 2 days | Schema, migrations |
| 3. Logic | 2 days | Custom endpoints |
| 4. Frontend | 2 days | Branded UI |
| 5. Integrations | 2 days | AFIP, Holistor, email |
| 6. Data | 1 day | Initial data populated |
| 7. Testing | 2 days | All tests passing |
| 8. Deployment | 1 day | Live & monitored |
| 9. Handoff | 1 day | Training & docs |
| **Total** | **14 days** | **Production-ready** |

---

## Key Files Reference

### Backend Critical Files

| File | Purpose | Modification Priority |
|------|---------|---------------------|
| `main.py` | App initialization | Low |
| `database.py` | DB connection | Low |
| `models.py` | Schema definition | **HIGH** |
| `schemas.py` | API validation | **HIGH** |
| `routers/auth.py` | Authentication | Low |
| `routers/users.py` | User management | Medium |
| `routers/` (others) | Entity management | Medium |
| `security.py` | Crypto & JWT | Low |

### Frontend Critical Files

| File | Purpose | Modification Priority |
|------|---------|---------------------|
| `App.jsx` | Routes & layout | Medium |
| `context/AuthContext.jsx` | Global auth state | Low |
| `components/Layout/` | UI wrapper | **HIGH** |
| `pages/` | Page components | **HIGH** |
| `utils/api.js` | HTTP client | Low |
| `index.css` | Theming | **HIGH** |

---

## Conclusion

This blueprint provides the complete foundation for replicating Larrañaga for new clients. The key to successful replication is:

1. **Start with the template** (don't rebuild from scratch)
2. **Customize incrementally** (database → backend → frontend)
3. **Test thoroughly** before deployment
4. **Document extensively** for the client

The 14-day timeline is realistic for a team of 2-3 developers familiar with the stack. Adjust based on:
- Complexity of custom business logic
- Integration requirements (AFIP, Holistor, etc.)
- Client expectations for initial feature set

For questions or updates to this blueprint, refer to the project's GitHub wiki or contact the core team.

---

**Last Updated:** 2026-04-27  
**Template Version:** 1.0  
**Maintainers:** Federico Rodriguez, Team Larrañaga
