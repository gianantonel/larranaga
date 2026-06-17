# Requerimiento Técnico — Agente de Automatización: Preparación de IVA Compras

**Cliente:** Estudio Larrañaga y Asociados — Santa Rosa, La Pampa
**Empresa de referencia:** MATERIALES BUTALO SRL (CUIT 30-70921208-3)
**Fecha:** Abril 2026
**Contacto:** Marisol Borrego — Estudio Larrañaga y Asociados.

---

## 1. Introducción y contexto

El estudio asesora a **más de 100 clientes** (personas físicas y jurídicas). Todas las liquidaciones de IVA se procesan mensualmente en el sistema contable **Holistor**.

La preparación del **libro de IVA Compras** hoy implica pasos manuales en Excel, repetitivos y propensos a error. Este documento describe el proceso actual con precisión para que el desarrollador diseñe una herramienta (script, agente o aplicación) que lo automatice total o parcialmente.

A lo largo del documento se usa **MATERIALES BUTALO SRL** como ejemplo, con datos reales de **Febrero 2026**. El sistema debe ser replicable para cualquier cliente.

---

## 2. Proceso actual paso a paso

Cada mes, para liquidar IVA de cada cliente:

1. **Acceso a ARCA (ex-AFIP)** — ingresar con CUIT + clave fiscal del cliente (o representación).
2. **Descarga de comprobantes recibidos.**
3. **Descarga de comprobantes emitidos.**
4. **Descarga de retenciones y percepciones de IVA** — servicio "Mis Retenciones" de ARCA, detalle de percepciones de IVA aplicadas por proveedores.
5. **Descarga de percepciones de Ganancias** — ídem "Mis Retenciones".
6. **Descarga de percepciones de IIBB** — portal **DGR La Pampa**.
7. **Preparación del archivo HWCRARCA** — abrir template Excel de Holistor (`HWCRARCA.xls`). Copiar columnas A–AD del archivo de Mis Comprobantes Recibidos, pegar como valores. Controles, correcciones y clasificaciones manuales.
8. **Importación en Holistor** — guardar como `.prn` e importar en **IVA Registración** con esquema **"ARCA-Cptes Recibidos"**.

---

## 3. Archivos involucrados

### 3.1 ARCA — "Mis Comprobantes Recibidos"

Archivo base. 30 columnas (A–AD). Estructura clave:

| Col. | Nombre en ARCA | Descripción | Ejemplo (FERVA S.A.) |
|------|----------------|-------------|----------------------|
| A | Fecha | Fecha de emisión | 03/02/2026 |
| B | Tipo | Tipo de comprobante (Factura A, B, C, NC A, etc.) | 1 - Factura A |
| C | Punto de Venta | N° de punto de venta del emisor | 55 |
| D | Número Desde | Número de comprobante | 826.210 |
| G | Tipo Doc. Emisor | Tipo de documento del proveedor | CUIT |
| H | Nro. Doc. Emisor | CUIT del proveedor | 30-60798895-8 |
| I | Denominación Emisor | Razón social | FERVA S.A. |
| L | Tipo Cambio | Tipo de cambio (1 para $) | 1 |
| O | IVA 10,5% | Importe de IVA al 10,5% | — |
| S | IVA 21% | Importe de IVA al 21% | $19.861,32 |
| T | Neto Grav. IVA 21% | Base imponible al 21% | $94.577,70 |
| W | Neto Gravado Total | Suma de netos gravados | $94.577,70 |
| X | Neto No Gravado | Importe no gravado | $0 |
| Y | Op. Exentas | Importe de operaciones exentas | $0 |
| AB | **Otros Tributos** ⚠ | Tributos adicionales **agrupados** (ver §4) | $3.783,11 |
| AC | Total IVA | Suma total de IVA | $19.861,32 |
| AD | Imp. Total | Total del comprobante | $118.222,13 |

### 3.2 HWCRARCA.xls — template Holistor

Puente entre ARCA y la importación en Holistor.

