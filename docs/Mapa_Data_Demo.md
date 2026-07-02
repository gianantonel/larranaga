# Mapa de la data de demo — de dónde viene cada dato

Dataset generado por `seed_demo_dataset()` (backend/app/mock_data.py). Cubre **el mes
actual + 4 de historial** (incluye **Junio 2026**, el mes del guión). Todo está
conectado: el mismo honorario de un cliente aparece en su Cuenta Corriente y en la
Liquidación del profesional a cargo.

## La cadena (cómo se conecta todo)

```
CLIENTE  ──tiene──►  HONORARIO del mes (R-03)
   │                      │
   │                      ├──► se carga como DEUDA en su CUENTA CORRIENTE (R-07)  [egreso]
   │                      │
   │                      └──► suma al total del PROFESIONAL a cargo (R-04, Liquidaciones)
   │
   └──cobros──►  CUENTA CORRIENTE (R-07)  [ingreso]
                     │
                     └── si el cobro es por transferencia/cheque/USD (no efectivo)
                         ──► cuenta como ADELANTO del profesional  ──► le baja la liquidación
```

## Quién le factura a quién (cliente → profesional → honorario)

| Profesional a cargo | Cliente | Honorario mensual |
|---|---|---|
| Rodrigo Larrañaga | Hotel Patagonia | fijo $3.800.000 |
| Rodrigo Larrañaga | Constructora Pampas | producto: 50 × Bolsa de cemento ($4.600) = $230.000 |
| Rodrigo Larrañaga | Gianfranco Esteban Antonel | fijo $280.000 |
| Manuel Larrañaga | Agropecuaria El Alba S.R.L. | producto: 400 × Kilo de carne ($9.500) = $3.800.000 |
| Manuel Larrañaga | Logística del Sur | fijo $760.000 |
| Mariana Ruiz | Consultora TechBA | fijo $2.500.000 |
| Mariana Ruiz | Restaurante El Gaucho | fijo $850.000 |
| Mariana Ruiz | Panadería San Martín | fijo $680.000 |
| Marisol Borrego | Comercio García | fijo $180.000 |
| Silvana Gómez | Distribuidora Norte | fijo $950.000 |
| Stefania Vicente | Farmacia del Centro | fijo $1.200.000 |
| Stefania Vicente | Estudio Arq. López | fijo $430.000 |

## De dónde sale cada número en cada pantalla

### Honorarios (R-03)
- **Fijo**: es el `importe_honorario` del cliente (columna de la tabla de arriba).
- **Producto**: `cantidad × precio_vigente del producto`. Ej. Constructora Pampas =
  50 bolsas × $4.600 = $230.000. El precio sale de "Productos de referencia".

### Cuentas Corrientes (R-07) — Saldo
- **Saldo = suma de ingresos (cobros) − suma de egresos (cargos de honorarios)**.
- Cada mes se carga el honorario como **egreso** (deuda) y, si el cliente pagó, un
  **ingreso** (cobro). Meses pasados: casi todo pagado. Mes actual: mezcla
  pagado / parcial / sin pagar → por eso hay clientes con deuda y otros al día.
- **Cobros en USD**: el monto está en dólares y se convierte a pesos con la
  cotización cargada (`monto × cotización`).

### Liquidaciones (R-04) — Total a cobrar del profesional
Fórmula (la calcula el sistema, no está "escrita a mano"):

```
Total a cobrar = Honorarios brutos − Adelantos + Saldo anterior + Reintegros
```

- **Honorarios brutos** = suma de los honorarios de TODOS sus clientes ese mes
  (la tabla de arriba, filtrada por profesional).
- **Adelantos** = cobros que ese profesional ya recibió de sus clientes por
  transferencia / cheque / USD, cargados en Cuentas Corrientes.
- **Reintegros** = gastos reembolsables del profesional (monotributo, IIBB, etc.),
  cargados en su liquidación (aparecen en ~30% de los casos).
- **Estado** (Pagado / Parcial / Sin liquidar) = según cuánto se le pagó vs. el total.

## Ejemplo para rastrear en vivo (Rodrigo Larrañaga, Junio 2026)

- Honorarios brutos $4.310.000 = Hotel Patagonia $3.800.000 + Constructora Pampas
  $230.000 + Gianfranco $280.000.
- Menos adelantos $510.000 (cobros por transferencia de esos clientes en R-07).
- = Total a cobrar $3.830.000.

Podés abrir cada cliente en **Cuentas Corrientes** y ver el mismo honorario como cargo
y el cobro que se convirtió en ese adelanto.

## Notas

- **Junio 2026**: mes completo, mayormente pagado → ideal para mostrar.
- **Mes actual (Julio)**: estados "en vivo" (pagado / parcial / sin liquidar).
- Los movimientos de demo llevan una nota interna que empieza con `[demo]`.
- Lo que NO es de demo y se mantiene: usuarios/logins, colaboradores y sus
  asignaciones, IVA, facturación y tareas.
