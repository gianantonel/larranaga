# Plan Maestro Integrado de Automatización
## Larrañaga & Asociados × Optimizar

**IVA & Contabilidad + Administración & Tesorería**
Requerimientos · AFIP SDK · Código · Claude Code · Fases · GitHub

*Documento interno — Equipo Optimizar | Abril 2026*

---

## 1. Catálogo Completo de Requerimientos

Todos los requerimientos de ambos módulos, ordenados de más fácil a más difícil de implementar. La columna **Área** indica si viene del módulo IVA/Contabilidad o del módulo Administración/Tesorería.

| # | Requerimiento | Área | Dificultad | Tiempo est. | AFIP SDK |
|---|---------------|------|------------|-------------|----------|
| **R-01** | Corrección comprobantes tipo B/C + formato tipo de cambio (col. L) | IVA | ⭐ Muy fácil | 1-2 sem | Sin SDK |
| **R-02** | División de comprobantes por múltiples alícuotas de IVA | IVA | ⭐ Muy fácil | 1-2 sem | Sin SDK |
| **R-03** | Cálculo automático de honorarios (fijo y valor producto) | ADM | ⭐ Muy fácil | 1-2 sem | Sin SDK |
| **R-04** | Liquidación mensual de profesionales — cálculo automático | ADM | ⭐ Muy fácil | 1-2 sem | Sin SDK |
| **R-05** | Separación retenciones IVA vs IIBB (col. AB — Otros Tributos) | IVA | ✅ Fácil | 1-2 sem | SDK 100% |
| **R-06** | Conciliación IVA compras/ventas — posición IVA del mes | IVA | ✅ Fácil | 1-2 sem | SDK 100% |
| **R-07** | Cuentas corrientes de clientes — registro y saldo en tiempo real | ADM | ✅ Fácil | 2-3 sem | Sin SDK |
| **R-08** | Tesorería — registro de ingresos y egresos con impacto automático | ADM | ✅ Fácil | 2-3 sem | Sin SDK |
| **R-09** | Imputación contable por CUIT (5 niveles: maestro → padrón → reglas → IA → fallback) | IVA | ⚡ Media | 2-3 sem | SDK Parcial |
| **R-10** | Generación HWCRARCA completo para Holistor/Onvio | IVA | ⚡ Media | 2-3 sem | Sin SDK |
| **R-11** | Flujo de fondos — seguimiento y proyección vs real | ADM | ⚡ Media | 2-3 sem | Sin SDK |
| **R-12** | Retiro de honorarios de socios — registro y control | ADM | ⚡ Media | 2-3 sem | Sin SDK |
| **R-13** | Actualización cuatrimestral de honorarios con pantalla de validación | ADM | ⚡ Media | 3-4 sem | Sin SDK |
| **R-14** | Control de billetes / caja — seguimiento efectivo por denominación | ADM | ⚡ Media | 3-4 sem | Sin SDK |
| **R-15** | Conciliación bancaria — importación y matching automático (Pampa, Santander, MP) | IVA + ADM | 🔧 Alta | 3-4 sem | Sin SDK |
| **R-16** | Reportes periódicos automáticos IVA-MES — 100+ clientes | IVA | 🔧 Alta | 4-6 sem | SDK 100% |
| **R-17** | Informes de gestión — deuda, honorarios, retiros, flujo real vs proyectado | ADM | 🔧 Alta | 4-6 sem | Sin SDK |
| **R-18** | Liquidación de impuestos: IVA, Ganancias, F931, VEPs automáticos | IVA | 🔴 Muy alta | 6+ sem | SDK 100% |
| **R-19** | Consulta IVA-MES por cliente desde ARCA | IVA | 🔴 Muy alta | 6+ sem | SDK Parcial |
| **R-20** | Migración histórica desde Excel (cuentas corrientes + liquidaciones pasadas) | IVA + ADM | 🔴 Muy alta | 6+ sem | Sin SDK |

---

## 2. AFIP SDK — Cobertura y Alternativas para lo que No Cubre

### 2.1 Requerimientos que AFIP SDK cubre

| Req. | Requerimiento | Servicio SDK | Datos clave que devuelve |
|------|---------------|--------------|--------------------------|
| R-05 | Separación retenciones IVA vs IIBB | Automatización **mis-retenciones** | `codigoRegimen` (IV=IVA, IB=IIBB, IG=Ganancias), `cuitAgenteRetencion`, `importeRetenido`, `fechaRetencion` |
| R-06 | Conciliación IVA — posición mensual | Automatización **mis-comprobantes** (t:R y t:E) | Todos los comprobantes emitidos/recibidos con neto, IVA por alícuota, otros tributos, total |
| R-09 | Imputación contable por CUIT | Web service **ws_sr_padron_a4** — `getPersona` | Actividad principal AFIP, forma jurídica, impuestos activos, email, domicilio fiscal |
| R-16 | Reportes IVA-MES — 100+ clientes | Automatización **mis-comprobantes** por cliente | Ídem R-06, automatizado con credenciales de cada cliente |
| R-18 | Liquidación impuestos + VEPs | WS **djprocessorcontribuyente** + `createVEP` | Upload DDJJ en base64. Genera VEP con impuesto, período, importe. Devuelve `nroVEP`. |
| R-19 | Consulta IVA-MES desde ARCA | Automatización mis-comprobantes + cálculo | No es consulta directa de saldo; se calcula: **débito − crédito − percepciones = posición** |

