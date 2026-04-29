# Fase 2 — Pipeline IVA Completo + Tesorería
## Plan de Tareas por Sprint · Semanas 4–6

> **Devs:** Fede (IVA pipeline + infra) · Gero (ADM + honorarios)
> **Rama:** `fase-2`
> **Entregables clave:** Pipeline IVA punta a punta (BUTALO SRL Feb 2026) + `registrar_cobro()` con impacto automático en todos los módulos ADM

---

## ⚠️ Cuello de botella crítico a vigilar

El **mayor riesgo** de la fase está en Gero con R-08. Si se traba, arrastra R-14.

**Estrategia de mitigación:** Gero hace primero el *esqueleto* de la API de R-08 (contratos de entrada/salida definidos, datos mockeados) para que Fede pueda avanzar en paralelo con R-09/R-10 sin esperar el comportamiento final.

---

## 🚀 Sprint 1 — Semana 4: Desbloqueo y Flujos Paralelos

**Objetivo:** Arrancar con las bases que desbloquean al resto. Al final de esta semana, Gero tiene `registrar_cobro()` funcional y Fede tiene la posición IVA calculada.

---

### Gero — R-08: Tesorería · Registro de Pagos

**Por qué primero:** Gero no puede arrancar R-14 hasta tener el core de `registrar_cobro()`. Esta es la pieza de mayor impacto en ADM — conecta CC cliente + tesorería + liquidación profesional.

#### G-01 · Modelo `Pago` y migración SQLite
- **Dificultad:** 🟢 Muy fácil
- **Tiempo:** ~2 hs
- **Descripción:** Verificar que el modelo `Pago` en `models.py` tiene todos los campos necesarios: `cliente_id, honorario_id, importe, forma_pago (efectivo/transferencia), profesional_destinatario_id, banco_destino, fuente_pago, fecha`. Agregar en `_migrate_sqlite()` si falta alguna columna.
- **Archivos:** `backend/app/models.py`, `backend/app/main.py`
- **Entregable:** `Pago` existe en DB con todos los campos. `_migrate_sqlite()` lo cubre.

#### G-02 · Endpoint `POST /pagos/`
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~4 hs
- **Descripción:** Crear `backend/app/routers/pagos.py`. El endpoint registra el pago y llama al servicio de cuentas corrientes para generar el movimiento Haber automáticamente. Responde con `pago_id` + lista de impactos ejecutados.
- **Archivos:** `backend/app/routers/pagos.py` (nuevo), `backend/app/routers/cuentas_corrientes.py`
- **Entregable:** `POST /pagos/` funciona. Registrar un pago genera un movimiento en CC del cliente.

#### G-03 · Endpoint `GET /pagos/?cliente_id=&periodo=`
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~2 hs
- **Descripción:** Listar pagos por cliente y/o período. Necesario para que el frontend muestre el historial y para que la liquidación calcule adelantos del mes.
- **Archivos:** `backend/app/routers/pagos.py`
- **Entregable:** `GET /pagos/` filtra por `cliente_id` y `periodo`.

#### G-04 · Registrar router en `main.py`
- **Dificultad:** 🟢 Muy fácil
- **Tiempo:** ~30 min
- **Descripción:** Agregar `from .routers import pagos` y `app.include_router(pagos.router)` en `main.py`.
- **Archivos:** `backend/app/main.py`
- **Entregable:** El router aparece en `/docs`.

---

### Fede — R-06: Conciliación IVA · Posición Mensual

**Por qué en paralelo:** Fede trabaja completamente aislado en el módulo IVA. Solo depende de que las tablas de comprobantes (R-01/R-02 Fase 1) ya existan.

#### F-01 · Endpoint `GET /iva/posicion?periodo=AAAA-MM`
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~3 hs
- **Descripción:** Calcular posición IVA del mes desde los comprobantes ya almacenados. Suma IVA de ventas (débito fiscal) y IVA de compras (crédito fiscal). Devuelve: `{ debito, credito, posicion, periodo }`. Sin SDK AFIP por ahora — usa datos de la DB local.
- **Archivos:** `backend/app/routers/iva.py`
- **Entregable:** `GET /iva/posicion?periodo=2026-02` devuelve la posición de febrero.

#### F-02 · Frontend: página `PosicionIVA.jsx`
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~3 hs
- **Descripción:** Página React con selector de período (mes/año) y 3 tarjetas: IVA Débito, IVA Crédito, Posición del Mes. Color verde si saldo a favor, rojo si deuda. Consume F-01.
- **Archivos:** `frontend/src/pages/PosicionIVA.jsx` (nuevo)
- **Entregable:** Pantalla funcional con datos reales del período seleccionado.

