# TODO — Plan Maestro Larrañaga (Optimizar)

Checklist oficial de implementación por fases. Referencia: [Plan Maestro](Plan_Maestro_de_Implementacion_Integral_Optimizar_para_Larrañaga.md).

Convención: marcar `[x]` al completar. Cada requerimiento (R-XX) corresponde a los documentos de requerimiento técnico del cliente.

---

## Fase 1 — Infra + Quick wins (sem 1–3)

- [x] **R-01 + R-02** Corrección tipo B/C + división alícuotas — *Dev 2, Python puro* ✓ `herramientas.py` + `Herramientas.jsx`
- [x] **R-05** Separación retenciones IVA vs IIBB — *Dev 1, AFIP SDK* ✓ `retenciones.py` + `Retenciones.jsx` (token AFIP cargado 2026-04-28)
- [x] **R-07** Cuentas corrientes — base de datos SQLite — *Dev 2* ✓ `cuentas_corrientes.py` + `CuentasCorrientes.jsx`
- [x] **R-03 + R-04** Cálculo honorarios + Liquidación profesionales — *Dev 2, Python puro* ✓ `honorarios.py` + `profesionales_adm.py` (versión Gero, integrada 2026-04-28)
- [ ] **Demo fin de fase**: procesar IVA de BUTALO SRL Feb 2026 punta a punta + registrar honorario de Juan Pérez con saldo en tiempo real.

## Fase 2 — Pipeline IVA + Tesorería (sem 4–6)

- [ ] **R-06** Conciliación IVA — posición mensual — *Dev 1, SDK*
- [ ] **R-09 + R-10** Imputación por CUIT + HWCRARCA completo — *Dev 2, Python + Claude API*
- [ ] **R-08** Tesorería con impacto automático — `registrar_cobro()` operativo — *Dev 2, Supabase*
- [ ] **R-14** Control de billetes / caja efectivo — *Dev 3, Supabase*

## Fase 3 — Conciliación bancaria + Flujo de fondos (sem 7–10)

- [ ] **R-15** Conciliación bancaria — parsers Pampa/Santander/MP + matching — *Dev 3, Python + Claude Vision*
- [ ] **R-11** Flujo de fondos — real vs proyectado — *Dev 2, Supabase*
- [ ] **R-12** Retiros de socios — *Dev 2, Supabase*
- [ ] **R-13** Actualización cuatrimestral de honorarios con pantalla de validación — *Dev 3, Python + React*

## Fase 4 — Reportes, IVA-MES e integración total (sem 11–15)

- [ ] **R-16 + R-19** Reportes IVA-MES automáticos + Consulta ARCA — *Dev 1, SDK*
- [ ] **R-17** Informes de gestión — todos los reportes ADM — *Dev 2, Python + React*
- [ ] **R-20** Migración histórica Excel → Supabase — *todos, Python + pandas*
- [ ] **R-18** MVP liquidación de impuestos + VEPs — *Dev 1, SDK*
