"""Genera PDF de verificación de Fase 1 con pasos paso-a-paso por R-XX.

Script STANDALONE — no depende de la base de datos ni del backend levantado.
Catálogo y guiones hardcodeados acá adentro.

Uso:
    cd backend
    .venv/Scripts/python.exe scripts/generate_verification_pdf.py

Output: docs/VERIFICACION_REQUISITOS_FASE1.pdf
"""
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
)


# ─── Catálogo de los 20 R-XX (Plan Maestro líneas 17-36) ──────────────────────

CATALOGO = [
    # Fase 1
    {"codigo":"R-01","fase":1,"area":"IVA","dificultad":"Muy fácil","ruta":"/herramientas","implementado":True,
     "titulo":"Corrección comprobantes tipo B/C + formato col. L",
     "descripcion":"Limpia el libro IVA compras corrigiendo tipos B/C y el formato de la columna L (tipo de cambio)."},
    {"codigo":"R-02","fase":1,"area":"IVA","dificultad":"Muy fácil","ruta":"/herramientas","implementado":True,
     "titulo":"División de comprobantes por múltiples alícuotas de IVA",
     "descripcion":"Divide cada comprobante en filas separadas por cada alícuota distinta (10.5%, 21%, 27%)."},
    {"codigo":"R-03","fase":1,"area":"ADM","dificultad":"Muy fácil","ruta":"/honorarios","implementado":True,
     "titulo":"Cálculo automático de honorarios (fijo y valor producto)",
     "descripcion":"Calcula honorario mensual por cliente, sea importe fijo o por unidades × precio de producto vigente."},
    {"codigo":"R-04","fase":1,"area":"ADM","dificultad":"Muy fácil","ruta":"/liquidaciones","implementado":True,
     "titulo":"Liquidación mensual de profesionales — cálculo automático",
     "descripcion":"Resuelve adelantos − honorarios + saldo anterior + reintegros por profesional, por mes."},
    {"codigo":"R-05","fase":1,"area":"IVA","dificultad":"Fácil","ruta":"/retenciones","implementado":True,
     "titulo":"Separación retenciones IVA vs IIBB (col. AB — Otros Tributos)",
     "descripcion":"Trae 'Mis Retenciones' desde ARCA y separa por código de régimen IVA, IIBB y Ganancias."},
    {"codigo":"R-07","fase":1,"area":"ADM","dificultad":"Fácil","ruta":"/cuentas-corrientes","implementado":True,
     "titulo":"Cuentas corrientes de clientes — registro y saldo en tiempo real",
     "descripcion":"Movimientos de cuenta corriente por cliente con saldo recalculado en cada cobro."},
    # Fase 2
    {"codigo":"R-06","fase":2,"area":"IVA","dificultad":"Fácil","ruta":"/iva","implementado":True,
     "titulo":"Conciliación IVA compras/ventas — posición IVA del mes",
     "descripcion":"Posición mensual: débito − crédito − percepciones = saldo a favor o a pagar."},
    {"codigo":"R-08","fase":2,"area":"ADM","dificultad":"Fácil","ruta":"/cobros","implementado":True,
     "titulo":"Tesorería — registro de pagos con impacto automático",
     "descripcion":"Registrar cobro impacta cuenta corriente, tesorería, liquidación profesional y caja billetes."},
    {"codigo":"R-09","fase":2,"area":"IVA","dificultad":"Media","ruta":"/maestro-proveedores","implementado":True,
     "titulo":"Imputación contable por CUIT (5 niveles)",
     "descripcion":"Maestro → padrón → reglas → IA → fallback. Asigna cuenta contable a cada proveedor."},
    {"codigo":"R-10","fase":2,"area":"IVA","dificultad":"Media","ruta":None,"implementado":True,
     "titulo":"Generación HWCRARCA completo para Holistor/Onvio",
     "descripcion":"Output final del pipeline IVA compras, validado Debe=Haber antes de escribir al disco."},
    {"codigo":"R-14","fase":2,"area":"ADM","dificultad":"Media","ruta":None,"implementado":True,
     "titulo":"Control de billetes / caja efectivo",
     "descripcion":"Seguimiento de efectivo por denominación (1000, 2000, 10k, 20k, ...). Integrado a R-08."},
    # Fase 3
    {"codigo":"R-11","fase":3,"area":"ADM","dificultad":"Media","ruta":"/flujo-fondos","implementado":True,
     "titulo":"Flujo de fondos — seguimiento y proyección vs real",
     "descripcion":"Mensual y anual por cliente. Detecta inconsistencias entre saldo CC y deuda calculada."},
    {"codigo":"R-12","fase":3,"area":"ADM","dificultad":"Media","ruta":"/retiros","implementado":True,
     "titulo":"Retiro de honorarios de socios — registro y control",
     "descripcion":"Triple impacto: tesorería + RetiroSocio + descuento billetes si es efectivo."},
    {"codigo":"R-13","fase":3,"area":"ADM","dificultad":"Media","ruta":"/actualizar-honorarios","implementado":True,
     "titulo":"Actualización cuatrimestral de honorarios con pantalla de validación",
     "descripcion":"Wizard de 3 pasos: preview de índice, selección de clientes, aplicación granular con historial."},
    {"codigo":"R-15","fase":3,"area":"IVA+ADM","dificultad":"Alta","ruta":"/conciliacion-bancaria","implementado":True,
     "titulo":"Conciliación bancaria — importación y matching automático",
     "descripcion":"Parsers Pampa/Santander/MP + matching IA contra movimientos contables."},
    # Fase 4
    {"codigo":"R-16","fase":4,"area":"IVA","dificultad":"Alta","ruta":None,"implementado":False,
     "titulo":"Reportes periódicos automáticos IVA-MES — 100+ clientes",
     "descripcion":"Automatización mis-comprobantes con credenciales por cliente. Pendiente Fase 4."},
    {"codigo":"R-17","fase":4,"area":"ADM","dificultad":"Alta","ruta":None,"implementado":False,
     "titulo":"Informes de gestión — deuda, honorarios, retiros, flujo real vs proyectado",
     "descripcion":"Suite de reportes ejecutivos para socios. Pendiente Fase 4."},
    {"codigo":"R-18","fase":4,"area":"IVA","dificultad":"Muy alta","ruta":None,"implementado":False,
     "titulo":"Liquidación de impuestos: IVA, Ganancias, F931, VEPs automáticos",
     "descripcion":"WS djprocessorcontribuyente + createVEP. Upload DDJJ y emisión de VEPs. Pendiente Fase 4."},
    {"codigo":"R-19","fase":4,"area":"IVA","dificultad":"Muy alta","ruta":None,"implementado":False,
     "titulo":"Consulta IVA-MES por cliente desde ARCA",
     "descripcion":"Cálculo de posición IVA por cliente con datos en vivo. Pendiente Fase 4."},
    {"codigo":"R-20","fase":4,"area":"IVA+ADM","dificultad":"Muy alta","ruta":None,"implementado":False,
     "titulo":"Migración histórica desde Excel (cuentas corrientes + liquidaciones pasadas)",
     "descripcion":"Importación masiva de Excel históricos. Pendiente Fase 4."},
]