> ⚠ Los servicios de automatización (`mis-comprobantes`, `mis-retenciones`) requieren **CUIT + clave fiscal del cliente**. Las credenciales se guardan **cifradas en Supabase** y se usan solo en runtime, nunca en logs.

### 2.2 Requerimientos sin cobertura SDK — Alternativas propuestas

| Req. | Requerimiento | Por qué no hay SDK | Alternativa de implementación |
|------|---------------|--------------------|-------------------------------|
| R-01 | Corrección B/C + formato col. L | Es transformación de datos del Excel de ARCA | Función Python/JS pura. ~20 líneas. `parseFloat(v).toFixed(2)` + corrección columnas. |
| R-02 | División por alícuotas | Transformación del mismo archivo | Función pura. Loop sobre O/Q/S/U/W, duplicar filas. |
| R-03 | Cálculo honorarios | Lógica interna del estudio | Python: tabla productos (cemento, carne, etc.) en Supabase. `fijo` → valor directo. `producto` → cantidad × precio vigente. |
| R-04 | Liquidación profesionales | Lógica interna | Python: suma adelantos del mes (tabla `pagos`) − honorarios + saldo anterior + reintegros. |
| R-07 | Cuentas corrientes | Base de datos del estudio | Supabase (PostgreSQL) + FastAPI + React. |
| R-08 | Tesorería | Base de datos interna | Misma Supabase. Un movimiento de tesorería se crea automáticamente por cada pago. |
| R-10 | Generación HWCRARCA | Formato Holistor, no ARCA | Python + openpyxl. .xlsx con estilos + .prn. Validación `Debe=Haber` antes de guardar. |
| R-11 | Flujo de fondos | Lógica interna | Supabase views calculadas. |
| R-12 | Retiro socios | Lógica interna | Tabla `retiros`. Crea egreso en tesorería + movimiento bancario para conciliar. |
| R-13 | Actualización cuatrimestral | Lógica interna | Endpoint Python + pantalla de validación React. |
| R-14 | Control billetes | Lógica interna | Tabla `denominaciones`. Cada movimiento en efectivo actualiza conteos. |
| R-15 | Conciliación bancaria | Bancos argentinos sin API pública unificada. DGR La Pampa sin API. | Ver §2.3. |
| R-17 | Informes de gestión | Lógica interna | Python queries + openpyxl/reportlab. |
| R-20 | Migración histórica Excel | No es proceso ARCA | Python + pandas. |

### 2.3 Conciliación bancaria — Estrategia por banco

| Banco | Formato extracto | Estrategia de obtención | Parser | Fallback |
|-------|------------------|-------------------------|--------|----------|
| **Banco Pampa** | Excel (.xlsx/.xls) desde homebanking. Sin API pública. | Descarga manual → upload a Google Drive → trigger automático | `parser_pampa.py`: mapeo columnas BLP. Regex CUIT en descripción. | Claude Vision si formato cambia o si viene en PDF |
| **Banco Santander** | Excel (.xlsx) desde homebanking. Sin API pública para estudios. | Descarga manual → Drive → trigger | `parser_santander.py`: Fecha, Concepto, Débito, Crédito, Saldo | Claude Vision |
| **Mercado Pago** | Excel o CSV desde panel mp.com. Sin API terceros sin app registrada. | Descarga manual o export programático via scraping autenticado | `parser_mercadopago.py`: CSV de MP. Detectar entrantes vs salientes. | Claude Vision |
| **Interbanking** (si aplica) | API REST oficial `developers.interbanking.com.ar` | Si el cliente tiene cuenta: API directa con `customer-id + API key`. Movimientos y saldos en JSON. | No requiere parser | Descarga manual si no tienen Interbanking |
| **Prometeo** (fallback) | Open Banking LATAM — cubre Galicia, BBVA, Santander, Macro, Nación en Argentina | Un solo punto de acceso a múltiples bancos | JSON unificado | Solo para cuentas del estudio, no de clientes |

**Algoritmo de matching** (válido para todos los bancos):

| Tipo movimiento | Buscar en | Criterio match | Match exitoso |
|-----------------|-----------|----------------|---------------|
| Crédito (transferencia entrante) | Tabla `pagos` / CC clientes | CUIT en descripción + importe exacto + fecha ±1 día | Marcar conciliado. Vincular al pago. |
| Débito (transferencia saliente) | Tabla `egresos` tesorería | Importe exacto + fecha ±1 día | Marcar conciliado. |
| Débito automático | Tabla `egresos` tesorería | Importe + palabras clave (CBU, SERV, IMP, SEPA) | Si match → conciliado. Si no → clasificación manual. |
| Retiro de socio (débito) | Tabla `retiros_socios` | Importe + fecha + nombre socio en descripción | Marcar conciliado. |
| Comisión / mantenimiento | Tabla `egresos` bancarios | Importe + banco + palabras (COM., MANT., IMP.) | Crear egreso automático categoría GBC si no existe. |
| Sin match (ambos lados) | — | — | Presentar para clasificación manual con sugerencia vía Claude API. |

---

## 3. Soluciones Técnicas — Código por Requerimiento

### 3.1 Stack base (aplica a todos los módulos)

