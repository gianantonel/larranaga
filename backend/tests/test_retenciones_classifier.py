"""Tests for retenciones classifier: IMPUESTO_TO_HOLISTOR mapping."""
import json
from pathlib import Path

import pytest

from app.afip_sdk.retenciones import IMPUESTO_TO_HOLISTOR, classify_regimen as classify_holistor

FIXTURE = Path(__file__).parent / "fixtures" / "mis_retenciones_sample.json"


# ─── IMPUESTO_TO_HOLISTOR mapping ────────────────────────────────────────────

@pytest.mark.parametrize("impuesto,expected", [
    (217, "PIVC"),
    (216, "PIVC"),
    (11,  "PGAN"),
    (10,  "PGAN"),
    (767, "OTRO"),
    (902, "PIBA"),
    (903, "PIBC"),
    (904, "PIBC"),
    (905, "PIBR"),
    (906, "PIBR"),
    (907, "PIBR"),
    (908, "PIBR"),
    (910, "PCOM"),
    (911, "SELL"),
])
def test_holistor_mapping(impuesto, expected):
    assert IMPUESTO_TO_HOLISTOR.get(impuesto) == expected


def test_unknown_impuesto_returns_otro():
    assert classify_holistor(9999) == "OTRO"


def test_iva_by_impuesto_code():
    assert classify_holistor(217) == "PIVC"


def test_ganancias_retencion():
    assert classify_holistor(11) == "PGAN"


def test_iibb_la_pampa():
    assert classify_holistor(902) == "PIBA"


def test_iibb_buenos_aires():
    assert classify_holistor(903) == "PIBC"


def test_string_input_coerced():
    assert classify_holistor("217") == "PIVC"


def test_none_input_returns_otro():
    assert classify_holistor(None) == "OTRO"


# ─── fixture-based classification ────────────────────────────────────────────

def test_fixture_records_classified():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rows = payload["data"]["rows"]
    codes = [classify_holistor(int(r["Impuesto"])) for r in rows]
    assert codes == ["PIVC", "PGAN", "PIBA"]
