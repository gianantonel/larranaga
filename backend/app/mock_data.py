"""
Script para poblar la base de datos con datos de prueba realistas
para el estudio contable y legal Larrañaga.
"""
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import random
from .models import (
    User, Client, ClientCollaborator, Task, Subtask,
    IVARecord, Invoice, IngresosBrutos, ActionLog,
    UserRole, UserStatus, TaskType, TaskStatus, InvoiceType,
    Profesional, TipoProfesional, ProductoReferencia, HistorialPrecioProducto,
    TipoHonorario, FeatureFlag,
    Liquidacion, PagoProfesional, Honorario, MovimientoCuentaCorriente,
    ReintegroGasto,
)
from .security import get_password_hash, encrypt_credential
from .database import SessionLocal, engine, Base


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(User).count() > 0:
        db.close()
        print("Base de datos ya tiene datos. Omitiendo seed.")
        return

    print("Poblando base de datos con datos de prueba...")

    # ─── Usuarios ────────────────────────────────────────────────────────────

    admins = [
        User(name="Optimizar", last_name="AI", email="optimizar.ai@gmail.com",
             password_hash=get_password_hash("optimizar123"), role=UserRole.super_admin,
             status=UserStatus.active, avatar_initials="OP"),
        User(name="Gian", last_name="Antonel", email="gianantonel@gmail.com",
             password_hash=get_password_hash("admin123"), role=UserRole.super_admin,
             status=UserStatus.active, avatar_initials="GA"),
        User(name="Federico", last_name="Rodriguez", email="rodriguezfederico765@gmail.com",
             password_hash=get_password_hash("admin123"), role=UserRole.super_admin,
             status=UserStatus.active, avatar_initials="FR"),
        User(name="Gero", last_name="Gambuli", email="gerogambuli2002@gmail.com",
             password_hash=get_password_hash("admin123"), role=UserRole.super_admin,
             status=UserStatus.active, avatar_initials="GG"),
    ]

    collaborators = [
        User(name="María", last_name="González", email="mgonzalez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.colaborador,
             status=UserStatus.active, avatar_initials="MG"),
        User(name="Carlos", last_name="Rodríguez", email="crodriguez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.colaborador,
             status=UserStatus.active, avatar_initials="CR"),
        User(name="Ana", last_name="Martínez", email="amartinez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.colaborador,
             status=UserStatus.active, avatar_initials="AM"),
        User(name="Diego", last_name="Fernández", email="dfernandez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.colaborador,
             status=UserStatus.active, avatar_initials="DF"),
        User(name="Laura", last_name="Sánchez", email="lsanchez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.colaborador,
             status=UserStatus.active, avatar_initials="LS"),
        User(name="Roberto", last_name="Gómez", email="rgomez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.colaborador,
             status=UserStatus.active, avatar_initials="RG"),
        User(name="Patricia", last_name="Torres", email="ptorres@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.colaborador,
             status=UserStatus.active, avatar_initials="PT"),
        User(name="Sebastián", last_name="Morales", email="smorales@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.colaborador,
             status=UserStatus.active, avatar_initials="SM"),
    ]

    for u in admins + collaborators:
        db.add(u)
    db.commit()
    for u in admins + collaborators:
        db.refresh(u)

    # ─── Clientes ─────────────────────────────────────────────────────────────

    clients_data = [
        {
            "name": "Restaurante El Gaucho",
            "business_name": "El Gaucho SRL",
            "cuit": "30-71234567-8",
            "clave_fiscal": "GauchoRest2024!",
            "address": "Av. Corrientes 1234, CABA",
            "phone": "+54 11 4567-8901",
            "email": "admin@elgaucho.com.ar",
            "category": "Gastronomía",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "561011",
        },
        {
            "name": "Farmacia del Centro",
            "business_name": "Farmacia del Centro SA",
            "cuit": "30-68901234-5",
            "clave_fiscal": "Farmacia2024#",
            "address": "San Martín 567, Rosario",
            "phone": "+54 341 234-5678",
            "email": "contable@farmaciadel centro.com.ar",
            "category": "Farmacia",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "477110",
        },
        {
            "name": "Consultora TechBA",
            "business_name": "TechBA SRL",
            "cuit": "30-72345678-9",
            "clave_fiscal": "TechBA_2024$",
            "address": "Av. del Libertador 8000, CABA",
            "phone": "+54 11 5678-9012",
            "email": "finanzas@techba.com.ar",
            "category": "Tecnología",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "620100",
        },
        {
            "name": "Hotel Patagonia",
            "business_name": "Hotel Patagonia SA",
            "cuit": "30-65432198-7",
            "clave_fiscal": "Patagonia!2024",
            "address": "Av. San Martín 200, Bariloche",
            "phone": "+54 2944 42-1234",
            "email": "admin@hotelpatagonia.com.ar",
            "category": "Hotelería",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "551011",
        },
        {
            "name": "Comercio García",
            "business_name": "Comercio Familiar García",
            "cuit": "20-28765432-6",
            "clave_fiscal": "Garcia_123",
            "address": "Belgrano 890, La Plata",
            "phone": "+54 221 456-7890",
            "email": "garcia.comercio@gmail.com",
            "category": "Comercio",
            "fiscal_condition": "Monotributo",
            "activity_code": "471900",
        },
        {
            "name": "Distribuidora Norte",
            "business_name": "Distribuidora Norte SA",
            "cuit": "30-71987654-3",
            "clave_fiscal": "DistNorte2024@",
            "address": "Ruta 9 km 450, Tucumán",
            "phone": "+54 381 567-8901",
            "email": "contabilidad@distnorte.com.ar",
            "category": "Distribución",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "462000",
        },
        {
            "name": "Estudio Arq. López",
            "business_name": "Estudio Arquitectura López",
            "cuit": "27-31234567-4",
            "clave_fiscal": "Lopez_Arq2024",
            "address": "Florida 123, CABA",
            "phone": "+54 11 3456-7890",
            "email": "estudiol opez@arq.com.ar",
            "category": "Profesional",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "711100",
        },
        {
            "name": "Panadería San Martín",
            "business_name": "Panadería San Martín",
            "cuit": "20-25678901-2",
            "clave_fiscal": "Pan123!",
            "address": "San Martín 45, Mar del Plata",
            "phone": "+54 223 234-5678",
            "email": "pansanmartin@gmail.com",
            "category": "Alimentación",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "107220",
        },
        {
            "name": "Constructora Pampas",
            "business_name": "Constructora Pampas SA",
            "cuit": "30-69876543-1",
            "clave_fiscal": "Pampas2024!!",
            "address": "Pellegrini 1500, Córdoba",
            "phone": "+54 351 678-9012",
            "email": "admin@constructorapampas.com.ar",
            "category": "Construcción",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "410001",
        },
        {
            "name": "Logística del Sur",
            "business_name": "Empresa Logística del Sur SRL",
            "cuit": "30-73456789-0",
            "clave_fiscal": "LogSur!2024",
            "address": "Av. Independencia 3000, CABA",
            "phone": "+54 11 6789-0123",
            "email": "ops@logisticadelsur.com.ar",
            "category": "Logística",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": "494000",
        },
        {
            "name": "Gianfranco Esteban Antonel",
            "business_name": "Gianfranco Esteban Antonel",
            "cuit": "23-34689789-9",
            "clave_fiscal": None,
            "address": None,
            "phone": None,
            "email": None,
            "category": "Monotributista",
            "fiscal_condition": "Monotributista Profesional",
            "activity_code": None,
        },
        {
            "name": "Agropecuaria El Alba S.R.L.",
            "business_name": "Agropecuaria El Alba S.R.L.",
            "cuit": "23-31134894-9",
            "clave_fiscal": None,
            "address": None,
            "phone": None,
            "email": None,
            "category": "Agropecuario",
            "fiscal_condition": "Responsable Inscripto",
            "activity_code": None,
        },
    ]

    clients = []
    for cd in clients_data:
        clave = cd.get("clave_fiscal")
        client = Client(
            name=cd["name"],
            business_name=cd["business_name"],
            cuit=cd["cuit"],
            clave_fiscal_encrypted=encrypt_credential(clave) if clave else None,
            address=cd["address"],
            phone=cd["phone"],
            email=cd["email"],
            category=cd["category"],
            fiscal_condition=cd["fiscal_condition"],
            activity_code=cd["activity_code"],
        )
        db.add(client)
        clients.append(client)
    db.commit()
    for c in clients:
        db.refresh(c)

    # ─── Asignaciones Colaborador → Cliente ──────────────────────────────────

    assignments = [
        (clients[0].id, collaborators[0].id),   # Gaucho → María
        (clients[0].id, collaborators[1].id),   # Gaucho → Carlos
        (clients[1].id, collaborators[0].id),   # Farmacia → María
        (clients[2].id, collaborators[2].id),   # TechBA → Ana
        (clients[3].id, collaborators[1].id),   # Hotel → Carlos
        (clients[4].id, collaborators[3].id),   # García → Diego
        (clients[5].id, collaborators[2].id),   # Distribuidora → Ana
        (clients[5].id, collaborators[4].id),   # Distribuidora → Laura
        (clients[6].id, collaborators[3].id),   # López → Diego
        (clients[7].id, collaborators[4].id),   # Panadería → Laura
        (clients[8].id, collaborators[0].id),   # Constructora → María
        (clients[9].id, collaborators[1].id),   # Logística → Carlos
        (clients[9].id, collaborators[2].id),   # Logística → Ana
    ]

    for client_id, collab_id in assignments:
        db.add(ClientCollaborator(
            client_id=client_id,
            collaborator_id=collab_id,
            assigned_by_id=admins[0].id
        ))
    db.commit()

    # ─── Registros IVA (12 meses) ─────────────────────────────────────────────

    iva_base = [
        # (ventas_gravadas_base, compras_gravadas_base)
        (850000, 420000),   # Gaucho
        (1200000, 680000),  # Farmacia
        (2500000, 900000),  # TechBA
        (3800000, 1200000), # Hotel
        (180000, 95000),    # García
        (5200000, 3100000), # Distribuidora
        (450000, 120000),   # López
        (320000, 180000),   # Panadería
        (4500000, 3200000), # Constructora
        (6800000, 4500000), # Logística
        (250000, 80000),    # Gianfranco Antonel (monotributista)
        (1500000, 700000),  # Agropecuaria El Alba
    ]

    for i, client in enumerate(clients):
        # Si hay más clientes que entries en iva_base, repetimos un default
        vg_base, cg_base = iva_base[i] if i < len(iva_base) else (500000, 200000)
        saldo_anterior = 0
        for m in range(12, 0, -1):
            period_date = date.today().replace(day=1) - timedelta(days=30 * m)
            period = period_date.strftime("%Y-%m")
            variation = random.uniform(0.8, 1.3)
            vg = round(vg_base * variation, 2)
            cg = round(cg_base * variation, 2)
            debito = round(vg * 0.21, 2)
            credito = round(cg * 0.21, 2)
            saldo = round(debito - credito - saldo_anterior, 2)
            filed = m > 2  # últimos 2 meses sin presentar

            rec = IVARecord(
                client_id=client.id,
                period=period,
                ventas_gravadas=vg,
                ventas_exentas=round(vg * 0.05, 2),
                ventas_no_gravadas=round(vg * 0.02, 2),
                debito_fiscal=debito,
                compras_gravadas=cg,
                compras_exentas=round(cg * 0.03, 2),
                compras_no_gravadas=round(cg * 0.01, 2),
                credito_fiscal=credito,
                saldo_a_favor_anterior=saldo_anterior if saldo_anterior > 0 else 0,
                saldo=max(saldo, 0),
                filed=filed,
                filed_at=datetime(period_date.year, period_date.month, 20) if filed else None,
                due_date=date(period_date.year, period_date.month, 20),
            )
            db.add(rec)
            saldo_anterior = abs(min(saldo, 0))  # carry forward if in favor

    db.commit()

    # ─── Facturas (histórico 12 meses) ───────────────────────────────────────

    receptor_cuits = [
        ("20-12345678-9", "Juan Pérez"),
        ("30-98765432-1", "Empresa ABC SA"),
        ("27-23456789-3", "María García"),
        ("30-11223344-5", "Comercio XYZ SRL"),
        ("20-34567890-2", "Roberto López"),
    ]

    for i, client in enumerate(clients):
        vg_base, _ = iva_base[i]
        invoice_count = 0
        for m in range(12, 0, -1):
            period_date = date.today().replace(day=1) - timedelta(days=30 * m)
            # Between 3-15 invoices per month per client
            n_invoices = random.randint(3, 15)
            for _ in range(n_invoices):
                inv_day = random.randint(1, 28)
                inv_date = date(period_date.year, period_date.month, inv_day)
                neto = round(random.uniform(vg_base * 0.03, vg_base * 0.2), 2)
                iva = round(neto * 0.21, 2)
                total = neto + iva
                receptor = random.choice(receptor_cuits)
                inv_type = InvoiceType.A if client.fiscal_condition == "Responsable Inscripto" else InvoiceType.B
                invoice_count += 1
                db.add(Invoice(
                    client_id=client.id,
                    collaborator_id=random.choice(collaborators).id,
                    invoice_type=inv_type,
                    punto_venta=1,
                    number=invoice_count,
                    date=inv_date,
                    receptor_cuit=receptor[0],
                    receptor_name=receptor[1],
                    concept="Servicios" if client.category in ["Tecnología", "Profesional"] else "Productos",
                    neto_gravado=neto,
                    iva_21=iva,
                    total=total,
                    cae="".join([str(random.randint(0, 9)) for _ in range(14)]),
                    status="emitida"
                ))
    db.commit()

    # ─── Ingresos Brutos ─────────────────────────────────────────────────────

    for i, client in enumerate(clients[:7]):  # Only first 7 clients
        vg_base, _ = iva_base[i]
        for m in range(12, 0, -1):
            period_date = date.today().replace(day=1) - timedelta(days=30 * m)
            period = period_date.strftime("%Y-%m")
            base = round(vg_base * random.uniform(0.9, 1.1), 2)
            alicuota = random.choice([0.02, 0.03, 0.035, 0.05])
            impuesto = round(base * alicuota, 2)
            ret = round(impuesto * 0.1, 2)
            saldo = round(impuesto - ret, 2)
            db.add(IngresosBrutos(
                client_id=client.id,
                period=period,
                jurisdiction="Buenos Aires" if i % 2 == 0 else "CABA",
                regime="CM",
                base_imponible=base,
                alicuota=alicuota * 100,
                impuesto=impuesto,
                retenciones=ret,
                percepciones=0,
                saldo=saldo,
                filed=m > 2,
                filed_at=datetime(period_date.year, period_date.month, 15) if m > 2 else None,
            ))
    db.commit()

    # ─── Tareas ──────────────────────────────────────────────────────────────

    task_templates = [
        (TaskType.ddjj_iva, "Presentación DDJJ IVA"),
        (TaskType.facturacion, "Facturación mensual"),
        (TaskType.ingresos_brutos, "Declaración Ingresos Brutos"),
        (TaskType.ddjj_ganancias, "DDJJ Ganancias anual"),
        (TaskType.comprobantes, "Generación comprobantes en línea"),
        (TaskType.legal, "Revisión contrato proveedor"),
    ]

    statuses = [
        TaskStatus.terminada, TaskStatus.terminada, TaskStatus.terminada,
        TaskStatus.en_curso, TaskStatus.pendiente, TaskStatus.bloqueada, TaskStatus.postergada
    ]

    for i, client in enumerate(clients):
        collab = collaborators[i % len(collaborators)]
        for j, (ttype, ttitle) in enumerate(task_templates):
            for m in range(6, 0, -1):
                period_date = date.today().replace(day=1) - timedelta(days=30 * m)
                period = period_date.strftime("%Y-%m")
                st = random.choice(statuses)
                due = date(period_date.year, period_date.month, 20)
                blocker = "Falta documentación del cliente" if st == TaskStatus.bloqueada else None

                task = Task(
                    title=f"{ttitle} - {period}",
                    description=f"Tarea de {ttitle.lower()} para el período {period}.",
                    task_type=ttype,
                    status=st,
                    client_id=client.id,
                    collaborator_id=collab.id,
                    period=period,
                    due_date=due,
                    blocker_comment=blocker,
                    completed_at=datetime(period_date.year, period_date.month, 18) if st == TaskStatus.terminada else None,
                    created_at=datetime(period_date.year, period_date.month, 1),
                )
                db.add(task)
                db.flush()

                # Subtasks
                subtask_templates = {
                    TaskType.ddjj_iva: [
                        "Recopilar libro IVA Ventas",
                        "Recopilar libro IVA Compras",
                        "Verificar comprobantes",
                        "Cargar datos en ARCA",
                        "Presentar declaración",
                        "Obtener acuse de recibo",
                    ],
                    TaskType.facturacion: [
                        "Revisar planilla de facturación",
                        "Verificar datos receptores",
                        "Emitir facturas en ARCA",
                        "Enviar facturas al cliente",
                    ],
                    TaskType.ingresos_brutos: [
                        "Calcular base imponible",
                        "Aplicar alícuotas",
                        "Verificar retenciones",
                        "Presentar en ARBA/AGIP",
                    ],
                    TaskType.comprobantes: [
                        "Verificar habilitación",
                        "Generar comprobantes",
                        "Descargar XML/PDF",
                    ],
                    TaskType.legal: [
                        "Revisar documentación",
                        "Análisis legal",
                        "Redactar escrito",
                        "Presentar ante organismo",
                    ],
                }
                subtask_list = subtask_templates.get(ttype, ["Paso 1", "Paso 2", "Paso 3"])
                for k, stitle in enumerate(subtask_list):
                    sub_st = TaskStatus.terminada if st == TaskStatus.terminada else (
                        TaskStatus.terminada if k < len(subtask_list) // 2 and st == TaskStatus.en_curso
                        else TaskStatus.pendiente
                    )
                    db.add(Subtask(
                        task_id=task.id,
                        title=stitle,
                        status=sub_st,
                        comment="Completado." if sub_st == TaskStatus.terminada else None,
                        created_at=datetime(period_date.year, period_date.month, 1),
                    ))

    db.commit()

    # ─── Action Logs ─────────────────────────────────────────────────────────

    action_types = [
        "task_created", "task_updated", "iva_filed",
        "invoice_created", "client_updated", "collaborator_assigned"
    ]

    for _ in range(100):
        days_ago = random.randint(0, 180)
        log_date = datetime.utcnow() - timedelta(days=days_ago)
        collab = random.choice(collaborators)
        client = random.choice(clients)
        action = random.choice(action_types)
        descriptions = {
            "task_created": f"Tarea creada para {client.name}",
            "task_updated": f"Estado de tarea actualizado",
            "iva_filed": f"DDJJ IVA presentada para {client.name}",
            "invoice_created": f"Factura emitida para {client.name}",
            "client_updated": f"Datos de {client.name} actualizados",
            "collaborator_assigned": f"{collab.name} asignado a {client.name}",
        }
        db.add(ActionLog(
            user_id=collab.id,
            client_id=client.id,
            action_type=action,
            description=descriptions[action],
            created_at=log_date,
        ))
    db.commit()

    db.close()

    print("[OK] Base de datos poblada correctamente con datos de prueba.")
    print("OK - Base de datos poblada correctamente con datos de prueba.")
    print("  Administradores (contraseña: admin123):")
    print("    admin1@larranaga.com")
    print("    admin2@larranaga.com")
    print("    admin3@larranaga.com")
    print("  Colaboradores (contraseña: colab123):")
    print("    mgonzalez@larranaga.com   — María González")
    print("    crodriguez@larranaga.com  — Carlos Rodríguez")
    print("    amartinez@larranaga.com   — Ana Martínez")
    print("    dfernandez@larranaga.com  — Diego Fernández")
    print("    lsanchez@larranaga.com    — Laura Sánchez")
    print("    rgomez@larranaga.com      — Roberto Gómez")
    print("    ptorres@larranaga.com     — Patricia Torres")
    print("    smorales@larranaga.com    — Sebastián Morales")


