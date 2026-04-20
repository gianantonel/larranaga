# AGENTS.md — Proyecto Larrañaga × Optimizar

Este archivo es la **guía de agentes de IA** (Claude Code, subagentes, agentes SDK) para el repo del proyecto Larrañaga. Léelo al iniciar cualquier tarea en este repo.

---

## Contexto del proyecto

- **Cliente:** Estudio Larrañaga y Asociados — Santa Rosa, La Pampa.
- **Empresa desarrolladora:** **Optimizar** (nosotros).
- **Objetivo:** automatizar el estudio contable en dos frentes:
  - **Módulo IVA / Contabilidad:** preparación de IVA Compras/Ventas, HWCRARCA para Holistor/Onvio, reportes IVA-MES, VEPs.
  - **Módulo Administración / Tesorería:** cuentas corrientes, tesorería, conciliación bancaria, liquidación profesionales, flujo de fondos, retiros socios.
- **Principio rector:** **"Carga única — impacto automático en todos los módulos"**.

## Documentos de referencia (leer antes de codear)

| Archivo | Para qué |
|---------|----------|
| `Requerimiento Técnico Admin y Tesorería Larrañaga.md` | Requerimiento del cliente para el módulo ADM |
| `Requerimiento Técnico IVA Larrañaga.md` | Requerimiento del cliente para el módulo IVA Compras |
| `Plan_Maestro_de_Implementacion_Integral_Optimizar_para_Larrañaga.md` | **Plan de fases y tareas oficiales de Optimizar** — leer siempre antes de elegir qué hacer |
| `afip_sdk.md` | Cómo usar AFIP SDK (REST + Python) en el proyecto |
| `afip_dev_credentials.txt` | CUIT de prueba 20-40937847-2 para dev |
| `.claude/skills/afip-sdk-actions/SKILL.md` | Skill Claude Code con patrones de integración AFIP SDK |

## Stack tecnológico

