"""
Tests para R-01: Correccion tipo B/C y columna L (Tipo Cambio).
Se usan tanto datos sinteticos (casos borde) como el fixture real de BUTALO SRL.

Nombres de columna reales del Excel de ARCA (header=1):
  "Tipo Cambio"          <- col L del Excel  (en el codigo: COL_TIPO_CAMBIO)
  "Imp. Total"           <- col AC del Excel (total, no se modifica)
  "Neto Grav. IVA 21%"  <- una de las columnas de neto que se ponen en 0
  "IVA 21%"             <- una de las columnas de IVA que se ponen en 0

Tipos AFIP B/C oficiales:
  B: 6 (Factura B), 7 (ND B), 8 (NC B)
  C: 11 (Factura C), 12 (ND C), 13 (NC C)
"""

import pytest
import pandas as pd
from pathlib import Path

from src.transformaciones.limpieza_inicial import (
    extraer_tipo,
    corregir_tipo_bc,
    corregir_columna_L,
    TIPOS_BC,
    COL_TIPO_CAMBIO,
    COLS_NETO,
    COLS_IVA,
)

FIXTURE = Path("tests/fixtures/comprobantes_butalo_feb2026.xlsx")


# ── Tests unitarios: extraer_tipo ────────────────────────────────────────────

def test_extraer_tipo_factura_a():
    assert extraer_tipo("1 - Factura A") == "1"

def test_extraer_tipo_factura_b():
    assert extraer_tipo("6 - Factura B") == "6"

def test_extraer_tipo_factura_c():
    assert extraer_tipo("11 - Factura C") == "11"

def test_extraer_tipo_nota_credito_c():
    assert extraer_tipo("13 - Nota de Credito C") == "13"

def test_extraer_tipo_valor_nulo():
    assert extraer_tipo(None) == ""

def test_todos_los_tipos_bc_estan_cubiertos():
    # B: 6 7 8  |  C: 11 12 13
    assert TIPOS_BC == {"6", "7", "8", "11", "12", "13"}


# ── Tests unitarios: corregir_tipo_bc ────────────────────────────────────────

@pytest.fixture
def df_mixto():
    """DataFrame con una factura A, una B y una C — columnas reales de ARCA."""
    return pd.DataFrame({
        "Tipo":                ["1 - Factura A", "6 - Factura B", "11 - Factura C"],
        "Neto Grav. IVA 21%": ["85000",          "5000",          "8000"],
        "IVA 21%":            ["17850",           "1050",          "1680"],
        "Tipo Cambio":        ["1",               "1",             "1"],
        "Imp. Total":         ["102850",          "6050",          "9680"],
    })


def test_factura_a_no_se_modifica(df_mixto):
    resultado = corregir_tipo_bc(df_mixto)
    assert resultado.loc[0, "Neto Grav. IVA 21%"] == "85000"
    assert resultado.loc[0, "IVA 21%"] == "17850"
    assert resultado.loc[0, "Imp. Total"] == "102850"

def test_factura_b_neto_va_a_cero(df_mixto):
    resultado = corregir_tipo_bc(df_mixto)
    assert resultado.loc[1, "Neto Grav. IVA 21%"] == "0"
    assert resultado.loc[1, "IVA 21%"] == "0"

def test_factura_b_total_no_cambia(df_mixto):
    resultado = corregir_tipo_bc(df_mixto)
    assert resultado.loc[1, "Imp. Total"] == "6050"

def test_factura_c_neto_va_a_cero(df_mixto):
    resultado = corregir_tipo_bc(df_mixto)
    assert resultado.loc[2, "Neto Grav. IVA 21%"] == "0"
    assert resultado.loc[2, "IVA 21%"] == "0"

def test_factura_c_total_no_cambia(df_mixto):
    resultado = corregir_tipo_bc(df_mixto)
    assert resultado.loc[2, "Imp. Total"] == "9680"


