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
    TipoHonorario, FeatureFlag, Empleado,
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

    # Producto de referencia: bolsa de cemento (para clientes constructoras)
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


def seed_empleados():
    """Seed idempotente de nómina de empleados (data fake) para cada cliente activo.

    Crea entre 3 y 6 empleados por cliente con nombres/CUIL/fecha de ingreso
    ficticios. No borra nada; sólo corre si la tabla `empleados` está vacía."""
    db = SessionLocal()
    rng = random.Random(2026)   # determinístico: misma data en cada arranque/entorno
    prod = db.query(ProductoReferencia).first()   # para empleados con honorario tipo producto
    medios = ["transferencia", "efectivo", "deposito", "cheque"]

    existentes = db.query(Empleado).all()
    if existentes:
        # Backfill de config en empleados de versiones previas (fake data sin honorario)
        changed = 0
        for e in existentes:
            if e.tipo_honorario is None:
                if prod and rng.random() < 0.2:
                    e.tipo_honorario = TipoHonorario.producto
                    e.producto_ref_id = prod.id
                    e.cantidad_unidades = float(rng.randint(5, 60))
                else:
                    e.tipo_honorario = TipoHonorario.fijo
                    e.importe_fijo = float(rng.randint(150, 1200) * 1000)
                changed += 1
            if not e.medio_pago:
                e.medio_pago = rng.choice(medios)
                changed += 1
        if changed:
            db.commit()
            print(f"[OK] Nómina: config backfilleada en empleados existentes.")
        db.close()
        return

    clientes = db.query(Client).filter(Client.is_active == True).order_by(Client.id).all()  # noqa: E712
    if not clientes:
        db.close()
        return

    print("Agregando nómina de empleados (data fake)...")
    total = 0
    for c in clientes:
        n = rng.randint(3, 6)
        usados = set()
        for _ in range(n):
            # evitar nombre+apellido repetido dentro del mismo cliente
            for _try in range(10):
                nombre = rng.choice(_NOMBRES)
                apellido = rng.choice(_APELLIDOS)
                if (nombre, apellido) not in usados:
                    usados.add((nombre, apellido))
                    break
            ingreso = date(2026, 1, 1) - timedelta(days=rng.randint(60, 2200))

            # Config de honorario por empleado: ~20% producto, resto fijo
            if prod and rng.random() < 0.2:
                tipo = TipoHonorario.producto
                importe_fijo = None
                producto_ref_id = prod.id
                cantidad = float(rng.randint(5, 60))
            else:
                tipo = TipoHonorario.fijo
                importe_fijo = float(rng.randint(150, 1200) * 1000)   # $150k–$1.2M
                producto_ref_id = None
                cantidad = None

            db.add(Empleado(
                client_id=c.id,
                nombre=nombre,
                apellido=apellido,
                cuil=_cuil(rng),
                fecha_ingreso=ingreso,
                activo=rng.random() > 0.08,   # ~8% dados de baja
                medio_pago=rng.choice(medios),
                tipo_honorario=tipo,
                importe_fijo=importe_fijo,
                producto_ref_id=producto_ref_id,
                cantidad_unidades=cantidad,
            ))
            total += 1

    db.commit()
    db.close()
    print(f"[OK] Nómina: {total} empleados creados en {len(clientes)} clientes.")


if __name__ == "__main__":
    seed_database()
    seed_empleados()


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


def seed_feature_flags():
    """Seed idempotente del catálogo de requisitos. Crea entries faltantes y
    refresca metadata; no toca el campo `enabled` (eso lo decide el super_admin)."""
    db = SessionLocal()
    creados = 0
    for it in CATALOGO_REQUISITOS:
        existing = db.query(FeatureFlag).filter_by(codigo=it["codigo"]).first()
        if existing is None:
            db.add(FeatureFlag(**it, enabled=False))
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
