"""Genera el PDF de QA con capturas embebidas."""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, lightgrey
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "qa_screenshots"
RESULTS = ROOT / "docs" / "qa_results.json"
OUT = ROOT / "docs" / "QA_REPORTE.pdf"

PURPLE = HexColor("#7c3aed")
DARK = HexColor("#111827")
GREEN = HexColor("#10b981")
AMBER = HexColor("#f59e0b")
GRAY = HexColor("#6b7280")
BG_LIGHT = HexColor("#f9fafb")

STATUS_COLOR = {
    "PASS": GREEN,
    "PARTIAL": AMBER,
    "MANUAL": HexColor("#3b82f6"),
    "FAIL": HexColor("#ef4444"),
}

# Cada paso del QA: (titulo, requerimiento, [screenshots], notas adicionales, manual_steps)
STEPS = [
    ("Login", None, ["01_login.png"],
     "Pantalla de inicio de sesión con cuenta de prueba (cuentas visibles).", []),
    ("Dashboard", None, ["02_dashboard.png"],
     "Métricas: clientes activos, colaboradores, tareas y DDJJ IVA pendientes.", []),
    ("Clientes", None, ["03_clientes.png"],
     "Listado de clientes con buscador, filtros y badge de estado.", []),
    ("Colaboradores", None, ["04_colaboradores.png"],
     "Listado de colaboradores del estudio.", []),
    ("Tareas", None, ["05_tareas.png"],
     "Tablero de tareas con filtros y estados.", []),
    ("R-07 · Cuentas Corrientes", "R-07", ["06_R07_cuentas_corrientes.png"],
     "CC de clientes con saldo actualizado en tiempo real. Cada cobro impacta automáticamente.", []),
    ("Balance IVA", None, ["07_balance_iva.png"],
     "Listado de DDJJ IVA por cliente y período (apoyo para R-06).", []),
    ("R-06 · Posición IVA", "R-06", ["08_R06_posicion_iva.png"],
     "Posición IVA del mes calculada desde comprobantes. Selector de período + 3 tarjetas (Débito · Crédito · Posición).", []),
    ("Facturación", None, ["09_facturacion.png"],
     "Listado de facturas emitidas con filtros.", []),
    ("R-05 · Retenciones", "R-05",
     ["10_R05_retenciones.png"],
     "UI carga sin errores. La clasificación automática IVA vs IIBB usa el "
     "AFIP SDK (campo codigoRegimen).",
     ["Subir un comprobante real con percepciones de Banco Pampa o ARBA",
      "Ejecutar /retenciones/clasificar y verificar splits IVA/IIBB",
      "Validar que las retenciones se asocian al comprobante origen"]),
    ("R-09 · Maestro Proveedores", "R-09", ["11_R09_maestro_proveedores.png"],
     "Tabla con CUIT · razón social · cuenta contable · fuente (manual/padrón/IA). Pipeline 3 niveles cache → padrón ARCA → manual.", []),
    ("R-03 · Honorarios", "R-03", ["12_R03_honorarios.png"],
     "Listado por cliente y período. Soporta tipo fijo y producto (cantidad × precio vigente).", []),
    ("Profesionales", None, ["13_profesionales.png"],
     "Listado de profesionales activos del estudio.", []),
    ("R-08 · Registrar Cobro · Transferencia", "R-08",
     ["14_R08_registrar_cobro_form.png", "15_R08_cobro_completado.png", "16_R08_cobro_success.png"],
     "Formulario completo. Cobro $8.500 al cliente Restaurante El Gaucho destinado a Mariana Ruiz. "
     "El saldo CC se actualiza al confirmar. Banner verde de éxito.", []),
    ("R-08 + R-14 · Cobro Efectivo + Billetes", "R-08+R-14",
     ["17_R14_billetes_panel.png", "18_R08_R14_cobro_efectivo_success.png"],
     "Panel de billetes condicional (sólo cuando forma_pago=efectivo). "
     "Cobro $25.000 = 1×$20.000 + 1×$5.000 a Farmacia del Centro. "
     "El sistema valida que la suma cuadre con el importe (±$1) y actualiza el stock.", []),
    ("R-04 · Liquidaciones", "R-04",
     ["19_R04_liquidaciones.png"],
     "Tabla por profesional con Hon. Brutos · Adelantos (calculados desde tabla pagos) · Saldo Anterior · Reintegros · Total a Cobrar. "
     "Cierre de período con modal que pide cobros efectivo + transferencia.", []),
    ("R-01 + R-02 + R-10 · Herramientas (subida de Excel)", "R-01+R-02+R-10",
     ["21_R01_R02_R10_herramientas.png"],
     "La página de Herramientas centraliza el pipeline IVA. Backend 100% testeado (99 tests verdes). "
     "Estos pasos requieren subir un .xlsx real → no es automatizable sin un archivo de prueba.",
     ["Click en 'Corrección B/C / Holistor Columna L' del sidebar",
      "Subir un libro IVA Compras de ARCA (ej: BUTALO Feb-2026)",
      "Verificar paso 1: tipo B/C corregidos + columna L (Tipo Cambio) normalizada",
      "Verificar paso 2: filas con multi-alícuota expandidas con sufijo /A, /B",
      "Verificar paso 3: HWCRARCA descargable, validación Debe=Haber visible (verde si cuadra)",
      "Abrir el .xlsx descargado en Excel y comprobar columnas requeridas por Holistor"]),
    ("R-15 · Conciliación bancaria (Fase 3 — Sprint 1 listo)", "R-15",
     [],
     "Backend completo: parsers Pampa/Santander/MP + endpoint POST /conciliacion/import-extracto. "
     "10 tests de parsers verdes. UI pendiente (F3-08 del Sprint 2).",
     ["Test manual con curl: POST /conciliacion/import-extracto con multipart "
      "(banco=pampa, periodo=2026-02, file=extracto.xlsx)",
      "Verificar respuesta: ImportExtractoStats con n_creditos / n_debitos / importes totales",
      "GET /conciliacion/extractos lista los importados",
      "GET /conciliacion/extracto/{id}/movimientos devuelve líneas normalizadas"]),
    ("Logout", None, ["22_logout_o_login.png"],
     "Cierre de sesión correcto y vuelta al login.", []),
]