| Capa | Tecnología | Rol | Por qué |
|------|-----------|-----|---------|
| Backend API | **Python + FastAPI** | Lógica de negocio, REST para frontend | Potente con pandas/openpyxl, excelente testing |
| Base de datos | **Supabase (PostgreSQL)** | Todas las entidades | SQL robusto, RLS multiusuario, APIs REST + Realtime |
| Frontend web | **React + TypeScript** | Interfaz para el estudio | Cualquier dispositivo, multiusuario, export Excel/PDF |
| Orquestación | **n8n** | Triggers por Drive, schedules, Gmail | Ya operativo en Optimizar |
| Procesamiento | Python + pandas + openpyxl | Parseo extractos, HWCRARCA, migración | Manejo nativo Excel |
| IA clasificación | **Claude API (Sonnet)** | Imputación contable ambigua, mov. bancarios desconocidos | Contexto contable en prompt, JSON estructurado |
| Credenciales | Supabase tabla cifrada | CUIT + clave fiscal por cliente | Nunca en código ni logs |
| Archivos | Google Drive | Extractos, HWCRARCA, configs por cliente | Trigger nativo en n8n |
| Desarrollo | **Claude Code + Agent Teams** | Los 3 devs con Claude Code en cada repo | Sprints paralelos, subagentes especializados |

### 3.2 Modelo de datos — Entidades principales

| Entidad | Campos clave | Relaciones | Módulo |
|---------|--------------|-----------|--------|
| **Cliente** | `id, nombre, cuit, tipo_honorario (fijo/producto), importe_honorario, producto_ref_id, profesional_id, activo` | → Pago (1:N), → Honorario (1:N), → Profesional (N:1) | R-07, R-03 |
| **Honorario** | `id, cliente_id, periodo (AAAAMM), importe_calculado, estado, fecha_emision` | → Cliente, → Pago (1:N) | R-03, R-07 |
| **Pago** | `id, cliente_id, honorario_id, fecha, importe, forma_pago, banco_destino, profesional_destinatario_id, fuente_pago` | → Cliente, → Honorario, → Profesional, → MovimientoTesoreria | R-07, R-08, R-04 |
| **Profesional** | `id, nombre, activo, tipo (profesional/socio)` | → Cliente (1:N), → Liquidacion (1:N), → Retiro (1:N) | R-04, R-12 |
| **Liquidacion** | `id, profesional_id, periodo, honorarios_totales, adelantos_percibidos, saldo_anterior, reintegro_gastos, total_a_cobrar, forma_cobro, saldo_siguiente` | → Profesional | R-04 |
| **MovimientoTesoreria** | `id, fecha, tipo, importe, forma_pago, categoria, pago_id, retiro_id, conciliado, movimiento_bancario_id` | → Pago, → Retiro, → MovimientoBancario | R-08, R-15 |
| **MovimientoBancario** | `id, banco, fecha, descripcion, importe, tipo, conciliado, movimiento_tesoreria_id, pago_id` | → MovimientoTesoreria (1:1), → Pago (1:1) | R-15 |
| **Retiro** | `id, socio_id, fecha, importe, forma_pago, banco_origen, conciliado` | → Profesional, → MovimientoTesoreria | R-12 |
| **ControlBilletes** | `id, denominacion, cantidad, fecha_actualizacion` | — | R-14 |
| **ProductoReferencia** | `id, nombre, precio_vigente, fecha_actualizacion, historial_precios[]` | → Cliente (1:N) | R-03 |
| **ExtractoBancario** | `id, banco, periodo, archivo_path, fecha_importacion, n_movimientos, n_conciliados, n_pendientes` | → MovimientoBancario (1:N) | R-15 |

### 3.3 Código clave — Cálculo de honorarios

```python
# src/honorarios/calcular.py
from supabase import create_client
from decimal import Decimal

def calcular_honorario(cliente_id: str, periodo: str) -> Decimal:
    """
    Calcula el honorario de un cliente para el período (AAAAMM).
    Soporta 'fijo' (importe directo) y 'producto' (cantidad × precio vigente).
    """
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    c = sb.table('clientes').select('*').eq('id', cliente_id).single().execute().data

    if c['tipo_honorario'] == 'fijo':
        return Decimal(str(c['importe_honorario']))

    if c['tipo_honorario'] == 'producto':
        prod = sb.table('productos_referencia') \
                 .select('precio_vigente').eq('id', c['producto_ref_id']) \
                 .single().execute().data
        return Decimal(str(c['cantidad_unidades'])) * Decimal(str(prod['precio_vigente']))

    raise ValueError(f'Tipo de honorario desconocido: {c["tipo_honorario"]}')
```

### 3.4 Código clave — Impacto automático de un pago