- Columnas **A–AD** → réplica de las de ARCA.
- Columnas desde **AE** → clasificación propia de Holistor. Destacan:
  - **AL — Tipo de Movimiento**: código del gasto/compra según parametrización del cliente (ej.: CMG, ETG, HON, CYL, CBM). Clasifica en plan de cuentas y tipo de operación AFIP.
  - **AP — Concepto No Gravado**: solo si col. X (Neto No Gravado) o Y (Op. Exentas) > 0. Ej.: NGC, NGB, EXC.
  - **AR — Percepciones / Retenciones**: solo si col. AB (Otros Tributos) > 0. Código de la percepción según Holistor (ej.: PIVC, PIBA).

### 3.3 ARCA — "Mis Retenciones"

Detalle de cada percepción/retención sufrida en el período. **Clave** para desglosar "Otros Tributos".

Campos mínimos por línea:
- Fecha.
- CUIT del emisor.
- Denominación.
- Régimen / concepto (ej.: *"IV-Régimen de percepción - IVA"*, *"Otras locaciones de servicios"*).
- Importe.

### 3.4 DGR La Pampa — Percepciones de IIBB

Percepciones de Ingresos Brutos provinciales aplicadas por proveedores agentes de percepción. Complemento para identificar "Otros Tributos".

---

## 4. Problema principal — columna "Otros Tributos" (AB)

ARCA agrupa en **una sola columna** importes de conceptos muy distintos:

| Concepto | Código Holistor |
|----------|-----------------|
| Percepciones de IVA | **PIVC** |
| Percepciones de IIBB La Pampa | **PIBA** |
| Percepciones de IIBB de otras provincias | PIBC, PIBR, PIBV, etc. |
| Impuestos Internos (combustibles, bebidas) | **PCOM** |
| Sellos | **SELL** |

Hoy, para saber qué es cada importe, hay que **cruzar manualmente** el comprobante con los archivos de retenciones de ARCA + DGR La Pampa, buscando por CUIT del emisor y fecha.

### Ejemplo 1 — FERVA S.A. (3 facturas del 03/02/2026)

CUIT 30-60798895-8. Todas con "Otros Tributos":

| Nro. Comp. | Emisor | Neto Gravado | IVA 21% | Otros Tributos |
|-----------|--------|--------------|---------|----------------|
| 55-826210 | FERVA S.A. | $94.577,70 | $19.861,32 | $3.783,11 |
| 55-826233 | FERVA S.A. | $42.781,86 | $8.984,19 | $2.353,01 |
| 55-826282 | FERVA S.A. | $657.363,15 | $138.046,26 | $36.154,97 |

Para clasificar $3.783,11 (factura 826210) el contador filtra Mis Retenciones ARCA por CUIT 30-60798895-8 + fecha 03/02/2026 y verifica el concepto. Si no aparece, consulta DGR La Pampa.

**El agente debe replicar este cruce automáticamente:** dado CUIT + fecha, buscar en los archivos de retenciones el importe que coincida y asignar el código Holistor.

### Caso especial — múltiples conceptos en "Otros Tributos"

Un proveedor puede aplicar simultáneamente **percepción de IVA + percepción de IIBB**. El monto total de AB es la suma de ambos; el cruce con retenciones permite individualizarlos.

Cuando hay 2 conceptos distintos, el comprobante debe **dividirse en 2 filas** en HWCRARCA: una por cada percepción, repitiendo todos los datos y asignando el código (AR) correspondiente a cada una.

---

## 5. Problema secundario — comprobantes con múltiples alícuotas de IVA

Holistor requiere **una fila por alícuota**. ARCA genera una sola fila con columnas separadas por alícuota. Cuando hay dos o más alícuotas, hay que dividir.

### Ejemplo — AMX Argentina S.A. (Claro) — Factura A 1331-1919733 (04/02/2026)

CUIT 30-66328849-7. Con IVA al 21% **y** al 27%.

- Neto Gravado Total: $270.867,03
- Otros Tributos: $17.670,80
- Total: $356.300,95

Debe generar **dos filas en HWCRARCA** (una por alícuota), más potencialmente una tercera si "Otros Tributos" corresponde a un concepto distinto:

1. **Fila 1** — mismos datos, solo neto gravado + IVA al 21%.
2. **Fila 2** — mismos datos, solo neto gravado + IVA al 27%.
3. **(Opcional) fila 3 o AR en fila 1** — imputación de Otros Tributos con su código.

**Alícuotas posibles en ARCA:** 0%, 2,5%, 5%, 10,5%, 21%, 27%.

**Regla de detección:** si más de una de las columnas **O, Q, S, U, W** (IVA por tasa) tiene valor > 0 → dividir.

---

## 6. Tratamiento de comprobantes tipo B y C

> **⚠ NOTA CLAVE:** *COMPROBANTES TIPO B NO DEBEN TOMARSE EN IVA — sección no aplica para tipo B.*

Las **facturas tipo C** son emitidas por monotributistas o en operaciones con consumidores finales. En tipo C el IVA ya está incluido en el precio y no se discrimina, pero el archivo de ARCA puede traerlas con IVA discriminado.

**Holistor requiere**, para tipo B/C:
- Neto Gravado e IVA = 0.
- Importe total únicamente en "Imp. Total" (AD).

Si no se corrige, la importación **duplica el IVA** o da errores de cuadre.

**Regla automática:**
```
SI tipo de comprobante contiene 'B' (ej.: '3 - Factura B', '8 - NDD B', '13 - NC B'):
  → NO tomar en IVA (saltar).
SI tipo de comprobante contiene 'C' (monotributistas):
  → poner Neto Gravado + IVA = 0, dejar solo total en AD.
```

En Feb 2026 (BUTALO): **10 facturas tipo C + 2 NC tipo C**.

---

## 7. Control de formato — columna L (Tipo de Cambio)

Para operaciones en pesos, L = 1. Holistor **requiere formato numérico con 2 decimales (1,00)**, no entero (1).

| | Valor |
|--|--|
| Correcto | `1,00` (o `1.00` en formato anglosajón) |
| Incorrecto | `1` (sin decimales) |
| Acción | Forzar formato numérico con 2 decimales en toda la columna |

Si queda como entero, la importación puede fallar o generar inconsistencias.

---

## 8. Clasificación — columnas AL, AP y AR

Paso más laborioso. Tablas de referencia para **MATERIALES BUTALO SRL**:

### 8.1 Columna AL — Tipo de Movimiento

| Código | Descripción | Clasificación AFIP | Cuenta contable |
|--------|-------------|--------------------|-----------------|
| CMG | Compras Gravadas Mercadería | Compras de Bs. en el país | 51000000 - COMPRA DE MERCED. Y MATERIALES |
| CMB | Compra Mercadería Bariloche | Compras de Bs. en el país | 51000000 - COMPRA DE MERCED. Y MATERIALES |
| ETG | Electricidad, Telefonía y Gas | Prestaciones de servicios | 42101002 - LUZ, GAS Y T.E. |
| HON | Honorarios Profesionales | Prestaciones de servicios | 42101005 - HONORARIOS PROFESIONALES |
| CYL | Combustibles y Lubricantes | Compras de Bs. en el país | 42102001 - COMBUSTIBLES Y LUBRICANTES |
| ALM | Alquiler de Maquinarias | Prestaciones de servicios | 42101004 - ALQUILER DE MAQUINARIAS |
| CBM | Compra Bien Uso Maquinarias | Inversiones - Bienes de Uso | 12605001 - VALOR ORIGEN MAQUINARIAS |
| CBU | Compra Bienes de Uso (genérico) | Inversiones - Bienes de Uso | — |
| CGG | Gastos Gravados | Prestaciones de servicios | 42101003 - GASTOS GENERALES |
| FYA | Fletes y Acarreos | Prestaciones de servicios | 42102002 - FLETES Y ACARREOS |
| GBC | Gastos Bancarios | Compras de Bs. en el país | 42103003 - COMIS., INTERESES Y GS. BCARIOS |
| INF | Sistemas Informáticos | Prestaciones de servicios | 42101003 - GASTOS GENERALES |
| MAC | Materiales de Construcción | Compras de Bs. en el país | 42105001 - COMPRA MATERIALES CONSTRUCCIÓN |
| MAN | Mantenimiento | Compras de Bs. en el país | 42101003 - GASTOS GENERALES |
| HER | Herramientas | Compras de Bs. en el país | 42102016 - HERRAMIENTAS Y ÚTILES DE TRABAJO |
| GPE | Gastos de Personal | Compras de Bs. en el país | 42102015 - GASTOS PERSONAL |

