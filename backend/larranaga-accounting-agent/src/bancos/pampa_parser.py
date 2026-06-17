"""F3-02: Parser para extractos del Banco Pampa.

Formato típico (Excel):
- Skiprows: 2 (primeras 2 filas son cabecera del banco/cuenta)
- Columnas: Fecha, Referencia, Débito, Crédito, Saldo
"""
from __future__ import annotations

import pandas as pd

from .base_parser import BankParser


class PampaParser(BankParser):
    banco = "pampa"
    col_map = {
        "Fecha": "fecha",
        "Referencia": "descripcion",
        "Concepto": "descripcion",
        "Débito": "debe",
        "Debito": "debe",
        "Crédito": "haber",
        "Credito": "haber",
        "Saldo": "saldo",
    }

    def _read_file(self, filepath: str) -> pd.DataFrame:
        # Probar primero sin skiprows; si la primera fila no parece tener "Fecha", reintentar.
        try:
            df = pd.read_excel(filepath, dtype=str)
            if "Fecha" not in [str(c).strip() for c in df.columns]:
                df = pd.read_excel(filepath, dtype=str, skiprows=2)
        except Exception:
            df = pd.read_excel(filepath, dtype=str, skiprows=2)
        return df