```python
# src/pagos/registrar_cobro.py
from supabase import AsyncClient
from decimal import Decimal

async def registrar_cobro(
    cliente_id: str,
    honorario_id: str,
    importe: Decimal,
    forma_pago: str,                              # 'efectivo' | 'transferencia'
    profesional_destino_id: str | None = None,
    banco_destino: str | None = None,
    fuente_pago: str | None = None,               # empresa o nombre que transfirió
    billetes: dict | None = None,                 # {20000: 5, 10000: 2} si efectivo
) -> dict:
    async with AsyncClient(SUPABASE_URL, SUPABASE_KEY) as sb:
        async with sb.begin():
            # 1. Registrar pago
            pago = await sb.table('pagos').insert({
                'cliente_id': cliente_id,
                'honorario_id': honorario_id,
                'importe': float(importe),
                'forma_pago': forma_pago,
                'profesional_destinatario_id': profesional_destino_id,
                'banco_destino': banco_destino,
                'fuente_pago': fuente_pago,
            }).execute()
            pago_id = pago.data[0]['id']

            # 2. Actualizar saldo CC
            await sb.rpc('actualizar_saldo_cliente', {
                'p_cliente_id': cliente_id,
                'p_importe_haber': float(importe)
            }).execute()

            # 3. Crear movimiento de tesorería
            await sb.table('movimientos_tesoreria').insert({
                'tipo': 'ingreso',
                'importe': float(importe),
                'forma_pago': forma_pago,
                'pago_id': pago_id,
                'conciliado': False,
            }).execute()

            # 4. Si transferencia a profesional → imputar como adelanto
            if forma_pago == 'transferencia' and profesional_destino_id:
                await sb.rpc('agregar_adelanto_profesional', {
                    'p_profesional_id': profesional_destino_id,
                    'p_periodo': get_periodo_actual(),
                    'p_importe': float(importe),
                    'p_pago_id': pago_id
                }).execute()

            # 5. Si efectivo → actualizar control de billetes
            if forma_pago == 'efectivo' and billetes:
                for denominacion, cantidad in billetes.items():
                    await sb.rpc('agregar_billetes', {
                        'p_denominacion': int(denominacion),
                        'p_cantidad': cantidad
                    }).execute()

            # 6. Queda disponible para conciliar al importar el extracto (no auto)

    return {'pago_id': pago_id, 'impactos': ['cc', 'tesoreria', 'liquidacion', 'billetes']}
```

### 3.5 Código clave — Parsers bancarios (pattern)

```python
# src/bancos/parsers/base_parser.py
import pandas as pd, re
from abc import ABC, abstractmethod
from decimal import Decimal

CUIT_RE = re.compile(r'\b(\d{2}-?\d{8}-?\d)\b')

class BankParser(ABC):
    banco: str
    col_map: dict

    def parse(self, filepath: str, periodo: str) -> list[dict]:
        df = self._read_file(filepath)
        df = self._normalize_columns(df)
        return [self._normalize_row(r, periodo) for _, r in df.iterrows()
                if self._is_valid_row(r)]

    def _normalize_row(self, r, periodo) -> dict:
        desc = str(r.get('descripcion', '')).strip().upper()
        debe  = self._to_decimal(r.get('debe',  0))
        haber = self._to_decimal(r.get('haber', 0))
        cuit_m = CUIT_RE.search(desc)
        return {
            'banco': self.banco, 'periodo': periodo,
            'fecha': pd.to_datetime(r['fecha'], dayfirst=True).strftime('%Y-%m-%d'),
            'descripcion': desc,
            'tipo': 'D' if debe > 0 else 'C',
            'importe': float(debe if debe > 0 else haber),
            'saldo': self._to_decimal(r.get('saldo', 0)),
            'cuit_detectado': cuit_m.group(0).replace('-', '') if cuit_m else None,
        }

    @staticmethod
    def _to_decimal(v) -> Decimal:
        return Decimal(str(v).replace(',', '').replace('$', '').strip() or '0')

    @abstractmethod
    def _read_file(self, fp): ...
    @abstractmethod
    def _normalize_columns(self, df): ...
    @abstractmethod
    def _is_valid_row(self, r) -> bool: ...


class PampaParser(BankParser):
    banco = 'pampa'
    col_map = {'Fecha': 'fecha', 'Referencia': 'descripcion',
               'Débito': 'debe', 'Crédito': 'haber', 'Saldo': 'saldo'}
    def _read_file(self, fp): return pd.read_excel(fp, dtype=str, skiprows=2)
    def _normalize_columns(self, df):
        df.columns = [c.strip() for c in df.columns]
        return df.rename(columns=self.col_map)
    def _is_valid_row(self, r): return pd.notna(r.get('fecha'))


class SantanderParser(BankParser):
    banco = 'santander'
    col_map = {'Fecha': 'fecha', 'Concepto': 'descripcion',
               'Importe Débito': 'debe', 'Importe Crédito': 'haber', 'Saldo': 'saldo'}
    def _read_file(self, fp): return pd.read_excel(fp, dtype=str, skiprows=1)
    def _normalize_columns(self, df):
        df.columns = [c.strip() for c in df.columns]
        return df.rename(columns=self.col_map)
    def _is_valid_row(self, r): return pd.notna(r.get('fecha'))


class MercadoPagoParser(BankParser):
    banco = 'mercadopago'
    col_map = {'FECHA': 'fecha', 'DESCRIPCIÓN': 'descripcion', 'MONTO': 'importe_raw'}
    def _read_file(self, fp): return pd.read_csv(fp, dtype=str)
    def _normalize_columns(self, df):
        df.columns = [c.strip().upper() for c in df.columns]
        df = df.rename(columns=self.col_map)
        df['debe']  = df['importe_raw'].apply(lambda x: abs(float(x)) if float(x) < 0 else 0)
        df['haber'] = df['importe_raw'].apply(lambda x: float(x) if float(x) > 0 else 0)
        return df
    def _is_valid_row(self, r): return pd.notna(r.get('fecha'))


PARSERS = {'pampa': PampaParser, 'santander': SantanderParser, 'mercadopago': MercadoPagoParser}

def get_parser(banco: str) -> BankParser:
    cls = PARSERS.get(banco.lower())
    if not cls: raise ValueError(f'Parser no encontrado para banco: {banco}')
    return cls()
```

---

## 4. Plan de Acción por Fases

El proyecto se divide en **4 fases de 3-4 semanas**. Cada fase tiene **máx. 4 requerimientos**, mezclando IVA y ADM para entregar valor visible en cada iteración. El cliente puede usar funcionalidades reales desde la Fase 1.