# ── Tests unitarios: corregir_columna_L ──────────────────────────────────────

@pytest.fixture
def df_col_l():
    return pd.DataFrame({
        "Tipo":         ["1 - Factura A", "1 - Factura A", "1 - Factura A", "1 - Factura A"],
        "Tipo Cambio":  ["1",             "1,0",           "1080",          "1450"],
        "Imp. Total":   ["100",           "200",           "300",           "400"],
    })

def test_columna_l_entero_a_decimal(df_col_l):
    resultado = corregir_columna_L(df_col_l)
    assert resultado.loc[0, "Tipo Cambio"] == "1,00"

def test_columna_l_con_coma_decimal(df_col_l):
    resultado = corregir_columna_L(df_col_l)
    assert resultado.loc[1, "Tipo Cambio"] == "1,00"

def test_columna_l_tipo_cambio_real(df_col_l):
    resultado = corregir_columna_L(df_col_l)
    assert resultado.loc[2, "Tipo Cambio"] == "1080,00"

def test_columna_l_tipo_cambio_1450(df_col_l):
    resultado = corregir_columna_L(df_col_l)
    assert resultado.loc[3, "Tipo Cambio"] == "1450,00"

def test_columna_l_es_string(df_col_l):
    resultado = corregir_columna_L(df_col_l)
    assert isinstance(resultado.loc[0, "Tipo Cambio"], str)

def test_columna_l_usa_coma_como_decimal(df_col_l):
    """Holistor requiere coma como separador decimal."""
    resultado = corregir_columna_L(df_col_l)
    for val in resultado["Tipo Cambio"]:
        assert "," in val, f"Valor '{val}' no tiene coma decimal"
        assert "." not in val, f"Valor '{val}' no debe tener punto decimal"


# ── Tests de integracion: fixture real BUTALO SRL ────────────────────────────

@pytest.mark.skipif(
    not FIXTURE.exists(),
    reason="Fixture real no disponible — copiar comprobantes_butalo_feb2026.xlsx"
)
class TestFixtureReal:

    @pytest.fixture
    def df_real(self):
        return pd.read_excel(FIXTURE, header=1, dtype=str)

    def test_lectura_correcta(self, df_real):
        assert len(df_real) == 359
        assert "Tipo" in df_real.columns
        assert COL_TIPO_CAMBIO in df_real.columns
        assert "Imp. Total" in df_real.columns

    def test_columna_L_son_strings_con_coma(self, df_real):
        resultado = corregir_columna_L(df_real)
        for val in resultado[COL_TIPO_CAMBIO]:
            assert isinstance(val, str), f"'{val}' no es string"
            assert "," in val, f"'{val}' no tiene coma decimal"

    def test_tipo_bc_total_intacto(self, df_real):
        totales_antes = df_real["Imp. Total"].copy()
        resultado = corregir_tipo_bc(df_real)
        mascara_bc = df_real["Tipo"].apply(extraer_tipo).isin(TIPOS_BC)
        pd.testing.assert_series_equal(
            resultado.loc[mascara_bc, "Imp. Total"].reset_index(drop=True),
            totales_antes[mascara_bc].reset_index(drop=True),
            check_names=False,
        )

    def test_tipo_bc_count(self, df_real):
        """BUTALO feb 2026 tiene exactamente 12 comprobantes C."""
        mascara_bc = df_real["Tipo"].apply(extraer_tipo).isin(TIPOS_BC)
        assert mascara_bc.sum() == 12

    def test_tipo_bc_neto_en_cero(self, df_real):
        resultado = corregir_tipo_bc(df_real)
        mascara_bc = df_real["Tipo"].apply(extraer_tipo).isin(TIPOS_BC)
        for col in ["Neto Grav. IVA 21%", "IVA 21%"]:
            if col in resultado.columns:
                valores = resultado.loc[mascara_bc, col]
                assert (valores == "0").all(), \
                    f"Columna '{col}' debe ser 0 en todas las filas B/C"