# Catálogo base de productos de referencia (idempotente por nombre).
# fuente_precio: None = manual; 'bcr_*' = precio del día de la Bolsa de Rosario.
_PRODUCTOS_BASE = [
    # (nombre,               unidad,     precio,    vigente_desde,   fuente_precio)
    ("Bolsa de cemento",     "bolsa",    4600.0,    date(2026, 4, 1), None),
    ("Kilo de carne",        "kg",       8500.0,    date(2026, 6, 1), None),
    ("Litro de leche",       "litro",    1200.0,    date(2026, 6, 1), None),
    # Granos con precio del día vinculado a la pizarra de la Bolsa de Rosario
    ("Soja (tonelada)",      "tonelada", 475000.0,  date(2026, 6, 1), "bcr_soja"),
    ("Maíz (tonelada)",      "tonelada", 264400.0,  date(2026, 6, 1), "bcr_maiz"),
    ("Trigo (tonelada)",     "tonelada", 292390.0,  date(2026, 6, 1), "bcr_trigo"),
]


def seed_productos_referencia():
    """Seed idempotente del catálogo base de productos de referencia.

    Crea cada producto SOLO si no existe otro con el mismo nombre (junto con su
    HistorialPrecioProducto inicial). Es independiente del seed de profesionales:
    `seed_profesionales_y_productos` corta apenas detecta profesionales existentes,
    así que en entornos ya inicializados (prod) nunca regenera el producto si falta.
    Este seed cierra ese hueco y es seguro de correr en cada arranque."""
    db = SessionLocal()
    try:
        creados = 0
        for nombre, unidad, precio, desde, fuente in _PRODUCTOS_BASE:
            if db.query(ProductoReferencia).filter(ProductoReferencia.nombre == nombre).first():
                continue
            prod = ProductoReferencia(nombre=nombre, unidad=unidad, precio_vigente=precio,
                                      fuente_precio=fuente)
            db.add(prod)
            db.flush()
            db.add(HistorialPrecioProducto(producto_id=prod.id, precio=precio, vigente_desde=desde))
            creados += 1
        if creados:
            db.commit()
            print(f"[OK] Productos de referencia: {creados} creados (catálogo base).")
    finally:
        db.close()


