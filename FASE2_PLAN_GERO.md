# FASE 2 — Plan de implementación (Gero)
### Features: F2-02 · F2-04 · F2-05 · F2-06 · F2-11 · F2-12
**Fecha de planificación:** 2026-04-29

---

## Estado del codebase (punto de partida)

| Elemento | Estado |
|---|---|
| Modelo `Pago` | ✅ Existe con todos los campos requeridos |
| `POST /profesionales/pagos` | ✅ Ya crea pago + impacta CC — se mantiene intacto |
| `_build_liquidacion_out()` | ✅ Ya calcula `adelantos_percibidos` desde `Pago` |
| Tabla `control_billetes` | ❌ No existe |
| Directorio `backend/app/services/` | ❌ No existe |
| Router `routers/pagos.py` dedicado | ❌ No existe (pagos viven en `profesionales_adm.py`) |
| Endpoint `/liquidaciones/preview` | ❌ No existe |

---

## Orden de ejecución (por dependencias)

```
F2-05 ──────────────────────────────────────────────────► F2-06
                                                              │
F2-02 (skeleton) ──► F2-06 (integrar billetes) ─────────────┘
         │
         ├──────────────────────────────────────────────► F2-04 (frontend)
         │
         └──► F2-11 (liquidación extendida) ─────────────► F2-12 (frontend)
```

---

## BLOQUE A — F2-05: Control de Billetes
> Sin dependencias. Primer paso obligatorio.

### Objetivo
Tabla de stock de efectivo en caja por denominación + auditoría de movimientos.

### Denominaciones a contemplar
`$1.000 · $2.000 · $5.000 · $10.000 · $20.000`

