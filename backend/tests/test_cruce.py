"""Tests for the cruce (cross-match) logic between RetencionPercepcion and ComprobanteRecibido."""
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.routers.comprobantes import _match_score


def _ret(cuit_agente: str, fecha: date | None = None):
    r = MagicMock()
    r.cuit_agente = cuit_agente
    r.fecha_retencion = fecha
    return r


def _cbte(nro_doc_emisor: str, fecha: date | None = None):
    c = MagicMock()
    c.nro_doc_emisor = nro_doc_emisor
    c.fecha_emision = fecha
    return c


# ─── match_score ─────────────────────────────────────────────────────────────

def test_exact_match_same_cuit_same_date():
    ret = _ret("30500012516", date(2025, 12, 1))
    cbte = _cbte("30500012516", date(2025, 12, 1))
    assert _match_score(ret, cbte) == "exact"


def test_approx_match_within_5_days():
    ret = _ret("30500012516", date(2025, 12, 1))
    cbte = _cbte("30500012516", date(2025, 12, 4))
    assert _match_score(ret, cbte) == "approx"


def test_approx_match_exactly_5_days():
    ret = _ret("30500012516", date(2025, 12, 1))
    cbte = _cbte("30500012516", date(2025, 12, 6))
    assert _match_score(ret, cbte) == "approx"


def test_none_match_date_too_far():
    ret = _ret("30500012516", date(2025, 12, 1))
    cbte = _cbte("30500012516", date(2025, 12, 8))
    assert _match_score(ret, cbte) == "none"


def test_none_match_different_cuit():
    ret = _ret("30500012516", date(2025, 12, 1))
    cbte = _cbte("20123456789", date(2025, 12, 1))
    assert _match_score(ret, cbte) == "none"


def test_none_match_null_comprobante():
    ret = _ret("30500012516", date(2025, 12, 1))
    assert _match_score(ret, None) == "none"


def test_approx_match_no_dates():
    """When one date is missing but CUITs match → approx (can't determine exact)."""
    ret = _ret("30500012516", None)
    cbte = _cbte("30500012516", None)
    assert _match_score(ret, cbte) == "approx"


def test_cuit_normalization_dashes():
    """CUITs with dashes should match CUITs without dashes."""
    ret = _ret("30-50001251-6", date(2025, 12, 1))
    cbte = _cbte("30500012516", date(2025, 12, 1))
    assert _match_score(ret, cbte) == "exact"


def test_cuit_normalization_spaces():
    ret = _ret(" 30500012516 ", date(2025, 12, 1))
    cbte = _cbte("30500012516", date(2025, 12, 1))
    assert _match_score(ret, cbte) == "exact"


def test_empty_cuit_agente_returns_none():
    ret = _ret("", date(2025, 12, 1))
    cbte = _cbte("30500012516", date(2025, 12, 1))
    assert _match_score(ret, cbte) == "none"