def seed_profesionales_y_productos():
    """Seed idempotente para R-03/R-04. Se ejecuta sobre la DB existente sin borrarla."""
    db = SessionLocal()

    if db.query(Profesional).count() > 0:
        db.close()
        return

    print("Agregando profesionales y productos de referencia (R-03/R-04)...")

    # Profesionales del estudio
    rodrigo  = Profesional(nombre="Rodrigo Larrañaga", tipo=TipoProfesional.socio)
    manuel   = Profesional(nombre="Manuel Larrañaga",  tipo=TipoProfesional.socio)
    marisol  = Profesional(nombre="Marisol Borrego",   tipo=TipoProfesional.socio)
    silvana  = Profesional(nombre="Silvana Gómez",     tipo=TipoProfesional.profesional)
    stefi    = Profesional(nombre="Stefania Vicente",  tipo=TipoProfesional.profesional)
    mariana  = Profesional(nombre="Mariana Ruiz",      tipo=TipoProfesional.profesional)

    for p in [rodrigo, manuel, marisol, silvana, stefi, mariana]:
        db.add(p)
    db.commit()
    for p in [rodrigo, manuel, marisol, silvana, stefi, mariana]:
        db.refresh(p)

    # Producto de referencia: bolsa de cemento (para clientes constructoras).
    # Ya sembrado por seed_productos_referencia (corre antes); lo buscamos para no duplicar.
    cemento = db.query(ProductoReferencia).filter(
        ProductoReferencia.nombre == "Bolsa de cemento"
    ).first()
    if cemento is None:
        cemento = ProductoReferencia(nombre="Bolsa de cemento", unidad="bolsa", precio_vigente=4600.0)
        db.add(cemento)
        db.commit()
        db.refresh(cemento)
        db.add(HistorialPrecioProducto(
            producto_id=cemento.id, precio=4600.0, vigente_desde=date(2026, 4, 1)
        ))
        db.commit()

    # Configurar honorarios en los clientes existentes (toma los primeros activos por orden de ID)
    existing_clients = (
        db.query(Client)
        .filter(Client.is_active == True, Client.tipo_honorario == None)
        .order_by(Client.id)
        .all()
    )

    configs = [
        # (tipo,       importe_fijo, prod,    unidades, profesional)
        ("fijo",       850000.0,     None,    None,     silvana),
        ("fijo",       1200000.0,    None,    None,     stefi),
        ("fijo",       2500000.0,    None,    None,     mariana),
        ("fijo",       3800000.0,    None,    None,     rodrigo),
        ("fijo",       180000.0,     None,    None,     marisol),
        ("fijo",       950000.0,     None,    None,     silvana),
        ("fijo",       430000.0,     None,    None,     stefi),
        ("fijo",       680000.0,     None,    None,     mariana),
        ("producto",   None,         cemento, 50.0,     rodrigo),
        ("fijo",       760000.0,     None,    None,     manuel),
    ]

    for client, (tipo, importe, prod, unidades, prof) in zip(existing_clients, configs):
        client.tipo_honorario = TipoHonorario.fijo if tipo == "fijo" else TipoHonorario.producto
        client.importe_honorario = importe
        client.producto_ref_id = prod.id if prod else None
        client.cantidad_unidades = unidades
        client.profesional_id = prof.id

    db.commit()
    db.close()
    print(f"[OK] R-03/R-04: {len([rodrigo, manuel, marisol, silvana, stefi, mariana])} profesionales y 1 producto de referencia creados.")


