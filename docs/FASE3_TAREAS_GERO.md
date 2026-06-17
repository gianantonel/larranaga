
# Tareas Fase 3 — Gero
**Estudio Larrañaga · Optimizar · Mayo 2026**

> Branch base: `fase-3` (creada desde `dev`)
> Total estimado: **~40 hs · ~2 semanas efectivas**
> Plan completo: ver `docs/FASE3_TASKS.md`

---

## 🎯 Visión general

Tres requerimientos distribuidos en 3 sprints + QA final:

| Requerimiento | Sprint | Descripción |
|---|---|---|
| **R-12** Retiros de socios | Sprint 1 (Semana 7) | Registrar retiros con impacto automático en tesorería + billetes |
| **R-11** Flujo de fondos | Sprint 2 (Semana 8) | Tablero proyección vs real + verificación de consistencia con CC |
| **R-13** Actualización cuatrimestral | Sprint 3 (Semana 9) | Pantalla de validación granular para subir honorarios |
| **E3-02 / E3-03** | Sprint 4 (Semana 10) | QA + demo |

Mapa de dependencias: tus 3 requerimientos son **independientes entre sí** y de Fede. Podés arrancar G3-01 sin esperar a nadie.

---

## 🚀 Sprint 1 — Semana 7 · R-12 Retiros de socios

> **Objetivo:** registrar retiros de socios (Pablo, Manuel, Marisol) con impacto automático en tesorería y billetes.

### G3-01 · Modelo `RetiroSocio` + migración
- **Dificultad:** 🟢 Fácil — **Tiempo:** ~2 hs
- **Tabla:** `retiros_socios` con columnas:
  - `id, profesional_id` (FK a `profesionales` con `tipo='socio'`)
  - `fecha, importe`
  - `forma_pago` (efectivo / transferencia)
  - `banco_origen` (nullable, solo si transferencia)
  - `conciliado` (bool, default false)
  - `movimiento_tesoreria_id` (FK opcional)
  - `notas`
- **Archivos:** `backend/app/models.py`, `backend/app/main.py` (no requiere migración explícita — `create_all` autocrea)
- **Entregable:** Tabla creada visible en `/docs` schema y testeada al levantar la app.

---

### G3-02 · Endpoint `POST /retiros/`
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Lógica de impacto automático:**
  1. Validar que el profesional sea `tipo='socio'` → 400 si no
  2. Crear `RetiroSocio`
  3. Crear `MovimientoCuentaCorriente` tipo egreso (en CC interna del estudio)
  4. Crear `MovimientoTesoreria` tipo egreso categoría `retiro_socio`
  5. Si `forma_pago=efectivo` → restar de `ControlBillete` (validar stock, 422 si insuficiente)
  6. Devolver `{retiro_id, mov_tesoreria_id, saldo_actualizado}`
- **Archivos:** `backend/app/routers/retiros.py` (nuevo), `backend/app/schemas.py`
- **Entregable:** Retiro de Pablo en efectivo $500.000 → tesorería decrementada + billetes actualizados.

---

### G3-03 · Endpoints `GET /retiros/`
- **Dificultad:** 🟢 Fácil — **Tiempo:** ~2 hs
- **Endpoints:**
  - `GET /retiros/?profesional_id=&period=AAAA-MM` (listado filtrable)
  - `GET /retiros/{id}` (detalle)
- **Archivos:** `backend/app/routers/retiros.py`

---

### G3-04 · Frontend `RetirosSocios.jsx`
- **Dificultad:** 🟡 Media — **Tiempo:** ~5 hs
- **Layout:**
  - Tabla con histórico de retiros (fecha, socio, importe, forma de pago, banco)
  - Filtros por socio + período
  - Botón "Nuevo retiro" → modal con: socio (dropdown solo `tipo='socio'`), importe, forma_pago (toggle), banco_origen (si transferencia), notas
  - Si efectivo y stock insuficiente → mostrar error y bloquear
- **Archivos:**
  - `frontend/src/pages/RetirosSocios.jsx` (nuevo, **usar tema dark consistente** con `card`/`input-field`/`btn-primary`)
  - `frontend/src/utils/api.js` — agregar `crearRetiro()`, `getRetiros()`
  - `frontend/src/App.jsx` — ruta `/retiros`
  - `frontend/src/components/Layout/Sidebar.jsx` — ítem "Retiros Socios"
- **Entregable:** UI completa funcionando end-to-end.

---

## ⚙️ Sprint 2 — Semana 8 · R-11 Flujo de fondos

> **Objetivo:** tablero que reemplaza el Excel actual del estudio. Responde "cuánto debería haber cobrado · cuánto cobré · cuánto me deben" para cada cliente y mes.