> **Principio de mezcla:** cada fase combina ≥1 requerimiento de IVA y ≥1 de ADM, y ≥1 que use AFIP SDK y ≥1 que no. Garantiza que ambas partes del estudio reciben valor en cada entrega.

### Fase 1 — Infraestructura base + Quick wins (Semanas 1–3)

**Objetivo:** tener la base técnica funcionando y los primeros 4 requerimientos operativos. El equipo accede a datos reales y puede demostrar valor al cliente.

| Req. | Requerimiento | Área | Por qué primero | Stack | Dev |
|------|---------------|------|-----------------|-------|-----|
| **R-01 + R-02** | Corrección B/C + División alícuotas | IVA | Cero dependencias. 1 día de código. Elimina trabajo manual repetitivo. Demo rápida. | Python puro | Dev 2 |
| **R-05** | Separación retenciones IVA vs IIBB | IVA | AFIP SDK resuelve 90%. `codigoRegimen` hace el trabajo. Demo con datos de BUTALO. | SDK 100% | Dev 1 |
| **R-07** | Cuentas corrientes — base de datos y registro | ADM | Prerequisito de todo el módulo ADM. | Supabase | Dev 2 |
| **R-03 + R-04** | Cálculo honorarios + Liquidación profesionales | ADM | Lógica pura sin dependencias. Elimina cálculos manuales Excel. | Python puro | Dev 2 |

**Entregables Fase 1:**
- Repo `larranaga-core`: schema Supabase completo, config de entorno, `CLAUDE.md` del proyecto.
- Repo `larranaga-arca-agent`: módulo retenciones (R-05) con tests contra fixtures reales.
- Repo `larranaga-accounting-agent`: módulos corrección B/C, división alícuotas (R-01/02).
- Repo `larranaga-admin-agent`: entidades Supabase (clientes, honorarios, profesionales). API FastAPI para CC y cálculo de honorarios.
- **Demo funcional:** procesar el libro IVA compras de **MATERIALES BUTALO SRL Febrero 2026** de punta a punta.
- **Demo funcional:** registrar un honorario de Juan Pérez y que el saldo se actualice en tiempo real.

**Setup de infraestructura (semana 1, todos los devs):**
- Crear los 5 repositorios en GitHub con estructura de carpetas y `CLAUDE.md`.
- Configurar Supabase: proyecto, schema, RLS, API keys.
- Variables de entorno: AFIP SDK token, Supabase, Google Drive.
- Configurar Claude Code en cada máquina: `settings.json`, subagentes, hooks.
- Fixtures con datos reales anonimizados: BUTALO SRL + 2 clientes del estudio.

### Fase 2 — Pipeline IVA completo + Tesorería (Semanas 4–6)

**Objetivo:** el pipeline IVA compras corre de punta a punta y genera el HWCRARCA listo para importar. Tesorería registra cobros con impacto automático en todos los módulos.

| Req. | Requerimiento | Área | Dependencias | Stack | Dev |
|------|---------------|------|--------------|-------|-----|
| **R-06** | Conciliación IVA — posición mensual | IVA | R-05 completado. SDK mis-comprobantes t:E y t:R. | SDK 100% | Dev 1 |
| **R-09 + R-10** | Imputación CUIT + Generación HWCRARCA | IVA | R-01, R-02, R-05 completados. Maestro de proveedores cargado. | Python + Claude API | Dev 2 |
| **R-08** | Tesorería — registro de pagos con impacto automático | ADM | R-07 completado. `registrar_cobro()` conecta todos los módulos. | Supabase | Dev 2 |
| **R-14** | Control de billetes / caja efectivo | ADM | R-08 completado. Se integra al registro de cobros en efectivo. | Supabase | Dev 3 |

**Entregables Fase 2:**
- Pipeline IVA completo: `mis-comprobantes → limpieza → retenciones → imputación → HWCRARCA.xlsx + .prn`. Listo para importar en Holistor/Onvio.
- Función `registrar_cobro()` operativa: cobro → CC cliente + tesorería + liquidación profesional + control billetes.
- Hook de validación: el HWCRARCA se valida (`Debe=Haber`) antes de escribir al disco.
- Tests de integración: flujo completo con datos BUTALO Feb 2026.

### Fase 3 — Conciliación bancaria + Flujo de fondos (Semanas 7–10)

**Objetivo:** módulo crítico de ADM (conciliación bancaria) + gestión financiera. Después de esta fase, el estudio reemplaza completamente sus Excel de tesorería y flujo de fondos.

| Req. | Requerimiento | Área | Dependencias | Stack | Dev |
|------|---------------|------|--------------|-------|-----|
| **R-15** | Conciliación bancaria — parsers + matching automático | IVA + ADM | R-08 completo (movimientos para cruzar). Parsers por banco. | Python + Claude Vision | Dev 3 |
| **R-11** | Flujo de fondos — seguimiento y proyección | ADM | R-08 completo. | Supabase | Dev 2 |
| **R-12** | Retiro de honorarios de socios | ADM | R-08 completo. | Supabase | Dev 2 |
| **R-13** | Actualización cuatrimestral de honorarios | ADM | R-07 completo. Tabla de índices + pantalla React. | Python + React | Dev 3 |

