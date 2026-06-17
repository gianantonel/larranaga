"""F3-12 (R-15): Sugerencia con Claude API para movimientos bancarios sin match.

Si `ANTHROPIC_API_KEY` está seteada, usa Claude para refinar el ranking de
candidatos heurístico devuelto por `sugerir_candidatos()`. Si no, devuelve
los candidatos heurísticos sin tocar.

El prompt está estructurado y devuelve JSON con:
    [{"pago_id": int, "score_ai": float, "razonamiento": str}]
"""
from __future__ import annotations

import json
import os
from typing import Any

from sqlalchemy.orm import Session

from .. import models
from . import conciliacion as svc


# Modelo y prompt config
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_TOKENS = 800
MAX_CANDIDATOS_AI = 5  # Sólo enviamos los top N a Claude


def _client():
    """Devuelve cliente Anthropic si la API key está disponible, sino None."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=key)
    except ImportError:
        return None


SYSTEM_PROMPT = """Sos un asistente especializado en conciliación bancaria de un estudio contable argentino.

Te paso un movimiento bancario sin conciliar y una lista de pagos candidatos. Tu tarea es:
1. Analizar la descripción del movimiento (puede contener nombre de empresa, CUIT, referencia)
2. Comparar contra cada candidato (cliente, importe, fecha)
3. Devolver un JSON array con los candidatos ordenados por probabilidad de match

Reglas:
- Usá el contexto: nombres de empresas, CUITs en la descripción, fechas cercanas, importes idénticos
- Si la descripción menciona "TRANSF DE [empresa]", priorizá clientes cuyo nombre coincida
- Si hay un CUIT en la descripción, priorizá clientes con ese CUIT
- score_ai entre 0 y 1
- razonamiento: una frase corta explicando por qué (en castellano)

Respondé EXCLUSIVAMENTE con el JSON array, sin texto adicional.
Formato: [{"pago_id": int, "score_ai": float, "razonamiento": "string"}]
"""


def _build_user_message(mov: models.MovimientoBancario, candidatos: list[dict[str, Any]]) -> str:
    cands_str = "\n".join(
        f"- pago_id={c['pago_id']} | cliente={c.get('client_name')} | "
        f"importe=${c['importe']:.2f} | fecha={c['fecha']} | score_heuristico={c['score']}"
        for c in candidatos
    )
    return f"""Movimiento bancario sin conciliar:
- Descripción: {mov.descripcion}
- Importe: ${mov.importe:.2f}
- Fecha: {mov.fecha.isoformat()}
- CUIT detectado: {mov.cuit_detectado or '(ninguno)'}
- Tipo: {mov.tipo} ({'crédito' if mov.tipo == 'C' else 'débito'})

Candidatos:
{cands_str}

Devolveme el JSON ordenado por score_ai descendente."""


def sugerir_con_ai(db: Session, movimiento_id: int, top_n: int = 3) -> list[dict[str, Any]]:
    """Sugiere candidatos refinados por Claude API. Fallback heurístico si no hay API key."""
    candidatos = svc.sugerir_candidatos(db, movimiento_id, top_n=MAX_CANDIDATOS_AI)
    if not candidatos:
        return []

    client = _client()
    if client is None:
        # Sin API key — devolver heurístico
        return candidatos[:top_n]

    mov = db.get(models.MovimientoBancario, movimiento_id)
    if not mov:
        return []

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_message(mov, candidatos)}],
        )
        text = resp.content[0].text.strip()
        # Claude a veces envuelve en ```json ... ``` — limpiamos
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(l for l in lines if not l.startswith("```"))
        ai_results = json.loads(text)
    except Exception as e:
        # Si falla la AI, devolvemos heurístico con nota
        return [{**c, "razonamiento": f"(AI no disponible: {e.__class__.__name__})"} for c in candidatos[:top_n]]

    # Cruzar AI results con candidatos heurísticos para preservar metadata
    by_id = {c["pago_id"]: c for c in candidatos}
    out = []
    for r in ai_results[:top_n]:
        pid = r.get("pago_id")
        if pid in by_id:
            out.append({
                **by_id[pid],
                "score_ai": float(r.get("score_ai", 0.0)),
                "razonamiento": r.get("razonamiento", ""),
            })
    return out or candidatos[:top_n]
