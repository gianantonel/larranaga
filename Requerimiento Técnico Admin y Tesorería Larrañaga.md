# Requerimiento Técnico — Sistema de Administración y Tesorería

**Cliente:** Estudio Larrañaga y Asociados — Santa Rosa, La Pampa
**Versión:** 2.0 — Abril 2026
**Contacto:** Marisol Borrego — marisol.larranagayasociados@gmail.com

---

## 1. Contexto y situación actual

El estudio gestiona hoy toda la administración interna con varios archivos Excel **desvinculados**. Cada operación (sobre todo cobro de honorarios y registro de gastos) exige tocar **4 o más archivos en forma manual**, lo que genera duplicación, errores y demoras.

Archivos Excel actuales:

1. **Cuentas corrientes de clientes** — libro con solapas alfabéticas (A, B, C…), una por cliente. Registra honorarios, pagos y saldo actualizado.
2. **Caja / Tesorería** — movimientos de fondos: ingresos por cobro y egresos por gasto.
3. **Liquidación de honorarios por profesional** — lo cobrado por cada socio/profesional (Rodrigo, Silvana, Stefi, Marisol, Mariana, etc.).
4. **Flujo de fondos estimado** — proyección y seguimiento de ingresos y egresos.
5. **Control de billetes** — seguimiento del efectivo disponible por denominación.

Un único cobro de honorarios genera **3 a 5 registros manuales independientes**. Los extractos bancarios (Banco Pampa, Banco Santander, Mercado Pago) se concilian manualmente.

---

## 2. Estructuras de datos actuales (con ejemplos reales)

### 2.1 Cuenta corriente de cliente

Formato base (columnas Debe / Haber / Saldo).

**Ejemplo — GESUALDO GUILLERMO:**

| Fecha | Concepto | Debe | Haber | Saldo |
|-------|----------|------|-------|-------|
| 30/06/2025 | HONORARIOS 06/2025 | $3.050.000 | — | $3.050.000 |
| 28/07/2025 | Transferencia de IDEAR a Marisol | — | $1.000.000 | $2.050.000 |
| 28/07/2025 | Transferencia de SGI a Stefania Vicente | — | $1.250.000 | $800.000 |
| 28/07/2025 | Transferencia de Guillermo Gesualdo a Mariana | — | $800.000 | $0 |

Un mismo honorario puede cancelarse con **múltiples transferencias de distintas fuentes** (empresas del cliente, el propio cliente) y cada una puede ir dirigida a **distintos profesionales** del estudio. Esto es central para la conciliación bancaria.

**Ejemplo — JUAN PÉREZ (honorario fijo mensual):**

| Fecha | Concepto | Debe | Haber | Saldo |
|-------|----------|------|-------|-------|
| 17/10/2025 | HONORARIOS 09/2025 | $220.000 | $220.000 | $0 |
| 10/11/2025 | HONORARIOS 10/2025 | $220.000 | $220.000 | $0 |
| 09/12/2025 | HONORARIOS 11/2025 | $220.000 | $220.000 | $0 |
| 31/12/2025 | HONORARIOS 12/2025 | $220.000 | $220.000 | $0 |
| 31/01/2026 | HONORARIOS 01/2026 | $254.300 | $254.300 | $0 |
| 12/03/2026 | HONORARIOS 02/2026 | $254.300 | $255.000 | -$700 |
|  | **Saldo actual** |  |  | **-$700 (a favor)** |

Cuando el pago supera el honorario, el saldo queda **negativo (a favor del cliente)** y se descuenta del próximo período.

### 2.2 Liquidación mensual de profesionales

**Ejemplo — Stefi, marzo y abril 2026:**

| Concepto | Marzo 2026 | Abril 2026 |
|----------|-----------|-----------|
| Honorarios del mes | $1.950.000 | $1.950.000 |
| **Total Honorarios** | **$1.950.000** | **$1.950.000** |
| Adelantos recibidos: |  |  |
| &nbsp;&nbsp;IDEAR | $1.445.000 | $1.445.000 |
| &nbsp;&nbsp;CAZENAVE VITAL | $540.000 | $0 |
| **Total Adelantos** | **$1.985.000** | **$1.445.000** |
| Saldo mes anterior | $379,41 | $177,56 |
| **Total a Cobrar Honorarios** | **-$35.379,41** | **$504.822,44** |
| Reintegro de Gastos: |  |  |
| &nbsp;&nbsp;Monotributo | $56.501,85 | $56.501,85 |
| &nbsp;&nbsp;Ingresos Brutos | $29.700,00 | $0 |
| &nbsp;&nbsp;Gastos Dep. Cheques | $0 | $0 |
| **Total Reintegro de Gastos** | **$86.201,85** | **$56.501,85** |
| **TOTAL A COBRAR** | **$50.822,44** | **$561.324,29** |
| Transferencia | $0 | $0 |
| Efectivo | $51.000 | $0 |
| Saldo a Favor próximo mes | -$177,56 | $561.324,29 |