**Entregables Fase 3:**
- Parsers bancarios operativos: **Pampa, Santander, Mercado Pago**. Maneja Excel y PDF (pdfplumber + Claude Vision para escaneados).
- Algoritmo de matching: créditos ↔ pagos de honorarios, débitos ↔ egresos, retiros socios ↔ extracto.
- **Cola de revisión**: movimientos sin match en interfaz React con sugerencia de categoría vía Claude API.
- Flujo de fondos: dashboard **real vs proyectado**, visualización mensual.
- Módulo de retiros de socios con historial y conciliación bancaria automática.
- Pantalla de actualización cuatrimestral: tabla `honorario actual / propuesto / checkbox confirmación individual`.

### Fase 4 — Reportes, IVA-MES e integración total (Semanas 11–15)

**Objetivo:** sistema completo. Se agregan reportes automáticos, consulta IVA-MES para 100+ clientes y migración histórica. El estudio puede eliminar todos los Excel.

| Req. | Requerimiento | Área | Dependencias | Stack | Dev |
|------|---------------|------|--------------|-------|-----|
| **R-16 + R-19** | Reportes IVA-MES automáticos + Consulta ARCA | IVA | R-06 completo. Credenciales por cliente operativas. | SDK 100% | Dev 1 |
| **R-17** | Informes de gestión — todos los reportes ADM | ADM | Todos los módulos ADM completos. Queries sobre Supabase. | Python + React | Dev 2 |
| **R-20** | Migración histórica desde Excel | IVA + ADM | Todos los módulos operativos. | Python + pandas | Todos |
| **R-18** | Liquidación impuestos + VEPs (MVP inicial) | IVA | R-06 completo. Solo IVA en primer MVP. Ganancias y F931 versión posterior. | SDK 100% | Dev 1 |

**Entregables Fase 4:**
- **Schedule automático:** el **día 5 de cada mes** el sistema descarga comprobantes de todos los clientes vía AFIP SDK y calcula la posición IVA.
- **Reportes IVA-MES:** Google Doc generado automáticamente por cliente con posición del mes, enviado por Gmail los días **15 y 25**.
- Todos los informes de gestión: estado CC, antigüedad deuda, honorarios cobrados por profesional, retiros socios, flujo real vs proyectado, conciliación bancaria.
- Script de migración: importa CC históricas, liquidaciones pasadas y tesorería desde los Excel actuales.
- **MVP liquidación IVA:** calcula saldo, presenta DDJJ vía `djprocessorcontribuyente`, genera VEP.

---

## 5. Claude Code — Setup para el Equipo de 3 Devs

Con la incorporación del módulo ADM, el sistema tiene **5 repositorios**. La asignación se actualiza para cubrir ambos módulos.

### 5.1 Asignación por desarrollador

| Dev | Repos a cargo | Requerimientos | Subagentes Claude Code |
|-----|---------------|----------------|------------------------|
| **Dev 1** — Infra + ARCA | `larranaga-core`, `larranaga-arca-agent`, `larranaga-n8n-flows` | R-05, R-06, R-16, R-19, R-18 + Setup Supabase, credenciales, CI/CD | `agente-retenciones`, `agente-conciliacion-iva`, `agente-iva-mes`, `agente-veps` |
| **Dev 2** — Contabilidad + ADM | `larranaga-accounting-agent`, `larranaga-admin-agent`, `larranaga-reports` | R-01, R-02, R-03, R-04, R-07, R-08, R-09, R-10, R-11, R-12, R-17 | `agente-hwcrarca`, `agente-honorarios`, `agente-tesoreria`, `agente-liquidacion-prof` |
| **Dev 3** — Bancario + ADM complementario | `larranaga-banking-agent` (colabora en `larranaga-admin-agent`) | R-13, R-14, R-15, R-20 + Frontend React (conciliación y actualización) | `agente-parsers-bancos`, `agente-conciliacion-bancaria`, `agente-migracion` |

### 5.2 Subagentes adicionales para el módulo ADM

**`.claude/agents/agente-honorarios.md`**
```yaml
---
name: agente-honorarios
description: Calcula y gestiona honorarios de clientes del estudio.
  Soporta tipos fijo y valor-producto. Úsame para calcular el honorario
  de un cliente en un período, procesar actualizaciones cuatrimestrales,
  o verificar consistencia entre cuentas corrientes y flujo de fondos.
tools: Read, Write, Bash
model: claude-sonnet-4-5-20250929
---

Sos un especialista en administración de estudio contable.

TIPOS DE HONORARIO:
  fijo:     importe directo en pesos (campo importe_honorario).
  producto: cantidad_unidades × precio_vigente del producto_ref_id.

REGLA CONSISTENCIA (verificar siempre):
  saldo_cuenta_corriente_cliente == deuda_en_flujo_fondos
  Si difieren más de $0.10 → alerta inmediata, no continuar.

ACTUALIZACIÓN CUATRIMESTRAL:
  1. Calcular nuevo importe aplicando índice
  2. Presentar tabla de validación (cliente, actual, propuesto, delta%)
  3. NO aplicar hasta confirmación explícita del operador
  4. Registrar en historial_actualizaciones
```

**`.claude/agents/agente-tesoreria.md`**
```yaml
---
name: agente-tesoreria
description: Gestiona movimientos de tesorería del estudio. Verifica
  que cada cobro de honorarios impacta correctamente en CC del cliente,
  liquidación del profesional, flujo de fondos y control de billetes.
tools: Read, Write, Bash
model: claude-sonnet-4-5-20250929
---

Sos el responsable de la caja del estudio Larrañaga.

REGLA DE ORO: carga única — impacto automático en todos los módulos.
Un cobro de honorarios SIEMPRE afecta:
  1. Cuenta corriente del cliente (saldo Haber)
  2. Movimiento de tesorería (ingreso)
  3. Liquidación del profesional destinatario (adelanto)
  4. Control de billetes (si fue en efectivo)
  5. Cola de conciliación bancaria (si fue transferencia)

NUNCA registres un cobro sin verificar que los 5 impactos se ejecutaron.
Si alguno falla → rollback completo, reportar el error con detalle.
```

