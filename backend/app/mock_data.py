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
    UserRole, TaskType, TaskStatus, InvoiceType
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
        User(name="Administrador 1", email="admin1@larranaga.com",
             password_hash=get_password_hash("admin123"), role=UserRole.admin1,
             avatar_initials="A1"),
        User(name="Administrador 2", email="admin2@larranaga.com",
             password_hash=get_password_hash("admin123"), role=UserRole.admin2,
             avatar_initials="A2"),
        User(name="Administrador 3", email="admin3@larranaga.com",
             password_hash=get_password_hash("admin123"), role=UserRole.admin3,
             avatar_initials="A3"),
    ]

    collaborators = [
        User(name="María González", email="mgonzalez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.collaborator,
             avatar_initials="MG"),
        User(name="Carlos Rodríguez", email="crodriguez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.collaborator,
             avatar_initials="CR"),
        User(name="Ana Martínez", email="amartinez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.collaborator,
             avatar_initials="AM"),
        User(name="Diego Fernández", email="dfernandez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.collaborator,
             avatar_initials="DF"),
        User(name="Laura Sánchez", email="lsanchez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.collaborator,
             avatar_initials="LS"),
        User(name="Roberto Gómez", email="rgomez@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.collaborator,
             avatar_initials="RG"),
        User(name="Patricia Torres", email="ptorres@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.collaborator,
             avatar_initials="PT"),
        User(name="Sebastián Morales", email="smorales@larranaga.com",
             password_hash=get_password_hash("colab123"), role=UserRole.collaborator,
             avatar_initials="SM"),
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
    ]

    clients = []
    for cd in clients_data:
        client = Client(
            name=cd["name"],
            business_name=cd["business_name"],
            cuit=cd["cuit"],
            clave_fiscal_encrypted=encrypt_credential(cd["clave_fiscal"]),
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
    ]

    for i, client in enumerate(clients):
        vg_base, cg_base = iva_base[i]
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


if __name__ == "__main__":
    seed_database()
