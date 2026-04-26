"""
Tests para R-02: División de Comprobantes por Múltiples Alícuotas

Cubre:
  - Funciones auxiliares (parse/format strings)
  - Detección de filas multi-alícuota
  - Expansión de filas individuales
  - Transformación completa
  - Validación post-expansión
  - Compatibilidad con R-01 (backward compatibility)
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Importar el módulo a testear
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.transformaciones.division_alicuotas import (
    parse_string_float,
    format_string_float,
    extraer_tipo,
    detect_multi_alicuota_rows,
    expand_multi_alicuota_row,
    aplicar_division_alicuotas,
    validar_expansion,
    ALICUOTA_COLS,
    COL_NUMERO_ALT as COL_NUMERO,
    COL_NETO_TOTAL,
    COL_IVA_TOTAL,
    COL_OTROS_TRIBUTOS,
    COL_IMP_TOTAL,
)


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: Funciones auxiliares
# ─────────────────────────────────────────────────────────────────────────────

class TestParseStringFloat:
    """Tests para parse_string_float()"""

    def test_parse_basic(self):
        assert parse_string_float("89.516,16") == 89516.16
        assert parse_string_float("1.234,56") == 1234.56
        assert parse_string_float("0,00") == 0.0
        assert parse_string_float("1,00") == 1.0

    def test_parse_no_thousands(self):
        assert parse_string_float("100,50") == 100.50
        assert parse_string_float("50,00") == 50.0

    def test_parse_empty_and_nan(self):
        assert parse_string_float("") == 0.0
        assert parse_string_float(None) == 0.0
        import pandas as pd
        assert parse_string_float(pd.NA) == 0.0

    def test_parse_invalid(self):
        assert parse_string_float("abc") == 0.0
        assert parse_string_float("  ") == 0.0


class TestFormatStringFloat:
    """Tests para format_string_float()"""

    def test_format_basic(self):
        assert format_string_float(89516.16) == "89.516,16"
        assert format_string_float(1234.56) == "1.234,56"
        assert format_string_float(0.0) == "0,00"
        assert format_string_float(1.0) == "1,00"

    def test_format_no_thousands(self):
        assert format_string_float(100.50) == "100,50"
        assert format_string_float(50.0) == "50,00"

    def test_format_large_numbers(self):
        assert format_string_float(1234567.89) == "1.234.567,89"
        assert format_string_float(10000000.00) == "10.000.000,00"

    def test_format_rounding(self):
        assert format_string_float(100.126) == "100,13"  # Redondea a 2 decimales
        assert format_string_float(100.124) == "100,12"


class TestExtraerTipo:
    """Tests para extraer_tipo()"""

    def test_extract_basic(self):
        assert extraer_tipo("1 - Factura A") == "1"
        assert extraer_tipo("6 - Factura B") == "6"
        assert extraer_tipo("11 - Factura C") == "11"

    def test_extract_with_spaces(self):
        assert extraer_tipo("  1  - Factura A") == "1"

    def test_extract_invalid(self):
        assert extraer_tipo("Invalid") == ""
        assert extraer_tipo("") == ""


class TestRoundtrip:
    """Tests roundtrip: parse → format → parse"""

    def test_roundtrip_values(self):
        valores = [89516.16, 1234.56, 0.0, 1.0, 100.50, 1234567.89]
        for v in valores:
            formateado = format_string_float(v)
            parseado = parse_string_float(formateado)
            assert abs(parseado - v) < 0.01, f"Roundtrip failed for {v}"


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES: DataFrames de prueba
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def df_single_alicuota():
    """DataFrame con una factura de alícuota única (21%)"""
    data = {
        "Fecha": ["20/04/2023"],
        "Tipo": ["1 - Factura A"],
        "Punto de Venta": ["001"],
        "Número": ["1001"],
        "CUIT Receptor": ["20123456789"],
        "Neto Grav. IVA 0%": ["0"],
        "IVA 0%": ["0"],
        "Neto Grav. IVA 2,5%": ["0"],
        "IVA 2,5%": ["0"],
        "Neto Grav. IVA 5%": ["0"],
        "IVA 5%": ["0"],
        "Neto Grav. IVA 10,5%": ["0"],
        "IVA 10,5%": ["0"],
        "Neto Grav. IVA 21%": ["1000,00"],
        "IVA 21%": ["210,00"],
        "Neto Grav. IVA 27%": ["0"],
        "IVA 27%": ["0"],
        "Neto Gravado Total": ["1000,00"],
        "Neto No Grav": ["0"],
        "Exentas": ["0"],
        "Total IVA": ["210,00"],
        "Otros Tributos": ["0"],
        "Imp. Total": ["1210,00"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def df_multi_alicuota_2rates():
    """DataFrame con factura multi-alícuota (21% + 27%)"""
    data = {
        "Fecha": ["20/04/2023"],
        "Tipo": ["1 - Factura A"],
        "Punto de Venta": ["001"],
        "Número": ["991"],
        "CUIT Receptor": ["20123456789"],
        "Neto Grav. IVA 0%": ["0"],
        "IVA 0%": ["0"],
        "Neto Grav. IVA 2,5%": ["0"],
        "IVA 2,5%": ["0"],
        "Neto Grav. IVA 5%": ["0"],
        "IVA 5%": ["0"],
        "Neto Grav. IVA 10,5%": ["0"],
        "IVA 10,5%": ["0"],
        "Neto Grav. IVA 21%": ["89.516,16"],
        "IVA 21%": ["18.798,39"],
        "Neto Grav. IVA 27%": ["181.350,87"],
        "IVA 27%": ["48.965,19"],
        "Neto Gravado Total": ["270.867,03"],
        "Neto No Grav": ["0"],
        "Exentas": ["0"],
        "Total IVA": ["67.763,58"],
        "Otros Tributos": ["0"],
        "Imp. Total": ["338.630,61"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def df_multi_alicuota_3rates():
    """DataFrame con factura multi-alícuota (5% + 21% + 27%)"""
    data = {
        "Fecha": ["20/04/2023"],
        "Tipo": ["1 - Factura A"],
        "Punto de Venta": ["001"],
        "Número": ["992"],
        "CUIT Receptor": ["20987654321"],
        "Neto Grav. IVA 0%": ["0"],
        "IVA 0%": ["0"],
        "Neto Grav. IVA 2,5%": ["0"],
        "IVA 2,5%": ["0"],
        "Neto Grav. IVA 5%": ["1000,00"],
        "IVA 5%": ["50,00"],
        "Neto Grav. IVA 10,5%": ["0"],
        "IVA 10,5%": ["0"],
        "Neto Grav. IVA 21%": ["2000,00"],
        "IVA 21%": ["420,00"],
        "Neto Grav. IVA 27%": ["3000,00"],
        "IVA 27%": ["810,00"],
        "Neto Gravado Total": ["6000,00"],
        "Neto No Grav": ["0"],
        "Exentas": ["0"],
        "Total IVA": ["1280,00"],
        "Otros Tributos": ["0"],
        "Imp. Total": ["7280,00"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def df_mixed():
    """DataFrame mixto: single + multi + B/C"""
    row_single = {
        "Fecha": "20/04/2023",
        "Tipo": "1 - Factura A",
        "Punto de Venta": "001",
        "Número": "1001",
        "CUIT Receptor": "20123456789",
        "Neto Grav. IVA 0%": "0",
        "IVA 0%": "0",
        "Neto Grav. IVA 2,5%": "0",
        "IVA 2,5%": "0",
        "Neto Grav. IVA 5%": "0",
        "IVA 5%": "0",
        "Neto Grav. IVA 10,5%": "0",
        "IVA 10,5%": "0",
        "Neto Grav. IVA 21%": "1000,00",
        "IVA 21%": "210,00",
        "Neto Grav. IVA 27%": "0",
        "IVA 27%": "0",
        "Neto Gravado Total": "1000,00",
        "Neto No Grav": "0",
        "Exentas": "0",
        "Total IVA": "210,00",
        "Otros Tributos": "0",
        "Imp. Total": "1210,00",
    }
    row_multi = {
        "Fecha": "20/04/2023",
        "Tipo": "1 - Factura A",
        "Punto de Venta": "001",
        "Número": "1002",
        "CUIT Receptor": "20987654321",
        "Neto Grav. IVA 0%": "0",
        "IVA 0%": "0",
        "Neto Grav. IVA 2,5%": "0",
        "IVA 2,5%": "0",
        "Neto Grav. IVA 5%": "0",
        "IVA 5%": "0",
        "Neto Grav. IVA 10,5%": "0",
        "IVA 10,5%": "0",
        "Neto Grav. IVA 21%": "500,00",
        "IVA 21%": "105,00",
        "Neto Grav. IVA 27%": "1000,00",
        "IVA 27%": "270,00",
        "Neto Gravado Total": "1500,00",
        "Neto No Grav": "0",
        "Exentas": "0",
        "Total IVA": "375,00",
        "Otros Tributos": "0",
        "Imp. Total": "1875,00",
    }
    row_bc = {
        "Fecha": "20/04/2023",
        "Tipo": "6 - Factura B",
        "Punto de Venta": "001",
        "Número": "1003",
        "CUIT Receptor": "20555666777",
        "Neto Grav. IVA 0%": "0",
        "IVA 0%": "0",
        "Neto Grav. IVA 2,5%": "0",
        "IVA 2,5%": "0",
        "Neto Grav. IVA 5%": "0",
        "IVA 5%": "0",
        "Neto Grav. IVA 10,5%": "0",
        "IVA 10,5%": "0",
        "Neto Grav. IVA 21%": "0",
        "IVA 21%": "0",
        "Neto Grav. IVA 27%": "0",
        "IVA 27%": "0",
        "Neto Gravado Total": "0",
        "Neto No Grav": "0",
        "Exentas": "0",
        "Total IVA": "0",
        "Otros Tributos": "0",
        "Imp. Total": "2000,00",
    }
    return pd.DataFrame([row_single, row_multi, row_bc])


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: Detección de multi-alícuota
# ─────────────────────────────────────────────────────────────────────────────

class TestDetectMultiAlicuota:
    """Tests para detect_multi_alicuota_rows()"""

    def test_single_alicuota_no_expansion(self, df_single_alicuota):
        result = detect_multi_alicuota_rows(df_single_alicuota)
        assert len(result) == 0, "Single alícuota no debe detectarse como multi"

    def test_multi_alicuota_2rates(self, df_multi_alicuota_2rates):
        result = detect_multi_alicuota_rows(df_multi_alicuota_2rates)
        assert 0 in result, "Debe detectarse la fila multi-alícuota"
        assert sorted(result[0]) == [21, 27], "Debe detectarse [21, 27]"

    def test_multi_alicuota_3rates(self, df_multi_alicuota_3rates):
        result = detect_multi_alicuota_rows(df_multi_alicuota_3rates)
        assert 0 in result, "Debe detectarse la fila multi-alícuota"
        # Ordenado desc: [27, 21, 5]
        assert result[0] == [27, 21, 5], "Debe detectarse [27, 21, 5] en orden desc"

    def test_mixed_dataframe(self, df_mixed):
        result = detect_multi_alicuota_rows(df_mixed)
        # Fila 0: single alícuota (21%) → no
        # Fila 1: multi alícuota (21% + 27%) → sí
        # Fila 2: B/C (todos ceros) → no
        assert len(result) == 1, "Debe detectar 1 fila multi-alícuota"
        assert 1 in result, "La fila 1 debe ser multi-alícuota"


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: Expansión de filas
# ─────────────────────────────────────────────────────────────────────────────

class TestExpandMultiAlicuota:
    """Tests para expand_multi_alicuota_row()"""

    def test_expand_2rates(self, df_multi_alicuota_2rates):
        row = df_multi_alicuota_2rates.iloc[0]
        filas = expand_multi_alicuota_row(row, [27, 21], 0, df_multi_alicuota_2rates)

        assert len(filas) == 2, "Debe expandir a 2 filas"

        # Fila A (27% primero por orden desc)
        fila_a = filas[0]
        assert fila_a[COL_NUMERO] == "991/A"
        assert parse_string_float(fila_a["Neto Grav. IVA 27%"]) == 181350.87
        assert parse_string_float(fila_a["Neto Grav. IVA 21%"]) == 0.0

        # Fila B (21%)
        fila_b = filas[1]
        assert fila_b[COL_NUMERO] == "991/B"
        assert parse_string_float(fila_b["Neto Grav. IVA 21%"]) == 89516.16
        assert parse_string_float(fila_b["Neto Grav. IVA 27%"]) == 0.0

    def test_expand_preserves_cabecera(self, df_multi_alicuota_2rates):
        row = df_multi_alicuota_2rates.iloc[0]
        filas = expand_multi_alicuota_row(row, [27, 21], 0, df_multi_alicuota_2rates)

        # Verificar que cabecera se preserva
        for fila in filas:
            assert fila["Fecha"] == "20/04/2023"
            assert fila["Tipo"] == "1 - Factura A"
            assert fila["Punto de Venta"] == "001"
            assert fila["CUIT Receptor"] == "20123456789"

    def test_expand_3rates(self, df_multi_alicuota_3rates):
        row = df_multi_alicuota_3rates.iloc[0]
        filas = expand_multi_alicuota_row(row, [27, 21, 5], 0, df_multi_alicuota_3rates)

        assert len(filas) == 3, "Debe expandir a 3 filas"

        # Verificar números con sufijos
        assert filas[0][COL_NUMERO] == "992/A"
        assert filas[1][COL_NUMERO] == "992/B"
        assert filas[2][COL_NUMERO] == "992/C"


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: Transformación completa
# ─────────────────────────────────────────────────────────────────────────────

class TestAplicarDivision:
    """Tests para aplicar_division_alicuotas()"""

    def test_single_alicuota_unchanged(self, df_single_alicuota):
        df_exp, stats = aplicar_division_alicuotas(df_single_alicuota)

        assert len(df_exp) == 1, "Single alícuota no debe expandirse"
        assert stats["total_entrada"] == 1
        assert stats["filas_multi_alicuota"] == 0
        assert stats["filas_expandidas"] == 0
        assert stats["total_salida"] == 1

    def test_multi_alicuota_expanded(self, df_multi_alicuota_2rates):
        df_exp, stats = aplicar_division_alicuotas(df_multi_alicuota_2rates)

        assert len(df_exp) == 2, "2 alícuotas → 2 filas"
        assert stats["total_entrada"] == 1
        assert stats["filas_multi_alicuota"] == 1
        assert stats["filas_expandidas"] == 1  # 2 - 1 = 1 nueva
        assert stats["total_salida"] == 2

    def test_mixed_dataframe_expanded(self, df_mixed):
        df_exp, stats = aplicar_division_alicuotas(df_mixed)

        # 3 filas entrada: 1 single + 1 multi(→2) + 1 B/C = 4 filas salida
        assert len(df_exp) == 4, "1 single + 2 expanded + 1 B/C = 4"
        assert stats["total_entrada"] == 3
        assert stats["filas_multi_alicuota"] == 1
        assert stats["total_salida"] == 4


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: Validación
# ─────────────────────────────────────────────────────────────────────────────

class TestValidarExpansion:
    """Tests para validar_expansion()"""

    def test_validate_single_alicuota(self, df_single_alicuota):
        df_exp, _ = aplicar_division_alicuotas(df_single_alicuota)
        resultado = validar_expansion(df_single_alicuota, df_exp)

        assert resultado["valido"], "Single alícuota sin expansión debe ser válida"
        assert len(resultado["errores"]) == 0

    def test_validate_multi_alicuota(self, df_multi_alicuota_2rates):
        df_exp, _ = aplicar_division_alicuotas(df_multi_alicuota_2rates)
        resultado = validar_expansion(df_multi_alicuota_2rates, df_exp)

        assert resultado["valido"], "Expansión de multi-alícuota debe ser válida"
        assert len(resultado["errores"]) == 0


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: Backward compatibility (R-01)
# ─────────────────────────────────────────────────────────────────────────────

class TestBackwardCompatibility:
    """Verifica que R-02 no rompa R-01"""

    def test_r01_output_passes_r02(self):
        """
        Simula output de R-01 (sin multi-alícuota) y verifica que pase por R-02
        sin cambios
        """
        # DataFrame simple (como output de R-01 limpieza)
        data = {
            "Fecha": ["20/04/2023", "21/04/2023"],
            "Tipo": ["1 - Factura A", "6 - Factura B"],
            "Punto de Venta": ["001", "001"],
            "Número": ["1", "2"],
            "CUIT Receptor": ["20123456789", "20555666777"],
            "Neto Grav. IVA 0%": ["0", "0"],
            "IVA 0%": ["0", "0"],
            "Neto Grav. IVA 2,5%": ["0", "0"],
            "IVA 2,5%": ["0", "0"],
            "Neto Grav. IVA 5%": ["0", "0"],
            "IVA 5%": ["0", "0"],
            "Neto Grav. IVA 10,5%": ["0", "0"],
            "IVA 10,5%": ["0", "0"],
            "Neto Grav. IVA 21%": ["1000,00", "0"],
            "IVA 21%": ["210,00", "0"],
            "Neto Grav. IVA 27%": ["0", "0"],
            "IVA 27%": ["0", "0"],
            "Neto Gravado Total": ["1000,00", "0"],
            "Neto No Grav": ["0", "0"],
            "Exentas": ["0", "0"],
            "Total IVA": ["210,00", "0"],
            "Otros Tributos": ["0", "0"],
            "Imp. Total": ["1210,00", "2000,00"],
        }
        df = pd.DataFrame(data)

        # Aplicar R-02
        df_exp, stats = aplicar_division_alicuotas(df)

        # Debe mantener 2 filas (sin expansión)
        assert len(df_exp) == 2
        assert stats["filas_multi_alicuota"] == 0
        assert stats["total_salida"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION TEST: Full pipeline (if needed)
# ─────────────────────────────────────────────────────────────────────────────

class TestFullPipeline:
    """Test end-to-end: parse mixed data, apply R-02, validate"""

    def test_full_pipeline(self, df_mixed):
        # 1. Detectar
        multi_map = detect_multi_alicuota_rows(df_mixed)
        assert len(multi_map) == 1

        # 2. Aplicar
        df_exp, stats = aplicar_division_alicuotas(df_mixed)
        assert stats["total_salida"] == 4

        # 3. Validar
        resultado = validar_expansion(df_mixed, df_exp)
        assert resultado["valido"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