### G3-05 · Servicio `flujo_fondos.py` + endpoint mensual
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Endpoint:** `GET /flujo-fondos/?periodo=AAAA-MM`
- **Output por cliente:**
  ```json
  {
    "cliente_id": 1,
    "cliente_nombre": "Gesualdo G.",
    "deuda_inicio": 0.0,
    "honorario_devengado": 3050000.0,
    "cobrado": 3050000.0,
    "deuda_fin": 0.0
  }
  ```
- Más fila TOTAL al final.
- **Cálculo:**
  - `deuda_inicio` = saldo CC al primer día del período
  - `honorario_devengado` = sum(`Honorario.importe` del período)
  - `cobrado` = sum(`Pago.importe` del período)
  - `deuda_fin` = saldo CC al último día del período
- **Archivos:** `backend/app/routers/flujo_fondos.py` (nuevo), `backend/app/services/flujo_fondos.py` (nuevo)

---

### G3-06 · Endpoint anual pivote
- **Dificultad:** 🟡 Media — **Tiempo:** ~3 hs
- **Endpoint:** `GET /flujo-fondos/anual?year=AAAA`
- **Output:** una fila por cliente con columnas Ene–Dic. Cada celda con `{hon_devengado, cobrado, deuda_fin}`.
- Fila TOTAL al pie.
- **Archivos:** `backend/app/routers/flujo_fondos.py`

---

### G3-07 · Frontend `FlujoDeFondos.jsx`
- **Dificultad:** 🔴 Alta — **Tiempo:** ~7 hs
- **Layout:**
  - Toggle Mensual / Anual
  - Tabla pivote con clientes como filas
  - Filtro por profesional responsable (dropdown)
  - Fila TOTAL al pie con totales agregados
  - Cell coloring: deuda > 0 en **rojo**, saldos a favor en **verde**
  - Botón "Exportar Excel" → genera .xlsx con la vista actual
- **Archivos:**
  - `frontend/src/pages/FlujoDeFondos.jsx` (nuevo, **tema dark**)
  - `frontend/src/utils/api.js` — `getFlujoFondosMensual(periodo)`, `getFlujoFondosAnual(year)`, `exportFlujoFondos(filtros)`
  - `App.jsx` — ruta `/flujo-fondos`
  - `Sidebar.jsx` — ítem "Flujo de Fondos"
- **Entregable:** Tablero completo replicando el Excel del estudio (ver `docs/Requerimiento_ADM_Tesoreria.md` § 2.3).

---

### G3-08 · Hook de consistencia CC ↔ Flujo
- **Dificultad:** 🟢 Fácil — **Tiempo:** ~2 hs
- **Endpoint:** `GET /flujo-fondos/verificar-consistencia?periodo=AAAA-MM`
- **Lógica:**
  - Para cada cliente: comparar saldo de CC contra "Deuda fin" del flujo de fondos
  - Si difieren más de **$0,10** → reportar inconsistencia con detalle
  - Output: `{periodo, ok: true/false, inconsistencias: [{cliente_id, cliente_nombre, saldo_cc, saldo_flujo, diferencia}]}`
- **Frontend:** mostrar warning amarillo arriba de la tabla en `FlujoDeFondos.jsx` si hay inconsistencias
- **Archivos:** `backend/app/services/flujo_fondos.py`

---

## 🔁 Sprint 3 — Semana 9 · R-13 Actualización cuatrimestral

> **Objetivo:** subir honorarios de 100+ clientes con un índice (IPC, manual o negociado) y validación granular cliente por cliente.

### G3-09 · Modelo `IndiceActualizacion` + endpoint preview
- **Dificultad:** 🟡 Media — **Tiempo:** ~4 hs
- **Tabla:** `indices_actualizacion`
  - `id, periodo` (AAAA-MM cuando se aplica)
  - `indice_pct` (float, ej: 12.5 para +12.5%)
  - `fuente` (`ipc` | `manual` | `negociado`)
  - `aplicado` (bool, default false)
  - `fecha_aplicacion` (nullable)
  - `notas`
- **Endpoint:** `POST /honorarios/preview-actualizacion`
  - Body: `{indice_pct, periodo_aplicacion, fuente}`
  - Devuelve tabla **sin persistir aún**: `[{cliente_id, cliente_nombre, importe_actual, importe_propuesto, delta_pct}]`
- **Archivos:** `backend/app/routers/honorarios.py`, `backend/app/models.py`

---

### G3-10 · Endpoint `POST /honorarios/aplicar-actualizacion`
- **Dificultad:** 🟡 Media — **Tiempo:** ~3 hs
- **Body:** `{indice_id, client_ids: [1, 2, 3, ...], periodo_aplicacion}`
- **Lógica:**
  - Para cada `client_id` confirmado: actualizar el `importe_honorario` o el `cantidad_unidades` (según tipo) del cliente
  - Persistir registro en historial (opcional: tabla `historial_actualizaciones_honorario` con cliente, importe_anterior, importe_nuevo, fecha)
  - Marcar `IndiceActualizacion.aplicado=true`
