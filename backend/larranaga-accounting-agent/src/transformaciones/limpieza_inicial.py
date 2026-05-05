"""
R-01: Corrección de comprobantes tipo B/C y formato columna L (Tipo de Cambio).

Reglas:
  - Comprobantes tipo B (6=Factura B, 7=ND B, 8=NC B)
    y tipo C (11=Factura C, 12=ND C, 13=NC C):
      -> Columnas neto gravado por alicuota -> 0
      -> Columnas IVA por alicuota         -> 0
      -> Imp. Total                        -> sin cambios

  - Columna "Tipo Cambio" (col L del Excel de ARCA):
      -> Forzar a string "1,00" (coma decimal, 2 digitos).
         Holistor espera este formato exacto como factor multiplicador.
         Si llega como entero 1 y se importa sin decimales, la importacion
         puede fallar silenciosamente o generar importes incorrectos.

Uso CLI:
    python -m src.transformaciones.limpieza_inicial entrada.xlsx salida.xlsx
"""

import sys
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Tipos de comprobante AFIP oficiales que requieren correccion
# ---------------------------------------------------------------------------
TIPOS_B  = {"6", "7", "8"}          # Factura B, ND B, NC B
TIPOS_C  = {"11", "12", "13"}       # Factura C, ND C, NC C
TIPOS_BC = TIPOS_B | TIPOS_C

# ---------------------------------------------------------------------------
# Nombres de columnas reales del Excel de ARCA (header=1 al leer)
# ---------------------------------------------------------------------------
COL_TIPO         = "Tipo"
COL_TIPO_CAMBIO  = "Tipo Cambio"    # columna L del Excel

COLS_NETO = [
    "Neto Grav. IVA 0%",
    "Neto Grav. IVA 2,5%",
    "Neto Grav. IVA 5%",
    "Neto Grav. IVA 10,5%",
    "Neto Grav. IVA 21%",
    "Neto Grav. IVA 27%",
    "Neto Gravado Total",   # columna resumen — también va a 0 en B/C
]
COLS_IVA = [
    "IVA 2,5%",
    "IVA 5%",
    "IVA 10,5%",
    "IVA 21%",
    "IVA 27%",
    "Total IVA",            # columna resumen — también va a 0 en B/C
]
COLS_A_CERO = COLS_NETO + COLS_IVA


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extraer_tipo(valor_tipo: str) -> str:
    """
    Extrae el codigo numerico del tipo de comprobante.
      "1 - Factura A"  -> "1"
      "6 - Factura B"  -> "6"
      "11 - Factura C" -> "11"
    """
    if pd.isna(valor_tipo):
        return ""
    return str(valor_tipo).split("-")[0].strip()


# ---------------------------------------------------------------------------
# Transformaciones
# ---------------------------------------------------------------------------

def corregir_tipo_bc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para filas B/C: pone en 0 todas las columnas de neto e IVA.
    El Imp. Total no se toca.
    """
    df = df.copy()
    mascara_bc = df[COL_TIPO].apply(extraer_tipo).isin(TIPOS_BC)

    for col in COLS_A_CERO:
        if col in df.columns:
            df.loc[mascara_bc, col] = "0"

    n = int(mascara_bc.sum())
    print(f"  -> Tipo B/C: {n} comprobantes corregidos")
    return df


def corregir_columna_L(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fuerza la columna Tipo Cambio a string con coma decimal y 2 digitos.
    Formato requerido por Holistor: "1,00", "1450,00", "1395,00".

      1     -> "1,00"
      1450  -> "1450,00"
      "1,0" -> "1,00"
    """
    df = df.copy()

    def parsear(valor) -> str:
        try:
            # Normalizar separador: coma -> punto para parsear como float
            limpio = str(valor).strip().replace(".", "").replace(",", ".")
            numero = round(float(limpio), 2)
            # Devolver con coma decimal para Holistor
            return f"{numero:.2f}".replace(".", ",")
        except (ValueError, TypeError):
            return "1,00"  # fallback seguro para operaciones en pesos

    if COL_TIPO_CAMBIO in df.columns:
        df[COL_TIPO_CAMBIO] = df[COL_TIPO_CAMBIO].apply(parsear)
        print(f"  -> Tipo Cambio: formato corregido en {len(df)} filas")
    else:
        print(f"  [!] Columna '{COL_TIPO_CAMBIO}' no encontrada, se omite")

    return df


# ---------------------------------------------------------------------------
# Funcion principal
# ---------------------------------------------------------------------------

def limpiar_comprobantes(ruta_entrada: str, ruta_salida: str) -> dict:
    """
    Lee el Excel de ARCA, aplica correcciones R-01 y guarda el resultado.

    Args:
        ruta_entrada: path al .xlsx original de ARCA
        ruta_salida:  path donde guardar el .xlsx corregido

    Returns:
        dict con estadisticas del procesamiento
    """
    print(f"\nLeyendo: {ruta_entrada}")

    # header=1: la fila 0 es el titulo con el CUIT del contribuyente
    df = pd.read_excel(ruta_entrada, header=1, dtype=str)

    total_filas = len(df)
    print(f"  -> {total_filas} comprobantes leidos")

    df = corregir_tipo_bc(df)
    df = corregir_columna_L(df)

    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(ruta_salida, index=False)
    print(f"  -> Guardado en: {ruta_salida}")

    mascara_bc = df[COL_TIPO].apply(extraer_tipo).isin(TIPOS_BC)
    return {
        "total":        total_filas,
        "tipo_bc":      int(mascara_bc.sum()),
        "tipo_a_otros": int((~mascara_bc).sum()),
        "salida":       ruta_salida,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def limpiar_comprobantes_desde_bytes(contenido: bytes) -> bytes:
    """
    Variante para uso desde el backend HTTP:
    recibe el archivo como bytes y devuelve el xlsx corregido como bytes.
    """
    import io
    df = pd.read_excel(io.BytesIO(contenido), header=1, dtype=str)
    df = corregir_tipo_bc(df)
    df = corregir_columna_L(df)
    out = io.BytesIO()
    df.to_excel(out, index=False)
    return out.getvalue()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python -m src.transformaciones.limpieza_inicial <entrada.xlsx> <salida.xlsx>")
        sys.exit(1)

    stats = limpiar_comprobantes(sys.argv[1], sys.argv[2])
    print(f"\nResumen: {stats['total']} totales | "
          f"{stats['tipo_bc']} B/C corregidos | "
          f"{stats['tipo_a_otros']} tipo A/otros sin cambios")
