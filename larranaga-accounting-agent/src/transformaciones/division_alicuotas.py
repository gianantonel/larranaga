"""
R-02: División de Comprobantes por Múltiples Alícuotas

Transforma archivos ARCA de formato "wide" (una fila con múltiples alícuotas)
a formato "long" (una fila por alícuota), requerido por Holistor.

Reglas:
  - Si una fila tiene 2+ netos con valores, expandir a N filas (una por alícuota)
  - Cada fila expandida:
    * Mantiene cabecera (Fecha, Tipo, Punto, Número, CUIT, CUIT Receptor, etc)
    * Una alícuota activa (neto+IVA), resto = 0
    * Imp. Total preservado exactamente
    * Otros Tributos: 100% en alícuota primaria (21% si existe, sino la más alta)
    * Número de comprobante con sufijo: "991" → "991/A", "991/B", etc

Ejemplo: Claro con IVA 21% (neto 89.516,16) + IVA 27% (neto 181.350,87)
  Entrada (1 fila):
    Fecha=20/04/23, Tipo=1, Punto=001, Número=991, Cuit=...,
    Neto 21%=89.516,16, IVA 21%=18.798,39,
    Neto 27%=181.350,87, IVA 27%=48.965,19,
    Imp. Total=259.630,61

  Salida (2 filas):
    Fila A: Neto 21%=89.516,16, IVA 21%=18.798,39, Neto 27%=0, IVA 27%=0,
            Imp. Total=108.314,55, Número=991/A
    Fila B: Neto 21%=0, IVA 21%=0, Neto 27%=181.350,87, IVA 27%=48.965,19,
            Imp. Total=230.316,06, Número=991/B
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Any


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES - Mapeo de índices ARCA (0-indexed)
# ─────────────────────────────────────────────────────────────────────────────

# Nombres de columnas ARCA (header=1)
COL_NUMERO = "Número"
COL_NETO_TOTAL = "Neto Gravado Total"
COL_IVA_TOTAL = "Total IVA"
COL_OTROS_TRIBUTOS = "Otros Tributos"
COL_IMP_TOTAL = "Imp. Total"

# Tasas de alícuota soportadas (en orden de prioridad para asignar Otros Tributos)
ALICUOTAS = [21, 27, 10.5, 5, 2.5, 0]
ALICUOTA_PRIMARIA = 21  # Prioridad para asignar Otros Tributos

# Mapeo de alícuota → columnas [neto, iva]
ALICUOTA_COLS = {
    0:    ("Neto Grav. IVA 0%",      "IVA 0%"),  # IVA 0% no existe en Excel, pero lo mantenemos
    2.5:  ("Neto Grav. IVA 2,5%",    "IVA 2,5%"),
    5:    ("Neto Grav. IVA 5%",      "IVA 5%"),
    10.5: ("Neto Grav. IVA 10,5%",   "IVA 10,5%"),
    21:   ("Neto Grav. IVA 21%",     "IVA 21%"),
    27:   ("Neto Grav. IVA 27%",     "IVA 27%"),
}

# Columnas que deben ser cero en filas B/C o en alícuotas inactivas
COLS_NETO_ALL = [col for col, _ in ALICUOTA_COLS.values()]
COLS_IVA_ALL = [col for _, col in ALICUOTA_COLS.values()]
COLS_A_CERO = COLS_NETO_ALL + COLS_IVA_ALL


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────

def parse_string_float(valor: str) -> float:
    """
    Convierte string ARCA con coma decimal a float.

    Ejemplos:
      "89.516,16" → 89516.16
      "1.234,56" → 1234.56
      "0" → 0.0
      "" → 0.0
      "1234.567,89" → 1234567.89
    """
    if pd.isna(valor) or valor == "" or str(valor).strip() == "":
        return 0.0

    try:
        # Limpiar y normalizar
        s = str(valor).strip()
        # Reemplazar . por '' (separador de miles) y , por . (decimal)
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def format_string_float(valor: float, decimales: int = 2) -> str:
    """
    Convierte float a string formato ARCA (coma decimal, puntos de miles).

    Ejemplos:
      89516.16 → "89.516,16"
      1234.56 → "1.234,56"
      0.0 → "0,00"
    """
    if pd.isna(valor):
        return "0,00"

    try:
        # Redondear a decimales especificados
        redondeado = round(float(valor), decimales)

        # Formatear con decimales
        formateado = f"{redondeado:.{decimales}f}"  # e.g., "89516.16"

        # Separar entero y decimal
        if "." in formateado:
            entero, decimal = formateado.split(".")
        else:
            entero, decimal = formateado, "00"

        # Agregar separadores de miles (puntos)
        entero_sep = ""
        for i, digit in enumerate(reversed(entero)):
            if i > 0 and i % 3 == 0:
                entero_sep = "." + entero_sep
            entero_sep = digit + entero_sep

        # Devolver con coma decimal
        return f"{entero_sep},{decimal}"
    except (ValueError, TypeError):
        return "0,00"


def extraer_tipo(valor_tipo: str) -> str:
    """
    Extrae el código numérico del tipo de comprobante.
    "1 - Factura A" → "1"
    "6 - Factura B" → "6"
    """
    if pd.isna(valor_tipo):
        return ""
    m = re.match(r'^\s*(\d+)\s*-', str(valor_tipo))
    return m.group(1) if m else ""


# ─────────────────────────────────────────────────────────────────────────────
# DETECCIÓN DE FILAS MULTI-ALÍCUOTA
# ─────────────────────────────────────────────────────────────────────────────

def detect_multi_alicuota_rows(df: pd.DataFrame) -> Dict[int, List[float]]:
    """
    Identifica filas con múltiples alícuotas activas.

    Args:
        df: DataFrame de ARCA (output de R-01)

    Returns:
        Dict: {fila_index: [lista de alícuotas activas]}
        Ejemplo: {5: [21, 27], 12: [5, 21, 27]}
    """
    multi_alicuota_rows = {}

    for idx, row in df.iterrows():
        alicuotas_activas = []

        for alicuota in ALICUOTAS:
            col_neto, col_iva = ALICUOTA_COLS[alicuota]

            if col_neto not in df.columns:
                continue

            neto = parse_string_float(row[col_neto])
            # Una alícuota está activa si tiene neto > 0 (ignoramos IVA)
            if neto > 0:
                alicuotas_activas.append(alicuota)

        if len(alicuotas_activas) > 1:
            multi_alicuota_rows[idx] = sorted(alicuotas_activas, reverse=True)

    return multi_alicuota_rows


# ─────────────────────────────────────────────────────────────────────────────
# EXPANSIÓN DE FILAS MULTI-ALÍCUOTA
# ─────────────────────────────────────────────────────────────────────────────

def expand_multi_alicuota_row(
    row: pd.Series,
    alicuotas: List[float],
    row_idx: int,
    df: pd.DataFrame
) -> List[pd.Series]:
    """
    Expande una fila multi-alícuota en N filas (una por alícuota).

    Args:
        row: pd.Series con la fila original
        alicuotas: [21, 27] o [5, 21, 27] (sorted desc)
        row_idx: índice original en df
        df: DataFrame completo (para acceso a columnas)

    Returns:
        List[pd.Series]: Filas expandidas (1 por alícuota)
    """
    filas_expandidas = []

    # Obtener número original para sufijo
    numero_original = str(row[COL_NUMERO]) if COL_NUMERO in row.index else ""

    # Determinar alícuota primaria (para Otros Tributos)
    alicuota_primaria = ALICUOTA_PRIMARIA if ALICUOTA_PRIMARIA in alicuotas else alicuotas[0]

    # Obtener Otros Tributos
    otros_tributos = parse_string_float(row[COL_OTROS_TRIBUTOS]) if COL_OTROS_TRIBUTOS in row.index else 0.0

    for pos, alicuota in enumerate(alicuotas):
        # Crear copia de la fila
        nueva_fila = row.copy()

        # Actualizar número con sufijo (A, B, C, ...)
        sufijo = chr(65 + pos)  # A, B, C, ...
        nuevo_numero = f"{numero_original}/{sufijo}"
        if COL_NUMERO in nueva_fila.index:
            nueva_fila[COL_NUMERO] = nuevo_numero

        # Zerear todas las columnas de neto e IVA
        for col in COLS_A_CERO:
            if col in nueva_fila.index:
                nueva_fila[col] = "0"

        # Activar solo la alícuota de esta fila
        col_neto, col_iva = ALICUOTA_COLS[alicuota]

        # Obtener valores de la fila original
        neto_original = parse_string_float(row[col_neto])
        iva_original = parse_string_float(row[col_iva])

        # Asignar a la fila expandida
        nueva_fila[col_neto] = format_string_float(neto_original)
        nueva_fila[col_iva] = format_string_float(iva_original)

        # Recalcular resúmenes (Neto Gravado Total, Total IVA)
        if COL_NETO_TOTAL in nueva_fila.index:
            nueva_fila[COL_NETO_TOTAL] = format_string_float(neto_original)
        if COL_IVA_TOTAL in nueva_fila.index:
            nueva_fila[COL_IVA_TOTAL] = format_string_float(iva_original)

        # Asignar Otros Tributos solo a la alícuota primaria
        if COL_OTROS_TRIBUTOS in nueva_fila.index:
            if alicuota == alicuota_primaria:
                nueva_fila[COL_OTROS_TRIBUTOS] = format_string_float(otros_tributos)
            else:
                nueva_fila[COL_OTROS_TRIBUTOS] = "0"

        # Recalcular Imp. Total: neto + IVA + otros tributos (solo en primaria)
        total_expandido = neto_original + iva_original
        if alicuota == alicuota_primaria:
            total_expandido += otros_tributos

        if COL_IMP_TOTAL in nueva_fila.index:
            nueva_fila[COL_IMP_TOTAL] = format_string_float(total_expandido)

        filas_expandidas.append(nueva_fila)

    return filas_expandidas


# ─────────────────────────────────────────────────────────────────────────────
# APLICACIÓN DE LA TRANSFORMACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def aplicar_division_alicuotas(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aplica la división por alícuotas al DataFrame completo.

    Args:
        df: DataFrame de ARCA (output de R-01, todas las columnas como strings)

    Returns:
        Tuple: (df_expandido, stats_dict)
        - df_expandido: DataFrame con filas expandidas
        - stats_dict: {
            "total_entrada": int (filas originales),
            "filas_multi_alicuota": int (filas con 2+ alícuotas),
            "filas_expandidas": int (filas nuevas creadas),
            "total_salida": int (filas finales),
          }
    """
    df = df.copy()

    # Detectar filas multi-alícuota
    multi_alicuota_map = detect_multi_alicuota_rows(df)

    total_entrada = len(df)
    filas_multi_alicuota = len(multi_alicuota_map)
    filas_expandidas = 0

    # Construir nueva lista de filas
    nuevas_filas = []

    for idx, row in df.iterrows():
        if idx in multi_alicuota_map:
            # Expandir esta fila
            alicuotas = multi_alicuota_map[idx]
            filas_exp = expand_multi_alicuota_row(row, alicuotas, idx, df)
            nuevas_filas.extend(filas_exp)
            filas_expandidas += len(filas_exp) - 1  # -1 porque la original se reemplaza
        else:
            # Fila sin expansión, copiar tal cual
            nuevas_filas.append(row)

    # Reconstruir DataFrame
    df_expandido = pd.DataFrame(nuevas_filas)
    df_expandido.reset_index(drop=True, inplace=True)

    total_salida = len(df_expandido)

    stats = {
        "total_entrada": total_entrada,
        "filas_multi_alicuota": filas_multi_alicuota,
        "filas_expandidas": filas_expandidas,
        "total_salida": total_salida,
    }

    print(f"  -> División por alícuotas:")
    print(f"     - Filas entrada: {total_entrada}")
    print(f"     - Filas multi-alícuota: {filas_multi_alicuota}")
    print(f"     - Filas expandidas: {filas_expandidas}")
    print(f"     - Filas salida: {total_salida}")

    return df_expandido, stats


