from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from .models import UserRole, UserStatus, TaskType, TaskStatus, InvoiceType, TipoHonorario, TipoProfesional


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
    last_name: Optional[str] = None
    cuit: Optional[str] = None
    email: str
    password: str
    role: UserRole = UserRole.colaborador
    status: UserStatus = UserStatus.pending


class UserUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    cuit: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserOut(BaseModel):
    id: int
    name: str
    last_name: Optional[str] = None
    cuit: Optional[str] = None
    email: str
    role: UserRole
    status: UserStatus
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
    # R-03: configuración de honorario
    tipo_honorario: Optional[str] = None
    importe_honorario: Optional[float] = None
    producto_ref_id: Optional[int] = None
    cantidad_unidades: Optional[float] = None
    profesional_id: Optional[int] = None

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



# ─── Retenciones / Percepciones (Mis Retenciones ARCA) ──────────────────────

class RetencionSyncRequest(BaseModel):
    client_id: int
    period: str  # YYYY-MM
    impuesto_retenido: int = 217  # 217=IVA, 11=Gan(ret), 10=Gan(perc), 767=BP
    descripcion_impuesto: str = "IVA"
    incluir_percepciones: bool = True
    incluir_retenciones: bool = True


class RetencionPercepcionOut(BaseModel):
    id: int
    client_id: int
    period: str
    cuit_agente: Optional[str] = None
    impuesto_retenido: Optional[int] = None
    codigo_regimen: Optional[int] = None
    tipo_operacion: Optional[str] = None
    fecha_retencion: date
    fecha_comprobante: Optional[date] = None
    importe: float
    numero_certificado: Optional[str] = None
    numero_comprobante: Optional[str] = None
    descripcion_comprobante: Optional[str] = None
    codigo_holistor: Optional[str] = None
    sdk_job_id: Optional[str] = None
    synced_at: Optional[datetime] = None
# ─── Cuentas Corrientes ──────────────────────────────────────────────────────

class MovimientoCCCreate(BaseModel):
    client_id: int
    tipo: str  # 'honorario' | 'pago' | 'ajuste'
    monto: float
    concepto: str
    fecha: date
    periodo_honorario: Optional[str] = None
    forma_pago: Optional[str] = None  # 'efectivo' | 'transferencia'
    profesional_id: Optional[int] = None
    notas: Optional[str] = None


class MovimientoCCOut(BaseModel):
    id: int
    client_id: int
    tipo: str
    monto: float
    concepto: str
    fecha: date
    periodo_honorario: Optional[str] = None
    forma_pago: Optional[str] = None
    profesional_id: Optional[int] = None
    notas: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── R-03 — Productos de Referencia y Honorarios ─────────────────────────────

class ProductoReferenciaCreate(BaseModel):
    nombre: str
    unidad: str = "unidad"
    precio_vigente: float
    fecha_actualizacion: date


class ProductoReferenciaUpdate(BaseModel):
    nombre: Optional[str] = None
    unidad: Optional[str] = None
    precio_vigente: Optional[float] = None
    fecha_actualizacion: Optional[date] = None
    activo: Optional[bool] = None


class ProductoReferenciaOut(BaseModel):
    id: int
    nombre: str
    unidad: str
    precio_vigente: float
    fecha_actualizacion: date
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class HonorarioCalcular(BaseModel):
    """Parámetros para calcular/generar honorarios de un período."""
    periodo: str  # YYYY-MM


class HonorarioOut(BaseModel):
    id: int
    client_id: int
    client_name: Optional[str] = None
    periodo: str
    importe: float
    estado: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClientHonorarioUpdate(BaseModel):
    """Actualizar configuración de honorario de un cliente."""
    tipo_honorario: Optional[TipoHonorario] = None
    importe_honorario: Optional[float] = None
    cantidad_unidades: Optional[float] = None
    producto_ref_id: Optional[int] = None
    profesional_id: Optional[int] = None


# ─── R-04 — Profesionales y Liquidaciones ────────────────────────────────────