# ─── Guiones detallados (los 6 R-XX de Fase 1) ────────────────────────────────

GUIONES_FASE1 = {
    "R-01": {
        "datos_prueba": "Libro IVA Compras de MATERIALES BUTALO SRL — Febrero 2026 (CSV exportado de ARCA).",
        "pasos": [
            "Login como super_admin (gianantonel@gmail.com / admin123).",
            "Entrar a /herramientas — sección 'Adaptador Libro IVA Compras'.",
            "Subir el CSV 'Libro IVA Compras BUTALO Feb-2026.csv'. Esperar barra de progreso.",
            "Verificar que en la tabla de salida los comprobantes tipo 'B' y 'C' tienen tipo corregido y la columna L (Tipo Cambio) viene con 2 decimales y separador de miles.",
            "Descargar el archivo procesado. Abrirlo en Excel y comparar: ningún registro con formato roto, ningún tipo B/C sin corrección.",
        ],
        "criterio_aceptacion": "El 100% de los registros B/C quedan corregidos. La columna L respeta formato '#.###,##'. Descarga genera archivo válido.",
    },
    "R-02": {
        "datos_prueba": "Mismo archivo de BUTALO — contiene comprobantes con alícuotas 10.5%, 21% y 27% mezcladas en la misma factura.",
        "pasos": [
            "Entrar a /herramientas con un usuario logueado.",
            "Subir el CSV de BUTALO Feb 2026.",
            "En la salida, ubicar un comprobante que en el archivo original tenía 3 alícuotas → debe aparecer dividido en 3 filas, una por alícuota.",
            "Sumar el neto + IVA de las 3 filas y validar que coincida con el total del comprobante original (diferencia ≤ 0.01).",
            "Verificar el stat 'R-02 multi-alícuota' en el panel superior — debe contar los comprobantes divididos.",
        ],
        "criterio_aceptacion": "Cada comprobante multi-alícuota queda dividido sin pérdida de monto. El stat de divisiones es > 0.",
    },
    "R-03": {
        "datos_prueba": "Cliente Comercio García (fijo $40.000) + cliente Agropecuaria El Alba (producto cemento, 50 unidades).",
        "pasos": [
            "Entrar a /honorarios. Filtrar por período actual (YYYY-MM).",
            "Para Comercio García (tipo fijo): verificar que el importe es exactamente $40.000.",
            "Para Agropecuaria El Alba (tipo producto): verificar que el importe = 50 × precio_vigente del producto cemento.",
            "Cambiar el precio del producto cemento desde /maestro-proveedores.",
            "Recalcular el período → el honorario de Agropecuaria refleja el nuevo precio.",
        ],
        "criterio_aceptacion": "Honorarios fijos coinciden con su importe configurado. Honorarios por producto reflejan precio vigente al período.",
    },
    "R-04": {
        "datos_prueba": "Profesional Silvana Gómez. Adelantos del mes: $30.000. Honorarios cobrados a clientes asignados: $120.000. Saldo anterior: $0.",
        "pasos": [
            "Entrar a /liquidaciones. Seleccionar período actual y profesional Silvana Gómez.",
            "Validar fórmula visible: 'Honorarios cobrados ($120.000) − Adelantos ($30.000) + Saldo anterior ($0) = $90.000 a pagar'.",
            "Marcar la liquidación como 'pagada' y verificar que se registra el saldo cero para el próximo período.",
            "Repetir con profesional Marisol Borrego (socio). Comparar resultados.",
            "Refrescar la página → los importes calculados persisten.",
        ],
        "criterio_aceptacion": "El neto liquidado = honorarios − adelantos + saldo anterior. Pagar la liquidación impacta saldo del período siguiente.",
    },
    "R-05": {
        "datos_prueba": "Mis Retenciones de Agropecuaria El Alba — Febrero 2026 (vía AFIP SDK con clave fiscal de prueba).",
        "pasos": [
            "Entrar a /retenciones. Seleccionar cliente Agropecuaria El Alba y período Feb-2026.",
            "Click en 'Sincronizar'. Esperar (puede tardar 1-3 min — pollea cada 3s).",
            "Una vez terminado, verificar que las retenciones aparecen segregadas en columnas: IVA (codigoRegimen=IV*), Ganancias (IG*), IIBB (IB*).",
            "Validar que el total por categoría coincide con un reporte manual de AFIP del mismo período.",
            "Borrar una retención y volver a sincronizar — debe re-traerla.",
        ],
        "criterio_aceptacion": "Todas las retenciones quedan clasificadas correctamente. No hay rows sin categoría. Totales coinciden con AFIP.",
    },
    "R-07": {
        "datos_prueba": "Cliente Restaurante El Gaucho. Saldo inicial: $0. Honorario del mes: $50.000. Cobro parcial: $30.000.",
        "pasos": [
            "Entrar a /cuentas-corrientes. Filtrar por Restaurante El Gaucho.",
            "Registrar un movimiento de débito 'Honorarios Marzo 2026' por $50.000. Saldo pasa a $50.000.",
            "Registrar un crédito 'Cobro parcial' por $30.000. Saldo pasa a $20.000.",
            "Refrescar la página → el saldo persistente sigue siendo $20.000.",
            "Verificar que el saldo del cliente en /clientes (campo saldo_cc) coincide con el visto en /cuentas-corrientes.",
        ],
        "criterio_aceptacion": "Cada movimiento actualiza el saldo en tiempo real y persiste tras refresh. Los movimientos quedan ordenados por fecha.",
    },
}


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
    s.add(ParagraphStyle(name="Step", fontSize=10.5, leading=14, textColor=colors.HexColor("#222"),
                         leftIndent=18, bulletIndent=4, spaceAfter=4))
    s.add(ParagraphStyle(name="Note", fontSize=9.5, leading=13, textColor=colors.HexColor("#666"),
                         italic=True, spaceAfter=6))
    return s


