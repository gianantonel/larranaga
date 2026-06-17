"""Genera PDF de informe del sistema de feature flags implementado.

Cubre: resumen ejecutivo, arquitectura backend + frontend, permisos,
3 vistas con screenshots, y sección comparativa super_admin vs colaborador.

Uso:
    cd backend
    .venv/Scripts/python.exe scripts/generate_informe_pdf.py

Output: docs/INFORME_SISTEMA_FEATURE_FLAGS.pdf
"""
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image,
)
from reportlab.lib.utils import ImageReader


REPO_ROOT = Path(__file__).resolve().parents[2]
IMG_DIR = REPO_ROOT / "docs" / "img"


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="H1Custom", fontSize=22, leading=28, textColor=colors.HexColor("#1a1a1a"),
                         spaceAfter=12, spaceBefore=4))
    s.add(ParagraphStyle(name="H2Custom", fontSize=16, leading=20, textColor=colors.HexColor("#222"),
                         spaceBefore=16, spaceAfter=8))
    s.add(ParagraphStyle(name="H3Custom", fontSize=12, leading=16, textColor=colors.HexColor("#444"),
                         spaceBefore=10, spaceAfter=4))
    s.add(ParagraphStyle(name="BodyCustom", fontSize=10.5, leading=14, textColor=colors.HexColor("#222"),
                         spaceAfter=4))
    s.add(ParagraphStyle(name="BulletItem", fontSize=10.5, leading=14, textColor=colors.HexColor("#222"),
                         leftIndent=18, bulletIndent=4, spaceAfter=3))
    s.add(ParagraphStyle(name="Caption", fontSize=9.5, leading=12, textColor=colors.HexColor("#666"),
                         italic=True, spaceAfter=10, alignment=1))
    s.add(ParagraphStyle(name="Mono", fontSize=9.5, leading=12, textColor=colors.HexColor("#0a0a0a"),
                         fontName="Courier", spaceAfter=4))
    return s


def _scaled_image(path: Path, max_width_cm: float = 15) -> Image:
    """Carga imagen y la escala manteniendo ratio para que entre en max_width_cm."""
    ir = ImageReader(str(path))
    iw, ih = ir.getSize()
    max_w = max_width_cm * cm
    if iw > max_w:
        ratio = max_w / iw
        return Image(str(path), width=max_w, height=ih * ratio)
    return Image(str(path), width=iw, height=ih)


def _section_header(story, st, title):
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(title, st["H1Custom"]))


