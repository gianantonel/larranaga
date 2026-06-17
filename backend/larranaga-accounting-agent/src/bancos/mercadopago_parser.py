"""F3-03: Parser para extractos de Mercado Pago.

MP exporta CSV con columna MONTO (positivo=entrada, negativo=salida).
"""
from __future__ import annotations

from decimal import Decimal

import pandas as pd

from .base_parser import BankParser


class MercadoPagoParser(BankParser):
    banco = "mercadopago"

    def _read_file(self, filepath: str) -> pd.DataFrame:
        # MP puede exportar como CSV o XLSX
        if str(filepath).lower().endswith(".csv"):
            return pd.read_csv(filepath, dtype=str)
        return pd.read_excel(filepath, dtype=str)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip().upper() for c in df.columns]
        col_map = {
            "FECHA": "fecha",
            "DESCRIPCIÓN": "descripcion",
            "DESCRIPCION": "descripcion",
            "DETALLE": "descripcion",
            "MONTO": "monto_raw",
            "IMPORTE": "monto_raw",
            "SALDO": "saldo",
        }
        df = df.rename(columns=col_map)

        # Convertir el monto único a debe/haber
        def _to_dec(v):
            return BankParser._to_decimal(v)

        if "monto_raw" in df.columns:
            df["debe"] = df["monto_raw"].apply(
                lambda v: float(abs(_to_dec(v))) if _to_dec(v) < 0 else 0.0
            )
            df["haber"] = df["monto_raw"].apply(
                lambda v: float(_to_dec(v)) if _to_dec(v) > 0 else 0.0
            )
        return df
