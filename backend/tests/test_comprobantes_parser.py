"""Tests for afip_sdk/comprobantes.py — parser and period helpers."""
import json
from pathlib import Path

import pytest

from app.afip_sdk.comprobantes import (
    extract_records,
    normalize_record,
    parse_importe,
    period_to_fechas,
)

FIXTURE = Path(__file__).parent / "fixtures" / "mis_comprobantes_sample.json"


# ─── period_to_fechas ────────────────────────────────────────────────────────

def test_period_to_fechas_standard():
    desde, hasta = period_to_fechas("2025-12")
    assert desde == "01/12/2025"
    assert hasta == "31/12/2025"


def test_period_to_fechas_february_non_leap():
    _, hasta = period_to_fechas("2025-02")
    assert hasta == "28/02/2025"


def test_period_to_fechas_february_leap():
    _, hasta = period_to_fechas("2024-02")
    assert hasta == "29/02/2024"


def test_period_to_fechas_april():
    _, hasta = period_to_fechas("2025-04")
    assert hasta == "30/04/2025"


# ─── parse_importe ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("843,90", 843.90),
    ("1.303,20", 1303.20),
    ("100000,00", 100000.0),
    ("0,00", 0.0),
    (None, 0.0),
    ("", 0.0),
    ("1.234.567,89", 1234567.89),
])
def test_parse_importe(raw, expected):
    assert parse_importe(raw) == pytest.approx(expected)


# ─── extract_records ─────────────────────────────────────────────────────────

def test_extract_records_flat_array():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    records = extract_records(payload)
    assert len(records) == 3


def test_extract_records_wrapped_rows():
    payload = {"status": "complete", "data": {"rows": [{"field": "val"}]}}
    records = extract_records(payload)
    assert len(records) == 1
    assert records[0]["field"] == "val"


def test_extract_records_empty():
    assert extract_records({"status": "complete", "data": []}) == []
    assert extract_records({"status": "complete", "data": {}}) == []


# ─── normalize_record ────────────────────────────────────────────────────────

def _first_record():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return normalize_record(extract_records(payload)[0])


def test_normalize_fecha_emision():
    n = _first_record()
    # normalize_record returns the raw date string; parsing to date is done in the router
    assert "12/2025" in n["fecha_emision"]


def test_normalize_nro_doc_emisor():
    n = _first_record()
    assert n["nro_doc_emisor"] == "30500012516"


def test_normalize_nro_doc_receptor():
    n = _first_record()
    assert n["nro_doc_receptor"] == "23311348949"


def test_normalize_otros_tributos():
    n = _first_record()
    assert n["otros_tributos"] == pytest.approx(843.90)


def test_normalize_imp_total():
    n = _first_record()
    assert n["imp_total"] == pytest.approx(121843.90)


def test_normalize_moneda():
    n = _first_record()
    assert n["moneda"] == "PES"


def test_normalize_cod_autorizacion():
    n = _first_record()
    assert n["cod_autorizacion"] == "86151427323266"


def test_normalize_tipo_comprobante():
    n = _first_record()
    assert n["tipo_comprobante"] == "FACTURA A"


def test_normalize_unicode_keys():
    """Fields with unicode accents (Emisión, Número) must be parsed correctly."""
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # Third record uses pre-escaped unicode keys (\u00f3 etc.)
    n = normalize_record(extract_records(payload)[2])
    assert n["tipo_comprobante"] == "NOTA DE CREDITO A"
    assert n["nro_doc_emisor"] == "30987654321"


def test_normalize_empty_cod_autorizacion_gives_empty_string():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    n = normalize_record(extract_records(payload)[2])
    assert n["cod_autorizacion"] == ""
