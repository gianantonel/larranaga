# Fase 3 — Conciliación bancaria + Flujo de fondos
## Plan de Tareas por Sprint · Semanas 7–10

> **Devs:** Fede (Bancario · IVA-link) · Gero (ADM avanzado · UI)
> **Rama:** `fase-3` (creada desde `dev` post-merge fase-2)
> **Entregables clave:** Parsers bancarios + matching automático + flujo de fondos real vs. proyectado + retiro de socios + actualización cuatrimestral de honorarios

Fuentes:
- `docs/Plan_Maestro_Implementacion.md` § Fase 3 (R-15, R-11, R-12, R-13)
- `docs/Requerimiento_ADM_Tesoreria.md` § 2.3, 2.4, 3, 4
- `docs/Requerimiento_IVA.md`

---

## ⚠️ Riesgo principal a vigilar

**R-15 (conciliación bancaria)** depende del formato real de los extractos de **Banco Pampa, Santander y Mercado Pago**. Hasta validar contra archivos reales, los parsers se desarrollan contra fixtures sintéticas razonables.

**Mitigación:** Fede arranca con parsers básicos + algoritmo de matching contra fixtures. En la **mitad del sprint 2** revalidamos con extractos reales. Si el formato cambia, el parser se ajusta sin tocar el matching.

---

## 🚀 Sprint 1 — Semana 7: Parsers bancarios + Retiros de socios

**Objetivo:** Importar un extracto bancario y dejarlo listo para conciliar. En paralelo, registrar retiros de socios con impacto en tesorería.

---

### Fede — R-15 (parte A): Parsers bancarios + import extracto

#### F3-01 · Modelo `MovimientoBancario` + `ExtractoBancario`
- **Dificultad:** 🟢 Fácil — **Tiempo:** ~3 hs
- **Tablas:**
  - `extractos_bancarios` (id, banco, periodo, archivo_path, fecha_importacion, n_movimientos, n_conciliados, n_pendientes)
  - `movimientos_bancarios` (id, extracto_id, banco, fecha, descripcion, importe, tipo D/C, saldo, cuit_detectado, conciliado, movimiento_tesoreria_id, pago_id)
- **Archivos:** `backend/app/models.py`, `backend/app/main.py` (migración)
- **Entregable:** Tablas creadas. Migración cubierta.

#### F3-02 · Servicio `parsers/base_parser.py` + `pampa_parser.py`
- **Dificultad:** 🟡 Media — **Tiempo:** ~5 hs
- **Descripción:** Implementar `BankParser` abstracto (ver Plan Maestro §3.5) con `parse(filepath, periodo) → list[dict]`. Detección de CUIT en descripción (regex `\b\d{2}-?\d{8}-?\d\b`). Implementar `PampaParser` concreto.
- **Archivos:** `larranaga-accounting-agent/src/bancos/base_parser.py`, `pampa_parser.py`
- **Tests:** `tests/test_parsers.py` con fixture sintética
- **Entregable:** Parser Pampa procesa Excel sintético → 30 movimientos normalizados.

#### F3-03 · Parsers Santander + Mercado Pago
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Descripción:** Misma estructura que Pampa, columnas distintas (ver Plan Maestro). MP es CSV con monto único (positivo=entrada, negativo=salida).
- **Archivos:** `santander_parser.py`, `mercadopago_parser.py`
- **Entregable:** 3 parsers operativos contra fixtures sintéticas.

#### F3-04 · Endpoint `POST /conciliacion/import-extracto`
- **Dificultad:** 🟡 Media — **Tiempo:** ~3 hs
- **Descripción:** Recibe `multipart/form-data` con `banco` (`pampa|santander|mercadopago`), `periodo` (YYYY-MM), `file`. Llama al parser correspondiente, persiste `ExtractoBancario` + `MovimientoBancario[]`. Devuelve stats: `{n_movimientos, n_creditos, n_debitos}`.
- **Archivos:** `backend/app/routers/conciliacion.py`
- **Entregable:** Importar un Excel de Pampa de febrero 2026 → tabla con 30 filas en DB.

---

### Gero — R-12: Retiros de socios