def generate(output_path: Path, fecha: datetime | None = None) -> Path:
    fecha = fecha or datetime.utcnow()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    st = _styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Informe Sistema Feature Flags — Larrañaga",
    )

    story = []

    # ─── Portada ──────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("Sistema de Feature Flags por Requisito", st["H1Custom"]))
    story.append(Paragraph("Informe de implementación — Estudio Larrañaga", st["H2Custom"]))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(f"Fecha: <b>{fecha.strftime('%d/%m/%Y %H:%M')}</b>", st["BodyCustom"]))
    story.append(Paragraph("Rama: <b>feature/req-flags-fase-1</b>", st["BodyCustom"]))
    story.append(Paragraph("Commit: <b>d6242d1</b> (sistema en web) + <b>796370a</b> (PDF Fase 1)",
                           st["BodyCustom"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Este documento describe el sistema de feature flags implementado para "
                           "controlar la visibilidad de cada requisito R-XX en la plataforma. "
                           "Incluye arquitectura, capturas de las vistas relevantes y una sección "
                           "comparativa entre los permisos de super_admin y colaborador.",
                           st["BodyCustom"]))
    story.append(PageBreak())

    # ─── Índice ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Contenido", st["H1Custom"]))
    indice = [
        "1. Resumen ejecutivo",
        "2. Arquitectura — Backend",
        "3. Arquitectura — Frontend",
        "4. Permisos y roles",
        "5. Vistas",
        "    5.1. Página /gestion-requisitos (super_admin)",
        "    5.2. Dashboard super_admin con Modo verificación",
        "    5.3. Dashboard colaborador",
        "6. Diferencias super_admin vs colaborador (sección comparativa)",
        "7. Cómo usarlo",
    ]
    for item in indice:
        story.append(Paragraph(item, st["BodyCustom"]))
    story.append(PageBreak())

    # ─── 1. Resumen ejecutivo ─────────────────────────────────────────────────
    _section_header(story, st, "1. Resumen ejecutivo")
    story.append(Paragraph(
        "Cada uno de los 20 requisitos del Plan Maestro (R-01 a R-20) ahora tiene un toggle "
        "<b>enabled</b> que controla su visibilidad para los colaboradores. Solo los usuarios con "
        "rol <b>super_admin</b> pueden modificar estos toggles desde la página dedicada "
        "<b>/gestion-requisitos</b>. Los <b>admin</b> regulares y los <b>colaborador</b> no ven "
        "esa página ni pueden tocar los flags.",
        st["BodyCustom"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Funcionalidades:", st["H3Custom"]))
    for txt in [
        "• Toggle on/off por requisito con persistencia en base de datos.",
        "• Modal de confirmación si se intenta activar un requisito no implementado.",
        "• Sidebar dinámico: los items se ocultan automáticamente para colaboradores cuando "
        "su requisito está OFF.",
        "• Rutas protegidas: URL directa a un requisito OFF redirige a /dashboard.",
        "• Modo verificación opcional (solo super_admin): badges R-XX inline sobre cada item del "
        "sidebar para identificar visualmente qué corresponde a qué.",
        "• Auditoría: cada toggle queda registrado en la tabla action_logs con usuario, fecha y valor.",
    ]:
        story.append(Paragraph(txt, st["BulletItem"]))

    story.append(PageBreak())

    # ─── 2. Backend ───────────────────────────────────────────────────────────
    _section_header(story, st, "2. Arquitectura — Backend")

    story.append(Paragraph("Modelo nuevo en <b>backend/app/models.py</b>:", st["H3Custom"]))
    story.append(Paragraph("Clase <b>FeatureFlag</b> con campos: codigo (PK), titulo, descripcion, "
                           "area, fase, dificultad, ruta_frontend, implementado, enabled, "
                           "updated_by_id, updated_at.",
                           st["BodyCustom"]))

    story.append(Paragraph("Schemas en <b>backend/app/schemas.py</b>:", st["H3Custom"]))
    for txt in [
        "• <b>FeatureFlagOut</b> — payload de lectura (todos los campos del modelo).",
        "• <b>FeatureFlagUpdate</b> — solo <b>{enabled: bool}</b>.",
    ]:
        story.append(Paragraph(txt, st["BulletItem"]))

    story.append(Paragraph("Router en <b>backend/app/routers/feature_flags.py</b>:", st["H3Custom"]))
    for txt in [
        "• <b>GET /feature-flags</b> — cualquier usuario autenticado. Devuelve los 20 flags "
        "ordenados por fase y código.",
        "• <b>PUT /feature-flags/{codigo}</b> — <b>solo super_admin</b> (depende de "
        "<b>require_super_admin</b> en backend/app/routers/auth.py). Cambia enabled, setea "
        "updated_by_id y updated_at, escribe entry en ActionLog.",
    ]:
        story.append(Paragraph(txt, st["BulletItem"]))

    story.append(Paragraph("Seed en <b>backend/app/mock_data.py</b>:", st["H3Custom"]))
    story.append(Paragraph(
        "Función <b>seed_feature_flags()</b> con el catálogo de 20 R-XX (datos del Plan Maestro). "
        "Idempotente: crea los faltantes y refresca metadata sin tocar el campo enabled "
        "(eso lo decide el super_admin). Se ejecuta automáticamente en startup.",
        st["BodyCustom"]))

    story.append(PageBreak())

    # ─── 3. Frontend ──────────────────────────────────────────────────────────
    _section_header(story, st, "3. Arquitectura — Frontend")

    story.append(Paragraph("Context en <b>frontend/src/context/FeatureFlagsContext.jsx</b>:",
                           st["H3Custom"]))
    story.append(Paragraph(
        "<b>FeatureFlagsProvider</b> hace GET /feature-flags al login y mantiene en memoria los "
        "20 flags. Expone los hooks <b>useFeatureFlag(codigo)</b> y <b>useFeatureFlags()</b>, "
        "más <b>setFlag(codigo, enabled)</b> que hace el PUT y actualiza el estado optimísticamente. "
        "También maneja el toggle <b>verificationMode</b> con persistencia en localStorage.",
        st["BodyCustom"]))

    story.append(Paragraph("Componentes nuevos:", st["H3Custom"]))
    for txt in [
        "• <b>&lt;FeatureGate codigo=&quot;R-XX&quot;&gt;</b> — wrapper: si el usuario es admin "
        "siempre renderiza children; si no, solo si el flag está enabled. Acepta array de códigos "
        "(cualquier enabled basta).",
        "• <b>&lt;RequirementBadge&gt;</b> — chip pequeño con color por estado (verde activo, "
        "amarillo inactivo, gris pendiente).",
    ]:
        story.append(Paragraph(txt, st["BulletItem"]))

    story.append(Paragraph("Página nueva — <b>/gestion-requisitos</b> "
                           "(frontend/src/pages/GestionRequisitos.jsx):", st["H3Custom"]))
    for txt in [
        "• Solo super_admin (resto redirige a /dashboard).",
        "• 4 tabs por fase, abierto Fase 1 por defecto.",
        "• Cada R-XX es una card con código, título, descripción, área, dificultad, "
        "indicador implementado/pendiente y toggle on/off.",
        "• Modal de confirmación cuando se intenta activar un requisito con implementado=false.",
        "• Botón 'Modo verificación' en el header.",
    ]:
        story.append(Paragraph(txt, st["BulletItem"]))

    story.append(Paragraph("Sidebar modificado:", st["H3Custom"]))
    for txt in [
        "• Cada NavLink de la sección Acciones está envuelto en <b>&lt;FeatureGate&gt;</b>.",
        "• Sección nueva 'Administración' al pie (solo super_admin) con el item "
        "'Gestión de Requisitos' y el toggle 'Modo verificación'.",
        "• Cuando Modo verificación está ON (solo super_admin), cada item muestra su badge R-XX "
        "a la derecha con el color según estado.",
    ]:
        story.append(Paragraph(txt, st["BulletItem"]))

    story.append(Paragraph("App.jsx — rutas gateadas:", st["H3Custom"]))
    story.append(Paragraph(
        "13 rutas protegidas con <b>&lt;Gated codigo=&quot;R-XX&quot;&gt;</b> que redirigen "
        "a /dashboard si el requisito está OFF y el usuario no es admin: /herramientas, /honorarios, "
        "/profesionales, /liquidaciones, /retenciones, /cuentas-corrientes, /iva, /posicion-iva, "
        "/cobros, /maestro-proveedores, /flujo-fondos, /retiros, /actualizar-honorarios, "
        "/conciliacion-bancaria.",
        st["BodyCustom"]))

    story.append(PageBreak())

    # ─── 4. Permisos ──────────────────────────────────────────────────────────
    _section_header(story, st, "4. Permisos y roles")
    story.append(Paragraph(
        "El enum UserRole del proyecto tiene cuatro valores: <b>super_admin</b>, <b>admin</b>, "
        "<b>colaborador</b>, <b>invitado</b>. La matriz de permisos del sistema de feature flags es:",
        st["BodyCustom"]))
    story.append(Spacer(1, 0.3 * cm))

    matrix = [
        ["Acción", "super_admin", "admin", "colaborador", "invitado"],
        ["Ver lista de flags (GET)", "Sí", "Sí", "Sí", "Sí"],
        ["Togglear un flag (PUT)", "Sí", "403", "403", "403"],
        ["Acceder a /gestion-requisitos", "Sí", "→ /dashboard", "→ /dashboard", "→ /dashboard"],
        ["Toggle 'Modo verificación' visible", "Sí", "No", "No", "No"],
        ["Badges R-XX en sidebar", "Sí (si modo ON)", "No", "No", "No"],
        ["Items del sidebar con req OFF", "Visibles", "Visibles", "Ocultos", "Ocultos"],
        ["URL directa a req OFF", "Renderiza", "Renderiza", "→ /dashboard", "→ /dashboard"],
    ]
    t = Table(matrix, colWidths=[6 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#ecfdf5")),
        ("BACKGROUND", (2, 1), (4, -1), colors.HexColor("#f9fafb")),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e5e5")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)

    story.append(PageBreak())

    # ─── 5. Vistas con screenshots ────────────────────────────────────────────
    _section_header(story, st, "5. Vistas")

    story.append(Paragraph("5.1. Página /gestion-requisitos (super_admin)", st["H2Custom"]))
    story.append(Paragraph(
        "Página principal del sistema. Solo accesible para super_admin. Cuatro tabs (uno por fase), "
        "cards con toggle individual y modal de confirmación al activar pendientes.",
        st["BodyCustom"]))
    story.append(Spacer(1, 0.3 * cm))
    img1 = IMG_DIR / "01-gestion-requisitos-fase1.png"
    if img1.exists():
        story.append(_scaled_image(img1, max_width_cm=16))
        story.append(Paragraph("Vista 1 — /gestion-requisitos en Fase 1, R-01 y R-02 activados.",
                               st["Caption"]))
    story.append(PageBreak())

    story.append(Paragraph("5.2. Dashboard super_admin con Modo verificación", st["H2Custom"]))
    story.append(Paragraph(
        "El super_admin ve TODOS los items del sidebar (incluso los que están OFF), más la sección "
        "Administración. Con el modo verificación activado, cada item muestra su badge R-XX a la "
        "derecha — verde si está activo, amarillo si está inactivo, gris si está pendiente.",
        st["BodyCustom"]))
    story.append(Spacer(1, 0.3 * cm))
    img2 = IMG_DIR / "02-dashboard-modo-verificacion.png"
    if img2.exists():
        story.append(_scaled_image(img2, max_width_cm=16))
        story.append(Paragraph("Vista 2 — Dashboard como super_admin con Modo verificación ON.",
                               st["Caption"]))
    story.append(PageBreak())

    story.append(Paragraph("5.3. Dashboard colaborador", st["H2Custom"]))
    story.append(Paragraph(
        "El colaborador (rol colaborador) ve un sidebar reducido: solo los items cuyo requisito "
        "está enabled, más las vistas base y Facturación (que no tiene flag). No ve la sección "
        "Administración, no ve badges, no puede entrar a /gestion-requisitos.",
        st["BodyCustom"]))
    story.append(Spacer(1, 0.3 * cm))
    img3 = IMG_DIR / "03-dashboard-colaborador.png"
    if img3.exists():
        story.append(_scaled_image(img3, max_width_cm=16))
        story.append(Paragraph("Vista 3 — Dashboard como colaborador (mgonzalez@larranaga.com).",
                               st["Caption"]))
    story.append(PageBreak())

    # ─── 6. Sección comparativa Vistas 2 vs 3 ─────────────────────────────────
    _section_header(story, st, "6. Diferencias super_admin vs colaborador")
    story.append(Paragraph(
        "Esta sección compara directamente las Vistas 2 y 3 (mismas pantallas, distinto rol). "
        "Estado de los flags al momento de la captura: <b>R-01, R-02, R-03, R-05, R-07 activos</b>; "
        "el resto inactivo.",
        st["BodyCustom"]))
    story.append(Spacer(1, 0.3 * cm))

    diffs = [
        ["Aspecto", "Super_admin (Vista 2)", "Colaborador (Vista 3)"],
        ["Items en sección Vistas",
         "4 (Dashboard, Clientes, Colaboradores, Tareas)",
         "4 (idénticos)"],
        ["Items en sección Acciones",
         "15 (todos visibles, incluso los OFF)",
         "5 (solo los que están enabled + Facturación)"],
        ["Items ocultos para el colaborador",
         "—",
         "Balance IVA, Posición IVA, Maestro Proveedores, Actualizar Honorarios, "
         "Profesionales, Liquidaciones, Registrar Cobro, Retiros Socios, Flujo de Fondos, "
         "Conciliación bancaria"],
        ["Sección Administración",
         "Sí (Gestión de Requisitos + Modo verificación)",
         "No existe"],
        ["Badges R-XX inline",
         "Sí (con Modo verificación ON): verde activo, amarillo inactivo, gris pendiente",
         "No existen, sin importar el estado del Modo verificación"],
        ["Acceso a /gestion-requisitos",
         "Renderiza la página completa",
         "Redirige inmediatamente a /dashboard"],
        ["URL directa a un requisito OFF",
         "Renderiza igual (admin ve todo)",
         "Redirige a /dashboard (FeatureGate cierra)"],
        ["Acción de togglear un flag",
         "Permitido (200 OK)",
         "403 Forbidden desde backend"],
        ["Datos visibles en Dashboard",
         "Idénticos (mismas tarjetas, mismas métricas, mismo gráfico)",
         "Idénticos (gating solo afecta sidebar y rutas, no contenido del dashboard)"],
    ]
    t2 = Table(diffs, colWidths=[4.5 * cm, 6 * cm, 6 * cm])
    t2.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f5f5f5")),
        ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#ecfdf5")),
        ("BACKGROUND", (2, 1), (2, -1), colors.HexColor("#fef3c7")),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e5e5")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "<b>Conclusión:</b> el sistema es transparente para el contenido (mismo Dashboard, mismas "
        "métricas, mismos clientes). El gating actúa exclusivamente sobre <i>qué puede acceder</i> "
        "el usuario: items del sidebar y rutas. Eso permite ocultar features no validadas para el "
        "cliente sin tocar la lógica de negocio.",
        st["BodyCustom"]))

    story.append(PageBreak())

    # ─── 7. Cómo usarlo ───────────────────────────────────────────────────────
    _section_header(story, st, "7. Cómo usarlo")
    story.append(Paragraph("Credenciales de prueba:", st["H3Custom"]))
    for txt in [
        "• <b>super_admin</b>: gianantonel@gmail.com / admin123 (también gerogambuli2002@gmail.com, "
        "rodriguezfederico765@gmail.com con admin123; optimizar.ai@gmail.com con optimizar123).",
        "• <b>colaborador</b>: mgonzalez@larranaga.com / colab123 (entre otros 8).",
    ]:
        story.append(Paragraph(txt, st["BulletItem"]))

    story.append(Paragraph("Flujo típico para una demo al cliente:", st["H3Custom"]))
    for i, txt in enumerate([
        "Login como super_admin (Gian o Gero).",
        "Entrar a sidebar → Administración → Gestión de Requisitos.",
        "Activar solo los R-XX que se quieren mostrar al cliente (por ejemplo los 6 de Fase 1).",
        "Logout y login como colaborador para verificar que solo ve esos items.",
        "Cerrar la demo: super_admin desactiva los flags si quiere volver a ocultar las features.",
    ], 1):
        story.append(Paragraph(f"<b>{i}.</b> {txt}", st["BulletItem"]))

    story.append(Paragraph("Regenerar este informe:", st["H3Custom"]))
    story.append(Paragraph(
        "cd backend && .venv/Scripts/python.exe scripts/generate_informe_pdf.py",
        st["Mono"]))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    out = REPO_ROOT / "docs" / "INFORME_SISTEMA_FEATURE_FLAGS.pdf"
    p = generate(out)
    print(f"PDF generado: {p}")
