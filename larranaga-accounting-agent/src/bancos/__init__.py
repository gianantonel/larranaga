"""Parsers de extractos bancarios para conciliación (R-15)."""
from .base_parser import BankParser, CUIT_RE
from .pampa_parser import PampaParser
from .santander_parser import SantanderParser
from .mercadopago_parser import MercadoPagoParser


PARSERS: dict[str, type[BankParser]] = {
    "pampa": PampaParser,
    "santander": SantanderParser,
    "mercadopago": MercadoPagoParser,
}


def get_parser(banco: str) -> BankParser:
    """Devuelve una instancia del parser correspondiente al banco."""
    cls = PARSERS.get(banco.lower())
    if cls is None:
        raise ValueError(f"Parser no encontrado para banco: {banco!r}")
    return cls()


__all__ = [
    "BankParser",
    "CUIT_RE",
    "PampaParser",
    "SantanderParser",
    "MercadoPagoParser",
    "PARSERS",
    "get_parser",
]