#### G3-01 · Modelo `RetiroSocio` + migración
- **Dificultad:** 🟢 Fácil — **Tiempo:** ~2 hs
- **Tabla:** `retiros_socios` (id, profesional_id [FK con `tipo='socio'`], fecha, importe, forma_pago, banco_origen, conciliado, movimiento_tesoreria_id, notas)
- **Archivos:** `backend/app/models.py`, `backend/app/main.py`
- **Entregable:** Tabla creada con migración.

#### G3-02 · Endpoint `POST /retiros/`
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Descripción:** Registra un retiro con impacto automático en tesorería:
  1. Validar que el profesional sea `tipo='socio'`
  2. Crear `RetiroSocio`
  3. Crear `MovimientoCuentaCorriente` tipo egreso a nombre del socio (CC interna del estudio o CC de socio si existe)
  4. Crear `MovimientoTesoreria` tipo egreso categoría `retiro_socio`
  5. Si forma_pago=efectivo → restar de billetes
  6. Devolver `{retiro_id, mov_tesoreria_id, saldo_actualizado}`
- **Archivos:** `backend/app/routers/retiros.py` (nuevo)
- **Entregable:** Retiro de Pablo en efectivo $500.000 → impacto en tesorería + billetes.

#### G3-03 · Endpoints `GET /retiros/`
- **Dificultad:** 🟢 Fácil — **Tiempo:** ~2 hs
- Listado filtrable por socio + período. Detalle por id.
- **Archivos:** `backend/app/routers/retiros.py`

#### G3-04 · Frontend: pantalla `RetirosSocios.jsx`
- **Dificultad:** 🟡 Media — **Tiempo:** ~5 hs
- **Descripción:** Tabla con histórico de retiros. Filtros por socio + período. Botón "Nuevo retiro" que abre modal con: socio (dropdown), importe, forma_pago (toggle efectivo/transferencia), banco_origen (si transferencia), notas. Si efectivo y stock insuficiente → bloquear.
- **Archivos:** `frontend/src/pages/RetirosSocios.jsx`, ruta + sidebar
- **Entregable:** UI completa funcionando end-to-end.

---

## ⚙️ Sprint 2 — Semana 8: Algoritmo de matching + Flujo de fondos

**Objetivo:** Movimientos bancarios importados se cruzan automáticamente con pagos/egresos. Inicio del módulo de flujo de fondos.

---

### Fede — R-15 (parte B): Matching automático + cola de revisión

#### F3-05 · Servicio `services/conciliacion.py` con algoritmo de matching
- **Dificultad:** 🔴 Alta — **Tiempo:** ~6 hs
- **Descripción:** Para cada movimiento bancario sin conciliar, intentar match contra (Plan Maestro §2.3):
  - **Crédito** → `Pago` con CUIT detectado (en descripción) + importe exacto + fecha ±1 día.
  - **Débito** → `Retiro` (importe + fecha + nombre socio en desc) o egreso de tesorería.
  - **Débito automático** → palabras clave (CBU, SERV, IMP, SEPA) → categoría parametrizada.
  - **Comisión bancaria** → palabras (COM., MANT., IMP.) → crear egreso categoría `gbc`.
- **Output:** `{matched: [...], pending: [...], stats: {auto, manual_required}}`
- **Archivos:** `backend/app/services/conciliacion.py`
- **Tests:** `tests/test_matching.py` con escenarios variados.

#### F3-06 · Endpoint `POST /conciliacion/{extracto_id}/run-matching`
- **Dificultad:** 🟡 Media — **Tiempo:** ~3 hs
- Ejecuta el algoritmo sobre un extracto importado, persiste matches y devuelve stats.
- **Archivos:** `backend/app/routers/conciliacion.py`

#### F3-07 · Endpoint `POST /conciliacion/movimiento/{id}/match-manual`
- **Dificultad:** 🟡 Media — **Tiempo:** ~3 hs
- Match manual: el operador asigna `pago_id` o `egreso_id` o crea categoría custom.
- **Archivos:** `backend/app/routers/conciliacion.py`