# ─────────────────────────────────────────────────────────────────────────────
# VALIDACIÓN POST-EXPANSIÓN
# ─────────────────────────────────────────────────────────────────────────────

def validar_expansion(df_orig: pd.DataFrame, df_expanded: pd.DataFrame) -> Dict[str, Any]:
    """
    Valida que la expansión haya sido correcta.

    Verifica:
      - Total de filas coherente (salida >= entrada)
      - Sumas de Imp. Total preservadas por grupo (mismo número/cuit)
      - Columnas de alícuota inactivas en ceros
      - Formato de números preservado

    Args:
        df_orig: DataFrame original (pre-expansión)
        df_expanded: DataFrame expandido (post-expansión)

    Returns:
        Dict: {
          "valido": bool,
          "errores": [lista de strings con problemas],
          "advertencias": [lista de strings con warnings],
        }
    """
    errores = []
    advertencias = []
    valido = True

    # Validación 1: Número de filas
    if len(df_expanded) < len(df_orig):
        errores.append(f"Filas salida ({len(df_expanded)}) < filas entrada ({len(df_orig)})")
        valido = False

    # Validación 2: Totales preservados (si hay Imp. Total)
    if COL_IMP_TOTAL in df_orig.columns and COL_IMP_TOTAL in df_expanded.columns:
        try:
            total_orig = sum(parse_string_float(v) for v in df_orig[COL_IMP_TOTAL])
            total_exp = sum(parse_string_float(v) for v in df_expanded[COL_IMP_TOTAL])

            # Permitir error de ±0.01 por redondeo
            if abs(total_orig - total_exp) > 0.01:
                advertencias.append(
                    f"Suma Imp. Total: original={total_orig:.2f}, "
                    f"expandida={total_exp:.2f} (diferencia={abs(total_orig - total_exp):.4f})"
                )
        except Exception as e:
            advertencias.append(f"No se pudo validar suma Imp. Total: {str(e)}")

    # Validación 3: Formato de números con sufijos
    if COL_NUMERO in df_expanded.columns:
        for idx, numero in enumerate(df_expanded[COL_NUMERO]):
            s = str(numero).strip()
            # Números expandidos deben tener formato "###/A", "###/B", etc. O sin sufijo
            if "/" in s:
                if not re.match(r'^\d+/[A-Z]$', s):
                    advertencias.append(f"Fila {idx}: número con formato sospechoso: '{s}'")

    resultado = {
        "valido": valido and len(errores) == 0,
        "errores": errores,
        "advertencias": advertencias,
    }

    if resultado["valido"]:
        print("  -> Validación: OK")
    else:
        print("  -> Validación: FALLOS")
        for err in errores:
            print(f"     ERROR: {err}")

    for adv in advertencias:
        print(f"     WARN: {adv}")

    return resultado