> **🔑 Vínculo clave a preservar:**
> Los "Adelantos" de la liquidación profesional son las **mismas transferencias** que figuran en la cuenta corriente del cliente como "Haber". El sistema debe imputar automáticamente cada pago recibido a: (a) la cuenta corriente del cliente, y (b) la liquidación del profesional destinatario.

### 2.3 Flujo de ingresos del estudio (tablero)

Tablero de control. Debe responder en cualquier momento:

1. ¿Cuánto debería haber cobrado este mes?
2. ¿Cuánto cobré efectivamente?
3. ¿Cuánto me deben?

Una fila por cliente con apertura mensual. Para cada mes: honorario devengado, cobrado, deuda al cierre. La columna "A cargo de" (profesional responsable) es dato secundario, solo para filtrar.

| Cliente | Deuda 31/12/25 | Hon. Enero | Cobrado Feb. | Deuda Ene. | Hon. Feb. | Cobrado Mar. | Deuda Feb. | Hon. Mar. |
|---------|----------------|------------|--------------|------------|-----------|--------------|------------|-----------|
| GESUALDO G. | $0 | $3.050.000 | $3.050.000 | $0 | $3.050.000 | $3.050.000 | $0 | $3.050.000 |
| JUAN PÉREZ | $0 | $254.300 | $254.300 | $0 | $254.300 | $255.000 | -$700 | $254.300 |
| (otros) | ... | ... | ... | ... | ... | ... | ... | ... |
| **TOTAL ESTUDIO** | ... | ... | ... | ... | ... | ... | ... | ... |

La fila **TOTAL** responde las tres preguntas. Se calcula **automáticamente** a partir de las cuentas corrientes, sin carga adicional.

> **⚠ Regla de consistencia crítica:**
> La columna "Deuda [mes]" debe coincidir **exactamente** con el saldo de la cuenta corriente de cada cliente. Si Juan Pérez figura con Deuda Feb = -$700, su CC debe mostrar ese mismo saldo. El sistema debe garantizar esta consistencia en tiempo real y alertar cualquier diferencia.

### 2.4 Tipos de honorarios y actualización cuatrimestral

#### 2.4.1 Honorario en importe fijo (en pesos)
Importe mensual fijo en pesos. Ej: Juan Pérez = $254.300/mes desde ene-2026, hasta la próxima actualización.

#### 2.4.2 Honorario en valor producto
Expresado en unidades de un producto de referencia (bolsas de cemento, kilos de carne, litros de combustible, etc.) y convertido a pesos al momento de facturar, con el precio vigente del producto. Permite actualización automática con la inflación del rubro.

**Ejemplo — constructora:**

| Período | Precio bolsa cemento | Unidades | Honorario |
|---------|---------------------|----------|-----------|
| Marzo 2026 | $4.200 | 50 | $210.000 |
| Abril 2026 | $4.600 | 50 | $230.000 *(actualización automática)* |

El sistema debe mantener una **tabla de productos de referencia** con precio actualizable, y calcular el honorario en pesos al generar cada período.

#### 2.4.3 Actualización cuatrimestral por índice

Independiente del tipo de honorario, cada cuatrimestre se aplica un índice (IPC, acordado internamente, etc.).

El sistema debe:
- Registrar el índice cuatrimestral aplicable (% de aumento).
- Calcular el nuevo importe para cada cliente según su tipo.
- **No aplicar en forma automática y masiva.** Mostrar pantalla de validación con listado + honorario actual + honorario propuesto + casilla de confirmación individual.
- Permitir **modificar el importe propuesto** por cliente antes de confirmar (negociaciones puntuales).
- Aplicar los cambios a los clientes seleccionados con vigencia a partir del mes indicado.
- Guardar **historial de actualizaciones**: fecha, índice, clientes actualizados, importes anteriores y nuevos.

**Pantalla de validación (ejemplo):**