#### F-03 · Agregar ruta en `App.jsx` y link en `Sidebar.jsx`
- **Dificultad:** 🟢 Muy fácil
- **Tiempo:** ~30 min
- **Descripción:** Agregar la ruta `/posicion-iva` en `App.jsx` y el ítem "Posición IVA" en el sidebar bajo la sección IVA.
- **Archivos:** `frontend/src/App.jsx`, `frontend/src/components/Layout/Sidebar.jsx`
- **Entregable:** Navegación funcionando.

---

## ⚙️ Sprint 2 — Semana 5: Conexión ADM + Cierre Pipeline IVA

**Objetivo:** Con R-08 encaminado, Gero ramifica hacia R-14. Fede cierra el pipeline IVA con imputación por CUIT y generación HWCRARCA.

---

### Gero — R-14: Control de Billetes / Caja Efectivo

**Por qué ahora:** R-08 ya tiene `registrar_cobro()` funcional. R-14 se "cuelga" de esa función para añadir desglose de denominaciones cuando el pago es en efectivo.

#### G-05 · Modelo `ControlBilletes` + migración
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~2 hs
- **Descripción:** Tabla `control_billetes` con campos `denominacion (int), cantidad (int), actualizado_en`. Denominaciones AR válidas: 1000, 2000, 5000, 10000, 20000, 50000, 100000. Agregar en `_migrate_sqlite()`.
- **Archivos:** `backend/app/models.py`, `backend/app/main.py`
- **Entregable:** Tabla en DB con seed de denominaciones en cero.

#### G-06 · Endpoints CRUD billetes
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~3 hs
- **Descripción:** `GET /billetes/` — saldo actual por denominación + total efectivo en caja. `POST /billetes/movimiento` — suma o resta `{denominacion, cantidad, tipo: ingreso|egreso}`.
- **Archivos:** `backend/app/routers/billetes.py` (nuevo)
- **Entregable:** Endpoints funcionando, registrables desde `/docs`.

#### G-07 · Integración: cobro efectivo → actualiza billetes
- **Dificultad:** 🟡 Media
- **Tiempo:** ~4 hs
- **Descripción:** Modificar `POST /pagos/` para que cuando `forma_pago = efectivo`, el body acepte `billetes: {denominacion: cantidad}` y llame internamente al servicio de billetes. El impacto debe ser atómico: si falla la actualización de billetes, el pago no se registra.
- **Archivos:** `backend/app/routers/pagos.py`, `backend/app/routers/billetes.py`
- **Entregable:** Un pago en efectivo con `{20000: 3, 10000: 1}` actualiza el stock de billetes correctamente.

#### G-08 · Frontend: formulario Registrar Cobro
- **Dificultad:** 🟡 Media
- **Tiempo:** ~5 hs
- **Descripción:** Página React `RegistrarCobro.jsx`. Campos: cliente (select con search), honorario asociado (select filtrado por cliente), importe, fecha, toggle efectivo/transferencia. Si efectivo → aparece grid de denominaciones para ingresar cantidad de cada billete. Si transferencia → campos banco destino, profesional destinatario. Botón Registrar llama a `POST /pagos/`.
- **Archivos:** `frontend/src/pages/RegistrarCobro.jsx` (nuevo)
- **Entregable:** Formulario completo funcionando end-to-end.

---

### Gero — R-04 (extender): Liquidación con Adelantos Reales

**Dependencia:** G-03 (listado de pagos) completado.

#### G-09 · Backend: preview liquidación mensual
- **Dificultad:** 🟡 Media
- **Tiempo:** ~4 hs
- **Descripción:** Extender el endpoint de liquidaciones para que descuente los pagos registrados en `POST /pagos/` como adelantos. `GET /liquidaciones/{profesional_id}/preview?periodo=AAAAMM` devuelve: `honorarios_brutos, adelantos_cobrados, saldo_anterior, reintegros, total_a_cobrar`.
- **Archivos:** `backend/app/routers/honorarios.py`
- **Entregable:** El preview descuenta correctamente los cobros registrados en el mes.

#### G-10 · Frontend: pantalla Liquidación del Mes
- **Dificultad:** 🟡 Media
- **Tiempo:** ~5 hs
- **Descripción:** Página `Liquidaciones.jsx` (reemplaza la eliminada en el merge con Gero). Tabla por profesional: honorarios brutos, adelantos ya cobrados (con detalle desplegable), saldo anterior, reintegros, **total a cobrar** en negrita. Botón "Cerrar Período" que llama a endpoint de cierre y bloquea edición.
- **Archivos:** `frontend/src/pages/Liquidaciones.jsx` (nuevo)
- **Entregable:** El cierre de período funciona y bloquea modificaciones.

