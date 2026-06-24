"""Genera un único PDF con todos los requisitos de Fase 1 (R-01, R-02, R-03, R-04, R-05, R-07).

El documento tiene portada + resumen + índice y luego una sección por requisito que
explica qué hace, el problema que resuelve, cómo funciona paso a paso, entradas/salidas,
archivos de implementación, endpoints, UI, validaciones, tests y la verificación E2E.

Uso:
    cd backend
    .venv/Scripts/python.exe scripts/generate_requisito_pdfs.py

Output: docs/Requisitos_Fase1.pdf
"""
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem,
    PageBreak,
)

# ─── Paleta ───────────────────────────────────────────────────────────────────
AZUL = colors.HexColor("#1e293b")
VIOLETA = colors.HexColor("#7c3aed")
GRIS = colors.HexColor("#64748b")
GRIS_CLARO = colors.HexColor("#f1f5f9")
VERDE = colors.HexColor("#059669")
BORDE = colors.HexColor("#cbd5e1")

# ─── Estilos ──────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()
H_TITULO = ParagraphStyle("hTit", parent=ss["Title"], textColor=AZUL, fontSize=22,
                          spaceAfter=2, leading=26)
H_SUB = ParagraphStyle("hSub", parent=ss["Normal"], textColor=GRIS, fontSize=11,
                       spaceAfter=14)
H_SEC = ParagraphStyle("hSec", parent=ss["Heading2"], textColor=VIOLETA, fontSize=13,
                       spaceBefore=14, spaceAfter=6, leading=16)
P = ParagraphStyle("p", parent=ss["Normal"], fontSize=10.5, leading=15, spaceAfter=6,
                   alignment=TA_LEFT)
P_LISTA = ParagraphStyle("pl", parent=P, spaceAfter=3, leftIndent=2)
CODE = ParagraphStyle("code", parent=ss["Code"], fontSize=9, leading=12,
                      textColor=AZUL, backColor=GRIS_CLARO, borderPadding=6,
                      spaceAfter=8)
PIE = ParagraphStyle("pie", parent=ss["Normal"], fontSize=8, textColor=GRIS)