#### F3-08 · Frontend: pantalla `ConciliacionBancaria.jsx`
- **Dificultad:** 🔴 Alta — **Tiempo:** ~8 hs
- **Layout:** Tres tabs:
  1. **Importar:** drag&drop archivo + selector banco + período + botón "Procesar".
  2. **Conciliados:** tabla read-only con badge verde, link al pago/egreso vinculado.
  3. **Pendientes:** tabla con filas accionables. Cada fila tiene dropdown "Asociar a..." con sugerencias auto-completadas (top 3 candidatos por similitud) + opción "Crear egreso nuevo".
- **Archivos:** `frontend/src/pages/ConciliacionBancaria.jsx`, ruta + sidebar.
- **Entregable:** Flujo E2E funcional con extracto BUTALO Feb 2026.

---

### Gero — R-11: Flujo de fondos — proyección y seguimiento

#### G3-05 · Vista calculada `flujo_fondos_mensual`
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Descripción:** Endpoint `GET /flujo-fondos/?periodo=AAAA-MM` que devuelve por cliente: `{deuda_inicio, hon_devengado, cobrado, deuda_fin}` (ver Plan Maestro §2.3 — tablero del estudio). Calcula desde `Honorario` + `Pago` + `MovimientoCuentaCorriente`.
- **Archivos:** `backend/app/routers/flujo_fondos.py` (nuevo), `services/flujo_fondos.py`

#### G3-06 · Endpoint `GET /flujo-fondos/anual?year=AAAA`
- **Dificultad:** 🟡 Media — **Tiempo:** ~3 hs
- Variante anual: una fila por cliente, columnas Ene–Dic con `hon_devengado` y `cobrado`. Fila final TOTAL.
- **Archivos:** `backend/app/routers/flujo_fondos.py`

#### G3-07 · Frontend: pantalla `FlujoDeFondos.jsx`
- **Dificultad:** 🔴 Alta — **Tiempo:** ~7 hs
- **Layout:** Toggle Mensual/Anual. Tabla pivote con clientes como filas. Filtro por profesional responsable. Fila TOTAL al pie. Las celdas con deuda > 0 destacadas en rojo, saldos a favor en verde. Export Excel.
- **Archivos:** `frontend/src/pages/FlujoDeFondos.jsx`
- **Entregable:** Tablero completo funcional.

#### G3-08 · Hook de consistencia CC ↔ Flujo
- **Dificultad:** 🟢 Fácil — **Tiempo:** ~2 hs
- **Descripción:** Endpoint `GET /flujo-fondos/verificar-consistencia?periodo=AAAA-MM` que compara saldo CC de cada cliente contra "Deuda mes" calculada en flujo. Si difieren > $0,10 → reporta inconsistencia. Frontend muestra warning en `FlujoDeFondos.jsx`.
- **Archivos:** `backend/app/services/flujo_fondos.py`

---

## 🔁 Sprint 3 — Semana 9: Actualización cuatrimestral + integración

**Objetivo:** R-13 completo. Refinamiento del matching con extractos reales. Mejoras de UX según feedback.

---

### Gero — R-13: Actualización cuatrimestral de honorarios

#### G3-09 · Modelo `IndiceActualizacion` + endpoint cálculo previsualización
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Tabla:** `indices_actualizacion` (id, periodo, indice_pct, fuente [`ipc`|`manual`|`negociado`], aplicado, fecha_aplicacion).
- **Endpoint:** `POST /honorarios/preview-actualizacion` con body `{indice_pct, periodo_aplicacion}` → devuelve tabla con `cliente`, `importe_actual`, `importe_propuesto`, `delta_pct`. Aún no aplica.
- **Archivos:** `backend/app/routers/honorarios.py`, `models.py`
- **Entregable:** Preview de 100 clientes con importe propuesto.

#### G3-10 · Endpoint `POST /honorarios/aplicar-actualizacion`
- **Dificultad:** 🟡 Media — **Tiempo:** ~3 hs
- Recibe lista de `client_id` confirmados (checkbox). Persiste `Honorario` con nuevo importe a partir de `periodo_aplicacion`. Marca `IndiceActualizacion.aplicado=true`.
- **Archivos:** `backend/app/routers/honorarios.py`