_NOMBRES = [
    "Juan", "María", "Carlos", "Ana", "Lucas", "Sofía", "Diego", "Valentina",
    "Martín", "Camila", "Jorge", "Florencia", "Pablo", "Julieta", "Gabriel",
    "Rocío", "Federico", "Agustina", "Nicolás", "Micaela", "Tomás", "Brenda",
    "Ezequiel", "Carla", "Matías", "Daniela", "Hernán", "Paula", "Sergio", "Lorena",
]
_APELLIDOS = [
    "Gómez", "Fernández", "Rodríguez", "López", "Martínez", "García", "Pérez",
    "Sánchez", "Romero", "Díaz", "Álvarez", "Torres", "Ruiz", "Ramírez", "Flores",
    "Benítez", "Acosta", "Medina", "Herrera", "Aguirre", "Suárez", "Molina",
    "Castro", "Ortiz", "Núñez", "Rojas", "Cabrera", "Vega", "Ledesma", "Ferreyra",
]


def _cuil(rng: random.Random) -> str:
    """Genera un CUIL plausible con formato XX-XXXXXXXX-X."""
    prefijo = rng.choice([20, 23, 24, 27])
    dni = rng.randint(10_000_000, 45_000_000)
    verif = rng.randint(0, 9)
    return f"{prefijo}-{dni:08d}-{verif}"