| Cliente | Tipo hon. | Honorario actual | Honorario propuesto | Δ% | Confirmar |
|---------|-----------|------------------|---------------------|-----|-----------|
| Juan Pérez | Importe fijo | $254.300 | $279.730 | +10% | ☐ |
| Constructora X | Valor producto | 50 bolsas | 50 bolsas | — | ☐ |
| Cliente Z | Importe fijo | $180.000 | $198.000 | +10% | ☐ |

> Los clientes con honorario en "valor producto" no cambian por el índice cuatrimestral (ya se actualizan con el precio del producto), pero pueden incluirse en la pantalla para revisión manual.

---

## 3. Objetivo del sistema

> **Principio rector:** *"Carga única — impacto automático en todos los módulos"*

Cada operación ingresada **una sola vez** debe reflejarse automáticamente en:
- Cuenta corriente del cliente
- Tesorería
- Liquidación del profesional
- Flujo de fondos
- Control bancario

El sistema también debe **importar extractos bancarios** y **conciliarlos** contra los movimientos registrados, informando diferencias.

---

## 4. Módulos requeridos

### 4.1 Cuentas corrientes de clientes

**Datos por cliente:**
- Nombre / razón social, CUIT.
- Profesional del estudio a cargo.
- Tipo de honorario: **importe fijo en pesos** o **valor producto** (producto de referencia + cantidad de unidades).
- Historial de honorarios facturados por período (mes/año, importe calculado).
- Pagos recibidos: fecha, período al que imputa, importe, forma de pago.
- Saldo deudor en tiempo real.
- Detalle de cada pago: efectivo o transferencia; si fue transferencia, de qué empresa/persona y a qué profesional.

**Funcional:**
- Búsqueda rápida (nombre, CUIT, apellido).
- Estado de cuenta completo con historial.
- **Alerta automática** de saldos vencidos (N días desde emisión).
- **Pagos parciales**: múltiples líneas para un mismo período (caso Gesualdo).
- El registro de un pago dispara automáticamente tesorería + liquidación del profesional + flujo de fondos.
- Saldo de CC siempre sincronizado con la planilla de seguimiento (sección 2.3).
- Cálculo automático del honorario del mes según tipo (fijo o valor producto × precio vigente).
- Módulo de actualización cuatrimestral con validación individual (sección 2.4.3).

### 4.2 Tesorería

Registro centralizado de **todos** los movimientos de fondos.

**Ingresos por cobro (automáticos desde CC):**
- Fecha de acreditación.
- Cliente, período.
- Importe.
- Forma: efectivo (con detalle de billetes) o transferencia (banco, cuenta, profesional destinatario).

**Egresos / gastos (manual):**
- Fecha, concepto, importe, forma de pago.
- Categoría (servicios, impuestos, sueldos, otros).
- Si fue transferencia: banco y cuenta origen.

**Control de billetes (efectivo):**
Seguimiento del efectivo por denominación, actualizado automáticamente con cada movimiento en efectivo.

| Denominación | Cantidad | Subtotal | % del total |
|--------------|----------|----------|-------------|
| $20.000 | 120 | $2.400.000 | 15% |
| $10.000 | 80 | $800.000 | 5% |
| $2.000 | 200 | $400.000 | 5% |
| $1.000 | 150 | $150.000 | 2% |
| **TOTAL** |  | **$3.750.000** | 100% |

- Cobros en efectivo: aumentan las denominaciones recibidas.
- Gastos en efectivo: reducen las denominaciones usadas.
- Permitir ingresar el **cambio / vuelto** por denominación.
- El total de efectivo en caja debe **cuadrar en todo momento** con el saldo de efectivo en el flujo de fondos.

### 4.3 Conciliación bancaria (módulo nuevo, crítico)

Entidades: **Banco Pampa**, **Banco Santander**, **Mercado Pago**.

#### 4.3.1 Importación de extractos

- Banco Pampa: formato exportable del homebanking (.xlsx / .xls). A confirmar.
- Banco Santander: ídem.
- Mercado Pago: panel de actividad, .xlsx / .csv.
- El sistema mapea columnas de cada banco al modelo interno: fecha, descripción, importe ingreso, importe egreso, saldo.

#### 4.3.2 Lógica de conciliación automática

| Tipo de movimiento bancario | Buscar coincidencia en... | Criterio de match |
|-----------------------------|---------------------------|-------------------|
| Transferencia entrante (crédito) | Pagos registrados en CC (columna Haber) | Fecha ± 1 día + importe exacto + banco/cuenta destino |
| Transferencia saliente (débito) | Gastos registrados en tesorería | Fecha ± 1 día + importe exacto |
| Débito automático (impuestos, servicios) | Gastos registrados o pendientes | Fecha + importe + descripción |
| Honorario de socio retirado (débito) | Retiros de honorarios (módulo 4.6) | Fecha + importe + profesional |
| Comisiones / mantenimiento bancario | Gastos bancarios en tesorería | Fecha + importe + banco |