**Lógica de asignación:**
- **CUIT del proveedor**: si ya fue procesado, el código histórico es señal fuerte.
- **Razón social**: palabras clave ("GAS", "LUZ", "TELEFONÍA", "HONORARIOS", "FLETE", "SEGURO").
- **Tabla de proveedores de Holistor**: almacena por CUIT el código por defecto. Exportable y usable como lookup.
- Si no se puede determinar → marcar **"requiere revisión manual"** y dejar **CGG** (Gastos Gravados) como default, resaltado.

### 8.2 Columna AP — Concepto No Gravado

Solo si X (Neto No Gravado) > 0 o Y (Op. Exentas) > 0.

| Código | Descripción | Uso |
|--------|-------------|-----|
| NGC | No Gravado en Compras | Importe no gravado general en facturas de compra |
| NGB | No Gravado Bariloche | No gravado para operaciones de la sucursal Bariloche |
| EXC | Exento en Compras | Operaciones exentas de IVA en compras |
| EXV | Exento en Ventas | Operaciones exentas en ventas (no aplica a compras) |
| 002 | Seguros | Primas de seguro (exentas de IVA) |
| CYL | Combustibles y Lubricantes | Componente no gravado en facturas de combustible |
| ETG | Electricidad, Telefonía y Gas | Componente no gravado en servicios públicos |

**Ejemplo:** factura de COOPERATIVA DE ELECTRICIDAD (CUIT 30-54571617-4, 11/02/2026) con Neto No Gravado $5,00 → AP = **ETG**.

### 8.3 Columna AR — Percepciones y Retenciones

Solo si AB (Otros Tributos) > 0. Identificar el concepto cruzando con retenciones y asignar código.

| Código | Descripción | Tipo | Cuándo usarlo |
|--------|-------------|------|---------------|
| PIVC | Percepción I.V.A. Compras | IVA | Proveedor agente de percepción de IVA. Aparece en Mis Retenciones ARCA como régimen **IV**. |
| PIBA | Percepción IIBB (general) | IIBB | Percepciones de Ingresos Brutos por agente provincial. |
| PIBC | Percepción IIBB Ciudad/Categ. | IIBB | Variante para CABA u otra jurisdicción. |
| PIBR | Percepción IIBB Río Negro | IIBB | Percepciones de IIBB de Río Negro. |
| PGAN | Percepciones de Ganancias | Ganancias | Aparece en Mis Retenciones ARCA. |
| PCOM | Impuestos Internos | Int. | Combustibles, bebidas alcohólicas, etc. |
| SELL | Sellos | Sellos | Impuesto de sellos en algunas jurisdicciones. |
| IBBA | IIBB Bariloche/otras | IIBB | Percepciones de IIBB sucursal Bariloche. |

**Ejemplo de cruce:** FERVA S.A. (30-60798895-8), factura 826210 del 03/02/2026, Otros Tributos $3.783,11. El agente busca en Mis Retenciones ARCA: CUIT 30-60798895-8 + fecha 03/02/2026 → encuentra régimen **"IV-Régimen de percepción"** por $3.783,11. Conclusión: **PIVC** en AR.

---

## 9. Lógica de decisión propuesta — árbol de procesamiento

Para cada fila del archivo de Mis Comprobantes Recibidos:

### Paso 1 — Filtrar y limpiar datos
- Eliminar fila 1 (encabezado secundario).
- Verificar col. L (Tipo de Cambio) → formato `1,00`.
- Identificar comprobantes tipo **B** → **excluir** (no tomar en IVA).
- Identificar tipo **C** → poner Neto Gravado + IVA = 0, mantener total en AD.