---

### Fede — R-09: Imputación Contable por CUIT

**Por qué ahora:** Prerequisito para R-10 (HWCRARCA necesita la cuenta contable de cada proveedor).

#### F-04 · Modelo `MaestroProveedores` + migración
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~2 hs
- **Descripción:** Tabla `maestro_proveedores` con campos `cuit (str, unique), razon_social, cuenta_contable, fuente (manual/padron/ia), activo`. Esta tabla es la caché local del padrón ARCA.
- **Archivos:** `backend/app/models.py`, `backend/app/main.py`
- **Entregable:** Tabla en DB, migración automática cubierta.

#### F-05 · Endpoint `GET /imputacion/cuit/{cuit}`
- **Dificultad:** 🟡 Media
- **Tiempo:** ~4 hs
- **Descripción:** Pipeline de 3 niveles: (1) Busca en `maestro_proveedores` local. (2) Si no encuentra, consulta padrón ARCA (ws_sr_padron_a4) y guarda el resultado. (3) Si ARCA no devuelve cuenta, retorna `cuenta_contable: null` para asignación manual. Responde con `{cuit, razon_social, cuenta_contable, fuente}`.
- **Archivos:** `backend/app/routers/imputacion.py` (nuevo), `backend/app/services/padron_arca.py` (nuevo)
- **Entregable:** El endpoint resuelve CUITs conocidos desde la caché y desconocidos desde el padrón ARCA.

#### F-06 · Frontend: pantalla Maestro de Proveedores
- **Dificultad:** 🟡 Media
- **Tiempo:** ~4 hs
- **Descripción:** Tabla con columnas CUIT, Razón Social, Cuenta Contable, Fuente (badge: manual/padrón/IA), Acciones. Botón "Buscar en ARCA" por fila que llama a F-05. Campo editable de cuenta contable para override manual. Buscador por CUIT o nombre.
- **Archivos:** `frontend/src/pages/MaestroProveedores.jsx` (nuevo)
- **Entregable:** El equipo puede gestionar y auditar las imputaciones contables.

---

### Fede — R-10: Generación HWCRARCA

**Dependencia:** F-05 (imputación por CUIT) completado.

#### F-07 · Backend: servicio `hwcrarca_builder.py`
- **Dificultad:** 🔴 Alta
- **Tiempo:** ~6 hs
- **Descripción:** Servicio Python que toma el DataFrame procesado (post R-01/R-02) y genera el `.xlsx` con formato Holistor usando `openpyxl`. Columnas obligatorias: Fecha, Tipo Cbte, Punto Venta, Nro, CUIT, Razón Social, Cuenta Contable, Neto, IVA, Otros Tributos, Total. Validación **Debe = Haber** antes de escribir — si no cuadra, lanza excepción con detalle de la diferencia.
- **Archivos:** `larranaga-accounting-agent/src/transformaciones/hwcrarca_builder.py` (nuevo)
- **Entregable:** `.xlsx` generado válido para importar en Holistor/Onvio.

#### F-08 · Endpoint `POST /herramientas/generar-hwcrarca`
- **Dificultad:** 🟡 Media
- **Tiempo:** ~3 hs
- **Descripción:** Recibe el archivo ARCA procesado (o el `session_id` del procesamiento anterior), llama a F-07, y devuelve el `.xlsx` como descarga + stats: `{filas, debe_total, haber_total, cuadre_ok}`.
- **Archivos:** `backend/app/routers/herramientas.py`
- **Entregable:** El endpoint descarga el HWCRARCA correctamente.

#### F-09 · Frontend: paso "Generar HWCRARCA" en Herramientas
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~2 hs
- **Descripción:** Agregar paso 3 en la página `Herramientas.jsx` (después de limpiar y dividir alícuotas). Muestra stats de cuadre (Debe/Haber en verde si OK, rojo si difieren). Botón de descarga `.xlsx`.
- **Archivos:** `frontend/src/pages/Herramientas.jsx`
- **Entregable:** El pipeline IVA completo es operable desde una sola pantalla.

---

## 🧪 Sprint 3 — Semana 6: Integración, QA y Entregables

**Objetivo:** No se programan features nuevas. Se conecta todo el cableado, se valida con datos reales y se documenta.

---

### Fede — Hook de validación Debe = Haber