**Ejemplo — Banco Pampa, Feb 2026:**
- Extracto: `28/02/2026 TRANSF. DE SGI S.R.L. $1.250.000` (crédito).
- Sistema busca en CC: `28/07/2025 Transferencia de SGI a Stefania Vicente $1.250.000` → **match**.
- Extracto: `15/02/2026 DÉBITO AUTOMÁTICO $45.000`.
- Sistema busca en tesorería: sin registro → **bancario sin registrar**.

#### 4.3.3 Resultado — tres categorías

1. **Conciliados** — match OK. Sin acción.
2. **Bancario sin registrar** — movimiento en extracto sin contrapartida. El operador debe clasificar: ¿cobro? ¿gasto? ¿transferencia entre cuentas propias?
3. **Registrado sin movimiento bancario** — registro sin contrapartida en extracto. Puede ser cobro en efectivo (OK), error de carga, o cheque no depositado.

#### 4.3.4 Informe de conciliación

- Resumen por banco: total de movimientos, conciliados, pendientes.
- Detalle de no conciliados con campo para clasificación.
- Registrar directamente desde el informe el movimiento faltante (crear gasto/ingreso desde extracto).
- Exportar a Excel o PDF.

### 4.4 Liquidación de honorarios de profesionales

Profesionales actuales: **Rodrigo, Silvana, Stefi, Marisol, Mariana** (+ futuros).

**Componentes de la liquidación mensual:**

| Concepto | Descripción / origen |
|----------|---------------------|
| Total Honorarios | Suma asignada al profesional en el período. Se fija al inicio de cada mes. |
| Adelantos recibidos | Transferencias de clientes destinadas al profesional (desde CC). Acumula automáticamente. |
| Saldo mes anterior | Arrastre del saldo a favor (o deuda) del mes anterior. |
| Total a cobrar honorarios | = Total Honorarios − Adelantos + Saldo anterior |
| Reintegro de Gastos | Gastos propios del profesional (Monotributo, IIBB, gastos bancarios, otros). Carga manual mensual. |
| Total a Cobrar | = Total a cobrar honorarios + Reintegro de gastos |
| Forma de cobro del saldo | Transferencia y/o efectivo. Impacta en tesorería al registrarse. |
| Saldo a Favor próximo mes | Remanente. Puede ser negativo si el profesional cobró de más. |

- Liquidación calculada **en tiempo real** durante el mes, sin esperar al cierre.
- **Alerta de sobreadelanto** si los adelantos superan los honorarios.
- **Cierre mensual**: fija el saldo y arrastra al siguiente mes.
- Historial completo por profesional.

### 4.5 Flujo de fondos

- Ingresos cobrados (honorarios): **automáticos** desde tesorería.
- Egresos: **automáticos** desde tesorería.
- Carga de **estimaciones futuras** (flujo proyectado).
- Comparativo por período: proyectado vs. real (ingresos, egresos, saldo).

**Flujo de fondos de socios — cálculo por socio/mes:**

| Campo | Fórmula / origen |
|-------|-----------------|
| Deuda inicio de mes | Saldo CC del socio al último día del mes anterior |
| (+) Honorarios del mes | Honorarios fijados para el socio en el período |
| (−) Percibido en el mes | Transferencias a favor del socio durante el mes |
| = Deuda fin de mes | Debe coincidir con saldo de CC al cierre |

> **⚠ Regla de consistencia:** "Deuda al [mes]" del flujo de socios = saldo CC del socio. El sistema debe validar en cada cierre y alertar diferencias.

### 4.6 Retiro de honorarios de socios

Socios: **Pablo Larrañaga, Manuel Larrañaga, Marisol Borrego**.

> Manuel y Marisol también cobran honorarios mensuales como el resto de los profesionales.

**Funcionamiento:**
- Registrar retiros: fecha, socio, importe, forma (transferencia / efectivo).
- Saldo acumulado: lo que el estudio adeuda al socio, o lo retirado en exceso.
- Historial consultable por socio y período, comparando contra lo devengado.

> **Nota al desarrollador:** la lógica del importe a retirar por socio (porcentaje, importe fijo, mixto) debe ser **configurable por el administrador**, para admitir distintas modalidades de distribución sin cambios de código.

