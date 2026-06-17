"""F3-02: Parser base para extractos bancarios.

Cada parser concreto define cómo leer el archivo y mapear columnas.
La normalización de filas (CUIT, débito/crédito, fecha) es común.

Output: lista de dicts con shape:
    {
        "banco": "pampa",
        "fecha": date(2026, 2, 15),
        "descripcion": "TRANSF DE 30709212083 BUTALO",
        "tipo": "C",                # C = crédito (entrada), D = débito (salida)
        "importe": 150000.0,        # siempre positivo
        "saldo": 1234567.89,        # opcional
        "cuit_detectado": "30709212083",  # opcional
    }
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd

# CUIT con o sin guiones: 11 dígitos consecutivos o 2-8-1
CUIT_RE = re.compile(r"\b(\d{2}[-]?\d{8}[-]?\d)\b")


class BankParser(ABC):
    banco: str = ""
    col_map: dict[str, str] = {}

    # ─── Pipeline público ────────────────────────────────────────────────────

    def parse(self, filepath: str | Path) -> list[dict[str, Any]]:
        """Lee el archivo, lo normaliza y devuelve lista de movimientos."""
        df = self._read_file(str(filepath))
        df = self._normalize_columns(df)
        movs: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            if not self._is_valid_row(row):
                continue
            mov = self._normalize_row(row)
            if mov is not None:
                movs.append(mov)
        return movs

    # ─── Helpers reutilizables ───────────────────────────────────────────────

    def _normalize_row(self, row: pd.Series) -> dict[str, Any] | None:
        """Normaliza una fila a la shape común."""
        try:
            fecha = self._parse_fecha(row.get("fecha"))
            if fecha is None:
                return None
            desc = str(row.get("descripcion") or "").strip().upper()
            debe = self._to_decimal(row.get("debe", 0))
            haber = self._to_decimal(row.get("haber", 0))
            if debe == 0 and haber == 0:
                return None
            tipo = "D" if debe > 0 else "C"
            importe = float(debe if debe > 0 else haber)
            saldo = self._to_decimal(row.get("saldo"))
            cuit_match = CUIT_RE.search(desc)
            cuit = cuit_match.group(1).replace("-", "") if cuit_match else None
            return {
                "banco": self.banco,
                "fecha": fecha,
                "descripcion": desc,
                "tipo": tipo,
                "importe": importe,
                "saldo": float(saldo) if saldo is not None else None,
                "cuit_detectado": cuit,
            }
        except Exception:
            return None

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return Decimal("0")
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        s = str(value).strip()
        if not s or s.lower() in ("nan", "none"):
            return Decimal("0")
        # Limpia $, espacios, separadores de miles
        s = s.replace("$", "").replace(" ", "")
        # Si tiene tanto "." como "," asumimos formato es-AR (1.234,56)
        if "." in s and "," in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        s = s.lstrip("+")
        try:
            return Decimal(s)
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @staticmethod
    def _parse_fecha(value: Any) -> date | None:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, date):
            return value
        s = str(value).strip()
        if not s:
            return None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
            try:
                return pd.to_datetime(s, format=fmt).date()
            except (ValueError, TypeError):
                pass
        try:
            return pd.to_datetime(s, dayfirst=True).date()
        except (ValueError, TypeError):
            return None

    # ─── Hooks abstractos ────────────────────────────────────────────────────

    @abstractmethod
    def _read_file(self, filepath: str) -> pd.DataFrame: ...

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renombra columnas según col_map. Override si hace falta lógica especial."""
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        return df.rename(columns=self.col_map)

    def _is_valid_row(self, row: pd.Series) -> bool:
        """Default: descarta filas sin fecha."""
        return pd.notna(row.get("fecha")) and str(row.get("fecha")).strip() != ""