- **Archivos:** `backend/app/routers/honorarios.py`

---

### G3-11 · Frontend `ActualizarHonorarios.jsx`
- **Dificultad:** 🟡 Media — **Tiempo:** ~5 hs
- **Layout en 3 steps:**
  1. **Step 1** — input índice (% con stepper) + dropdown fuente (IPC/manual/negociado) + selector período de aplicación + botón "Calcular preview"
  2. **Step 2** — tabla con columnas: cliente, importe actual, importe propuesto, Δ%, **checkbox** por fila. Toggle "Seleccionar todos". Botón "Aplicar a seleccionados (N)".
  3. **Step 3** — confirmación con resumen: cuántos se aplicaron, importe total devengado proyectado para el próximo mes
- **Archivos:**
  - `frontend/src/pages/ActualizarHonorarios.jsx` (nuevo, **tema dark**)
  - `App.jsx` — ruta `/actualizar-honorarios`
  - `Sidebar.jsx` — ítem "Actualizar Honorarios"

---

## 🧪 Sprint 4 — Semana 10 · QA

### E3-02 · Test E2E flujo cobro + retiro + cierre flujo de fondos
- **Tiempo:** ~3 hs
- **Escenario:**
  1. Registrar pago de Gesualdo de $3.050.000 en transferencia
  2. Registrar retiro de Pablo de $500.000 en efectivo
  3. Llamar a `/flujo-fondos/verificar-consistencia?periodo=AAAA-MM` → debe retornar `ok: true`
  4. Verificar que el flujo refleja correctamente el devengado/cobrado/saldo
- **Archivos:** `backend/tests/test_flujo_fondos_e2e.py`

---

### E3-03 · Demo manual + actualización del README rama
- **Tiempo:** ~3 hs (compartido con Fede)
- **Entregables:**
  - Capturas de cada pantalla nueva (Retiros, FlujoDeFondos, ActualizarHonorarios)
  - Sección en README `fase-3` describiendo qué se entrega
  - Demo grabada (Loom o similar) de 5–10 min mostrando los 3 flujos

---

## 📋 Checklist de cierre

- [ ] G3-01: tabla `retiros_socios` creada
- [ ] G3-02: `POST /retiros/` con 3 impactos (CC + tesorería + billetes)
- [ ] G3-03: `GET /retiros/` con filtros
- [ ] G3-04: `RetirosSocios.jsx` operativo en sidebar
- [ ] G3-05: `GET /flujo-fondos/?periodo` calcula correctamente
- [ ] G3-06: `GET /flujo-fondos/anual` pivote anual
- [ ] G3-07: `FlujoDeFondos.jsx` con toggle, filtros y export
- [ ] G3-08: hook consistencia funciona y se muestra en UI
- [ ] G3-09: preview de actualización con tabla
- [ ] G3-10: aplicación granular con checkboxes
- [ ] G3-11: `ActualizarHonorarios.jsx` con 3 steps
- [ ] E3-02: test E2E verde
- [ ] E3-03: demo + README

---

## 🎨 Convenciones del proyecto (recordatorio)

- **Tema dark** consistente: usar siempre `card`, `input-field`, `btn-primary`, `btn-secondary`, `table-header`, `table-row`, `modal-panel`, `badge-*` (definidos en `frontend/src/index.css`)
- **NO** usar `bg-white`, `text-gray-700`, `border-gray-200` (eso fue lo que rompió el QA en RegistrarCobro y Liquidaciones)
- Endpoints batch deben registrarse **antes** del individual en FastAPI
- Toda lógica con impacto múltiple va en `services/` y se llama desde el router (router thin, service thick)
- Tests con SQLite en memoria + `StaticPool` (ver `backend/tests/test_flujo_cobro.py` como referencia)

---

## 🔗 Referencias

- Plan completo Fase 3: `docs/FASE3_TASKS.md`
- Plan maestro: `docs/Plan_Maestro_Implementacion.md` § Fase 3
- Requerimientos ADM (con ejemplos de Gesualdo, Juan Pérez, etc.): `docs/Requerimiento_ADM_Tesoreria.md`
- Patrones de referencia ya implementados:
  - `backend/app/routers/pagos.py` (router con impacto múltiple)
  - `backend/app/services/billetes.py` + `services/liquidacion.py` (services)
  - `frontend/src/pages/RegistrarCobro.jsx` + `Liquidaciones.jsx` (UI dark theme)

---

*Documento Optimizar × Larrañaga · Tareas Gero Fase 3 · Mayo 2026*
