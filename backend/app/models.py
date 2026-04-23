from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, Date, LargeBinary
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


class UserRole(str, enum.Enum):
    admin1 = "admin1"
    admin2 = "admin2"
    admin3 = "admin3"
    collaborator = "collaborator"


class TaskType(str, enum.Enum):
    facturacion = "facturacion"
    comprobantes = "comprobantes"
    ddjj_iva = "ddjj_iva"
    ddjj_ganancias = "ddjj_ganancias"
    ddjj_bienes_personales = "ddjj_bienes_personales"
    ingresos_brutos = "ingresos_brutos"
    legal = "legal"
    otros = "otros"


class TaskStatus(str, enum.Enum):
    pendiente = "pendiente"
    en_curso = "en_curso"
    terminada = "terminada"
    bloqueada = "bloqueada"
    postergada = "postergada"


class InvoiceType(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    M = "M"
    E = "E"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.collaborator)
    is_active = Column(Boolean, default=True)
    avatar_initials = Column(String(3))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="collaborator")
    client_assignments = relationship("ClientCollaborator", back_populates="collaborator", foreign_keys="ClientCollaborator.collaborator_id")
    action_logs = relationship("ActionLog", back_populates="user")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    business_name = Column(String(200))
    cuit = Column(String(13), unique=True, index=True)
    clave_fiscal_encrypted = Column(Text)
    address = Column(String(255))
    phone = Column(String(30))
    email = Column(String(100))
    category = Column(String(50))
    fiscal_condition = Column(String(50))
    activity_code = Column(String(20))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="client")
    collaborators = relationship("ClientCollaborator", back_populates="client")
    iva_records = relationship("IVARecord", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")
    ingresos_brutos = relationship("IngresosBrutos", back_populates="client")
    retenciones_percepciones = relationship("RetencionPercepcion", back_populates="client", cascade="all, delete-orphan")
    comprobantes_recibidos = relationship("ComprobanteRecibido", back_populates="client", cascade="all, delete-orphan")
    action_logs = relationship("ActionLog", back_populates="client")

    limpiezas_iva = relationship("LimpiezaIVA", back_populates="client")


class LimpiezaIVA(Base):
    """Historial de archivos procesados por R-01 (Limpieza Libro IVA Compras)."""
    __tablename__ = "limpiezas_iva"

    id                     = Column(Integer, primary_key=True, index=True)
    client_id              = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id                = Column(Integer, ForeignKey("users.id"), nullable=False)
    nombre_original        = Column(String(255), nullable=False)
    nombre_corregido       = Column(String(255), nullable=False)
    archivo_corregido      = Column(LargeBinary, nullable=False)   # xlsx como bytes
    total_filas            = Column(Integer, default=0)
    filas_bc_corregidas    = Column(Integer, default=0)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="limpiezas_iva")
    user   = relationship("User")
    movimientos_cc = relationship("MovimientoCuentaCorriente", back_populates="client", cascade="all, delete-orphan")



class ClientCollaborator(Base):
    __tablename__ = "client_collaborators"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    collaborator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by_id = Column(Integer, ForeignKey("users.id"))

    client = relationship("Client", back_populates="collaborators")
    collaborator = relationship("User", foreign_keys=[collaborator_id], back_populates="client_assignments")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.pendiente)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    collaborator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    period = Column(String(7))  # YYYY-MM format
    due_date = Column(Date)
    completed_at = Column(DateTime(timezone=True))
    blocker_comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client", back_populates="tasks")
    collaborator = relationship("User", back_populates="tasks")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")
    action_logs = relationship("ActionLog", back_populates="task")


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.pendiente)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    task = relationship("Task", back_populates="subtasks")


class IVARecord(Base):
    __tablename__ = "iva_records"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    period = Column(String(7), nullable=False)  # YYYY-MM
    # Ventas
    ventas_gravadas = Column(Float, default=0)
    ventas_exentas = Column(Float, default=0)
    ventas_no_gravadas = Column(Float, default=0)
    debito_fiscal = Column(Float, default=0)
    # Compras
    compras_gravadas = Column(Float, default=0)
    compras_exentas = Column(Float, default=0)
    compras_no_gravadas = Column(Float, default=0)
    credito_fiscal = Column(Float, default=0)
    # Balance
    saldo_a_favor_anterior = Column(Float, default=0)
    saldo = Column(Float, default=0)  # positive = to pay, negative = in favor
    # Filing
    filed = Column(Boolean, default=False)
    filed_at = Column(DateTime(timezone=True))
    due_date = Column(Date)
    vep_number = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="iva_records")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    collaborator_id = Column(Integer, ForeignKey("users.id"))
    invoice_type = Column(Enum(InvoiceType), nullable=False)
    punto_venta = Column(Integer, default=1)
    number = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    receptor_cuit = Column(String(13))
    receptor_name = Column(String(200))
    concept = Column(String(50))
    neto_gravado = Column(Float, default=0)
    neto_no_gravado = Column(Float, default=0)
    exento = Column(Float, default=0)
    iva_21 = Column(Float, default=0)
    iva_105 = Column(Float, default=0)
    total = Column(Float, nullable=False)
    cae = Column(String(14))
    cae_vto = Column(Date)
    status = Column(String(20), default="emitida")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="invoices")