#### G3-11 · Frontend: pantalla `ActualizarHonorarios.jsx`
- **Dificultad:** 🟡 Media — **Tiempo:** ~5 hs
- **Layout:** Step 1 — input índice + selector período. Step 2 — tabla `cliente / actual / propuesto / Δ% / [✓]`. Botón "Aplicar a seleccionados". Step 3 — confirmación con resumen de cuántos se aplicaron.
- **Archivos:** `frontend/src/pages/ActualizarHonorarios.jsx`

---

### Fede — R-15 (parte C): Refinamiento + Claude API fallback

#### F3-12 · Sugerencia con Claude API para movimientos sin match
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Descripción:** Para movimientos pendientes después del matching automático, llamar a Claude API con prompt: "Acá hay un movimiento bancario [descripción, importe, fecha]. Estos son los pagos pendientes [lista top 10 por importe similar]. ¿Cuál es el match más probable y por qué?". Devuelve sugerencia con score de confianza.
- **Archivos:** `backend/app/services/conciliacion_ai.py`

#### F3-13 · Tests integración con extractos reales
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Descripción:** Si el cliente nos pasa extractos reales de Pampa/Santander/MP de un mes, agregar como fixture. Asegurar parser y matching los procesa sin error. Documentar diferencias contra fixture sintética.
- **Archivos:** `tests/fixtures/extractos_reales/`, `tests/test_parsers_real.py`

---

## 🧪 Sprint 4 — Semana 10: QA + Documentación

#### E3-01 · [Fede] Test E2E: importar extracto Pampa → matching automático → conciliar 80% → revisión manual del 20%
- **Tiempo:** ~3 hs
- **Archivos:** `tests/test_conciliacion_e2e.py`

#### E3-02 · [Gero] Test E2E: registrar pago + retiro socio + cierre flujo de fondos consistente
- **Tiempo:** ~3 hs
- **Archivos:** `backend/tests/test_flujo_fondos_e2e.py`

#### E3-03 · [Ambos] Demo manual + actualización del README de la rama fase-3
- **Tiempo:** ~3 hs

---

## 📊 Resumen de carga total

| Dev | Tareas | Tiempo estimado |
|-----|--------|-----------------|
| **Fede** | F3-01 → F3-13 + E3-01 + E3-03 | ~50 hs (~2.5 semanas efectivas) |
| **Gero** | G3-01 → G3-11 + E3-02 + E3-03 | ~40 hs (~2 semanas efectivas) |

---

## 🗺️ Mapa de dependencias

```
SPRINT 1 (Semana 7)
  Fede:  F3-01 → F3-02 → F3-03 → F3-04
  Gero:  G3-01 → G3-02 → G3-03 → G3-04
  [Independientes — sin bloqueos]

SPRINT 2 (Semana 8)
  Fede:  F3-04 → F3-05 → F3-06 → F3-07 → F3-08
  Gero:  G3-05 → G3-06 → G3-07 → G3-08

SPRINT 3 (Semana 9)
  Fede:  F3-12 → F3-13
  Gero:  G3-09 → G3-10 → G3-11

SPRINT 4 (Semana 10)
  Ambos: E3-01, E3-02, E3-03
```

---

## ✅ Checklist de cierre de Fase 3

- [ ] Parsers operativos para Pampa, Santander y Mercado Pago (Excel + CSV)
- [ ] Algoritmo de matching automático conecta ≥70% de movimientos en fixture BUTALO
- [ ] UI de revisión manual permite resolver el 100% de pendientes en ≤5 min/extracto
- [ ] `POST /retiros/` con impacto automático en tesorería + billetes
- [ ] Pantalla flujo de fondos consistente con CC (verificación pasa)
- [ ] Pantalla actualización cuatrimestral aplica a 100 clientes con confirmación granular
- [ ] Tests E2E verdes
- [ ] Demo grabada con extracto real
- [ ] Rama `fase-3` mergeada a `dev`

---

## 🔜 Vista preliminar Fase 4 (no bloqueante para esta planificación)

- **R-16/R-19:** Reportes IVA-MES automáticos + consulta ARCA
- **R-17:** Informes de gestión consolidados (deuda, honorarios, retiros, flujo)
- **R-18:** Liquidación impuestos + VEPs (MVP IVA primero)
- **R-20:** Migración histórica desde Excel del estudio

---

*Documento Optimizar × Larrañaga · Fase 3 · Mayo 2026*
