# Fase 3 — Gero · Cierre de entrega

**Estudio Larrañaga · Optimizar · Mayo 2026**
Branch: `gero` (ya integra `fase-2` y `fase-3` por fast-forward)

---

## 🎯 Alcance entregado

Tres requerimientos cuatrimestrales, 11 historias de implementación + 2 de QA, todo testeado E2E.

| Req | Descripción | Tareas |
|---|---|---|
| **R-12** | Retiros de honorarios de socios con impacto en tesorería + caja de billetes | G3-01..04 |
| **R-11** | Flujo de fondos (devengado vs cobrado) + hook de consistencia CC ↔ Flujo | G3-05..08 |
| **R-13** | Actualización cuatrimestral por índice (IPC / manual / negociado) con validación granular | G3-09..11 |
| **E3** | Tests E2E backend (pytest) + capturas + esta entrega | E3-02, E3-03 |

---

## 🗂️ Cambios por archivo

### Backend

**Modelos nuevos** ([backend/app/models.py](../backend/app/models.py)):
- `MovimientoTesoreria` — libro central de movimientos del estudio (ingreso/egreso × categoría: cobro_cliente, retiro_socio, gasto_general, impuesto, sueldo, gasto_bancario, otro).
- `RetiroSocio` — retiros con FK a `MovimientoTesoreria`.
- `IndiceActualizacion` — cabecera de cada actualización cuatrimestral (persiste con `aplicado=false` desde el preview).
- `HistorialActualizacionHonorario` — auditoría de cada cambio en `importe_honorario`.

**Routers nuevos / modificados:**
- `routers/retiros.py` (nuevo) — `POST /retiros/`, `GET /retiros/`, `GET /retiros/{id}`.
- `routers/flujo_fondos.py` (nuevo) — `GET /flujo-fondos/?periodo`, `GET /flujo-fondos/anual?year`, `GET /flujo-fondos/verificar-consistencia?periodo`.
- `routers/honorarios.py` (extendido) — `POST /honorarios/preview-actualizacion`, `POST /honorarios/aplicar-actualizacion`. Endpoints viejos (`/actualizacion-cuatrimestral/...`) preservados por compatibilidad.

**Services:**
- `services/flujo_fondos.py` (nuevo) — `saldo_cc_a_fecha`, `flujo_fondos_mensual`, `flujo_fondos_anual`, `verificar_consistencia`.

### Frontend

**Páginas nuevas** ([frontend/src/pages/](../frontend/src/pages/)):
- `RetirosSocios.jsx` — listado + filtros + modal de nuevo retiro con detalle de billetes si efectivo.
- `FlujoDeFondos.jsx` — toggle Mensual/Anual, filtros (período, profesional), tabla pivote con coloreo de saldos, export CSV.
- `ActualizarHonorarios.jsx` — wizard de 3 steps (definir índice → preview con checkboxes → confirmación con devengado proyectado).

**Sidebar**: 3 ítems agregados ("Retiros Socios", "Flujo de Fondos", "Actualizar Honorarios").
**API helpers** en [frontend/src/utils/api.js](../frontend/src/utils/api.js): `getRetiros`, `crearRetiro`, `getFlujoFondosMensual/Anual`, `verificarConsistenciaFlujo`, `previewActualizacionHonorarios`, `aplicarActualizacionHonorarios`.

### Tests E2E

[backend/tests/test_flujo_fondos_e2e.py](../backend/tests/test_flujo_fondos_e2e.py) — **5 tests verdes** (SQLite en memoria + StaticPool):

1. `test_e2e_pago_retiro_consistencia_ok` — escenario principal (pago $3.05M + retiro $500k → consistencia OK + flujo correcto + tesorería + billetes).
2. `test_consistencia_detecta_honorario_sin_cc` — el hook detecta cuando un Honorario no se reflejó en CC.
3. `test_flujo_anual_coincide_con_mensual` — el total anual del mes M coincide con el total del endpoint mensual.
4. `test_aplicar_indice_actualizacion_persiste_historial` — preview crea índice → aplicar marca aplicado y registra historial → re-aplicar 409.
5. `test_retiro_no_socio_rechazado` — solo profesionales `tipo=socio` pueden retirar.

