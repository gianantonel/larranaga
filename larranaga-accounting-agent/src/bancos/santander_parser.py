"""F3-03: Parser para extractos del Banco Santander."""
from __future__ import annotations

import pandas as pd

from .base_parser import BankParser


class SantanderParser(BankParser):
    banco = "santander"
    col_map = {
        "Fecha": "fecha",
        "Concepto": "descripcion",
        "Descripción": "descripcion",
        "Importe Débito": "debe",
        "Débito": "debe",
        "Importe Crédito": "haber",
        "Crédito": "haber",
        "Saldo": "saldo",
    }

    def _read_file(self, filepath: str) -> pd.DataFrame:
        try:
            df = pd.read_excel(filepath, dtype=str)
            if "Fecha" not in [str(c).strip() for c in df.columns]:
                df = pd.read_excel(filepath, dtype=str, skiprows=1)
        except Exception:
            df = pd.read_excel(filepath, dtype=str, skiprows=1)
        return df