### 5.3 Hooks adicionales para el módulo ADM

**Hook: verificar consistencia CC ↔ flujo de fondos**
```python
# scripts/hooks/verificar_consistencia.py
# Se dispara al cerrar un período mensual
import sys
from supabase import create_client

def verificar_consistencia(periodo: str):
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = sb.rpc('verificar_consistencia_periodo', {'p_periodo': periodo}).execute()
    diferencias = [r for r in result.data if abs(r['diferencia']) > 0.10]

    if diferencias:
        for d in diferencias:
            print(f'INCONSISTENCIA: {d["cliente"]} | CC={d["saldo_cc"]} | '
                  f'FF={d["saldo_ff"]} | Diff={d["diferencia"]}', file=sys.stderr)
        sys.exit(2)  # Bloquea la operación y manda error de vuelta a Claude

    print(f'CONSISTENCIA OK período {periodo}: {len(result.data)} clientes verificados')
```

---

## 6. Arquitectura del Sistema de Administración

El módulo ADM es una **aplicación web** usada desde cualquier dispositivo. Se integra con el módulo IVA a nivel de base de datos.

### 6.1 Decisión técnica: web app vs. desktop

**Recomendación: aplicación web full-stack.** Justificación:

| Criterio | Web (React + FastAPI) | Desktop | Ganador |
|----------|----------------------|---------|---------|
| Multiusuario simultáneo | Nativo — múltiples usuarios misma base | Complejo — requiere sincronización | **Web** |
| Acceso desde cualquier dispositivo | Sí — cualquier browser | Solo la máquina con el programa | **Web** |
| Perfiles de acceso | Row Level Security Supabase (operador/admin/consulta) | Implementación propia | **Web** |
| Exportación Excel/PDF | openpyxl + reportlab, descarga desde browser | Mismas libs, mismo esfuerzo | Empate |
| Despliegue y actualizaciones | Una vez en el servidor → todos actualizados | Cada PC | **Web** |
| Complejidad de desarrollo | Moderada con Claude Code | Similar | Empate |
| Seguridad credenciales | Supabase RLS + HTTPS + JWT | Más fácil hardcodear accidentalmente | **Web** |

### 6.2 Estructura del repositorio `larranaga-admin-agent`

```
larranaga-admin-agent/
├── backend/
│   ├── main.py                     # FastAPI app, CORS, auth
│   ├── routers/
│   │   ├── clientes.py             # CRUD clientes, CC, honorarios
│   │   ├── pagos.py                # Registrar cobros — impacto automático
│   │   ├── tesoreria.py            # Movimientos, egresos, control billetes
│   │   ├── profesionales.py        # Liquidaciones, adelantos, cierre mes
│   │   ├── socios.py               # Retiros, historial
│   │   ├── conciliacion.py         # Import extractos, matching, informe
│   │   └── informes.py             # Todos los reportes exportables
│   ├── services/
│   │   ├── honorarios.py           # Lógica fijo/producto
│   │   ├── liquidacion.py          # Liquidación profesional
│   │   ├── conciliacion.py         # Algoritmo de matching bancario
│   │   └── billetes.py             # Control de efectivo por denominación
│   ├── parsers/
│   │   ├── base_parser.py
│   │   ├── pampa_parser.py
│   │   ├── santander_parser.py
│   │   └── mercadopago_parser.py
│   └── db/
│       ├── schema.sql              # DDL completo Supabase
│       └── functions.sql           # RPCs: actualizar_saldo, agregar_adelanto…
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── CuentasCorrientes.tsx
│   │   │   ├── Tesoreria.tsx
│   │   │   ├── Liquidaciones.tsx
│   │   │   ├── ConciliacionBancaria.tsx
│   │   │   ├── FlujoDeFondos.tsx
│   │   │   └── Informes.tsx
│   │   └── components/
│   │       ├── RegistrarCobro.tsx         # Form multilínea (caso Gesualdo)
│   │       ├── ActualizarHonorarios.tsx   # Pantalla validación cuatrimestral
│   │       └── TablasConciliacion.tsx
├── tests/
│   ├── fixtures/
│   │   ├── clientes_test.json
│   │   └── extracto_pampa_feb2026.xlsx
│   ├── test_honorarios.py
│   ├── test_liquidacion.py
│   └── test_conciliacion.py
└── .claude/
    └── agents/
        ├── agente-honorarios.md
        └── agente-tesoreria.md
```

---

## 7. Puntos de Integración entre Módulo IVA y Módulo ADM

Los dos módulos comparten la **misma base de datos Supabase** y se complementan en puntos específicos.

