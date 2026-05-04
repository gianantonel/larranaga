"""Genera el PDF del QA de Fase 3 (R-15 Conciliación bancaria — Fede)."""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, lightgrey
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "qa_fase3_screenshots"
RESULTS = ROOT / "docs" / "qa_fase3_results.json"
OUT = ROOT / "docs" / "QA_FASE3_REPORTE.pdf"

PURPLE = HexColor("#7c3aed")
DARK = HexColor("#111827")
GREEN = HexColor("#10b981")
AMBER = HexColor("#f59e0b")
GRAY = HexColor("#6b7280")
BG_LIGHT = HexColor("#f9fafb")

STATUS_COLOR = {"PASS": GREEN, "PARTIAL": AMBER, "FAIL": HexColor("#ef4444")}

PASOS = [
    ("T1", "Login + sidebar muestra 'Conciliación bancaria'", ["01_dashboard_sidebar.png"],
     "Tras loguearse como Fede, el sidebar incluye el ítem 'Conciliación bancaria' agrupado en Acciones."),
    ("T2", "Pantalla carga con tabs Importar / Extractos", ["02_tab_importar.png"],
     "La pantalla principal muestra el formulario de import (banco, periodo, archivo) con tema dark."),
    ("T3", "Subir extracto Pampa Feb-2026", ["03_extracto_seleccionado.png", "04_import_exito.png"],
     "Selección del archivo de fixture (15 movimientos) y procesamiento. Banner verde de éxito con stats: créditos vs débitos."),
    ("T4", "Tab 'Extractos importados' lista lo procesado", ["05_tab_extractos.png"],
     "Listado con columnas: Banco · Período · Archivo · Movimientos · Conciliados · Pendientes · Acción."),
    ("T5", "Detalle del extracto con todos los movimientos", ["06_detalle_extracto.png"],
     "Tabla de 15 filas con Fecha · Tipo (Crédito/Débito) · Descripción · Importe · CUIT · Estado · Acción."),
    ("T6", "Correr matching automático", ["07_matching_ejecutado.png"],
     "Click en 'Correr matching automático'. 3 movimientos pasan a estado Conciliado: "
     "BUTALO $150.000 (CUIT match), GESUALDO $300.000 (CUIT+importe), GAUCHO $8.500 (CUIT match)."),
    ("T7", "Filtro Conciliados", ["08_filtro_conciliados.png"],
     "Filtra la tabla y muestra sólo los movimientos ya matcheados con su pago vinculado."),
    ("T8", "Filtro Pendientes", ["09_filtro_pendientes.png"],
     "Muestra movimientos sin match: comisiones bancarias, débitos automáticos, retiros, créditos sin CUIT."),
    ("T9", "Buscador por descripción / CUIT", ["10_buscador.png"],
     "Buscador filtra en vivo por substring. Probado con 'TRANSF' → muestra todas las transferencias."),
    ("T10", "Modal 'Asociar manualmente' con candidatos sugeridos", ["11_modal_match_manual.png"],
     "Modal con info del movimiento + top 5 pagos candidatos ordenados por score. "
     "Cada candidato tiene cliente, fecha, importe y botón 'Asociar' para matchearlo manualmente."),
]


def build():
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    results_map = {r[0]: (r[1], r[2]) for r in results}

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=22, textColor=PURPLE,
                       spaceAfter=12, spaceBefore=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14, textColor=DARK,
                       spaceAfter=8, spaceBefore=14)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=14,
                         alignment=TA_LEFT, spaceAfter=4)
    note = ParagraphStyle("note", parent=body, leftIndent=12, fontSize=9, textColor=GRAY)

    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title="QA Fase 3 — Larrañaga",
    )

    story = []

    # Cover
    story.append(Paragraph("QA Fase 3 — R-15 Conciliación Bancaria", h1))
    story.append(Paragraph(
        "Validación E2E de la pantalla de conciliación bancaria implementada por Fede en Fase 3. "
        "Pruebas ejecutadas con Playwright headless contra el sistema corriendo en localhost.",
        body
    ))
    story.append(Spacer(1, 8))

    # Resumen
    n_pass = sum(1 for r in results if r[2] == "PASS")
    n_partial = sum(1 for r in results if r[2] == "PARTIAL")
    n_fail = sum(1 for r in results if r[2] == "FAIL")

    summary = [
        ["Total pruebas", str(len(results))],
        ["PASS", str(n_pass)],
        ["PARTIAL", str(n_partial)],
        ["FAIL", str(n_fail)],
        ["Tests unidad/integración", "11 verdes (8 conciliacion + 3 E2E)"],
        ["Branch", "fase-3 (mergeado a fede + fase-2)"],
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

    # Tabla resultados
    story.append(Paragraph("Resultados por prueba", h2))
    rows = [["#", "Prueba", "Resultado", "Detalle"]]
    for tid, desc, status in results:
        color = STATUS_COLOR.get(status, GRAY)
        rows.append([
            tid,
            Paragraph(desc, body),
            Paragraph(f'<b><font color="{color.hexval()}">{status}</font></b>', body),
            "—",
        ])
    t = Table(rows, colWidths=[1.2 * cm, 9 * cm, 2 * cm, 5 * cm])
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

    page_w = A4[0] - 3.6 * cm

    # Detalle por paso
    for tid, label, screenshots, descripcion in PASOS:
        story.append(Paragraph(f"{tid}. {label}", h2))

        if tid in results_map:
            status, _ = results_map[tid]
            color = STATUS_COLOR.get(status, GRAY)
            story.append(Paragraph(
                f'<b><font color="{color.hexval()}">{status}</font></b> · {results_map[tid][0]}',
                body
            ))

        story.append(Paragraph(descripcion, body))
        story.append(Spacer(1, 6))

        for shot in screenshots:
            p = SHOTS / shot
            if not p.exists():
                story.append(Paragraph(f"<i>(captura no disponible: {shot})</i>", note))
                continue
            img = Image(str(p))
            iw, ih = img.imageWidth, img.imageHeight
            ratio = ih / iw
            target_w = page_w
            target_h = target_w * ratio
            max_h = 13 * cm
            if target_h > max_h:
                target_h = max_h
                target_w = target_h / ratio
            img.drawWidth = target_w
            img.drawHeight = target_h
            story.append(Spacer(1, 4))
            story.append(KeepTogether([img, Paragraph(f"<i>{shot}</i>", note)]))
            story.append(Spacer(1, 6))

        story.append(PageBreak())

    doc.build(story)
    print(f"PDF: {OUT}")


if __name__ == "__main__":
    build()