### 4.7 Informes y estadísticas de gestión

| Informe | Descripción |
|---------|-------------|
| Estado de cuentas corrientes | Saldo de todos los clientes al día. Filtros: deuda vencida, rango de importe, período. |
| Antigüedad de deuda | Clientes con saldo pendiente agrupados por rango de días de mora. |
| Honorarios cobrados | Por período (mes/trimestre/año) y por profesional. |
| Liquidación mensual por profesional | Mes en curso y meses anteriores. |
| Retiros de socios | Por socio (Pablo, Manuel, Marisol), con saldo acumulado. |
| Flujo real vs. proyectado | Comparativo por período. |
| Informe de conciliación bancaria | Por banco y período. |
| Control de caja (billetes) | Saldo por denominación + historial. |
| Movimientos de tesorería | Filtros: tipo, forma de pago, período, cliente, profesional. |

---

## 5. Flujos operativos principales

### 5.1 Registro de un cobro de honorarios (reemplaza 4–5 pasos manuales)

1. El operador ingresa: cliente, período, importe, forma de pago.
2. Si **efectivo** → detalle de billetes → se actualiza control de caja.
3. Si **transferencia** → banco destino + profesional destinatario.
4. Se actualiza saldo de CC del cliente.
5. Se registra el ingreso en tesorería.
6. Si es transferencia a un profesional → imputa en su liquidación como adelanto.
7. Se actualiza el flujo de fondos.
8. El movimiento queda disponible para conciliación bancaria.
9. Todos los informes se actualizan en tiempo real.

### 5.2 Conciliación bancaria mensual

1. El operador descarga el extracto (Pampa, Santander o Mercado Pago).
2. Lo importa seleccionando el banco.
3. El sistema ejecuta la conciliación automática (sección 4.3.2).
4. Muestra resultado: conciliados / sin registrar / sin movimiento bancario.
5. El operador revisa los no conciliados: clasifica o marca "en revisión".
6. Se emite el informe de conciliación.

### 5.3 Cierre mensual de liquidación de profesionales

1. Al cierre, el sistema calcula la liquidación final de cada profesional.
2. Se presenta para revisión: honorarios, adelantos, reintegros, saldo.
3. El operador confirma o ajusta.
4. Se registra la forma de cobro del saldo (transferencia y/o efectivo).
5. El pago impacta en tesorería y flujo de fondos.
6. Saldo remanente → arrastra al mes siguiente.

---

## 6. Consideraciones técnicas y funcionales

- **Multiusuario** (al menos 4 personas del equipo).
- **Perfiles de acceso**:
  - Operador de caja (carga de movimientos).
  - Administrador (configuración, cierre de períodos).
  - Consulta (solo lectura de informes).
- Acceso desde cualquier dispositivo del estudio (web preferible, o escritorio en red local).
- Exportación de informes a Excel y PDF.
- **Historial con trazabilidad** completa: quién cargó, cuándo, modificaciones, anulaciones.
- **Migración de datos históricos** desde los Excel actuales (CC, liquidaciones pasadas).
- **Tablas de referencia mantenibles por admin** (profesionales, clientes, bancos, categorías de gasto) sin tocar código.
- Poder incorporar nuevos profesionales / socios sin cambios estructurales.

---

## 7. Pedido al equipo de desarrollo

Con base en este documento, definir y proponer:

1. **Arquitectura del sistema** — ¿web, escritorio, base de datos relacional? Justificar para personal contable no técnico, multiusuario, seguridad.
2. **Flujo de datos entre módulos** — diagrama mostrando cómo un cobro impacta en CC, tesorería, liquidación, flujo y conciliación.
3. **Lógica de conciliación bancaria** — algoritmo de matching, tolerancias de fecha, centavos, protocolo de no identificados.
4. **Modelo de datos** — entidades principales (Cliente, Pago, Profesional, Liquidación, MovimientoBancario, etc.) y relaciones.
5. **Formato de importación de extractos** — qué formatos soporta cada banco, posibilidad de descarga automática, mapeo inicial.
6. **Estrategia de migración** de datos históricos desde Excel.
7. **Estimación de tiempos y versiones** — ¿MVP con CC en primera versión y conciliación después, o conjunto? Tiempos.
8. **Escalabilidad** — capacidad de agregar módulos futuros (facturación, integración con AFIP/ARCA) sin rediseño.

---

*Documento preparado por: Marisol Borrego — Estudio Larrañaga y Asociados — Santa Rosa, La Pampa — Abril 2026.*
