# Fase 3 — Cierre de tareas de Fede
**Estudio Larrañaga · Optimizar · Mayo 2026**

> Branch: `fase-3` · Tests: **125 verdes** (29 backend nuevos + 116 accounting agent)
> Requerimiento R-15 (Conciliación bancaria) — completo end-to-end

---

## Tareas completadas

| ID | Descripción | Estado |
|---|---|---|
| **F3-01** | Modelos `ExtractoBancario` + `MovimientoBancario` | ✅ |
| **F3-02** | `BankParser` ABC + `PampaParser` | ✅ |
| **F3-03** | `SantanderParser` + `MercadoPagoParser` | ✅ |
| **F3-04** | `POST /conciliacion/import-extracto` | ✅ |
| **F3-05** | Algoritmo de matching automático (CUIT + importe + fecha + keywords) | ✅ |
| **F3-06** | `POST /conciliacion/{id}/run-matching` | ✅ |
| **F3-07** | `POST /conciliacion/movimiento/{id}/match-manual` + `/desconciliar` + `/sugerencias` | ✅ |
| **F3-08** | Frontend `ConciliacionBancaria.jsx` (3 tabs + tabla + modal manual) | ✅ |
| **F3-12** | Refinamiento opcional con Claude API (fallback heurístico) | ✅ |
| **F3-13** | Fixture sintética realista del Banco Pampa Feb-2026 | ✅ |
| **E3-01** | Test E2E del pipeline completo (import → matching → manual → desconciliar) | ✅ |

---

## Endpoints expuestos

```
POST  /conciliacion/import-extracto              multipart: banco + periodo + file
GET   /conciliacion/extractos                    listado con filtros
GET   /conciliacion/extracto/{id}/movimientos    con flag solo_pendientes
POST  /conciliacion/{id}/run-matching            algoritmo automático
POST  /conciliacion/movimiento/{id}/match-manual operador asocia pago
POST  /conciliacion/movimiento/{id}/desconciliar libera pago
GET   /conciliacion/movimiento/{id}/sugerencias  ?top_n=3&use_ai=true
```

---

## Frontend

**Pantalla `ConciliacionBancaria.jsx`** (`/conciliacion-bancaria`)

- **Tab Importar:** drag&drop + selector banco/período → muestra stats post-import
- **Tab Extractos:** listado de extractos con conciliados/pendientes
- **Detalle:** tabla de movimientos con filtros (todos/pendientes/conciliados) + buscador por descripción/CUIT
- **Modal manual:** top 5 candidatos con score + botón "Asociar"

Tema dark consistente (clases `card`/`input-field`/`btn-primary`/`modal-panel`/`badge-*`).

---

## Tests

```
backend/tests/                                       29 nuevos
  test_flujo_cobro.py (E-02 — fase 2)               3
  test_conciliacion.py (F3-05/06/07)                8
  test_pipeline_conciliacion.py (E3-01)             3 (E2E)
  + tests previos                                  15

larranaga-accounting-agent/tests/                 116 (sin cambios)
  test_bancos_parsers.py (F3-02/F3-03)             10
  + tests previos                                 106

TOTAL FASE 3 (Fede)                              125 verdes
```

Comando: `pytest backend/tests/ larranaga-accounting-agent/tests/`

---

## Activar IA en sugerencias

El endpoint `GET /conciliacion/movimiento/{id}/sugerencias?use_ai=true` usa Claude para refinar el ranking de candidatos.

```bash
# En backend/.env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5  # opcional
```

Sin API key, devuelve sugerencias heurísticas (importe + fecha + CUIT). El servicio `services/conciliacion_ai.py` maneja el fallback de forma transparente.

---

## Reemplazar fixture por extracto real

```bash
# 1. Exportar el extracto del homebanking (mensual, .xlsx)
# 2. Reemplazar el archivo:
cp /ruta/extracto_real.xlsx larranaga-accounting-agent/tests/fixtures/extracto_pampa_feb2026.xlsx

# 3. Re-correr los tests:
pytest backend/tests/test_pipeline_conciliacion.py -v
```

Si el formato del banco cambió, ajustar `larranaga-accounting-agent/src/bancos/pampa_parser.py` (o `santander_parser.py` / `mercadopago_parser.py`).

---

## Lo que queda manual

1. **Test con extractos reales** del Banco Pampa, Santander y Mercado Pago (cuando los pase Larrañaga)
2. **Demo grabada** del flujo completo (5–10 min)
3. **Configurar `ANTHROPIC_API_KEY`** si se quiere usar IA en sugerencias
4. **E3-03** Demo + README de la rama (compartido con Gero al cerrar Fase 3)

---

*Documento Optimizar × Larrañaga · Cierre de tareas de Fede en Fase 3 · Mayo 2026*