class ProfesionalCreate(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    email: Optional[str] = None
    tipo: TipoProfesional = TipoProfesional.profesional


class ProfesionalUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    tipo: Optional[TipoProfesional] = None
    activo: Optional[bool] = None


class ProfesionalOut(BaseModel):
    id: int
    nombre: str
    apellido: Optional[str] = None
    email: Optional[str] = None
    tipo: TipoProfesional
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReintegroGastoCreate(BaseModel):
    concepto: str
    importe: float


class ReintegroGastoOut(BaseModel):
    id: int
    liquidacion_id: int
    concepto: str
    importe: float
    created_at: datetime

    class Config:
        from_attributes = True


class LiquidacionCreate(BaseModel):
    profesional_id: int
    periodo: str  # YYYY-MM
    honorarios_totales: float
    saldo_anterior: float = 0


class LiquidacionUpdate(BaseModel):
    honorarios_totales: Optional[float] = None
    forma_cobro: Optional[str] = None
    monto_cobrado: Optional[float] = None
    cerrada: Optional[bool] = None


class LiquidacionOut(BaseModel):
    id: int
    profesional_id: int
    profesional_nombre: Optional[str] = None
    periodo: str
    honorarios_totales: float
    adelantos_percibidos: float
    saldo_anterior: float
    reintegro_gastos: float
    total_a_cobrar: float
    forma_cobro: Optional[str] = None
    monto_cobrado: float
    saldo_siguiente: float
    cerrada: bool
    created_at: datetime
    reintegros: List[ReintegroGastoOut] = []

    class Config:
        from_attributes = True



class RetencionSyncResponse(BaseModel):
    client_id: int
    period: str
    sdk_job_id: Optional[str] = None
    status: str  # complete | error
    total_records: int
    inserted: int
    skipped_duplicates: int
    summary_by_holistor: dict  # {"PIVC": {"count": 7, "total": 8045.13}}
    records: List[RetencionPercepcionOut]


# ─── Comprobantes Recibidos (Mis Comprobantes ARCA, t=R) ─────────────────────

class ComprobanteSyncRequest(BaseModel):
    client_id: int
    period: str                    # YYYY-MM
    tipos_comprobantes: Optional[List[int]] = None  # [1, 6, 11...] — None = todos


class ComprobanteRecibidoOut(BaseModel):
    id: int
    client_id: int
    period: str
    fecha_emision: date
    tipo_comprobante: Optional[str] = None
    punto_venta: Optional[str] = None
    numero_desde: Optional[str] = None
    numero_hasta: Optional[str] = None
    cod_autorizacion: Optional[str] = None
    # Emisor (quien aplica la percepción = cuit_agente en retenciones)
    nro_doc_emisor: Optional[str] = None
    denominacion_emisor: Optional[str] = None
    # Receptor (nuestro cliente)
    nro_doc_receptor: Optional[str] = None
    moneda: Optional[str] = None
    imp_neto_gravado: float = 0
    imp_neto_no_gravado: float = 0
    imp_op_exentas: float = 0
    otros_tributos: float = 0
    iva: float = 0
    imp_total: float = 0
    sdk_job_id: Optional[str] = None
    synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComprobanteSyncResponse(BaseModel):
    client_id: int
    period: str
    sdk_job_id: Optional[str] = None
    status: str
    total_records: int
    inserted: int
    skipped_duplicates: int
    records: List[ComprobanteRecibidoOut]


# ─── Cruce Retenciones ↔ Comprobantes ────────────────────────────────────────

class CruceItem(BaseModel):
    retencion_id: int
    comprobante_id: Optional[int] = None
    client_id: int
    period: str
    fecha_retencion: date
    cuit_agente: Optional[str] = None
    importe_retencion: float
    codigo_holistor: Optional[str] = None
    # datos del comprobante cruzado (None si sin match)
    fecha_emision: Optional[date] = None
    tipo_comprobante: Optional[str] = None
    numero_desde: Optional[str] = None
    denominacion_receptor: Optional[str] = None
    imp_total: Optional[float] = None
    otros_tributos_comprobante: Optional[float] = None
    match_score: Optional[str] = None  # "exact" | "approx" | "none"

    class Config:
        from_attributes = True


class CruceResponse(BaseModel):
    client_id: int
    period: str
    total_retenciones: int
    matched: int
    unmatched: int
    items: List[CruceItem]


# ─── R-03: Productos de referencia ───────────────────────────────────────────

class ProductoReferenciaCreate(BaseModel):
    nombre: str
    unidad: Optional[str] = None
    precio_vigente: float


class ProductoReferenciaUpdate(BaseModel):
    nombre: Optional[str] = None
    unidad: Optional[str] = None
    precio_vigente: Optional[float] = None


class HistorialPrecioOut(BaseModel):
    id: int
    precio: float
    vigente_desde: date
    created_at: datetime

    class Config:
        from_attributes = True


class ProductoReferenciaOut(BaseModel):
    id: int
    nombre: str
    unidad: Optional[str] = None
    precio_vigente: float
    actualizado_en: Optional[datetime] = None
    created_at: datetime
    historial: List[HistorialPrecioOut] = []

    class Config:
        from_attributes = True


class ClientHonorarioUpdate(BaseModel):
    tipo_honorario: Optional[str] = None       # "fijo" | "producto"
    importe_honorario: Optional[float] = None
    producto_ref_id: Optional[int] = None
    cantidad_unidades: Optional[float] = None
    profesional_id: Optional[int] = None


class HonorarioOut(BaseModel):
    id: int
    client_id: int
    client_name: Optional[str] = None
    period: str
    importe: float
    tipo: str
    precio_producto_snapshot: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClienteActualizacionItem(BaseModel):
    client_id: int
    client_name: str
    tipo_honorario: Optional[str] = None
    importe_actual: Optional[float] = None
    importe_propuesto: Optional[float] = None
    delta_pct: Optional[float] = None
    aplica_indice: bool = True


class ActualizacionCuatrimestralPreview(BaseModel):
    indice_pct: float
    clientes: List[ClienteActualizacionItem]


class ActualizacionItem(BaseModel):
    client_id: int
    nuevo_importe: float
    confirmar: bool = True


class ActualizacionCuatrimestralApply(BaseModel):
    indice_pct: float
    vigente_desde: str    # YYYY-MM
    actualizaciones: List[ActualizacionItem]


# ─── R-04: Profesionales, pagos y liquidaciones ───────────────────────────────

class ProfesionalCreate(BaseModel):
    nombre: str
    tipo: str = "profesional"    # "profesional" | "socio"


class ProfesionalUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    activo: Optional[bool] = None


class ProfesionalOut(BaseModel):
    id: int
    nombre: str
    tipo: str
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PagoCreate(BaseModel):
    client_id: int
    honorario_id: Optional[int] = None
    fecha: date
    importe: float
    forma_pago: str              # "efectivo" | "transferencia"
    fuente_pago: Optional[str] = None
    banco_destino: Optional[str] = None
    profesional_destinatario_id: Optional[int] = None
    notas: Optional[str] = None


class PagoOut(BaseModel):
    id: int
    client_id: int
    client_name: Optional[str] = None
    honorario_id: Optional[int] = None
    fecha: date
    importe: float
    forma_pago: str
    fuente_pago: Optional[str] = None
    banco_destino: Optional[str] = None
    profesional_destinatario_id: Optional[int] = None
    profesional_destinatario_nombre: Optional[str] = None
    notas: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReintegroGastoCreate(BaseModel):
    concepto: str
    importe: float


class ReintegroGastoOut(BaseModel):
    id: int
    liquidacion_id: int
    concepto: str
    importe: float
    created_at: datetime

    class Config:
        from_attributes = True


class LiquidacionHonorariosSet(BaseModel):
    honorarios_totales: float


class LiquidacionCerrarRequest(BaseModel):
    cobro_efectivo: float = 0
    cobro_transferencia: float = 0


class LiquidacionOut(BaseModel):
    id: int
    profesional_id: int
    profesional_nombre: Optional[str] = None
    period: str
    honorarios_totales: float
    adelantos_percibidos: float
    saldo_anterior: float
    reintegros_gastos: float
    total_a_cobrar: float
    cobro_efectivo: float
    cobro_transferencia: float
    saldo_siguiente: float
    cerrada: bool
    cerrada_en: Optional[datetime] = None
    reintegros: List[ReintegroGastoOut] = []
    alerta_sobreadelanto: bool = False

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