### Archivos a modificar/crear
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/services/__init__.py` ← nuevo directorio
- `backend/app/services/billetes.py` ← nuevo
- `backend/app/routers/billetes.py` ← nuevo
- `backend/app/main.py`

### Detalle de implementación

#### models.py — agregar 2 tablas

```python
class ControlBillete(Base):
    __tablename__ = "control_billetes"
    id          = Column(Integer, primary_key=True)
    denominacion = Column(Integer, nullable=False, unique=True, index=True)
    cantidad    = Column(Integer, nullable=False, default=0)
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class MovimientoBillete(Base):
    __tablename__ = "movimientos_billetes"
    id          = Column(Integer, primary_key=True)
    denominacion = Column(Integer, nullable=False)
    delta       = Column(Integer, nullable=False)          # positivo=entrada, negativo=salida
    concepto    = Column(String(200), nullable=False)      # ej: "cobro_pago_42"
    pago_id     = Column(Integer, ForeignKey("pagos.id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
```

#### schemas.py — agregar

```python
BilleteOut(denominacion: int, cantidad: int, subtotal: float)
BilletesStockOut(billetes: list[BilleteOut], total_efectivo: float)
MovimientoBilleteCreate(denominacion: int, delta: int, concepto: str)
MovimientoBilleteOut(id, denominacion, delta, concepto, pago_id, created_at)
```

#### services/billetes.py — funciones

```python
DENOMINACIONES = [1000, 2000, 5000, 10000, 20000]

get_stock_all(db) -> dict[int, ControlBillete]
    # Devuelve {denominacion: ControlBillete} para las 5 denominaciones

aplicar_movimiento(db, denominacion, delta, concepto, pago_id=None)
    # Valida denominacion ∈ DENOMINACIONES
    # Actualiza ControlBillete.cantidad += delta
    # Si cantidad resultante < 0 → raise HTTPException(400, "Stock insuficiente")
    # Crea MovimientoBillete para auditoría
```

#### routers/billetes.py — endpoints

```
GET  /billetes/            → BilletesStockOut (stock actual de las 5 denominaciones)
POST /billetes/movimiento  → MovimientoBilleteOut (movimiento manual, solo admin)
```

#### main.py — cambios

```python
# En create_tables() / seed:
for denom in [1000, 2000, 5000, 10000, 20000]:
    if not db.query(ControlBillete).filter_by(denominacion=denom).first():
        db.add(ControlBillete(denominacion=denom, cantidad=0))
db.commit()

# Registrar router:
app.include_router(billetes_router, prefix="/api")
```

---

## BLOQUE B — F2-02: Endpoint dedicado POST /pagos/
> Depende de: F2-05 (services/billetes ya disponible)

### Objetivo
Router propio en `/pagos/` que registra un cobro y dispara impacto automático en la cuenta corriente del cliente. El endpoint existente `/profesionales/pagos` se mantiene intacto.

### Archivos a modificar/crear
- `backend/app/schemas.py`
- `backend/app/routers/pagos.py` ← nuevo
- `backend/app/main.py`

### Detalle de implementación

#### schemas.py — agregar

```python
class PagoCreateV2(BaseModel):
    cliente_id:              int
    honorario_id:            Optional[int] = None
    importe:                 float
    forma_pago:              FormaPago              # efectivo | transferencia
    profesional_destino_id:  Optional[int] = None
    fecha:                   date = Field(default_factory=date.today)
    fuente_pago:             Optional[str] = None
    banco_destino:           Optional[str] = None
    notas:                   Optional[str] = None
    # Solo cuando forma_pago = efectivo:
    billetes: Optional[dict[str, int]] = None
    # Ej: {"1000": 3, "5000": 2} → $3.000 + $10.000 = $13.000

class PagoImpactoOut(BaseModel):
    pago:              PagoOut
    movimiento_cc_id:  int
    saldo_cc_actual:   float
```

#### routers/pagos.py — endpoints

```
POST /pagos/       → PagoImpactoOut   (registrar cobro + impacto CC)
GET  /pagos/       → list[PagoOut]    (filtros: client_id, profesional_id, period)
GET  /pagos/{id}   → PagoOut          (detalle single)
```

#### Lógica de POST /pagos/

```
1. Validar cliente existe
2. Validar profesional_destino_id existe (si provisto)
3. Validar honorario_id existe y pertenece al cliente (si provisto)
4. Crear Pago(client_id, honorario_id, importe, forma_pago, profesional_destinatario_id,
             fecha, fuente_pago, banco_destino, notas)
5. db.flush() → obtener pago.id
6. Crear MovimientoCuentaCorriente(
       client_id, tipo="ingreso", monto=importe,
       concepto=f"Cobro honorario{' — '+fuente_pago if fuente_pago else ''}",
       fecha, forma_pago, profesional_id=profesional_destino_id
   )
7. Si forma_pago == efectivo y billetes present → [F2-06]
8. db.commit()
9. Calcular saldo CC actual (suma de movimientos del cliente)
10. Return PagoImpactoOut
```

---

## BLOQUE C — F2-06: Cobro en efectivo → actualizar billetes
> Depende de: F2-02 + F2-05

### Archivos a modificar
- `backend/app/routers/pagos.py`

### Lógica a agregar en POST /pagos/ (después del flush, antes del commit)

```python
if data.forma_pago == FormaPago.efectivo and data.billetes:
    total_billetes = sum(int(denom) * qty for denom, qty in data.billetes.items())
    if abs(total_billetes - data.importe) > 1:          # tolerancia ±$1
        raise HTTPException(422, detail={
            "error": "La suma de billetes no coincide con el importe",
            "total_billetes": total_billetes,
            "importe": data.importe,
            "diferencia": total_billetes - data.importe,
        })
    for denom_str, qty in data.billetes.items():
        if qty > 0:
            billetes_service.aplicar_movimiento(
                db, int(denom_str), qty,
                concepto=f"cobro_pago_{pago.id}",
                pago_id=pago.id
            )
```

---

## BLOQUE D — F2-11: Liquidación extendida con preview detallado
> Depende de: F2-02 (pagos reales en DB)

### Objetivo
Endpoint de preview que desglosa honorarios reales (desde tabla `honorarios`), adelantos cobrados (desde `pagos`), saldo anterior y reintegros, con listas de detalle por ítem.

**Diferencia clave respecto a lo existente:**
El campo `honorarios_totales` actual es ingresado manualmente por el admin. El nuevo endpoint calcula `honorarios_brutos` automáticamente sumando los registros de la tabla `Honorario` para los clientes asignados al profesional.

### Archivos a modificar/crear
- `backend/app/schemas.py`
- `backend/app/services/liquidacion.py` ← nuevo
- `backend/app/routers/profesionales_adm.py`

### schemas.py — agregar

```python
class HonorarioDetalleItem(BaseModel):
    cliente_id:     int
    cliente_nombre: str
    honorario_id:   int
    importe:        float
    tipo:           str      # "fijo" | "producto"

class AdelantoDetalleItem(BaseModel):
    pago_id:        int
    fecha:          date
    importe:        float
    forma_pago:     str
    fuente_pago:    Optional[str]
    cliente_nombre: str

class ReintegroDetalleItem(BaseModel):
    reintegro_id: int
    concepto:     str
    importe:      float

class LiquidacionPreviewOut(BaseModel):
    profesional_id:    int
    profesional_nombre: str
    periodo:           str      # YYYY-MM
    honorarios_brutos: float    # suma real de tabla honorarios
    adelantos_cobrados: float   # suma real de tabla pagos
    saldo_anterior:    float    # del cierre del mes anterior
    reintegros_total:  float
    total_a_cobrar:    float    # honorarios - adelantos + saldo_ant + reintegros
    detalle_honorarios: list[HonorarioDetalleItem]
    detalle_adelantos:  list[AdelantoDetalleItem]
    detalle_reintegros: list[ReintegroDetalleItem]
    cerrada:           bool
```

#### services/liquidacion.py — función principal

```python
def calcular_preview(db, profesional_id: int, periodo: str) -> LiquidacionPreviewOut:
    prof = db.get(Profesional, profesional_id)
    if not prof:
        raise HTTPException(404, "Profesional no encontrado")

    first, last = _period_bounds(periodo)

    # Honorarios brutos: clientes asignados al profesional con honorario en el período
    honorarios = db.query(Honorario).join(Client).filter(
        Client.profesional_id == profesional_id,
        Honorario.period == periodo,
    ).all()
    honorarios_brutos = sum(h.importe for h in honorarios)
    detalle_honorarios = [HonorarioDetalleItem(
        cliente_id=h.client_id, cliente_nombre=h.client.name,
        honorario_id=h.id, importe=h.importe, tipo=h.tipo
    ) for h in honorarios]

    # Adelantos: pagos donde este profesional es destinatario en el período
    pagos = db.query(Pago).filter(
        Pago.profesional_destinatario_id == profesional_id,
        Pago.fecha >= first, Pago.fecha <= last,
    ).all()
    adelantos_cobrados = sum(p.importe for p in pagos)
    detalle_adelantos = [...]

    # Saldo anterior del cierre del mes previo
    saldo_anterior = _get_saldo_anterior(db, profesional_id, periodo)

    # Reintegros de la liquidación del período (si existe)
    reintegros_total, detalle_reintegros = _get_reintegros(db, profesional_id, periodo)

    total_a_cobrar = honorarios_brutos - adelantos_cobrados + saldo_anterior + reintegros_total
    cerrada = _is_cerrada(db, profesional_id, periodo)

    return LiquidacionPreviewOut(...)
```

#### routers/profesionales_adm.py — agregar 2 endpoints

```
GET /profesionales/liquidaciones/{profesional_id}/preview?periodo=AAAAMM
    → LiquidacionPreviewOut (individual)

GET /profesionales/liquidaciones/preview?periodo=AAAAMM
    → list[LiquidacionPreviewOut] (batch: todos los profesionales activos)
```

> ⚠️ El endpoint batch debe registrarse ANTES del endpoint individual en el router para evitar que FastAPI interprete "preview" como un profesional_id.

---

## BLOQUE E — F2-04: Frontend Registrar Cobro
> Depende de: F2-02 backend

### Archivo nuevo: `frontend/src/pages/RegistrarCobro.jsx`

#### Campos del formulario
| Campo | Tipo | Notas |
|---|---|---|
| Cliente | Dropdown searchable | Filtra por clientes activos |
| Honorario | Dropdown | Se carga al seleccionar cliente; muestra período + importe |
| Importe | Number input | Formateado como moneda ARS |
| Fecha | Date picker | Default: hoy |
| Forma de pago | Toggle efectivo / transferencia | Radio visual |
| Profesional destinatario | Dropdown | Lista profesionales activos |
| Panel Billetes | Condicional | Solo visible cuando forma_pago = efectivo |

#### Panel de Billetes (detalle)
```
┌─────────────────────────────────────────────┐
│  Denominación │ Cantidad │    Subtotal       │
│  $ 1.000      │ [  3  ]  │    $ 3.000        │
│  $ 2.000      │ [  0  ]  │    $ 0            │
│  $ 5.000      │ [  2  ]  │    $ 10.000       │
│  $ 10.000     │ [  1  ]  │    $ 10.000       │
│  $ 20.000     │ [  0  ]  │    $ 0            │
├───────────────────────────────────────────── │
│  Total en billetes:         $ 23.000         │
│  Importe registrado:        $ 23.000  ✅     │
│  (muestra ⚠️ si difieren)                   │
└─────────────────────────────────────────────┘
```

#### Flujo de submit
```
1. Validar campos requeridos (cliente, importe, forma_pago, profesional_destino)
2. Si efectivo: validar suma billetes == importe (warn visual antes de enviar)
3. POST /pagos/ con { cliente_id, honorario_id, importe, forma_pago,
                       profesional_destino_id, fecha, billetes }
4. Success → toast "Cobro registrado" + reset formulario
5. Error → mostrar mensaje del backend (incluyendo detalle de billetes si 422)
```

### Archivos a modificar
- `frontend/src/utils/api.js` — agregar:
  - `registrarCobro(data)` → `POST /pagos/`
  - `getPagosRegistrados(params)` → `GET /pagos/`
  - `getBilletesStock()` → `GET /billetes/`
- `frontend/src/App.jsx` — agregar ruta `/cobros` → RegistrarCobro
- `frontend/src/components/Layout/Sidebar.jsx` — agregar ítem "Registrar Cobro"

---

## BLOQUE F — F2-12: Frontend Liquidaciones del mes
> Depende de: F2-11 backend

### Archivo nuevo: `frontend/src/pages/Liquidaciones.jsx`

#### Layout de la pantalla
```
┌──────────────────────────────────────────────────────────────────┐
│  Liquidaciones del mes    [Período: Abril 2026 ▼]               │
├────────────────┬──────────┬──────────┬──────────┬───────┬───────┤
│ Profesional    │ Hon. Br. │ Adelant. │ Saldo A. │ Rein. │ Total │
├────────────────┼──────────┼──────────┼──────────┼───────┼───────┤
│ ▶ García, J.   │ $120.000 │ $40.000  │ $5.000   │$2.000 │$87.000│  [Cerrar]
│   ▼ (expandido)│          │          │          │       │       │
│     Honorarios: Cliente A $60.000 · Cliente B $60.000           │
│     Adelantos:  12/04 efectivo $40.000 — Cliente A              │
│     Reintegros: Monotributo $2.000                               │
├────────────────┼──────────┼──────────┼──────────┼───────┼───────┤
│ ▶ López, M.    │ $90.000  │ $90.000  │ $0       │  $0   │ $0    │  CERRADO
├────────────────┼──────────┼──────────┼──────────┼───────┼───────┤
│ TOTALES        │ $210.000 │$130.000  │ $5.000   │$2.000 │$87.000│
└──────────────────────────────────────────────────────────────────┘
```

#### Modal "Cerrar período"
- Aparece al hacer click en botón "Cerrar" de una fila
- Campos: `Cobro en efectivo $` + `Cobro por transferencia $`
- Muestra: Total a cobrar (read-only), suma cobros ingresados, saldo que arrastra
- Botón "Confirmar cierre" → `POST /profesionales/liquidaciones/{id}/{period}/cerrar`
- Badge CERRADO aparece en la fila tras el cierre

### Archivos a modificar
- `frontend/src/utils/api.js` — agregar:
  - `getLiquidacionPreview(profesionalId, periodo)` → `GET /profesionales/liquidaciones/{id}/preview?periodo=X`
  - `getLiquidacionesPreviewAll(periodo)` → `GET /profesionales/liquidaciones/preview?periodo=X`
- `frontend/src/App.jsx` — agregar ruta `/liquidaciones` → Liquidaciones
- `frontend/src/components/Layout/Sidebar.jsx` — agregar ítem "Liquidaciones"

---

## TODO-LIST completa

### BLOQUE A — F2-05 Billetes
- [ ] A1. Agregar modelos `ControlBillete` y `MovimientoBillete` a `models.py`
- [ ] A2. Agregar schemas `BilleteOut`, `BilletesStockOut`, `MovimientoBilleteCreate`, `MovimientoBilleteOut` a `schemas.py`
- [ ] A3. Crear directorio `backend/app/services/` con `__init__.py`
- [ ] A4. Crear `backend/app/services/billetes.py` con `get_stock_all()` y `aplicar_movimiento()`
- [ ] A5. Crear `backend/app/routers/billetes.py` con `GET /billetes/` y `POST /billetes/movimiento`
- [ ] A6. Registrar router billetes y seedear `ControlBillete` (5 denominaciones, qty=0) en `main.py`

### BLOQUE B — F2-02 Router /pagos/
- [ ] B1. Agregar schema `PagoCreateV2` (incluye campo `billetes` opcional) y `PagoImpactoOut` a `schemas.py`
- [ ] B2. Crear `backend/app/routers/pagos.py` con skeleton `POST /pagos/`, `GET /pagos/`, `GET /pagos/{id}`
- [ ] B3. Implementar lógica completa de `POST /pagos/`: validaciones, crear `Pago`, crear `MovimientoCuentaCorriente` tipo ingreso, devolver `PagoImpactoOut` con saldo CC actualizado
- [ ] B4. Registrar router pagos con prefix `/pagos` en `main.py`

### BLOQUE C — F2-06 Integración efectivo → billetes
- [ ] C1. En `POST /pagos/`: validar que `sum(denom×qty) == importe` (±$1); devolver 422 con detalle si no coincide
- [ ] C2. En `POST /pagos/`: iterar `billetes` y llamar `services/billetes.aplicar_movimiento()` por cada denominación con qty > 0

### BLOQUE D — F2-11 Preview liquidación
- [ ] D1. Crear `backend/app/services/liquidacion.py` con `calcular_preview()`: suma honorarios por clientes del profesional, suma pagos del período, saldo anterior, reintegros, total_a_cobrar con listas de detalle
- [ ] D2. Agregar schemas `HonorarioDetalleItem`, `AdelantoDetalleItem`, `ReintegroDetalleItem`, `LiquidacionPreviewOut` a `schemas.py`
- [ ] D3. Agregar endpoint `GET /profesionales/liquidaciones/{profesional_id}/preview?periodo` a `profesionales_adm.py`
- [ ] D4. Agregar endpoint `GET /profesionales/liquidaciones/preview?periodo` (batch) a `profesionales_adm.py` — registrar ANTES del endpoint individual

### BLOQUE E — F2-04 Frontend Registrar Cobro
- [ ] E1. Agregar `registrarCobro()`, `getPagosRegistrados()` y `getBilletesStock()` a `frontend/src/utils/api.js`
- [ ] E2. Crear `frontend/src/pages/RegistrarCobro.jsx`: selectores de cliente, honorario, profesional; campos importe y fecha
- [ ] E3. Implementar toggle efectivo/transferencia y panel condicional de billetes con filas por denominación, subtotales y alerta de suma
- [ ] E4. Implementar submit: `POST /pagos/` + toast de éxito + reset del formulario
- [ ] E5. Agregar ruta `/cobros` → RegistrarCobro en `App.jsx` y nav item en `Sidebar.jsx`

### BLOQUE F — F2-12 Frontend Liquidaciones
- [ ] F1. Agregar `getLiquidacionPreview()`, `getLiquidacionesPreviewAll()` a `frontend/src/utils/api.js`
- [ ] F2. Crear `frontend/src/pages/Liquidaciones.jsx`: selector de período, tabla con columnas (Hon. Brutos, Adelantos, Saldo Ant., Reintegros, Total a Cobrar), badge CERRADO
- [ ] F3. Implementar fila expandible con detalle de honorarios por cliente, adelantos por pago y reintegros
- [ ] F4. Implementar botón "Cerrar período": modal con campos cobro_efectivo + cobro_transferencia → llama `cerrarLiquidacion` existente → refresca tabla
- [ ] F5. Agregar ruta `/liquidaciones` → Liquidaciones en `App.jsx` y nav item en `Sidebar.jsx`

---

## Decisiones de diseño

| Decisión | Justificación |
|---|---|
| `POST /pagos/` nuevo, no reemplaza `POST /profesionales/pagos` | Evita romper el frontend de Profesionales que ya usa la ruta existente |
| Preview calcula `honorarios_brutos` desde tabla `Honorario`, no desde campo manual | Cuadre automático sin intervención del admin |
| Endpoint batch `/liquidaciones/preview` registrado antes del individual | FastAPI matchea rutas en orden; "preview" sería interpretado como `profesional_id` si va después |
| Validación billetes con tolerancia ±$1 | Errores de redondeo por centavos no deben bloquear el cobro |
| `services/` extrae lógica pesada de los routers | Los routers quedan como controladores delgados; la lógica es testeable por separado |
