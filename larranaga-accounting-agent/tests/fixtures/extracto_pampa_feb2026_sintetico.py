"""Fixture sintética realista de un extracto Pampa Feb 2026.

Genera un Excel con ~30 movimientos mezclando:
- Transferencias entrantes con CUIT en descripción (deberían matchear con Pagos)
- Transferencias entrantes sin CUIT (importe + fecha exacta)
- Comisiones bancarias y mantenimiento (categoría auto, no conciliados)
- Retiros de socios (débitos a categorizar)
- 2-3 movimientos sin match (para revisión manual)

Para reemplazar con un extracto REAL del banco:
  1. Exportar el extracto desde el homebanking (mensual, formato Excel)
  2. Reemplazar este archivo con el .xlsx real
  3. Re-correr los tests con `pytest tests/test_pipeline_conciliacion.py`
"""
from pathlib import Path

import pandas as pd


def crear_extracto_pampa(out_path: Path) -> Path:
    """Crea un .xlsx sintético en `out_path` y devuelve el path."""
    rows = [
        # === Transferencias entrantes con CUIT (deberían matchear) ===
        {"Fecha": "01/02/2026", "Referencia": "TRANSF DE 30709212083 BUTALO SRL HONORARIOS",
         "Débito": "", "Crédito": "150000,00", "Saldo": "1150000,00"},
        {"Fecha": "03/02/2026", "Referencia": "TRANSF DE 20123456789 GESUALDO GUILLERMO",
         "Débito": "", "Crédito": "300000,00", "Saldo": "1450000,00"},
        {"Fecha": "08/02/2026", "Referencia": "TRANSF DE 30716234561 RESTAURANTE EL GAUCHO",
         "Débito": "", "Crédito": "8500,00", "Saldo": "1458500,00"},
        {"Fecha": "12/02/2026", "Referencia": "DEPOSITO TRANSFERENCIA 30709212083",
         "Débito": "", "Crédito": "75000,00", "Saldo": "1533500,00"},

        # === Transferencias sin CUIT pero coinciden importe+fecha ===
        {"Fecha": "15/02/2026", "Referencia": "DEPOSITO EFECTIVO VENTANILLA",
         "Débito": "", "Crédito": "120000,00", "Saldo": "1653500,00"},

        # === Comisiones bancarias / mantenimiento (clasificación automática) ===
        {"Fecha": "05/02/2026", "Referencia": "COM. MANTENIMIENTO CUENTA",
         "Débito": "2500,00", "Crédito": "", "Saldo": "1531000,00"},
        {"Fecha": "10/02/2026", "Referencia": "IMP. SELLOS BANCARIOS",
         "Débito": "750,00", "Crédito": "", "Saldo": "1530250,00"},
        {"Fecha": "20/02/2026", "Referencia": "COMISION POR TRANSFERENCIA SAL.",
         "Débito": "1250,00", "Crédito": "", "Saldo": "1529000,00"},

        # === Débitos automáticos servicios ===
        {"Fecha": "07/02/2026", "Referencia": "DEBITO SERV. EDESAL ENERGIA",
         "Débito": "45000,00", "Crédito": "", "Saldo": "1485250,00"},
        {"Fecha": "07/02/2026", "Referencia": "DEBITO CBU SEPA INTERNET",
         "Débito": "12000,00", "Crédito": "", "Saldo": "1473250,00"},

        # === Retiros de socios (débitos sin match auto) ===
        {"Fecha": "14/02/2026", "Referencia": "TRANSF SAL. PABLO LARRANAGA",
         "Débito": "500000,00", "Crédito": "", "Saldo": "1033250,00"},
        {"Fecha": "21/02/2026", "Referencia": "TRANSF SAL. MARISOL BORREGO",
         "Débito": "350000,00", "Crédito": "", "Saldo": "683250,00"},

        # === Sin match (revisión manual) ===
        {"Fecha": "25/02/2026", "Referencia": "TRANSFERENCIA DESCONOCIDA REF 0099",
         "Débito": "", "Crédito": "55000,00", "Saldo": "738250,00"},
        {"Fecha": "26/02/2026", "Referencia": "PAGO IMP IIBB ARBA",
         "Débito": "32000,00", "Crédito": "", "Saldo": "706250,00"},

        # === Más transferencias entrantes ===
        {"Fecha": "27/02/2026", "Referencia": "TRANSF DE 27987654321 FARMACIA DEL CENTRO",
         "Débito": "", "Crédito": "25000,00", "Saldo": "731250,00"},
    ]

    df = pd.DataFrame(rows)
    df.to_excel(out_path, index=False)
    return out_path


if __name__ == "__main__":
    p = crear_extracto_pampa(Path(__file__).parent / "extracto_pampa_feb2026.xlsx")
    print(f"Extracto sintético creado: {p}")