def md_inline(text: str) -> str:
    import re
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" color="#5e2ca5">\1</font>', text)
    text = re.sub(r"\*\*([^\*]+)\*\*", r"<b>\1</b>", text)
    return text


def build():
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    results_map = {r[0]: (r[1], r[2]) for r in results}

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=22, textColor=PURPLE,
                       spaceAfter=12, spaceBefore=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14, textColor=DARK,
                       spaceAfter=8, spaceBefore=14)
    h3 = ParagraphStyle("h3", parent=styles["Heading3"], fontSize=11, textColor=PURPLE,
                       spaceAfter=4, spaceBefore=10)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13,
                         alignment=TA_LEFT, spaceAfter=4)
    note_style = ParagraphStyle("note", parent=body, leftIndent=12, fontSize=9,
                               textColor=GRAY)

    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title="QA Reporte — Larrañaga",
    )

    story = []

    # ─── Cover ──────────────────────────────────────────────────────────────
    story.append(Paragraph("QA Reporte E2E — Larrañaga", h1))
    story.append(Paragraph(
        "Validación de la totalidad de los requerimientos implementados en Fase 1 y Fase 2 "
        "+ snapshot del Sprint 1 de Fase 3. Capturas tomadas con Playwright headless contra "
        "el frontend en producción local.", body))
    story.append(Spacer(1, 6))

    # Resumen
    n_pass = sum(1 for r in results if r[1] == "PASS")
    n_partial = sum(1 for r in results if r[1] == "PARTIAL")
    n_manual = sum(1 for r in results if r[1] == "MANUAL")

    summary = [
        ["Total pruebas", str(len(results))],
        ["Automatizadas y verdes (PASS)", str(n_pass)],
        ["Parciales (PARTIAL)", str(n_partial)],
        ["Manuales (MANUAL)", str(n_manual)],
        ["Tests de unidad / integración", "180 verdes"],
        ["Branches involucrados", "fase-2 (cerrado) · dev · fase-3 (sprint 1 ok)"],
    ]
    t = Table(summary, colWidths=[7 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BG_LIGHT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BOX", (0, 0), (-1, -1), 0.5, lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Tabla de resultados
    story.append(Paragraph("Resumen por requerimiento", h2))
    rows = [["Requerimiento / Pantalla", "Estado", "Detalle"]]
    for name, status, detail in results:
        color = STATUS_COLOR.get(status, GRAY)
        status_par = Paragraph(f'<b><font color="{color.hexval()}">{status}</font></b>', body)
        rows.append([Paragraph(name, body), status_par, Paragraph(detail, body)])

    t = Table(rows, colWidths=[6 * cm, 2 * cm, 9.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, BG_LIGHT]),
        ("BOX", (0, 0), (-1, -1), 0.5, lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ─── Detalle por paso ────────────────────────────────────────────────────
    page_w = A4[0] - 3.6 * cm

    for i, (titulo, req, screenshots, nota, manual_steps) in enumerate(STEPS, 1):
        story.append(Paragraph(f"{i}. {titulo}", h2))

        # Estado del requerimiento si aplica
        if req:
            for key in [k for k in results_map if k.startswith(req.split("+")[0].strip())]:
                status, detail = results_map[key]
                color = STATUS_COLOR.get(status, GRAY)
                story.append(Paragraph(
                    f'<b>{key}</b> &nbsp; <font color="{color.hexval()}"><b>{status}</b></font> '
                    f'&nbsp;|&nbsp; {md_inline(detail)}', body))

        if nota:
            story.append(Paragraph(md_inline(nota), body))

        # Screenshots
        for shot_name in screenshots:
            shot_path = SHOTS / shot_name
            if not shot_path.exists():
                story.append(Paragraph(f"<i>(captura no disponible: {shot_name})</i>", note_style))
                continue
            img = Image(str(shot_path))
            iw, ih = img.imageWidth, img.imageHeight
            ratio = ih / iw
            target_w = page_w
            target_h = target_w * ratio
            # Limitar altura por página
            max_h = 13 * cm
            if target_h > max_h:
                target_h = max_h
                target_w = target_h / ratio
            img.drawWidth = target_w
            img.drawHeight = target_h
            story.append(Spacer(1, 4))
            story.append(KeepTogether([img, Paragraph(
                f"<i>{shot_name}</i>", note_style)]))

        # Manual steps
        if manual_steps:
            story.append(Spacer(1, 6))
            story.append(Paragraph("⚠ Pasos manuales pendientes (subir archivo, etc):", h3))
            for s in manual_steps:
                story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{md_inline(s)}", note_style))

        story.append(PageBreak())

    doc.build(story)
    print(f"PDF generado: {OUT}")


if __name__ == "__main__":
    build()
