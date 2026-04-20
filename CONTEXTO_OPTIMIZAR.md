# Contexto Optimizar — Equipo y proyecto

Este documento fija el contexto que el equipo de **Optimizar** comparte para el proyecto **Larrañaga y Asociados**. Sirve de onboarding para cualquier colaborador o agente de IA que abra el repo.

## Empresa

**Optimizar** (también llamada **Optimizar IA**) es la empresa desarrolladora a cargo de este proyecto. Cuando en documentación, commits o PRs se dice "nosotros" o "el equipo", se refiere a Optimizar.

## Cliente

**Estudio Larrañaga y Asociados** — Santa Rosa, La Pampa.
Estudio contable argentino que necesita gestionar facturación ARCA, IVA, DDJJ, Ingresos Brutos, cuentas corrientes, tesorería, conciliación bancaria y liquidación de profesionales de sus clientes.

## Principio rector

**"Carga única — impacto automático en todos los módulos."** Un cobro de honorarios impacta simultáneamente: CC cliente + tesorería + liquidación profesional + control billetes (si efectivo) + cola conciliación (si transferencia). Si uno falla → **rollback completo**.

## Equipo (3 devs)

| Dev | Foco |
|-----|------|
| Dev 1 | AFIP/SDK, retenciones, VEPs, n8n, infra CI/CD |
| Dev 2 | IVA/contabilidad, HWCRARCA, backend ADM (honorarios, tesorería, flujo fondos) |
| Dev 3 | Parsers bancarios, conciliación, frontend React |

## Plan por fases

Cada fase dura 3–4 semanas y combina IVA + ADM para entregar valor visible al cliente. Detalle completo: [Plan Maestro](Plan_Maestro_de_Implementacion_Integral_Optimizar_para_Larrañaga.md). Checklist operativo: [TODO.md](TODO.md).

## Documentos clave del repo

- [AGENTS.md](AGENTS.md) — guía para agentes de IA (Claude Code, subagentes, SDK).
- [Plan Maestro](Plan_Maestro_de_Implementacion_Integral_Optimizar_para_Larrañaga.md) — fases oficiales Optimizar.
- [Requerimiento IVA](Requerimiento%20T%C3%A9cnico%20IVA%20Larra%C3%B1aga.md) — del cliente, módulo IVA Compras.
- [Requerimiento Admin y Tesorería](Requerimiento%20T%C3%A9cnico%20Admin%20y%20Tesorer%C3%ADa%20Larra%C3%B1aga.md) — del cliente, módulo ADM.
- [afip_sdk.md](afip_sdk.md) — integración AFIP SDK.
- [.claude/skills/afip-sdk-actions/SKILL.md](.claude/skills/afip-sdk-actions/SKILL.md) — skill Claude Code para AFIP.

## Reglas de oro

1. **Carga única → impacto automático** (ver principio rector).
2. **Consistencia CC ↔ flujo de fondos**: diff > $0.10 → alerta, no continuar.
3. **Credenciales** cifradas con Fernet en Supabase; nunca en logs ni código.
4. **Tipo B** no toma IVA (los C sí con Neto+IVA=0, total en AD).
5. **HWCRARCA**: validar Debe = Haber antes de escribir.
6. **Actualización cuatrimestral**: nunca masiva; pantalla de validación por cliente.
7. **Dev por defecto**: `AFIP_ENV=dev` + CUIT `20409378472`. Prod sólo con cert cargado.
8. **Tests mockean AFIP**: ningún test CI golpea SDK real.
