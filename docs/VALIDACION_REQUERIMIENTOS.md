# Validación de Requerimientos — Fase 1 y Fase 2
**Estudio Larrañaga · Optimizar · Mayo 2026**

> Este documento valida cada requerimiento implementado en las Fases 1 y 2 con evidencia de tests automatizados, endpoints expuestos y pantallas en producción.
>
> **Tests verdes:** 175 (59 backend FastAPI + 116 accounting agent).
> **Branches:** `fase-2` (mergeado a `dev`) · `fase-3` creada desde `dev`.

---

## Resumen ejecutivo

| Fase | Requerimientos | Estado |
|------|----------------|--------|
| **Fase 1** | R-01 · R-02 · R-03 · R-04 · R-05 · R-07 | ✅ Completa |
| **Fase 2** | R-06 · R-08 · R-09 · R-10 · R-14 + extensión R-04 | ✅ Completa |
| **Fase 3** | R-11 · R-12 · R-13 · R-15 | 🚧 Plan listo (`docs/FASE3_TASKS.md`) |

---

## Fase 1 — Quick wins (Semanas 1–3)

### R-01 · Corrección B/C + formato Tipo Cambio
| Aspecto | Evidencia |
|---|---|
| **Implementación** | `larranaga-accounting-agent/src/transformaciones/limpieza_inicial.py` |
| **Tests** | `tests/test_limpieza_inicial.py` — 22 tests verdes |
| **Endpoint** | `POST /herramientas/limpiar-libro-iva` |
| **UI** | Pantalla **Herramientas** (acción "Corrección B/C / Holistor Columna L") |
| **Validación** | Procesa 359 filas × 30 columnas del fixture BUTALO Feb-2026 sin errores |

### R-02 · División por múltiples alícuotas
| Aspecto | Evidencia |
|---|---|
| **Implementación** | `larranaga-accounting-agent/src/transformaciones/division_alicuotas.py` |
| **Tests** | `tests/test_division_alicuotas.py` — 40 tests verdes |
| **Endpoint** | Integrado en `POST /herramientas/limpiar-libro-iva` (tras R-01) |
| **Validación** | Detecta filas multi-alícuota (21% + 27%), expande con sufijo `/A`, `/B`, preserva `Imp. Total` |

### R-03 · Cálculo de honorarios fijo + producto
| Aspecto | Evidencia |
|---|---|
| **Modelos** | `Honorario` (tipo: fijo/producto), `ProductoReferencia` |
| **Endpoints** | `POST /honorarios/`, `GET /honorarios/?client_id=&period=`, `POST /honorarios/calcular` |
| **UI** | Pantalla **Honorarios** con filtros y modal de creación |
| **Validación** | Cálculo automático: tipo `fijo` → importe directo, tipo `producto` → cantidad × precio vigente |

### R-04 · Liquidación mensual de profesionales
| Aspecto | Evidencia |
|---|---|
| **Endpoints** | `GET /profesionales/liquidaciones/{id}/{period}`, `POST /profesionales/liquidaciones/{id}/{period}/cerrar` |
| **UI** | Pantalla **Liquidaciones** (tema dark unificado) — tabla por profesional con expand de detalle |
| **Extensión Fase 2** | Adelantos calculados automáticamente desde tabla `pagos` |

### R-05 · Separación retenciones IVA vs IIBB
| Aspecto | Evidencia |
|---|---|
| **Implementación** | `larranaga-accounting-agent/src/clasificadores/retenciones_classifier.py` |
| **Tests** | `tests/test_retenciones_classifier.py` |
| **AFIP SDK** | Integración con `mis-retenciones` — `codigoRegimen` discrimina IV/IB/IG |

### R-07 · Cuentas corrientes en tiempo real
| Aspecto | Evidencia |
|---|---|
| **Modelo** | `MovimientoCuentaCorriente` (tipo ingreso/egreso, monto, fecha, forma_pago, profesional_id) |
| **Endpoints** | `/cuentas-corrientes/{client_id}` (saldo + movimientos) |
| **UI** | Pantalla **Cuentas Corrientes** con buscador, listado y modal de detalle |

---

## Fase 2 — Pipeline IVA + Tesorería (Semanas 4–6)

### R-06 · Conciliación IVA — posición mensual
| Aspecto | Evidencia |
|---|---|
| **Endpoint** | `GET /iva/posicion?periodo=YYYY-MM` |
| **UI** | Pantalla **Posición IVA** con 3 tarjetas (Débito · Crédito · Posición) y selector de período |
| **Lógica** | Suma IVA débito (ventas) − IVA crédito (compras). Color verde si saldo a favor, rojo si deuda. |

### R-08 · Tesorería — `POST /pagos/` con impacto automático
| Aspecto | Evidencia |
|---|---|
| **Endpoint** | `POST /pagos/` (`backend/app/routers/pagos.py`) |
| **UI** | Pantalla **Registrar Cobro** (tema dark, panel de billetes condicional) |
| **Test E2E** | `backend/tests/test_flujo_cobro.py::test_cobro_efectivo_impacta_4_modulos` ✅ |
| **4 impactos verificados** | (a) CC del cliente · (b) tabla `pagos` · (c) preview liquidación profesional · (d) stock billetes |
| **Rollback** | `test_cobro_efectivo_billetes_no_cuadran_rollback` ✅ — si billetes no cuadran (HTTP 422), nada se persiste |

