"""Tests F3-02 / F3-03: parsers bancarios para Pampa, Santander y MP."""
import io
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.bancos import get_parser, PampaParser, SantanderParser, MercadoPagoParser
from src.bancos.base_parser import CUIT_RE


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_xlsx(df: pd.DataFrame, tmp_path: Path, name: str) -> Path:
    p = tmp_path / name
    df.to_excel(p, index=False)
    return p


# ─── CUIT regex ──────────────────────────────────────────────────────────────

def test_cuit_re_detecta_con_guiones():
    m = CUIT_RE.search("TRANSF DE 30-70921208-3 BUTALO SRL")
    assert m and m.group(1) == "30-70921208-3"


def test_cuit_re_detecta_sin_guiones():
    m = CUIT_RE.search("PAGO 20123456789 JUAN PEREZ")
    assert m and m.group(1) == "20123456789"


def test_cuit_re_no_falsos_positivos():
    # 10 dígitos no es CUIT
    assert CUIT_RE.search("REF 1234567890 PAGO") is None


# ─── PampaParser ─────────────────────────────────────────────────────────────

def test_pampa_parser_credito_y_debito(tmp_path):
    df = pd.DataFrame([
        {"Fecha": "01/02/2026", "Referencia": "TRANSF DE 30709212083 BUTALO",
         "Débito": "", "Crédito": "150000,00", "Saldo": "1234567,89"},
        {"Fecha": "03/02/2026", "Referencia": "PAGO IMPUESTO IIBB",
         "Débito": "12500,50", "Crédito": "", "Saldo": "1222067,39"},
    ])
    p = _make_xlsx(df, tmp_path, "pampa.xlsx")

    movs = PampaParser().parse(p)
    assert len(movs) == 2

    m1 = movs[0]
    assert m1["banco"] == "pampa"
    assert m1["fecha"] == date(2026, 2, 1)
    assert m1["tipo"] == "C"
    assert m1["importe"] == 150000.0
    assert m1["cuit_detectado"] == "30709212083"

    m2 = movs[1]
    assert m2["tipo"] == "D"
    assert m2["importe"] == 12500.50
    assert m2["cuit_detectado"] is None


def test_pampa_filas_invalidas_se_omiten(tmp_path):
    df = pd.DataFrame([
        {"Fecha": "01/02/2026", "Referencia": "OK", "Débito": "", "Crédito": "100", "Saldo": ""},
        {"Fecha": "", "Referencia": "Sin fecha", "Débito": "", "Crédito": "200", "Saldo": ""},
        {"Fecha": "02/02/2026", "Referencia": "Sin importe", "Débito": "", "Crédito": "", "Saldo": ""},
    ])
    p = _make_xlsx(df, tmp_path, "pampa.xlsx")
    movs = PampaParser().parse(p)
    assert len(movs) == 1
    assert movs[0]["descripcion"] == "OK"


# ─── SantanderParser ─────────────────────────────────────────────────────────

def test_santander_parser_columnas_alternativas(tmp_path):
    df = pd.DataFrame([
        {"Fecha": "10/02/2026", "Concepto": "DEPOSITO 20999888777",
         "Importe Débito": "", "Importe Crédito": "75000", "Saldo": "500000"},
    ])
    p = _make_xlsx(df, tmp_path, "santander.xlsx")
    movs = SantanderParser().parse(p)
    assert len(movs) == 1
    assert movs[0]["importe"] == 75000.0
    assert movs[0]["cuit_detectado"] == "20999888777"
    assert movs[0]["tipo"] == "C"


# ─── MercadoPagoParser ───────────────────────────────────────────────────────

def test_mercadopago_csv_monto_unico(tmp_path):
    p = tmp_path / "mp.csv"
    p.write_text(
        "FECHA,DESCRIPCION,MONTO\n"
        "15/02/2026,Pago de Cliente A,12500.00\n"
        "16/02/2026,Comisión MP,-350.50\n",
        encoding="utf-8",
    )
    movs = MercadoPagoParser().parse(p)
    assert len(movs) == 2

    entrada = next(m for m in movs if m["importe"] == 12500.0)
    assert entrada["tipo"] == "C"

    salida = next(m for m in movs if m["importe"] == 350.50)
    assert salida["tipo"] == "D"


# ─── Factory ─────────────────────────────────────────────────────────────────

def test_get_parser_devuelve_instancia_correcta():
    assert isinstance(get_parser("pampa"), PampaParser)
    assert isinstance(get_parser("Santander"), SantanderParser)
    assert isinstance(get_parser("mercadopago"), MercadoPagoParser)


def test_get_parser_banco_desconocido_falla():
    with pytest.raises(ValueError):
        get_parser("galicia")


# ─── Formato es-AR de números ────────────────────────────────────────────────

def test_to_decimal_formato_es_ar():
    p = PampaParser()
    assert float(p._to_decimal("1.234.567,89")) == 1234567.89
    assert float(p._to_decimal("$ 12.500,50")) == 12500.50
    assert float(p._to_decimal("100")) == 100.0
    assert float(p._to_decimal("")) == 0.0
    assert float(p._to_decimal(None)) == 0.0