class IngresosBrutos(Base):
    __tablename__ = "ingresos_brutos"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    period = Column(String(7), nullable=False)
    jurisdiction = Column(String(50), default="Buenos Aires")
    regime = Column(String(30), default="CM")  # CM = Convenio Multilateral
    base_imponible = Column(Float, default=0)
    alicuota = Column(Float, default=0)
    impuesto = Column(Float, default=0)
    retenciones = Column(Float, default=0)
    percepciones = Column(Float, default=0)
    saldo = Column(Float, default=0)
    filed = Column(Boolean, default=False)
    filed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="ingresos_brutos")


class RetencionPercepcion(Base):
    """Retenciones y percepciones sufridas por un cliente (Mis Retenciones de ARCA).

    Alimentado por la automatizacion `mis-retenciones` via AFIP SDK.
    Clave para R-05: resolver la col. AB (Otros Tributos) del archivo de Mis Comprobantes Recibidos.
    """
    __tablename__ = "retenciones_percepciones"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    period = Column(String(7), nullable=False, index=True)  # YYYY-MM

    # Datos crudos del response de AFIP SDK
    cuit_agente = Column(String(13), index=True)             # cuitAgenteRetencion
    impuesto_retenido = Column(Integer)                      # 217=IVA, 11=Ganancias(ret), 10=Ganancias(perc), 767=BP
    codigo_regimen = Column(Integer)                         # p.ej. 596
    tipo_operacion = Column(String(20))                      # PERCEPCION / RETENCION
    fecha_retencion = Column(Date, nullable=False, index=True)
    fecha_comprobante = Column(Date)
    importe = Column(Float, nullable=False)
    numero_certificado = Column(String(50))
    numero_comprobante = Column(String(50))
    descripcion_comprobante = Column(String(100))

    # Clasificacion
    codigo_holistor = Column(String(10))                     # PIVC / PGAN / PIBA / OTRO

    # Trazabilidad del job AFIP SDK que trajo este registro
    sdk_job_id = Column(String(64))
    synced_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="retenciones_percepciones")
    # FK hacia el comprobante cruzado (se llena por el endpoint /retenciones/cruce)
    comprobante_id = Column(Integer, ForeignKey("comprobantes_recibidos.id"), nullable=True)
    comprobante = relationship("ComprobanteRecibido", back_populates="retenciones", foreign_keys=[comprobante_id])


class ComprobanteRecibido(Base):
    """Comprobantes recibidos por un cliente (Mis Comprobantes de ARCA, t=R).

    Alimentado por la automatizacion `mis-comprobantes` via AFIP SDK.
    Clave para R-05: cruzar con RetencionPercepcion por cuit_emisor+fecha+importe.
    """
    __tablename__ = "comprobantes_recibidos"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    period = Column(String(7), nullable=False, index=True)  # YYYY-MM

    # Campos crudos normalizados del response AFIP SDK
    fecha_emision = Column(Date, nullable=False, index=True)
    tipo_comprobante = Column(String(5))                   # "1", "6", "11"...
    punto_venta = Column(String(5))
    numero_desde = Column(String(20))
    numero_hasta = Column(String(20))
    cod_autorizacion = Column(String(20), index=True)       # CAE
    # Emisor: quien emite la factura y aplica la percepción (= cuit_agente en Mis Retenciones)
    tipo_doc_emisor = Column(String(5))
    nro_doc_emisor = Column(String(13), index=True)         # CUIT del emisor/agente
    denominacion_emisor = Column(String(200))
    # Receptor: nuestro cliente (El Alba)
    tipo_doc_receptor = Column(String(5))
    nro_doc_receptor = Column(String(13), index=True)
    moneda = Column(String(5), default="PES")
    tipo_cambio = Column(Float, default=1.0)
    imp_neto_gravado = Column(Float, default=0)
    imp_neto_no_gravado = Column(Float, default=0)
    imp_op_exentas = Column(Float, default=0)
    otros_tributos = Column(Float, default=0)               # col AB Holistor — a cruzar
    iva = Column(Float, default=0)                          # Total IVA (suma de alicuotas)
    imp_total = Column(Float, default=0)

    # Trazabilidad
    sdk_job_id = Column(String(64))
    synced_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="comprobantes_recibidos")
    retenciones = relationship("RetencionPercepcion", back_populates="comprobante",
                               foreign_keys="RetencionPercepcion.comprobante_id")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    action_type = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="action_logs")
    client = relationship("Client", back_populates="action_logs")
    task = relationship("Task", back_populates="action_logs")


class MovimientoCuentaCorriente(Base):
    __tablename__ = "movimientos_cc"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(20), nullable=False) # 'ingreso' or 'egreso'
    monto = Column(Float, nullable=False)
    concepto = Column(String(255), nullable=False)
    fecha = Column(Date, nullable=False)
    notas = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="movimientos_cc")