| Punto de integración | Módulo IVA | Módulo ADM | Cómo se conectan |
|---------------------|-----------|-----------|------------------|
| **CUIT del proveedor** | El imputador (R-09) consulta padrón ARCA por CUIT para asignar cuenta | Clientes usan CUIT como identificador primario | Tabla compartida `maestro_proveedores` en Supabase |
| **Retenciones y percepciones** | R-05 clasifica percepciones del libro IVA compras | R-15 (conciliación) necesita identificar si un débito es percepción bancaria (SIRCREB) | Tabla `percepciones_clasificadas`. R-05 alimenta R-15 |
| **Conciliación bancaria** | Pagos de honorarios recibidos = créditos bancarios a conciliar | Pagos registrados en CC (R-07) son los registros contables que cruzan | La tabla `pagos` del ADM es **fuente de verdad** para créditos del extracto |
| **Posición IVA** | R-06 calcula IVA débito − crédito − percepciones | Flujo de fondos (R-11) necesita el IVA a pagar como egreso proyectado | `posicion_iva` escrita por R-06 y leída por flujo de fondos |
| **Clientes compartidos** | Clientes IVA (BUTALO, Gesualdo, etc.) = clientes ADM | ADM gestiona la CC de cada cliente | Tabla `clientes` compartida. Campo `cuit` es el identificador unificado |
| **Reportes consolidados** | Reporte IVA-MES (R-16) incluye posición fiscal | Informes de gestión (R-17) incluyen deuda y honorarios del mismo cliente | API de informes lee ambos módulos — vista integrada fiscal Y comercial |

---

## 8. n8n — Cuándo Usarlo vs. Cuándo Usar Código

**Principio general:** preferir **código (Python/JS)** sobre n8n para la lógica de negocio. n8n es mejor para **orquestación, scheduling y triggers simples**.

| Tarea | n8n o Código | Justificación |
|-------|--------------|---------------|
| Trigger: nuevo archivo en Google Drive (extracto bancario) | **n8n** | Trigger nativo. 0 código. Detecta archivo y llama al parser Python vía HTTP. |
| Trigger: schedule día 5 cada mes (procesar IVA todos los clientes) | **n8n** | Schedule nativo. Itera clientes y llama servicio Python. |
| Trigger: schedule día 15 y 25 (enviar reportes IVA-MES) | **n8n** | Schedule + Gmail node. Más rápido que código. |
| Lógica de clasificación retenciones (R-05) | **Python** | Lógica con tabla de mapeo. Tests unitarios. |
| Lógica de cálculo de honorarios (R-03) | **Python** | Cálculo determinístico con tipos fijo/producto. |
| Lógica de conciliación bancaria (R-15) | **Python** | Algoritmo de matching con tolerancias. Tests rigurosos. |
| Imputación contable con Claude API (R-09 nivel 4) | **Python** | Llamada a Claude con prompt contable estructurado. |
| Generación HWCRARCA (R-10) | **Python** | openpyxl con estilos y validación de cuadre. |
| Notificación Gmail: HWCRARCA listo | **n8n** | Gmail node nativo. |
| Registro de cobro de honorarios (R-08) | **Python + FastAPI** | Transacción con 5 impactos. Necesita rollback. Obligatorio. |
| Exportación informes a Excel/PDF (R-17) | **Python** | openpyxl + reportlab. Control fino del formato. |
| Webhook para que el frontend notifique un pago nuevo | **FastAPI** | Frontend llama a la API directamente. |

> **Regla práctica:** si la tarea tiene **lógica de negocio compleja, necesita tests, o involucra transacciones de BD → código Python**. Si es **trigger + HTTP + notificación → n8n**.

---

## 9. Preguntas Pendientes para la Segunda Reunión

| # | Pregunta | Módulo | Por qué es crítica |
|---|----------|--------|--------------------|
| 1 | ¿Qué formato exacto exporta el Banco Pampa? ¿.xlsx, .xls o PDF? ¿Columnas limpias o texto abreviado? | ADM | Define si el parser es trivial (Excel limpio) o necesita Claude Vision (PDF/abreviado). |
| 2 | ¿Qué módulos de Onvio ya están activos? ¿El importador de comprobantes ARCA de Onvio está en uso? | IVA | Si Onvio importa solo, generamos formato Onvio en lugar de HWCRARCA. Cambia R-10. |
| 3 | ¿Cuántos clientes tienen honorario tipo 'valor producto'? ¿Qué productos de referencia usan? | ADM | Define `productos_referencia`. Necesitamos lista completa y precios para fixtures. |
| 4 | ¿Los 3 bancos (Pampa, Santander, MP) están a nombre del estudio o de clientes? | ADM | Si son del estudio → conciliación tesorería. Si de clientes → lógica distinta. |
| 5 | ¿Los clientes de Larrañaga tienen cuenta en Interbanking? | ADM | Si sí → conciliación via API directa sin parseo. Simplifica mucho R-15. |
| 6 | ¿Cuánto tiempo tarda hoy registrar un cobro como el de Gesualdo (3 transferencias, 3 profesionales)? | ADM | Para ROI real. Si tarda 15 min, con el sistema 2 min — argumento comercial. |
| 7 | ¿Cómo determina el estudio el índice de actualización cuatrimestral? ¿IPC? ¿Interno? ¿Negociado? | ADM | Define si el sistema busca IPC (INDEC API) o el operador ingresa manual. |
| 8 | ¿Los socios (Pablo, Manuel, Marisol) cobran retiros regular o variable? ¿Hay fórmula? | ADM | Define si retiros es solo registro o también calcula el sugerido. |
| 9 | ¿Cuántos períodos históricos migrar? ¿Desde qué año? | ADM + IVA | Un mes es trivial. 3 años requiere migración robusta con validaciones. |
| 10 | ¿Preferencia de acceso del equipo? ¿Web browser o app de escritorio? | ADM | Confirmar decisión de web app. Si prefieren desktop, cambia el stack. |

---

*Documento preparado por el equipo de **Optimizar** — Uso interno — Abril 2026.*
