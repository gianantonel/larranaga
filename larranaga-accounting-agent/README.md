# larranaga-accounting-agent

Módulo de transformaciones sobre los Excel que exporta ARCA (Libro IVA Compras).

## Alcance inicial

- **R-01** — Corrección comprobantes tipo B/C + formato tipo de cambio (col. L).
- **R-02** — División de comprobantes por múltiples alícuotas (pendiente).

## Estructura

```
src/transformaciones/limpieza_inicial.py   # R-01
tests/test_limpieza_inicial.py             # tests unitarios
tests/fixtures/                            # Excels reales (no commitear)
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Tests

```bash
pytest -v
```