def chip(texto, color):
    t = Table([[texto]], colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def tabla_kv(filas):
    data = [[Paragraph(f"<b>{k}</b>", P), Paragraph(v, P)] for k, v in filas]
    t = Table(data, colWidths=[4.2 * cm, 11.8 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
        ("BACKGROUND", (0, 0), (0, -1), GRIS_CLARO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(i, P_LISTA), leftIndent=10, value="•") for i in items],
        bulletType="bullet", start="•", leftIndent=12,
    )


# ─── Contenido por requisito ──────────────────────────────────────────────────
REQUISITOS = [
    {
        "codigo": "R-01",
        "titulo": "Corrección de comprobantes tipo B/C + formato de Tipo de Cambio",
        "area": "IVA / Contabilidad", "dificultad": "Muy fácil", "estado": "COMPLETO",
        "que_hace": "Toma el Excel \"Mis Comprobantes Recibidos\" exportado de ARCA y lo deja "
                    "listo para importar en Holistor, corrigiendo dos cosas que ARCA exporta mal: "
                    "(1) los comprobantes tipo B y C, y (2) el formato de la columna L (Tipo de Cambio).",
        "problema": "ARCA exporta los comprobantes tipo B y C con el neto gravado y el IVA "
                    "discriminados, pero para esos tipos el IVA no se puede computar como crédito "
                    "fiscal y Holistor espera esos campos en cero (solo el Importe Total). "
                    "Además, la columna de Tipo de Cambio viene con formato inconsistente que "
                    "Holistor rechaza. Hoy el estudio corrige esto a mano, comprobante por comprobante.",
        "como_funciona": [
            "Lee el Excel con <b>header en la fila 1</b> (la fila 0 trae el CUIT del titular).",
            "<b>corregir_tipo_bc()</b>: detecta los tipos AFIP B (6, 7, 8) y C (11, 12, 13) y "
            "pone en \"0\" todas las columnas de neto gravado e IVA por alícuota, sin tocar el "
            "Importe Total (que se conserva intacto).",
            "<b>corregir_columna_L()</b>: normaliza el Tipo de Cambio a string con coma decimal "
            "y dos decimales (ej. \"1450,00\"), que es lo que Holistor necesita. Si el valor es "
            "inválido usa un fallback seguro de \"1,00\" (operaciones en pesos).",
            "Devuelve el mismo Excel corregido, manteniendo todas las columnas y el orden original.",
        ],
        "entradas": "Excel .xlsx/.xls \"Mis Comprobantes Recibidos\" de ARCA (≈30 columnas).",
        "salidas": "Excel corregido descargable + estadísticas (filas de entrada, B/C corregidos).",
        "archivos": [
            "larranaga-accounting-agent/src/transformaciones/limpieza_inicial.py — lógica pura",
            "backend/app/routers/herramientas.py — endpoint HTTP",
            "frontend/src/pages/Herramientas.jsx — pantalla \"Adaptador Libro IVA Compras\"",
        ],
        "endpoint": "POST /herramientas/limpiar-libro-iva  (recibe client_id + archivo, devuelve corregido)",
        "ui": "Pantalla <b>Adaptador IVA</b>: seleccionar cliente → arrastrar el Excel → "
              "\"Procesar archivo\" → descargar el corregido.",
        "validaciones": [
            "El Importe Total nunca se modifica (solo se ceran neto e IVA en B/C).",
            "Fallback \"1,00\" para Tipo de Cambio inválido evita romper la importación.",
        ],
        "tests": "larranaga-accounting-agent/tests/test_limpieza_inicial.py — verde "
                 "(detección de tipo, corrección B/C, formato col. L, + fixture real BUTALO).",
        "e2e": "Verificado en navegador con el archivo real <b>BUTALO Feb-2026</b>: 359 filas de "
               "entrada, <b>12 comprobantes B/C corregidos</b>, archivo corregido descargado OK.",
    },
    {
        "codigo": "R-02",
        "titulo": "División de comprobantes por múltiples alícuotas de IVA",
        "area": "IVA / Contabilidad", "dificultad": "Muy fácil", "estado": "COMPLETO",
        "que_hace": "Cuando un mismo comprobante tiene IVA a más de una alícuota (por ejemplo 21% "
                    "y 27% en la misma factura), lo divide en una fila por cada alícuota, para que "
                    "Holistor pueda imputar cada porción a su cuenta contable correcta.",
        "problema": "ARCA exporta un comprobante multi-alícuota en una sola fila con varias columnas "
                    "de neto/IVA. Holistor necesita una fila por alícuota. Separar esto a mano es "
                    "lento y propenso a errores de cuadre.",
        "como_funciona": [
            "<b>detect_multi_alicuota_rows()</b>: recorre las columnas de neto por alícuota "
            "(10,5% / 21% / 27%) y detecta las filas con dos o más alícuotas activas (neto > 0).",
            "<b>expand_multi_alicuota_row()</b>: por cada fila multi-alícuota genera N filas, "
            "una por alícuota. Cada fila nueva conserva la cabecera (fecha, tipo, punto de venta, "
            "CUIT, etc.), deja activa solo una alícuota (su neto y su IVA) y pone el resto en cero.",
            "El <b>Importe Total se recalcula</b> por fila (neto + IVA + otros tributos). Los "
            "\"otros tributos\" se asignan 100% a la alícuota primaria (21% si existe, si no la más alta), "
            "de modo que la suma de las filas expandidas reproduce exactamente el total original.",
            "El número de comprobante recibe un sufijo para trazabilidad: \"991\" → \"991/A\", \"991/B\".",
            "<b>validar_expansion()</b>: post-validación que verifica que las sumas se preservan y "
            "los formatos quedan correctos. Las filas sin multi-alícuota pasan intactas (compatible con R-01).",
        ],
        "entradas": "El mismo Excel de ARCA, después de aplicar R-01.",
        "salidas": "Excel con las filas multi-alícuota ya expandidas + cantidad de filas divididas.",
        "archivos": [
            "larranaga-accounting-agent/src/transformaciones/division_alicuotas.py",
            "Integrado en POST /herramientas/limpiar-libro-iva (corre después de R-01)",
        ],
        "endpoint": "POST /herramientas/limpiar-libro-iva  (R-01 + R-02 en un solo paso)",
        "ui": "Misma pantalla <b>Adaptador IVA</b>; el resultado muestra \"Multi-alícuota (R-02)\".",
        "validaciones": [
            "La suma de las filas expandidas = Importe Total del comprobante original.",
            "Parseo dual de formato numérico (ARCA con coma decimal y estándar con punto).",
            "Redondeo consistente a 2 decimales; validación posterior de cuadre por fila.",
        ],
        "tests": "larranaga-accounting-agent/tests/test_division_alicuotas.py — verde "
                 "(detección, expansión 2 y 3 tasas, sufijos, roundtrip, compatibilidad con R-01).",
        "e2e": "Verificado con BUTALO Feb-2026: <b>9 comprobantes multi-alícuota expandidos</b>, "
               "pasando de 359 a <b>368 filas de salida</b> (359 + 9). Cuadre correcto.",
    },
    {
        "codigo": "R-03",
        "titulo": "Cálculo automático de honorarios (fijo y valor producto)",
        "area": "Administración", "dificultad": "Muy fácil", "estado": "COMPLETO",
        "que_hace": "Calcula automáticamente el honorario mensual de cada cliente, soportando dos "
                    "modalidades: importe fijo, o cantidad de unidades multiplicada por el precio "
                    "vigente de un producto de referencia (ej. bolsa de cemento).",
        "problema": "El estudio calcula honorarios en planillas Excel. Los honorarios \"por producto\" "
                    "obligan a actualizar manualmente cada cliente cuando cambia el precio de referencia. "
                    "Es repetitivo y se presta a errores.",
        "como_funciona": [
            "Cada cliente se configura con un <b>tipo_honorario</b>: \"fijo\" o \"producto\".",
            "<b>Tipo fijo</b>: el honorario es directamente el campo importe_honorario del cliente.",
            "<b>Tipo producto</b>: honorario = cantidad_unidades × precio_vigente del producto de "
            "referencia. Al calcular se guarda un <b>snapshot del precio</b> usado, para que quede "
            "registrado con qué valor se liquidó.",
            "El cálculo puede correrse por cliente individual o para todos los clientes activos del "
            "período de una sola vez (\"Calcular período\").",
            "Los productos de referencia tienen <b>historial de precios</b> (cada cambio queda "
            "registrado con su fecha de vigencia).",
        ],
        "entradas": "Configuración de honorario por cliente + catálogo de productos de referencia.",
        "salidas": "Honorarios calculados por cliente y período, con tipo, importe y precio snapshot.",
        "archivos": [
            "backend/app/routers/honorarios.py — endpoints y lógica de cálculo",
            "backend/app/models.py — Honorario, ProductoReferencia, HistorialPrecioProducto",
            "frontend/src/pages/Honorarios.jsx — pantalla de gestión",
        ],
        "endpoint": "GET /honorarios/  ·  POST /honorarios/calcular/{client_id}/{period}  ·  "
                    "POST /honorarios/calcular-periodo/{period}  ·  gestión de productos de referencia",
        "ui": "Pantalla <b>Honorarios</b>: tarjetas de resumen, CRUD de productos de referencia, "
              "configuración por cliente y botón \"Calcular período\".",
        "validaciones": [
            "Rechaza el cálculo si el cliente no tiene tipo_honorario configurado.",
            "Tipo fijo exige importe_honorario; tipo producto exige producto y cantidad.",
            "Recalcular un período reemplaza el honorario previo (idempotente).",
        ],
        "tests": "Cubierto por la lógica de cálculo del router (tipos fijo/producto y validaciones).",
        "e2e": "Verificado en navegador: \"Calcular período\" generó <b>10 honorarios</b> para "
               "Jun-2026 por un total de <b>$11.580.000</b>, cada uno con su tipo e importe.",
    },
    {
        "codigo": "R-04",
        "titulo": "Liquidación mensual de profesionales",
        "area": "Administración", "dificultad": "Muy fácil", "estado": "COMPLETO",
        "que_hace": "Arma la liquidación mensual de cada profesional del estudio: cuánto le "
                    "corresponde cobrar combinando los honorarios de sus clientes, los adelantos "
                    "que ya percibió, el saldo del mes anterior y los reintegros de gastos.",
        "problema": "La liquidación de cada profesional se calcula a mano cruzando varias planillas "
                    "(honorarios, adelantos, saldos arrastrados). Es lento y difícil de auditar.",
        "como_funciona": [
            "<b>Fórmula:</b> total_a_cobrar = honorarios_totales − adelantos + saldo_anterior + reintegros.",
            "<b>honorarios_totales</b>: surge de los honorarios calculados (R-03) de los clientes "
            "asignados al profesional.",
            "<b>adelantos</b>: se suman en tiempo real desde la tabla de pagos cuyo destinatario es "
            "ese profesional, en el período.",
            "<b>saldo_anterior</b>: se arrastra del cierre del mes anterior (liquidación ya cerrada).",
            "<b>reintegros</b>: gastos cargados manualmente que se le devuelven al profesional.",
            "Al cerrar el mes se registran los cobros (efectivo/transferencia) y se calcula el "
            "<b>saldo_siguiente</b> que se arrastra al período próximo.",
        ],
        "entradas": "Honorarios del período (R-03), pagos/adelantos, reintegros y saldo previo.",
        "salidas": "Liquidación por profesional con el desglose y el total a cobrar; cierre de mes.",
        "archivos": [
            "backend/app/routers/profesionales_adm.py — endpoints de liquidación",
            "backend/app/services/liquidacion.py — cálculo de preview",
            "frontend/src/pages/Liquidaciones.jsx — pantalla por profesional",
        ],
        "endpoint": "GET /profesionales/liquidaciones/preview  ·  "
                    "GET /profesionales/liquidaciones/{id}/{period}  ·  "
                    "POST /profesionales/liquidaciones/{id}/{period}/cerrar",
        "ui": "Pantalla <b>Liquidaciones</b>: tabla por profesional con honorarios, adelantos, "
              "reintegros, total a cobrar y botón de cierre, con totales generales.",
        "validaciones": [
            "Depende de que los honorarios del período estén calculados (R-03) — by design.",
            "El saldo anterior solo se arrastra de liquidaciones efectivamente cerradas.",
        ],
        "tests": "Cubierto por el servicio de cálculo (mismo cálculo en preview y cierre).",
        "e2e": "Verificado en navegador: tras calcular honorarios (R-03), la pantalla de "
               "Liquidaciones mostró los <b>6 profesionales</b> con su honorario y un total general "
               "de <b>$11.580.000</b>, confirmando la integración R-03 → R-04.",
    },
    {
        "codigo": "R-05",
        "titulo": "Separación de retenciones IVA vs IIBB vs Ganancias",
        "area": "IVA / Contabilidad", "dificultad": "Fácil", "estado": "FUNCIONAL (requiere clave fiscal)",
        "que_hace": "Trae \"Mis Retenciones\" de ARCA para un cliente y período (vía scraping con "
                    "clave fiscal) y clasifica cada retención/percepción según su impuesto, "
                    "separando IVA, Ingresos Brutos (IIBB) y Ganancias, y mapeándolas al código "
                    "Holistor correspondiente.",
        "problema": "Para armar la columna AB (Otros Tributos) del libro IVA hay que distinguir qué "
                    "retenciones son de IVA, cuáles de IIBB (por provincia) y cuáles de Ganancias. "
                    "Hacerlo a mano desde el portal de ARCA es tedioso.",
        "como_funciona": [
            "El usuario elige cliente, período e impuesto y dispara \"Consultar ARCA\".",
            "El backend encola un <b>job en segundo plano</b> (el scraping de ARCA tarda 1–3 min, "
            "más de lo que tolera un request HTTP normal) y el frontend va consultando su estado.",
            "Al terminar, cada registro se persiste de forma <b>idempotente</b> (evita duplicados por "
            "número de certificado o por CUIT+fecha+comprobante).",
            "<b>classify_regimen()</b> mapea el código de impuesto AFIP a un código Holistor: "
            "IVA → PIVC; Ganancias → PGAN; IIBB → PIBA/PIBC/PIBR según provincia; sellos/comercio "
            "→ SELL/PCOM; lo no mapeado → OTRO.",
            "La pantalla muestra chips de resumen por código y el detalle por registro, con el "
            "código de régimen y el código Holistor de cada uno.",
        ],
        "entradas": "CUIT + clave fiscal del cliente (cifrada), período e impuesto a consultar.",
        "salidas": "Registros de retenciones/percepciones clasificados + resumen por código Holistor.",
        "archivos": [
            "backend/app/afip_sdk/retenciones.py — clasificador (classify_regimen) y mapa de códigos",
            "backend/app/routers/retenciones.py — sync asíncrono + listados",
            "frontend/src/components/UI/RetencionesPanel.jsx — filtro, chips y tabla",
        ],
        "endpoint": "POST /retenciones/sync  ·  GET /retenciones/sync/{job_id}  ·  "
                    "GET /retenciones/  ·  GET /retenciones/summary/{client_id}",
        "ui": "Pantalla <b>Retenciones y Percepciones</b>: selección de cliente/período/impuesto "
              "(IVA, Ganancias, Bienes Personales e IIBB por provincia) y consulta a ARCA.",
        "validaciones": [
            "Exige que el cliente tenga CUIT y clave fiscal cargada.",
            "Sincronización idempotente: no duplica registros ya traídos.",
            "Manejo de errores del scraping con estado del job (pending/running/done/error).",
        ],
        "tests": "backend/tests/test_retenciones_classifier.py — verde (mapeo de códigos a Holistor, "
                 "IVA/Ganancias/IIBB, coerción de tipos y código desconocido → OTRO).",
        "e2e": "La pantalla se verificó en navegador (selección de cliente/período/impuesto y filtro "
               "IIBB disponible). La consulta en vivo a ARCA <b>requiere la clave fiscal real del "
               "cliente</b>, por lo que la traída de datos no se valida en este entorno de prueba.",
    },
    {
        "codigo": "R-07",
        "titulo": "Cuentas corrientes de clientes — saldo en tiempo real",
        "area": "Administración", "dificultad": "Fácil", "estado": "COMPLETO",
        "que_hace": "Lleva la cuenta corriente de cada cliente: registra movimientos (ingresos y "
                    "egresos) y muestra el saldo recalculado en el momento, indicando si el cliente "
                    "está en deuda o a favor.",
        "problema": "El estudio sigue los saldos de clientes en planillas separadas que se "
                    "desactualizan. No hay una vista única y confiable del saldo al día.",
        "como_funciona": [
            "Cada movimiento tiene un <b>tipo</b>: \"ingreso\" (el cliente paga) o \"egreso\" "
            "(un cargo/honorario al cliente), con monto, concepto y fecha.",
            "El <b>saldo se calcula en la base de datos</b> con una sola operación "
            "SUM(CASE...): los ingresos suman y los egresos restan. Saldo > 0 = a favor del "
            "cliente; saldo < 0 = deuda.",
            "El mismo cálculo se usa tanto en el listado de clientes como en el endpoint dedicado "
            "de saldo, garantizando consistencia.",
            "La pantalla lista los clientes con su saldo y, al seleccionar uno, muestra el "
            "historial de movimientos y permite cargar uno nuevo.",
        ],
        "entradas": "Movimientos de cuenta corriente (tipo, monto, concepto, fecha).",
        "salidas": "Saldo por cliente (deuda / a favor) + historial de movimientos.",
        "archivos": [
            "backend/app/routers/cuentas_corrientes.py — movimientos y saldo (SQL)",
            "backend/app/routers/clients.py — saldo_cc por cliente (mismo helper)",
            "frontend/src/pages/CuentasCorrientes.jsx — listado, saldo y detalle",
        ],
        "endpoint": "GET /cuentas-corrientes/client/{id}  ·  POST /cuentas-corrientes/  ·  "
                    "GET /cuentas-corrientes/client/{id}/saldo",
        "ui": "Pantalla <b>Cuentas Corrientes</b>: buscador de clientes, saldo destacado "
              "(verde a favor / rojo deuda), historial y modal de \"Nuevo Movimiento\".",
        "validaciones": [
            "tipo restringido a \"ingreso\" o \"egreso\" (validado en la API).",
            "monto debe ser mayor a 0.",
            "Saldo calculado en la BD (eficiente, sin cargar todos los movimientos a memoria).",
        ],
        "tests": "Suite backend en verde tras refactorizar el cálculo de saldo a SQL.",
        "e2e": "Verificado en navegador: \"Restaurante El Gaucho\" muestra <b>$5.000 (Deuda)</b> "
               "con su historial de movimientos; el saldo coincide tras el refactor a SQL.",
    },
]


def seccion_requisito(req):
    """Devuelve la lista de flowables de un requisito (una sección del PDF único)."""
    flow = []
    flow.append(Paragraph(f"{req['codigo']} · {req['titulo']}", H_TITULO))
    flow.append(Paragraph("Estudio Larrañaga & Asociados · Plataforma de gestión · Fase 1", H_SUB))

    meta = Table([[
        chip(f"Área: {req['area']}", AZUL),
        chip(f"Dificultad: {req['dificultad']}", GRIS),
        chip(f"Estado: {req['estado']}", VERDE if req["estado"].startswith("COMPLETO") else VIOLETA),
    ]], colWidths=[5.6 * cm, 5.2 * cm, 5.2 * cm])
    meta.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    flow.append(meta)
    flow.append(Spacer(1, 10))

    flow.append(Paragraph("Qué hace", H_SEC))
    flow.append(Paragraph(req["que_hace"], P))

    flow.append(Paragraph("Problema que resuelve", H_SEC))
    flow.append(Paragraph(req["problema"], P))

    flow.append(Paragraph("Cómo funciona (paso a paso)", H_SEC))
    flow.append(bullets(req["como_funciona"]))

    flow.append(Paragraph("Entradas y salidas", H_SEC))
    flow.append(tabla_kv([("Entradas", req["entradas"]), ("Salidas", req["salidas"])]))
    flow.append(Spacer(1, 6))

    flow.append(Paragraph("Implementación", H_SEC))
    flow.append(tabla_kv([
        ("Endpoint(s)", req["endpoint"]),
        ("Pantalla (UI)", req["ui"]),
    ]))
    flow.append(Spacer(1, 4))
    flow.append(Paragraph("<b>Archivos clave:</b>", P))
    flow.append(bullets([Paragraph(a, P_LISTA).text for a in req["archivos"]]))

    flow.append(Paragraph("Validaciones y reglas", H_SEC))
    flow.append(bullets(req["validaciones"]))

    flow.append(Paragraph("Tests automatizados", H_SEC))
    flow.append(Paragraph(req["tests"], P))

    flow.append(Paragraph("Verificación end-to-end", H_SEC))
    flow.append(Paragraph(req["e2e"], P))

    return flow


def portada_e_indice():
    """Portada + resumen ejecutivo + índice de los requisitos de Fase 1."""
    flow = []
    flow.append(Spacer(1, 3 * cm))
    flow.append(Paragraph("Requisitos de Fase 1", H_TITULO))
    flow.append(Paragraph(
        "Estudio Larrañaga &amp; Asociados · Plataforma de gestión · Documentación funcional",
        H_SUB))
    flow.append(Spacer(1, 0.6 * cm))
    flow.append(Paragraph(
        "La Fase 1 cubre los seis requisitos de arranque de la plataforma: la adaptación del "
        "libro IVA compras de ARCA (R-01 y R-02), el cálculo de honorarios y la liquidación de "
        "profesionales (R-03 y R-04), la separación de retenciones (R-05) y las cuentas "
        "corrientes de clientes (R-07). Este documento describe en detalle qué hace cada uno, "
        "cómo funciona, dónde está implementado y cómo se verificó.", P))
    flow.append(Spacer(1, 0.5 * cm))

    encab = ["Código", "Requisito", "Área", "Estado"]
    filas = [[Paragraph(f"<b>{c}</b>", P) for c in encab]]
    for r in REQUISITOS:
        filas.append([
            Paragraph(f"<b>{r['codigo']}</b>", P),
            Paragraph(r["titulo"], P),
            Paragraph(r["area"], P),
            Paragraph(r["estado"], P),
        ])
    t = Table(filas, colWidths=[2 * cm, 8.5 * cm, 3 * cm, 2.5 * cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 0.8 * cm))
    flow.append(Paragraph(
        f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
        "Optimizar × Larrañaga · Uso interno", PIE))
    return flow


def main():
    out_dir = Path(__file__).resolve().parents[2] / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    ruta = out_dir / "Requisitos_Fase1.pdf"

    doc = SimpleDocTemplate(
        str(ruta), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
        title="Requisitos de Fase 1 — Larrañaga & Asociados", author="Optimizar × Larrañaga",
    )

    flow = []
    flow += portada_e_indice()
    for req in REQUISITOS:
        flow.append(PageBreak())
        flow += seccion_requisito(req)

    doc.build(flow)
    print(f"  OK  {ruta}")
    print(f"\nPDF único con {len(REQUISITOS)} requisitos de Fase 1 generado en {ruta}")


if __name__ == "__main__":
    main()