def _periodos_recientes(n: int) -> list:
    """[mes_actual, mes-1, ..., mes-(n-1)] como 'YYYY-MM' (más nuevo primero)."""
    y, m = date.today().year, date.today().month
    out = []
    for _ in range(n):
        out.append(f"{y}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return out


def _calc_honorario_cliente(c: Client, db: Session):
    """(importe, precio_snapshot) según la config del cliente. (None, None) si no configurado."""
    if c.tipo_honorario == TipoHonorario.fijo and c.importe_honorario:
        return float(c.importe_honorario), None
    if c.tipo_honorario == TipoHonorario.producto and c.producto_ref_id and c.cantidad_unidades:
        prod = db.get(ProductoReferencia, c.producto_ref_id)
        if prod:
            return round(float(c.cantidad_unidades) * float(prod.precio_vigente), 2), prod.precio_vigente
    return None, None


def seed_simulacion_pagos():
    """Data fake con HISTORIAL de varios meses (idempotente por entidad/período).

    Por cada uno de los últimos meses siembra:
      - Honorarios (R-03) de los clientes configurados (para que las liquidaciones de
        profesionales tengan total a cobrar histórico).
      - Liquidaciones + pagos de profesionales (Liquidaciones), con mezcla de
        estados. Los meses pasados quedan mayormente pagados; el mes actual es
        una mezcla pagado/parcial/sin liquidar."""
    db = SessionLocal()
    try:
        rng = random.Random(7)
        periodos = _periodos_recientes(5)        # mes actual + 4 anteriores
        actual = periodos[0]

        def _fecha(per):
            yy, mm = int(per[:4]), int(per[5:7])
            return date(yy, mm, rng.randint(1, 26))

        def _estado_roll(per):
            """(omitir, full): meses pasados casi todo pagado; mes actual, mezcla."""
            roll = rng.random()
            if per == actual:
                return (roll < 0.35), (roll < 0.7)
            return (roll < 0.10), (roll < 0.85)

        # ── 0) Honorarios (R-03) por período ─────────────────────────────────
        clientes = db.query(Client).filter(
            Client.is_active == True, Client.tipo_honorario.isnot(None),   # noqa: E712
        ).all()
        for per in periodos:
            for c in clientes:
                if db.query(Honorario).filter(Honorario.client_id == c.id, Honorario.period == per).first():
                    continue
                importe, snap = _calc_honorario_cliente(c, db)
                if importe is None:
                    continue
                db.add(Honorario(client_id=c.id, period=per, importe=importe,
                                 tipo=c.tipo_honorario.value, precio_producto_snapshot=snap))
        db.commit()

        # ── Profesionales (Liquidaciones) ────────────────────────────────────
        from .services import liquidacion as liqsvc
        profs = db.query(Profesional).filter(Profesional.activo == True).order_by(Profesional.id).all()  # noqa: E712
        for per in periodos:
            for p in profs:
                liq = db.query(Liquidacion).filter(
                    Liquidacion.profesional_id == p.id, Liquidacion.period == per,
                ).first()
                if liq and liq.pagos:
                    continue
                try:
                    preview = liqsvc.calcular_preview(db, p.id, per)
                except Exception:
                    continue
                total = preview.total_a_cobrar
                if total <= 0:
                    continue
                omitir, full = _estado_roll(per)
                if omitir:
                    continue
                if not liq:
                    liq = Liquidacion(profesional_id=p.id, period=per)
                    db.add(liq)
                    db.flush()
                medio = rng.choice(["transferencia", "efectivo"])
                liq.medio_pago = medio
                monto = round(total, 2) if full else round(total * rng.choice([0.3, 0.4, 0.5]), 2)
                db.add(PagoProfesional(liquidacion_id=liq.id, monto=monto, medio_pago=medio, fecha=_fecha(per)))
        db.commit()
        print(f"[OK] Simulación con historial generada ({len(periodos)} meses).")
    finally:
        db.close()


def seed_movimientos_cc_fake():
    """Data fake de R-07 (Cuentas Corrientes) para visualizar la Fase A: cobros con
    'mes que se cobra', forma de pago, y adelantos por transferencia a profesionales.

    Idempotente: marca sus movimientos con notas que empiezan en '[seed-r07]' y no
    vuelve a sembrar si ya existe alguno."""
    db = SessionLocal()
    try:
        ya = (
            db.query(MovimientoCuentaCorriente)
            .filter(MovimientoCuentaCorriente.notas.like("[seed-r07]%"))
            .first()
        )
        if ya:
            db.close()
            return

        rng = random.Random(707)
        periodos = _periodos_recientes(3)  # mes actual + 2 anteriores

        def _fecha(per):
            yy, mm = int(per[:4]), int(per[5:7])
            return date(yy, mm, rng.randint(2, 26))

        # Clientes con profesional a cargo → el adelanto por transferencia tiene sentido
        clientes = (
            db.query(Client)
            .filter(Client.is_active == True, Client.profesional_id.isnot(None))  # noqa: E712
            .order_by(Client.id)
            .limit(6)
            .all()
        )
        if not clientes:
            db.close()
            return

        total = 0
        for c in clientes:
            base = float(c.importe_honorario or rng.randint(300, 1500) * 1000)
            for per in periodos:
                # 1) Cargo de honorarios del mes (egreso = deuda del cliente)
                db.add(MovimientoCuentaCorriente(
                    client_id=c.id, tipo="egreso", monto=round(base, 2),
                    concepto=f"Honorarios {per}", fecha=_fecha(per),
                    periodo_honorario=per, notas="[seed-r07] cargo",
                ))
                total += 1

                # 2) Cobro del mes: ~55% transferencia (adelanto al profesional), resto efectivo
                if rng.random() < 0.85:  # no todos los meses están cobrados
                    if rng.random() < 0.55:
                        db.add(MovimientoCuentaCorriente(
                            client_id=c.id, tipo="ingreso", monto=round(base, 2),
                            concepto=f"Cobro honorarios {per} (transf.)", fecha=_fecha(per),
                            periodo_honorario=per, forma_pago="transferencia",
                            profesional_id=c.profesional_id,
                            notas="[seed-r07] cobro transferencia (adelanto)",
                        ))
                    else:
                        db.add(MovimientoCuentaCorriente(
                            client_id=c.id, tipo="ingreso", monto=round(base, 2),
                            concepto=f"Cobro honorarios {per} (efectivo)", fecha=_fecha(per),
                            periodo_honorario=per, forma_pago="efectivo",
                            notas="[seed-r07] cobro efectivo",
                        ))
                    total += 1

        # Ejemplo en USD: cobro por transferencia en dólares (adelanto al profesional)
        c0 = clientes[0]
        per0 = periodos[0]
        db.add(MovimientoCuentaCorriente(
            client_id=c0.id, tipo="ingreso", monto=1500.0, moneda="USD", cotizacion=1180.0,
            concepto=f"Cobro honorarios {per0} (USD, transf.)", fecha=_fecha(per0),
            periodo_honorario=per0, forma_pago="transferencia", profesional_id=c0.profesional_id,
            notas="[seed-r07] cobro USD (adelanto)",
        ))
        total += 1

        db.commit()
        print(f"[OK] R-07: {total} movimientos de cuenta corriente fake creados.")
    finally:
        db.close()


def limpiar_demo_transaccional(db):
    """Borra SOLO la capa transaccional del demo (respetando FKs). NO toca usuarios,
    colaboradores, clientes, profesionales, productos, IVA, facturas ni tareas."""
    db.query(PagoProfesional).delete(synchronize_session=False)
    db.query(ReintegroGasto).delete(synchronize_session=False)
    db.query(Liquidacion).delete(synchronize_session=False)
    db.query(Honorario).delete(synchronize_session=False)
    db.query(MovimientoCuentaCorriente).delete(synchronize_session=False)
    db.commit()


def _mes_es(period: str) -> str:
    meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return f"{meses[int(period[5:7])]} {period[:4]}"


def _asegurar_config_clientes(db, rng):
    """Configura honorario + profesional a los clientes activos que no lo tengan, para
    que TODOS entren en el eje del demo (Honorarios ↔ Liquidaciones ↔ CC)."""
    profs = db.query(Profesional).filter(Profesional.activo == True).order_by(Profesional.id).all()  # noqa: E712
    if not profs:
        return
    # Soja vinculada a la Bolsa de Rosario → honorario del agro sale del precio real
    soja = db.query(ProductoReferencia).filter(ProductoReferencia.fuente_precio == "bcr_soja").first()
    cemento = db.query(ProductoReferencia).filter(ProductoReferencia.nombre.ilike("%cemento%")).first()
    sin_config = (
        db.query(Client)
        .filter(Client.is_active == True, Client.tipo_honorario.is_(None))  # noqa: E712
        .order_by(Client.id).all()
    )
    for i, c in enumerate(sin_config):
        c.profesional_id = profs[i % len(profs)].id
        nom = (c.name or "").lower()
        if soja and any(k in nom for k in ("agro", "campo", "cereal", "gana", "rural")):
            c.tipo_honorario = TipoHonorario.producto
            c.producto_ref_id = soja.id
            c.cantidad_unidades = float(rng.choice([6, 8, 10, 12]))   # toneladas de soja
            c.importe_honorario = None
        elif cemento and any(k in nom for k in ("construc", "obra", "pampas")):
            c.tipo_honorario = TipoHonorario.producto
            c.producto_ref_id = cemento.id
            c.cantidad_unidades = float(rng.choice([40, 60, 80]))
            c.importe_honorario = None
        else:
            c.tipo_honorario = TipoHonorario.fijo
            c.importe_honorario = float(rng.choice([280, 350, 480, 620, 900]) * 1000)
    db.commit()


def seed_demo_dataset(db=None):
    """Genera el dataset de demo COHERENTE del eje Clientes ↔ Honorarios (R-03) ↔
    Liquidaciones (R-04) ↔ Cuentas Corrientes (R-07), centrado en el mes actual + 4
    meses de historial, con números que cuadran:

      - Honorario mensual por cliente (fijo o producto).
      - CC: cargo del honorario (egreso) + cobro (ingreso) con mezcla realista de
        estados y medios (efectivo/transferencia/cheque + algún USD). Los cobros NO en
        efectivo se imputan como ADELANTO al profesional a cargo del cliente.
      - Liquidación por profesional: honorarios_totales = suma real de honorarios de sus
        clientes; el total a cobrar (honorarios − adelantos + reintegros) sale de
        calcular_preview, y el pago (total/parcial) se registra en base a ese total.

    Idempotente por seguridad: si ya hay honorarios cargados, no hace nada (para
    regenerar de cero, correr limpiar_demo_transaccional primero)."""
    from .services import liquidacion as liqsvc
    own = db is None
    if own:
        db = SessionLocal()
    try:
        if db.query(Honorario).count() > 0:
            return
        rng = random.Random(2026)
        _asegurar_config_clientes(db, rng)

        periodos = list(reversed(_periodos_recientes(5)))  # viejo → nuevo
        demo = periodos[-1]                                 # mes actual

        def _fecha(per, lo=2, hi=26):
            yy, mm = int(per[:4]), int(per[5:7])
            return date(yy, mm, rng.randint(lo, hi))

        clientes = (
            db.query(Client)
            .filter(Client.is_active == True, Client.tipo_honorario.isnot(None))  # noqa: E712
            .order_by(Client.id).all()
        )

        for per in periodos:
            es_demo = (per == demo)
            for c in clientes:
                importe, snap = _calc_honorario_cliente(c, db)
                if not importe or importe <= 0:
                    continue
                # 1) Honorario del mes
                db.add(Honorario(client_id=c.id, period=per, importe=importe,
                                 tipo=c.tipo_honorario.value, precio_producto_snapshot=snap))
                # 2) CC — cargo del honorario (deuda del cliente)
                db.add(MovimientoCuentaCorriente(
                    client_id=c.id, tipo="egreso", monto=round(importe, 2),
                    concepto=f"Honorarios {_mes_es(per)}", fecha=_fecha(per, 1, 5),
                    periodo_honorario=per, notas="[demo] cargo honorarios"))
                # 3) CC — cobro (estado realista)
                r = rng.random()
                if es_demo:
                    modo = "full" if r < 0.45 else ("parcial" if r < 0.72 else "nada")
                else:
                    modo = "full" if r < 0.9 else "nada"
                if modo == "nada":
                    continue
                pagado = round(importe, 2) if modo == "full" else round(importe * rng.choice([0.4, 0.5, 0.6]), 2)
                fp = rng.choices(["transferencia", "efectivo", "cheque", "usd"],
                                 weights=[50, 22, 16, 12])[0]
                mov = dict(client_id=c.id, tipo="ingreso", fecha=_fecha(per, 6, 27),
                           periodo_honorario=per)
                if fp == "usd":
                    cot = float(rng.choice([1160, 1180, 1200, 1215]))
                    mov.update(monto=round(pagado / cot, 2), moneda="USD", cotizacion=cot,
                               forma_pago="transferencia", profesional_id=c.profesional_id,
                               concepto=f"Cobro honorarios {_mes_es(per)} (USD, transf.)",
                               notas="[demo] cobro USD (adelanto)")
                elif fp == "efectivo":
                    mov.update(monto=pagado, moneda="ARS", forma_pago="efectivo",
                               concepto=f"Cobro honorarios {_mes_es(per)} (efectivo)",
                               notas="[demo] cobro efectivo")
                else:  # transferencia | cheque → adelanto al profesional
                    mov.update(monto=pagado, moneda="ARS", forma_pago=fp,
                               profesional_id=c.profesional_id,
                               concepto=f"Cobro honorarios {_mes_es(per)} ({fp})",
                               notas=f"[demo] cobro {fp} (adelanto)")
                db.add(MovimientoCuentaCorriente(**mov))
            db.commit()

            # 4) Liquidaciones de los profesionales para el período
            profs = db.query(Profesional).filter(Profesional.activo == True).order_by(Profesional.id).all()  # noqa: E712
            for p in profs:
                brutos = (
                    db.query(Honorario).join(Client, Honorario.client_id == Client.id)
                    .filter(Client.profesional_id == p.id, Honorario.period == per).all()
                )
                total_brutos = sum(h.importe for h in brutos)
                if total_brutos <= 0:
                    continue
                liq = Liquidacion(profesional_id=p.id, period=per,
                                  honorarios_totales=round(total_brutos, 2))
                db.add(liq)
                db.flush()
                # Reintegro ocasional (gasto reembolsable del profesional)
                if rng.random() < 0.3:
                    concepto = rng.choice(["monotributo", "ingresos brutos", "gastos bancarios"])
                    db.add(ReintegroGasto(liquidacion_id=liq.id, concepto=concepto,
                                          importe=float(rng.choice([30, 45, 60, 90]) * 1000)))
                db.flush()
                # Total a cobrar real (honorarios − adelantos + reintegros)
                try:
                    total = liqsvc.calcular_preview(db, p.id, per).total_a_cobrar
                except Exception:
                    total = total_brutos
                if total <= 0:
                    continue
                rr = rng.random()
                if es_demo:
                    pago = total if rr < 0.4 else (round(total * 0.5, 2) if rr < 0.7 else 0)
                else:
                    pago = total if rr < 0.9 else round(total * 0.5, 2)
                if pago and pago > 0:
                    medio = rng.choice(["transferencia", "efectivo"])
                    liq.medio_pago = medio
                    db.add(PagoProfesional(liquidacion_id=liq.id, monto=round(pago, 2),
                                           medio_pago=medio, fecha=_fecha(per, 27, 28)))
            db.commit()
        print(f"[OK] Demo dataset generado: {len(periodos)} meses, {len(clientes)} clientes.")
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    seed_database()
    seed_profesionales_y_productos()
    seed_demo_dataset()


# ─── Catálogo Requisitos R-XX (Plan Maestro líneas 17-36) ─────────────────────

CATALOGO_REQUISITOS = [
    # Fase 1
    {"codigo":"R-01","fase":1,"area":"IVA","dificultad":"Muy fácil","ruta_frontend":"/herramientas","implementado":True,
     "titulo":"Corrección comprobantes tipo B/C + formato col. L",
     "descripcion":"Limpia el libro IVA compras corrigiendo tipos B/C y el formato de la columna L (tipo de cambio)."},
    {"codigo":"R-02","fase":1,"area":"IVA","dificultad":"Muy fácil","ruta_frontend":"/herramientas","implementado":True,
     "titulo":"División de comprobantes por múltiples alícuotas de IVA",
     "descripcion":"Divide cada comprobante en filas separadas por cada alícuota distinta (10.5%, 21%, 27%)."},
    {"codigo":"R-03","fase":1,"area":"ADM","dificultad":"Muy fácil","ruta_frontend":"/honorarios","implementado":True,
     "titulo":"Cálculo automático de honorarios (fijo y valor producto)",
     "descripcion":"Calcula honorario mensual por cliente, sea importe fijo o por unidades × precio de producto vigente."},
    {"codigo":"R-04","fase":1,"area":"ADM","dificultad":"Muy fácil","ruta_frontend":"/liquidaciones","implementado":True,
     "titulo":"Liquidación mensual de profesionales — cálculo automático",
     "descripcion":"Resuelve adelantos − honorarios + saldo anterior + reintegros por profesional, por mes."},
    {"codigo":"R-05","fase":1,"area":"IVA","dificultad":"Fácil","ruta_frontend":"/retenciones","implementado":True,
     "titulo":"Separación retenciones IVA vs IIBB (col. AB — Otros Tributos)",
     "descripcion":"Trae 'Mis Retenciones' desde ARCA y separa por código de régimen IVA, IIBB y Ganancias."},
    {"codigo":"R-07","fase":1,"area":"ADM","dificultad":"Fácil","ruta_frontend":"/cuentas-corrientes","implementado":True,
     "titulo":"Cuentas corrientes de clientes — registro y saldo en tiempo real",
     "descripcion":"Movimientos de cuenta corriente por cliente con saldo recalculado en cada cobro."},
    # Fase 2
    {"codigo":"R-06","fase":2,"area":"IVA","dificultad":"Fácil","ruta_frontend":"/iva","implementado":True,
     "titulo":"Conciliación IVA compras/ventas — posición IVA del mes",
     "descripcion":"Posición mensual: débito − crédito − percepciones = saldo a favor o a pagar."},
    {"codigo":"R-08","fase":2,"area":"ADM","dificultad":"Fácil","ruta_frontend":"/cobros","implementado":True,
     "titulo":"Tesorería — registro de pagos con impacto automático",
     "descripcion":"Registrar cobro impacta cuenta corriente, tesorería, liquidación profesional y caja billetes."},
    {"codigo":"R-09","fase":2,"area":"IVA","dificultad":"Media","ruta_frontend":"/maestro-proveedores","implementado":True,
     "titulo":"Imputación contable por CUIT (5 niveles)",
     "descripcion":"Maestro → padrón → reglas → IA → fallback. Asigna cuenta contable a cada proveedor."},
    {"codigo":"R-10","fase":2,"area":"IVA","dificultad":"Media","ruta_frontend":None,"implementado":True,
     "titulo":"Generación HWCRARCA completo para Holistor/Onvio",
     "descripcion":"Output final del pipeline IVA compras, validado Debe=Haber antes de escribir al disco."},
    {"codigo":"R-14","fase":2,"area":"ADM","dificultad":"Media","ruta_frontend":None,"implementado":True,
     "titulo":"Control de billetes / caja efectivo",
     "descripcion":"Seguimiento de efectivo por denominación. Integrado a R-08."},
    # Fase 3
    {"codigo":"R-11","fase":3,"area":"ADM","dificultad":"Media","ruta_frontend":"/flujo-fondos","implementado":True,
     "titulo":"Flujo de fondos — seguimiento y proyección vs real",
     "descripcion":"Mensual y anual por cliente. Detecta inconsistencias entre saldo CC y deuda calculada."},
    {"codigo":"R-12","fase":3,"area":"ADM","dificultad":"Media","ruta_frontend":"/retiros","implementado":True,
     "titulo":"Retiro de honorarios de socios — registro y control",
     "descripcion":"Triple impacto: tesorería + RetiroSocio + descuento billetes si es efectivo."},
    {"codigo":"R-13","fase":3,"area":"ADM","dificultad":"Media","ruta_frontend":"/actualizar-honorarios","implementado":True,
     "titulo":"Actualización cuatrimestral de honorarios con pantalla de validación",
     "descripcion":"Wizard de 3 pasos: preview de índice, selección de clientes, aplicación granular con historial."},
    {"codigo":"R-15","fase":3,"area":"IVA+ADM","dificultad":"Alta","ruta_frontend":"/conciliacion-bancaria","implementado":True,
     "titulo":"Conciliación bancaria — importación y matching automático",
     "descripcion":"Parsers Pampa/Santander/MP + matching IA contra movimientos contables."},
    # Fase 4
    {"codigo":"R-16","fase":4,"area":"IVA","dificultad":"Alta","ruta_frontend":None,"implementado":False,
     "titulo":"Reportes periódicos automáticos IVA-MES — 100+ clientes",
     "descripcion":"Automatización mis-comprobantes con credenciales por cliente. Pendiente Fase 4."},
    {"codigo":"R-17","fase":4,"area":"ADM","dificultad":"Alta","ruta_frontend":None,"implementado":False,
     "titulo":"Informes de gestión — deuda, honorarios, retiros, flujo real vs proyectado",
     "descripcion":"Suite de reportes ejecutivos para socios. Pendiente Fase 4."},
    {"codigo":"R-18","fase":4,"area":"IVA","dificultad":"Muy alta","ruta_frontend":None,"implementado":False,
     "titulo":"Liquidación de impuestos: IVA, Ganancias, F931, VEPs automáticos",
     "descripcion":"WS djprocessorcontribuyente + createVEP. Pendiente Fase 4."},
    {"codigo":"R-19","fase":4,"area":"IVA","dificultad":"Muy alta","ruta_frontend":None,"implementado":False,
     "titulo":"Consulta IVA-MES por cliente desde ARCA",
     "descripcion":"Cálculo de posición IVA por cliente con datos en vivo. Pendiente Fase 4."},
    {"codigo":"R-20","fase":4,"area":"IVA+ADM","dificultad":"Muy alta","ruta_frontend":None,"implementado":False,
     "titulo":"Migración histórica desde Excel (cuentas corrientes + liquidaciones pasadas)",
     "descripcion":"Importación masiva de Excel históricos. Pendiente Fase 4."},
]


# Acciones activadas por defecto (ambos niveles) — las pantallas del guión (Fase 1).
_FLAGS_DEMO_ON = {"R-01", "R-03", "R-04", "R-05", "R-07"}


def seed_feature_flags():
    """Seed idempotente del catálogo de requisitos. Crea entries faltantes y
    refresca metadata; NO toca `enabled`/`enabled_admin` de los existentes (eso lo
    deciden super_admin/admin). En los nuevos, arranca ON solo las del guión."""
    db = SessionLocal()
    creados = 0
    for it in CATALOGO_REQUISITOS:
        existing = db.query(FeatureFlag).filter_by(codigo=it["codigo"]).first()
        if existing is None:
            on = it["codigo"] in _FLAGS_DEMO_ON
            db.add(FeatureFlag(**it, enabled_admin=on, enabled=on))
            creados += 1
        else:
            for k, v in it.items():
                if k == "codigo": continue
                if getattr(existing, k) != v:
                    setattr(existing, k, v)
    db.commit()
    db.close()
    if creados:
        print(f"[OK] FeatureFlags: {creados} requisitos creados.")