#### F-10 · Hook pre-exportación en `hwcrarca_builder.py`
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~2 hs
- **Descripción:** Asegurar que el hook de validación está implementado como función separada `validar_cuadre(df) -> ValidationResult`. Si `abs(debe_total - haber_total) > 0.01` → lanzar excepción con detalle fila por fila de dónde rompe el cuadre. El endpoint debe capturar esta excepción y devolver HTTP 422 con el detalle.
- **Archivos:** `larranaga-accounting-agent/src/transformaciones/hwcrarca_builder.py`
- **Entregable:** El HWCRARCA nunca se descarga si no cuadra. El error es legible para el operador.

---

### Ambos — Tests de Integración End-to-End

#### E-01 · [Fede] Test pipeline IVA completo — BUTALO SRL Feb 2026
- **Dificultad:** 🟡 Media
- **Tiempo:** ~4 hs
- **Descripción:** Test de integración que corre el pipeline completo: archivo ARCA crudo → R-01 (limpieza) → R-02 (división alícuotas) → R-09 (imputación CUIT) → R-10 (HWCRARCA). Verificar: (a) filas de entrada vs salida, (b) cuadre Debe=Haber, (c) que el `.xlsx` tiene todas las columnas requeridas por Holistor.
- **Archivos:** `larranaga-accounting-agent/tests/test_pipeline_completo.py`
- **Fixture:** `tests/fixtures/butalo_feb2026.xlsx`
- **Entregable:** Test verde en CI. El HWCRARCA de BUTALO pasa validación completa.

#### E-02 · [Gero] Test flujo ADM — cobro con impacto en 4 módulos
- **Dificultad:** 🟡 Media
- **Tiempo:** ~4 hs
- **Descripción:** Test de integración que simula el cobro de honorario en efectivo: `POST /pagos/` con billetes. Verificar los 4 impactos: (a) CC cliente tiene nuevo movimiento Haber, (b) movimiento de tesorería creado, (c) preview liquidación descuenta el adelanto, (d) control billetes actualizado con denominaciones correctas.
- **Archivos:** `backend/tests/test_flujo_cobro.py`
- **Entregable:** Test verde con los 4 assertions. Si alguno falla el pago se revierte (rollback).

#### E-03 · [Ambos] Demo manual con datos reales
- **Dificultad:** 🟢 Fácil
- **Tiempo:** ~2 hs
- **Descripción:** Demo funcional con el equipo: (1) procesar libro IVA BUTALO Feb 2026 punta a punta desde la pantalla Herramientas y descargar el HWCRARCA. (2) Registrar un cobro de honorario de Juan Pérez desde la pantalla Registrar Cobro y verificar que el saldo CC se actualiza en tiempo real.
- **Entregable:** Capturas de pantalla / video corto del flujo completo para la reunión de cierre de fase.

---

## 📊 Resumen de carga total

| Dev | Tareas | Tiempo estimado |
|-----|--------|-----------------|
| **Gero** | G-01 → G-10 + E-02 + E-03 | ~40 hs (~2 semanas efectivas) |
| **Fede** | F-01 → F-10 + E-01 + E-03 | ~40 hs (~2 semanas efectivas) |

---

## 🗺️ Mapa de dependencias

```
SPRINT 1 (Semana 4)
  Gero:  G-01 → G-02 → G-03 → G-04
  Fede:  F-01 → F-02 → F-03
  [Trabajan en paralelo, sin bloqueos entre sí]

SPRINT 2 (Semana 5)
  Gero:  G-05 → G-06 → G-07 → G-08
         G-03 → G-09 → G-10
  Fede:  F-04 → F-05 → F-06
         F-05 → F-07 → F-08 → F-09
  [G-07 depende de G-02 completado. F-07 depende de F-05 completado.]

SPRINT 3 (Semana 6)
  Fede:  F-07 → F-10 → E-01
  Gero:  G-07 → E-02
  Todos: E-03
```

---

## ✅ Checklist de cierre de Fase 2

- [ ] `GET /iva/posicion` calcula posición IVA del mes correctamente
- [ ] `POST /pagos/` registra cobro con impacto en CC + tesorería + liquidación + billetes (si efectivo)
- [ ] `GET /imputacion/cuit/{cuit}` resuelve en 3 niveles (caché → ARCA → manual)
- [ ] HWCRARCA.xlsx generado desde Herramientas, pasa validación Debe=Haber
- [ ] Liquidación mensual descuenta adelantos cobrados en el mes
- [ ] Control de billetes actualizado en tiempo real por cobros en efectivo
- [ ] Test pipeline IVA completo verde (BUTALO Feb 2026)
- [ ] Test flujo cobro verde (4 impactos verificados)
- [ ] Demo end-to-end grabada / documentada
- [ ] Rama `fase-2` actualizada y pusheada a origin

---

*Documento Optimizar × Larrañaga · Fase 2 · Abril 2026*