- **Backend:** Python 3.12 + FastAPI.
- **Base de datos:** Supabase (PostgreSQL) con Row Level Security.
- **Frontend:** React + TypeScript.
- **Procesamiento:** pandas + openpyxl (IVA, extractos), reportlab (PDF).
- **IA clasificación:** Claude API Sonnet (imputación contable, categorización de movimientos bancarios no identificados).
- **AFIP:** AFIP SDK (https://app.afipsdk.com) — web services + automatizaciones.
- **Orquestación:** n8n para schedules, triggers de Drive y envío de mails.
- **Archivos:** Google Drive.
- **Credenciales de clientes:** tabla cifrada Supabase (Fernet) — nunca en logs ni código.

## Repositorios del proyecto (5)

| Repo | Responsable | Contenido |
|------|-------------|-----------|
| `larranaga-core` | Dev 1 | Schema Supabase, RPCs, libs compartidas, CI/CD |
| `larranaga-arca-agent` | Dev 1 | Integración AFIP SDK — retenciones, comprobantes, padrón, VEPs |
| `larranaga-accounting-agent` | Dev 2 | Transformaciones IVA (B/C, alícuotas), imputación, HWCRARCA |
| `larranaga-admin-agent` | Dev 2 + Dev 3 | Backend FastAPI + frontend React del módulo ADM completo |
| `larranaga-banking-agent` | Dev 3 | Parsers bancarios (Pampa, Santander, MP) + algoritmo de conciliación |
| `larranaga-n8n-flows` | Dev 1 | Workflows n8n (schedules, triggers, mails) |
| `larranaga-reports` | Dev 2 | Generación de informes Excel/PDF y Google Docs IVA-MES |

## Plan por fases (oficial Optimizar)

Cada fase dura **3–4 semanas** y combina requerimientos de IVA **y** ADM. El cliente recibe valor visible en cada entrega.

### Fase 1 — Infra + Quick wins (sem 1–3)
- **R-01 + R-02** Corrección B/C + División alícuotas (Dev 2, Python puro)
- **R-05** Separación retenciones IVA vs IIBB (Dev 1, SDK)
- **R-07** Cuentas corrientes — base de datos (Dev 2, Supabase)
- **R-03 + R-04** Cálculo honorarios + Liquidación profesionales (Dev 2, Python puro)
- **Demo:** procesar IVA de BUTALO SRL Feb 2026 de punta a punta + registrar honorario de Juan Pérez con saldo en tiempo real.

### Fase 2 — Pipeline IVA + Tesorería (sem 4–6)
- **R-06** Conciliación IVA — posición mensual (Dev 1, SDK)
- **R-09 + R-10** Imputación CUIT + HWCRARCA completo (Dev 2, Python + Claude API)
- **R-08** Tesorería con impacto automático (Dev 2, Supabase) — `registrar_cobro()` operativo
- **R-14** Control de billetes / caja efectivo (Dev 3, Supabase)

### Fase 3 — Conciliación bancaria + Flujo de fondos (sem 7–10)
- **R-15** Conciliación bancaria — parsers Pampa/Santander/MP + matching (Dev 3, Python + Claude Vision)
- **R-11** Flujo de fondos — real vs proyectado (Dev 2, Supabase)
- **R-12** Retiros de socios (Dev 2, Supabase)
- **R-13** Actualización cuatrimestral de honorarios con pantalla de validación (Dev 3, Python + React)

### Fase 4 — Reportes, IVA-MES e integración total (sem 11–15)
- **R-16 + R-19** Reportes IVA-MES automáticos + Consulta ARCA (Dev 1, SDK)
- **R-17** Informes de gestión — todos los reportes ADM (Dev 2, Python + React)
- **R-20** Migración histórica Excel → Supabase (todos, Python + pandas)
- **R-18** MVP liquidación de impuestos + VEPs (Dev 1, SDK)

## Subagentes Claude Code disponibles

| Subagente | Repo | Función |
|-----------|------|---------|
| `agente-retenciones` | arca-agent | Clasifica percepciones/retenciones ARCA por régimen |
| `agente-conciliacion-iva` | arca-agent | Calcula posición IVA del mes |
| `agente-iva-mes` | arca-agent | Descarga comprobantes mensuales y genera reporte |
| `agente-veps` | arca-agent | Genera VEPs desde DDJJ |
| `agente-hwcrarca` | accounting-agent | Genera archivo HWCRARCA con validación Debe=Haber |
| `agente-honorarios` | admin-agent | Calcula honorarios fijo/producto + actualización cuatrimestral |
| `agente-tesoreria` | admin-agent | Registra cobros verificando los 5 impactos automáticos |
| `agente-liquidacion-prof` | admin-agent | Calcula liquidación mensual de cada profesional |
| `agente-parsers-bancos` | banking-agent | Parsea extractos de Pampa/Santander/MP |
| `agente-conciliacion-bancaria` | banking-agent | Matching entre extracto y movimientos registrados |
| `agente-migracion` | core | Migra datos históricos desde Excel |

## Reglas de oro para agentes

1. **Carga única — impacto automático.** Un cobro de honorarios SIEMPRE impacta: CC cliente + tesorería + liquidación profesional + control billetes (si efectivo) + cola conciliación (si transferencia). Si uno falla → **rollback completo**.
2. **Consistencia CC ↔ flujo de fondos.** `saldo_cuenta_corriente_cliente == deuda_en_flujo_fondos`. Si difieren >$0.10 → alerta inmediata, no continuar.
3. **Credenciales.** Nunca loguear AFIP access token ni clave fiscal del cliente. Se desencriptan solo en runtime dentro del request.
4. **Tipo B.** Los comprobantes tipo **B no se toman en IVA** (los C sí, con Neto+IVA=0 y total en AD).
5. **HWCRARCA.** Antes de escribir al disco, validar **Debe = Haber** contable.
6. **Actualización cuatrimestral.** Nunca masiva/automática — siempre con pantalla de validación individual por cliente.
7. **Dev por defecto.** `AFIP_ENV=dev` + CUIT `20409378472` para pruebas. `prod` solo por cliente real con certificado cargado.
8. **Tests mockean AFIP.** Ningún test de CI debe golpear el SDK real.

## Flujo de trabajo

1. **Antes de empezar una tarea**: identificar a qué requerimiento (R-XX) pertenece en el Plan Maestro y qué fase es.
2. **Leer** el requerimiento técnico del cliente correspondiente al módulo.
3. **Consultar** `afip_sdk.md` si la tarea toca AFIP.
4. **Activar el subagente apropiado** o el skill `afip-sdk-actions` si aplica.
5. **Escribir código + tests** en el repo correspondiente.
6. **Validar consistencia** antes de mergear (regla 2).
7. **Actualizar el todo list** y marcar tareas completadas una a una, no en batch.

---

*Equipo Optimizar — Proyecto Larrañaga y Asociados — Abril 2026.*