### Paso 2 — Detectar y expandir alícuotas múltiples
- Contar columnas de IVA con valor > 0 (O, Q, S, U, W).
- Si hay más de una → dividir en N filas, una por alícuota, replicando datos y distribuyendo importes.

### Paso 3 — Asignar Tipo de Movimiento (AL)
1. Consultar tabla de proveedores de Holistor (lookup por CUIT).
2. Si no está → reglas por palabras clave en razón social.
3. Si nada matchea → default **CGG** + flag "requiere revisión".

### Paso 4 — Asignar Concepto No Gravado (AP)
- Solo si X > 0 o Y > 0.
- Consultar tabla de conceptos + reglas por tipo de proveedor.

### Paso 5 — Asignar Percepción / Retención (AR)
- Solo si AB > 0.
- Buscar en archivo Mis Retenciones ARCA: CUIT emisor + fecha + importe.
- Si no aparece → buscar en DGR La Pampa.
- Identificar régimen (**IV** = IVA, **IG** = Ganancias, **IB** = IIBB).
- Mapear al código Holistor (PIVC, PGAN, PIBA, etc.).
- Si hay **múltiples conceptos** en AB → dividir comprobante en filas adicionales.

### Paso 6 — Generar salida
- Archivo HWCRARCA completo con todas las columnas.
- **Resaltar en color** (amarillo) las filas marcadas para revisión manual.
- Log/resumen: N° de comprobantes procesados, divididos por alícuota, Otros Tributos identificados automáticamente, casos que requieren revisión.
- Exportar **.prn** listo para importar en Holistor.

---

## 10. Funcionalidades esperadas

### 10.1 Entradas
- Excel de **Mis Comprobantes Recibidos** (.xlsx / .csv).
- **Mis Retenciones / Percepciones** ARCA (.xls / .xlsx).
- **Percepciones IIBB DGR La Pampa** (formato a definir).
- **Tabla de proveedores de Holistor** con códigos de movimiento (.pdf / .xlsx).
- Tablas de referencia de Holistor: Tipos de Movimiento, Conceptos No Gravados, Percepciones/Retenciones (exportables o cargadas manualmente una vez por cliente).

### 10.2 Procesamiento automático
- Lectura y parseo de todos los archivos.
- Limpieza: formatos numéricos, ceros, tipos B/C.
- Detección y expansión de múltiples alícuotas.
- Cruce automático con retenciones para clasificar "Otros Tributos".
- Clasificación de Tipo de Movimiento por CUIT/razón social (tabla configurable).
- Clasificación de Conceptos No Gravados por tipo de proveedor.

### 10.3 Salidas
- **HWCRARCA.xlsx** completo con AL, AP, AR.
- **.prn** listo para Holistor.
- **Reporte de control**: comprobantes marcados para revisión manual, con motivo.
- **Log**: estadísticas del período.

### 10.4 Interfaz y usabilidad
- Puede ser script Python, app de escritorio o planilla con macros (a definir).
- Ejecutable por **personal contable sin conocimientos de programación**.
- Tablas de referencia mantenibles sin tocar código.
- **Replicable para distintos clientes** (cada uno con sus propias tablas Holistor).

---

## 11. Escalabilidad

- **Más de 100 clientes.** El sistema debe correr para distintos clientes sin reconfiguración de código.
- Cada cliente tiene sus propias tablas (Tipos de Movimiento, Conceptos No Gravados, Percepciones) → **archivos de configuración por cliente** (ej.: una carpeta por cliente).
- **Ventas (HWVTARCA)** — proceso análogo al de compras. El sistema podría extenderse más adelante para cubrirlo.
- **Migración futura de Holistor a ONVIO** — diseñar con **capas de transformación separadas del formato de salida**, para adaptar a nuevo formato sin reescribir la lógica.

---

*Documento preparado por: Marisol Borrego — Estudio Larrañaga y Asociados — Santa Rosa, La Pampa — Abril 2026.*