### R-09 · Imputación contable por CUIT
| Aspecto | Evidencia |
|---|---|
| **Modelo** | `MaestroProveedor` (cuit, razon_social, cuenta_contable, fuente: manual/padron/ia/fallback) |
| **Endpoint** | `GET /imputacion/cuit/{cuit}` — pipeline 3 niveles (cache → padrón ARCA → manual) |
| **UI** | Pantalla **Maestro Proveedores** (tema dark) con búsqueda, edición inline y badge de fuente |

### R-10 · Generación HWCRARCA
| Aspecto | Evidencia |
|---|---|
| **Implementación** | `larranaga-accounting-agent/src/transformaciones/hwcrarca_builder.py` |
| **Tests** | `tests/test_hwcrarca_builder.py` — 37 tests · `tests/test_pipeline_completo.py` — 17 tests E2E con fixture BUTALO |
| **Hook validación** | `validar_cuadre()` con tolerancia dual (absoluta $0,01 + relativa 1%) — lanza `CuadreError` |
| **Endpoint** | `POST /herramientas/generar-hwcrarca` — devuelve .xlsx + stats Debe/Haber, HTTP 422 si no cuadra |
| **UI** | Paso 3 en **Herramientas** con botón de descarga y stats coloreados |

### R-14 · Control de billetes / caja efectivo
| Aspecto | Evidencia |
|---|---|
| **Modelos** | `ControlBillete` (5 denominaciones: 1.000 · 2.000 · 5.000 · 10.000 · 20.000), `MovimientoBillete` (auditoría) |
| **Endpoints** | `GET /billetes/`, `POST /billetes/movimiento` |
| **Integración R-08** | Si `forma_pago=efectivo` y `billetes` provistos: validación suma == importe (±$1) y aplicación atómica |
| **UI** | Panel embebido en **Registrar Cobro** con stock visible y total calculado en vivo |

---

## Cobertura de tests

```
backend/tests/                               59 passed
  test_comprobantes_parser.py                ✅
  test_cruce.py                              ✅
  test_retenciones_classifier.py             ✅
  test_flujo_cobro.py (E-02)                 ✅ NEW
larranaga-accounting-agent/tests/           116 passed
  test_limpieza_inicial.py                   ✅ 22
  test_division_alicuotas.py                 ✅ 40
  test_hwcrarca_builder.py                   ✅ 37
  test_pipeline_completo.py                  ✅ 17
─────────────────────────────────────────────────────
TOTAL                                       175 passed
```

---

## Endpoints expuestos (snapshot de OpenAPI)

| Categoría | Endpoints |
|---|---|
| **IVA** | `/iva/`, `/iva/posicion`, `/iva/{id}/file`, `/iva/summary/{client_id}` |
| **Pagos (R-08)** | `POST /pagos/`, `GET /pagos/`, `GET /pagos/{id}` |
| **Billetes (R-14)** | `GET /billetes/`, `POST /billetes/movimiento` |
| **Liquidaciones** | `GET /profesionales/liquidaciones/preview` (batch), `GET /profesionales/liquidaciones/{id}/preview`, `POST /profesionales/liquidaciones/{id}/{period}/cerrar` |
| **Imputación (R-09)** | `GET /imputacion/cuit/{cuit}`, `GET /imputacion/proveedores`, `PATCH /imputacion/proveedores/{id}` |
| **Herramientas** | `POST /herramientas/limpiar-libro-iva` (R-01+R-02), `POST /herramientas/generar-hwcrarca` (R-10) |

---

## UI verificada en Chrome

✅ Login (Federico Rodriguez · Super Admin) → Dashboard carga con métricas.
✅ Sidebar muestra **Registrar Cobro** y **Liquidaciones** (módulos nuevos de Fase 2).
✅ Pantalla **Registrar Cobro** con tema dark unificado (cliente, importe, transferencia/efectivo).
✅ Cobro de prueba: $15.000 · Restaurante El Gaucho · Manuel Larrañaga → banner verde "registrado correctamente · Saldo CC: $15.000".
✅ Pantalla **Liquidaciones** del mes muestra Manuel Larrañaga con $15.000 en columna **Adelantos** (impacto verificado en pantalla).

---

## Próximo: Fase 3

Ver `docs/FASE3_TASKS.md` para el plan detallado:
- **R-15** Conciliación bancaria (Pampa · Santander · Mercado Pago) + matching automático
- **R-11** Flujo de fondos · seguimiento + proyección
- **R-12** Retiro de honorarios de socios
- **R-13** Actualización cuatrimestral con pantalla de validación granular

División Fede / Gero documentada · ~50 hs Fede · ~40 hs Gero.

---

*Documento Optimizar × Larrañaga · Mayo 2026*