def _status_label(it: dict) -> str:
    return "IMPLEMENTADO" if it["implementado"] else "PENDIENTE Fase 4"


def generate(output_path: Path, fecha: datetime | None = None) -> Path:
    fecha = fecha or datetime.utcnow()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    st = _styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Verificación Fase 1 — Larrañaga",
    )

    story = []
    fase1_codes = [it["codigo"] for it in CATALOGO if it["fase"] == 1]
    by_codigo = {it["codigo"]: it for it in CATALOGO}

    # Portada
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("Verificación de Fase 1", st["H1Custom"]))
    story.append(Paragraph("Estudio Larrañaga — Sistema Optimizar AI", st["H2Custom"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"Fecha de generación: <b>{fecha.strftime('%d/%m/%Y %H:%M')}</b>", st["BodyCustom"]))
    story.append(Paragraph(f"Cobertura detallada: <b>{', '.join(fase1_codes)}</b> (los 6 requisitos de Fase 1).",
                           st["BodyCustom"]))
    story.append(Paragraph("Para cada requisito, este documento describe datos de prueba, pasos paso a paso y "
                           "criterio de aceptación. Las Fases 2, 3 y 4 incluyen un resumen al final.",
                           st["BodyCustom"]))
    story.append(PageBreak())

    # Índice
    story.append(Paragraph("Índice", st["H1Custom"]))
    for codigo in fase1_codes:
        it = by_codigo[codigo]
        story.append(Paragraph(f"<b>{codigo}</b> — {it['titulo']}", st["BodyCustom"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Resumen Fases 2/3/4 (al final)", st["BodyCustom"]))
    story.append(PageBreak())

    # Secciones detalladas Fase 1
    for codigo in fase1_codes:
        it = by_codigo[codigo]
        guion = GUIONES_FASE1.get(codigo)
        if not guion: continue

        story.append(Paragraph(f"{codigo} — {it['titulo']}", st["H1Custom"]))

        meta = [
            ["Área", it.get("area") or "—"],
            ["Fase", str(it.get("fase") or "—")],
            ["Dificultad", it.get("dificultad") or "—"],
            ["Ruta UI", it.get("ruta") or "—"],
            ["Estado", _status_label(it)],
        ]
        t = Table(meta, colWidths=[3.5 * cm, 12 * cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
            ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#ddd")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#eee")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph("Descripción", st["H3Custom"]))
        story.append(Paragraph(it["descripcion"], st["BodyCustom"]))

        story.append(Paragraph("Datos de prueba", st["H3Custom"]))
        story.append(Paragraph(guion["datos_prueba"], st["BodyCustom"]))

        story.append(Paragraph("Pasos de verificación", st["H3Custom"]))
        for i, paso in enumerate(guion["pasos"], 1):
            story.append(Paragraph(f"<b>{i}.</b> {paso}", st["Step"]))

        story.append(Paragraph("Criterio de aceptación", st["H3Custom"]))
        story.append(Paragraph(guion["criterio_aceptacion"], st["Note"]))

        story.append(PageBreak())

    # Resumen Fases 2/3/4
    story.append(Paragraph("Resumen — Fases 2, 3 y 4", st["H1Custom"]))
    story.append(Paragraph("Los siguientes requisitos no son foco de esta demo. Su guion detallado de "
                           "verificación se completa al cerrar la fase correspondiente.", st["BodyCustom"]))
    story.append(Spacer(1, 0.3 * cm))

    for fase in [2, 3, 4]:
        story.append(Paragraph(f"Fase {fase}", st["H2Custom"]))
        rows = [["Código", "Título", "Área", "Estado"]]
        for it in CATALOGO:
            if it["fase"] != fase: continue
            rows.append([it["codigo"], it["titulo"], it.get("area") or "—", _status_label(it)])
        if len(rows) == 1: continue
        t = Table(rows, colWidths=[1.8 * cm, 8.5 * cm, 2.4 * cm, 4.5 * cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#ddd")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#eee")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5 * cm))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "docs" / "VERIFICACION_REQUISITOS_FASE1.pdf"
    p = generate(out)
    print(f"PDF generado: {p}")