Suite total: **75/75 passed** (los 5 nuevos no rompen los 70 existentes).
Correr: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_flujo_fondos_e2e.py -v`

---

## 🧠 Decisiones de diseño y tradeoffs

### `MovimientoTesoreria` — modelo nuevo no pedido explícitamente
La doc original menciona un `mov_tesoreria_id` en `RetiroSocio`, pero **el modelo no existía**. Lo creé porque es el "libro de tesorería" que el cliente describe en `Requerimiento_ADM_Tesoreria.md` § 4.2 y porque R-11 (flujo de fondos) lo va a necesitar para gastos manuales en el futuro.

### CC interna del estudio — no implementada en el retiro
La doc pedía crear un `MovimientoCuentaCorriente` egreso al registrar el retiro, pero `MovimientoCuentaCorriente.client_id` es `NOT NULL` y el estudio no es un `Client`. Decisión: **no se crea movimiento_cc del estudio**; el retiro queda registrado en `RetiroSocio` + `MovimientoTesoreria`, y la liquidación del socio (R-04) puede consultar `RetiroSocio` para calcular cuánto retiró. Si el equipo prefiere implementar la CC del estudio, requiere hacer `client_id` nullable y ajustar `_saldo_cc`.

### Hook de consistencia — semántica
Compara, por cliente y período:
- **Calculado** = `deuda_inicio + devengado − cobrado` (regla contable).
- **Real** = `−saldo_cc al fin del período`.

Si `|calculado − real| > tolerancia` (default $0,10), reporta inconsistencia. Esto detecta el **bug actual del sistema**: los `Honorario` no generan automáticamente movimientos de CC, así que el saldo no refleja el devengado. El hook expone ese gap explícitamente para que el equipo decida si lo arregla o lo deja documentado.

### Export CSV en lugar de Excel
[FlujoDeFondos.jsx](../frontend/src/pages/FlujoDeFondos.jsx) exporta CSV con BOM UTF-8 (abre directo en Excel). Evité agregar la dependencia `xlsx` (~700 KB minified) porque CSV cubre el caso de uso.

### Actualización por índice — qué pasa con clientes `tipo=producto`
`POST /honorarios/preview-actualizacion` los lista con `aplica_indice=false` (visible en el preview). `POST /honorarios/aplicar-actualizacion` los saltea con `motivo: "tipo_honorario=producto"` si vienen en `client_ids`. Esto es por diseño: los honorarios producto se recalculan automáticamente al cambiar `ProductoReferencia.precio_vigente`.

### Convención de signos del flujo
- `saldo_cc > 0` → cliente tiene **a favor** (pagó más).
- `saldo_cc < 0` → cliente **debe**.
- `deuda = −saldo_cc` (positivo = debe; negativo = a favor).
- En la UI: deuda > 0 en **rojo**; deuda < 0 (a favor) en **verde**.

---

## 📸 Capturas

Carpeta: [docs/qa_fase3_gero_screenshots/](qa_fase3_gero_screenshots/)

| # | Pantalla | Descripción |
|---|---|---|
| 01 | [Retiros — listado](qa_fase3_gero_screenshots/01_retiros_listado.png) | 3 retiros (Marisol $80k transf, Manuel $60k efectivo, Rodrigo $300k transf) |
| 02 | [Retiros — modal nuevo](qa_fase3_gero_screenshots/02_retiros_modal_nuevo.png) | Form modal con socio, importe, forma de pago toggle, banco, fecha |
| 03 | [Flujo mensual con warning](qa_fase3_gero_screenshots/03_flujo_mensual_warning.png) | Abril 2026: panel amarillo "10 clientes con inconsistencia" + tabla con devengado $11.58M |
| 04 | [Flujo anual](qa_fase3_gero_screenshots/04_flujo_anual.png) | Año 2026 pivote: 12 columnas, fila TOTAL, columna sticky "Cliente" |
| 05 | [Actualizar — Step 1](qa_fase3_gero_screenshots/05_actualizar_step1.png) | Definir índice (steppers ±0.5, fuente IPC/Manual/Negociado, período) |
| 06 | [Actualizar — Step 2](qa_fase3_gero_screenshots/06_actualizar_step2.png) | Preview tabla con checkboxes, TOTAL dinámico, "1 cliente no aplicable" colapsable |
| 07 | [Actualizar — Step 3](qa_fase3_gero_screenshots/07_actualizar_step3.png) | Confirmación: 9 clientes, devengado proyectado $12.768.750, tabla anterior/nuevo |

---

## ✅ Checklist Fase 3 (FASE3_TAREAS_GERO.md)

- [x] G3-01: tabla `retiros_socios` creada (+ `movimientos_tesoreria` agregada por necesidad)
- [x] G3-02: `POST /retiros/` con triple impacto (RetiroSocio + MovimientoTesoreria + ControlBillete)
- [x] G3-03: `GET /retiros/` con filtros (profesional_id, period)
- [x] G3-04: `RetirosSocios.jsx` operativo en sidebar
- [x] G3-05: `GET /flujo-fondos/?periodo` calcula correctamente
- [x] G3-06: `GET /flujo-fondos/anual` pivote anual con totales por mes
- [x] G3-07: `FlujoDeFondos.jsx` con toggle, filtros y export CSV
- [x] G3-08: hook de consistencia + warning UI con detalle expandible
- [x] G3-09: modelo `IndiceActualizacion` + endpoint preview que persiste el índice
- [x] G3-10: `POST /honorarios/aplicar-actualizacion` granular con historial
- [x] G3-11: `ActualizarHonorarios.jsx` con 3 steps (wizard)
- [x] E3-02: 5 tests E2E pasando (75/75 en suite total)
- [x] E3-03: 7 capturas + este documento

---

## 📌 Pendiente (manual)

- **Demo grabada (Loom o similar)** de 5–10 min mostrando los 3 flujos: Retiros → Flujo de Fondos (mensual + anual + warning) → Actualizar Honorarios (3 steps). Las capturas en [qa_fase3_gero_screenshots/](qa_fase3_gero_screenshots/) sirven de guion.

---

*Documento Optimizar × Larrañaga · Cierre Fase 3 Gero · Mayo 2026*
