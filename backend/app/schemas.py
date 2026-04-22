from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from .models import UserRole, TaskType, TaskStatus, InvoiceType


# ─── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserOut"


# ─── Users ───────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole = UserRole.collaborator


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    avatar_initials: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Clients ─────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    name: str
    business_name: Optional[str] = None
    cuit: Optional[str] = None
    clave_fiscal: Optional[str] = None  # plain text, will be encrypted
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    category: Optional[str] = None
    fiscal_condition: Optional[str] = None
    activity_code: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    clave_fiscal: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    category: Optional[str] = None
    fiscal_condition: Optional[str] = None
    activity_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CollaboratorBrief(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class ClientOut(BaseModel):
    id: int
    name: str
    business_name: Optional[str] = None
    cuit: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    category: Optional[str] = None
    fiscal_condition: Optional[str] = None
    activity_code: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    collaborators: List[CollaboratorBrief] = []
    task_count: Optional[int] = 0
    pending_tasks: Optional[int] = 0
    saldo_cc: Optional[float] = 0.0

    class Config:
        from_attributes = True


class ClientCredentials(BaseModel):
    cuit: Optional[str] = None
    clave_fiscal: Optional[str] = None  # decrypted, only for authorized users


# ─── Tasks ───────────────────────────────────────────────────────────────────

class SubtaskCreate(BaseModel):
    title: str
    status: TaskStatus = TaskStatus.pendiente
    comment: Optional[str] = None


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    comment: Optional[str] = None


class SubtaskOut(BaseModel):
    id: int
    task_id: int
    title: str
    status: TaskStatus
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: TaskType
    client_id: int
    collaborator_id: Optional[int] = None
    period: Optional[str] = None
    due_date: Optional[date] = None
    blocker_comment: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    collaborator_id: Optional[int] = None
    period: Optional[str] = None
    due_date: Optional[date] = None
    blocker_comment: Optional[str] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    task_type: TaskType
    status: TaskStatus
    client_id: int
    client_name: Optional[str] = None
    collaborator_id: Optional[int] = None
    collaborator_name: Optional[str] = None
    period: Optional[str] = None
    due_date: Optional[date] = None
    blocker_comment: Optional[str] = None
    created_at: datetime
    subtasks: List[SubtaskOut] = []

    class Config:
        from_attributes = True


# ─── IVA ─────────────────────────────────────────────────────────────────────

class IVARecordCreate(BaseModel):
    client_id: int
    period: str
    ventas_gravadas: float = 0
    ventas_exentas: float = 0
    ventas_no_gravadas: float = 0
    debito_fiscal: float = 0
    compras_gravadas: float = 0
    compras_exentas: float = 0
    compras_no_gravadas: float = 0
    credito_fiscal: float = 0
    saldo_a_favor_anterior: float = 0
    due_date: Optional[date] = None


class IVARecordUpdate(BaseModel):
    ventas_gravadas: Optional[float] = None
    ventas_exentas: Optional[float] = None
    ventas_no_gravadas: Optional[float] = None
    debito_fiscal: Optional[float] = None
    compras_gravadas: Optional[float] = None
    compras_exentas: Optional[float] = None
    compras_no_gravadas: Optional[float] = None
    credito_fiscal: Optional[float] = None
    saldo_a_favor_anterior: Optional[float] = None
    filed: Optional[bool] = None
    filed_at: Optional[datetime] = None
    vep_number: Optional[str] = None


class IVARecordOut(BaseModel):
    id: int
    client_id: int
    client_name: Optional[str] = None
    period: str
    ventas_gravadas: float
    ventas_exentas: float
    ventas_no_gravadas: float
    debito_fiscal: float
    compras_gravadas: float
    compras_exentas: float
    compras_no_gravadas: float
    credito_fiscal: float
    saldo_a_favor_anterior: float
    saldo: float
    filed: bool
    filed_at: Optional[datetime] = None
    due_date: Optional[date] = None
    vep_number: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Invoices ─────────────────────────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    client_id: int
    invoice_type: InvoiceType
    punto_venta: int = 1
    date: date
    receptor_cuit: Optional[str] = None
    receptor_name: Optional[str] = None
    concept: Optional[str] = "Servicios"
    neto_gravado: float = 0
    neto_no_gravado: float = 0
    exento: float = 0
    iva_21: float = 0
    iva_105: float = 0
    total: float


class InvoiceOut(BaseModel):
    id: int
    client_id: int
    client_name: Optional[str] = None
    collaborator_id: Optional[int] = None
    collaborator_name: Optional[str] = None
    invoice_type: InvoiceType
    punto_venta: int
    number: int
    date: date
    receptor_cuit: Optional[str] = None
    receptor_name: Optional[str] = None
    concept: Optional[str] = None
    neto_gravado: float
    neto_no_gravado: float
    exento: float
    iva_21: float
    iva_105: float
    total: float
    cae: Optional[str] = None
    cae_vto: Optional[date] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Ingresos Brutos ─────────────────────────────────────────────────────────

class IngresosBrutosOut(BaseModel):
    id: int
    client_id: int
    period: str
    jurisdiction: str
    regime: str
    base_imponible: float
    alicuota: float
    impuesto: float
    retenciones: float
    percepciones: float
    saldo: float
    filed: bool
    filed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Cuentas Corrientes ──────────────────────────────────────────────────────

class MovimientoCCCreate(BaseModel):
    client_id: int
    tipo: str  # 'ingreso' or 'egreso'
    monto: float
    concepto: str
    fecha: date
    notas: Optional[str] = None


class MovimientoCCOut(BaseModel):
    id: int
    client_id: int
    tipo: str
    monto: float
    concepto: str
    fecha: date
    notas: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_clients: int
    active_clients: int
    total_collaborators: int
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    blocked_tasks: int
    tasks_this_month: int
    iva_pendientes: int
    iva_presentados_mes: int


class CollaboratorStats(BaseModel):
    collaborator_id: int
    collaborator_name: str
    total_tasks: int
    completed: int
    pending: int
    in_progress: int
    blocked: int
    clients_count: int


class AssignCollaborator(BaseModel):
    collaborator_id: int
