"""F3-05 (R-15): Algoritmo de matching automático para movimientos bancarios.

Recorre los movimientos sin conciliar de un extracto e intenta cruzar contra:
- Créditos: Pagos registrados (preferentemente con CUIT detectado)
- Débitos: Retiros de socios o egresos manuales (no implementado aún)
- Comisiones bancarias / débitos automáticos: por palabras clave en descripción

Output:
    {
      "extracto_id": int,
      "matched": [{movimiento_bancario_id, pago_id, tipo_match, score}],
      "pending": [movimiento_bancario_id, ...],
      "stats": {
        "total": int, "auto": int, "manual_required": int,
        "by_type": {"credito_cuit": int, "credito_importe": int, ...}
      }
    }
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from .. import models


# ─── Tolerancias ─────────────────────────────────────────────────────────────

IMPORTE_TOL_ABS = 1.0          # ±$1 — tolerancia absoluta
IMPORTE_TOL_REL = 0.001        # ±0.1% — para importes muy grandes
FECHA_TOL_DIAS = 1             # ±1 día

# Palabras clave para clasificar débitos automáticos / comisiones
KEYWORDS_COMISION_BANCARIA = ("COM.", "COMISION", "MANT.", "MANTENIMIENTO", "IMP.", "IMPUESTO", "IIBB", "DEBITO BANCARIO")
KEYWORDS_SERVICIOS = ("CBU", "SERV", "SEPA", "SERVICIO PUBLICO")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _importe_match(a: float, b: float) -> bool:
    """Retorna True si `a` y `b` son iguales con tolerancia (abs $1 o rel 0.1%)."""
    diff = abs(a - b)
    if diff <= IMPORTE_TOL_ABS:
        return True
    rel = diff / max(abs(a), abs(b), 1.0)
    return rel <= IMPORTE_TOL_REL


def _fecha_dentro(fecha_mov: date, fecha_pago: date, tol_dias: int = FECHA_TOL_DIAS) -> bool:
    return abs((fecha_mov - fecha_pago).days) <= tol_dias


def _has_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    if not text:
        return False
    upper = text.upper()
    return any(k in upper for k in keywords)


# ─── Matchers ────────────────────────────────────────────────────────────────

def _match_credito_a_pago(
    db: Session,
    mov: models.MovimientoBancario,
) -> Optional[tuple[int, str, float]]:
    """Intenta matchear un crédito (entrada) contra un Pago de cliente.

    Retorna (pago_id, tipo_match, score) si encuentra match, sino None.
    Tipos: 'credito_cuit_exacto', 'credito_cuit_aprox', 'credito_importe'.
    """
    # Estrategia 1: si el movimiento tiene CUIT detectado, buscar pagos del cliente con ese CUIT
    if mov.cuit_detectado:
        cliente = db.query(models.Client).filter_by(cuit=mov.cuit_detectado).first()
        if cliente:
            candidatos = (
                db.query(models.Pago)
                .filter(
                    models.Pago.client_id == cliente.id,
                    models.Pago.fecha >= mov.fecha - timedelta(days=FECHA_TOL_DIAS),
                    models.Pago.fecha <= mov.fecha + timedelta(days=FECHA_TOL_DIAS),
                    models.Pago.forma_pago == "transferencia",
                )
                .all()
            )
            for p in candidatos:
                if _importe_match(mov.importe, p.importe):
                    score = 1.0 if mov.fecha == p.fecha else 0.85
                    tipo = "credito_cuit_exacto" if mov.fecha == p.fecha else "credito_cuit_aprox"
                    # Verificar que ese pago no esté ya conciliado
                    if not db.query(models.MovimientoBancario).filter_by(pago_id=p.id, conciliado=True).first():
                        return (p.id, tipo, score)

    # Estrategia 2: buscar por importe + fecha exacta (sin CUIT)
    candidatos = (
        db.query(models.Pago)
        .filter(
            models.Pago.fecha == mov.fecha,
            models.Pago.forma_pago == "transferencia",
        )
        .all()
    )
    for p in candidatos:
        if _importe_match(mov.importe, p.importe):
            if not db.query(models.MovimientoBancario).filter_by(pago_id=p.id, conciliado=True).first():
                return (p.id, "credito_importe_fecha_exacta", 0.7)

    return None


def _match_debito_comision(mov: models.MovimientoBancario) -> Optional[tuple[str, float]]:
    """Detecta si un débito es una comisión bancaria por keywords. Retorna (categoria, score)."""
    if _has_keyword(mov.descripcion, KEYWORDS_COMISION_BANCARIA):
        return ("comision_bancaria", 0.6)
    if _has_keyword(mov.descripcion, KEYWORDS_SERVICIOS):
        return ("debito_automatico", 0.5)
    return None


# ─── Pipeline principal ──────────────────────────────────────────────────────

def correr_matching(db: Session, extracto_id: int) -> dict[str, Any]:
    """Ejecuta el matching automático sobre todos los movimientos pendientes de un extracto.

    Persiste los matches encontrados (marca `conciliado=True` y vincula `pago_id`).
    Devuelve stats.
    """
    extracto = db.get(models.ExtractoBancario, extracto_id)
    if not extracto:
        raise ValueError(f"Extracto {extracto_id} no encontrado")

    movimientos = (
        db.query(models.MovimientoBancario)
        .filter_by(extracto_id=extracto_id, conciliado=False)
        .all()
    )

    stats: dict[str, int] = {
        "credito_cuit_exacto": 0,
        "credito_cuit_aprox": 0,
        "credito_importe_fecha_exacta": 0,
        "comision_bancaria": 0,
        "debito_automatico": 0,
    }
    matched: list[dict[str, Any]] = []
    pending: list[int] = []

    for mov in movimientos:
        if mov.tipo == "C":  # crédito
            res = _match_credito_a_pago(db, mov)
            if res:
                pago_id, tipo, score = res
                mov.pago_id = pago_id
                mov.conciliado = True
                mov.notas = f"auto-matched: {tipo} (score {score})"
                stats[tipo] = stats.get(tipo, 0) + 1
                matched.append({
                    "movimiento_bancario_id": mov.id,
                    "pago_id": pago_id,
                    "tipo_match": tipo,
                    "score": score,
                })
                continue

        elif mov.tipo == "D":  # débito
            res = _match_debito_comision(mov)
            if res:
                categoria, score = res
                mov.notas = f"auto-categoria: {categoria} (score {score})"
                # No conciliamos automáticamente — sólo categorizamos
                stats[categoria] = stats.get(categoria, 0) + 1

        pending.append(mov.id)

    # Forzar flush para que la query siguiente cuente los cambios pendientes
    db.flush()

    # Actualizar contadores del extracto
    n_conciliados = (
        db.query(models.MovimientoBancario)
        .filter_by(extracto_id=extracto_id, conciliado=True)
        .count()
    )
    extracto.n_conciliados = n_conciliados
    extracto.n_pendientes = extracto.n_movimientos - n_conciliados

    db.commit()

    return {
        "extracto_id": extracto_id,
        "matched": matched,
        "pending": pending,
        "stats": {
            "total": len(movimientos),
            "auto": len(matched),
            "manual_required": len(pending),
            "by_type": stats,
        },
    }


def sugerir_candidatos(
    db: Session, movimiento_id: int, top_n: int = 3
) -> list[dict[str, Any]]:
    """Para un movimiento pendiente, sugiere los top N pagos candidatos.

    Útil para la UI de conciliación manual (F3-07/F3-08).
    """
    mov = db.get(models.MovimientoBancario, movimiento_id)
    if not mov:
        return []

    if mov.tipo != "C":
        return []  # Sólo soportamos sugerencias para créditos por ahora

    # Buscar pagos no conciliados, ordenados por similitud de importe + cercanía de fecha
    pagos = (
        db.query(models.Pago)
        .filter(models.Pago.forma_pago == "transferencia")
        .all()
    )
    # Excluir los ya conciliados
    pago_ids_conciliados = {
        m.pago_id for m in db.query(models.MovimientoBancario).filter(
            models.MovimientoBancario.pago_id.isnot(None),
            models.MovimientoBancario.conciliado.is_(True),
        ).all()
    }
    pagos = [p for p in pagos if p.id not in pago_ids_conciliados]

    def _score(p: models.Pago) -> float:
        importe_diff = abs(mov.importe - p.importe)
        importe_score = max(0.0, 1.0 - importe_diff / max(mov.importe, 1.0))
        fecha_diff = abs((mov.fecha - p.fecha).days)
        fecha_score = max(0.0, 1.0 - fecha_diff / 30.0)
        cuit_score = 1.0 if (mov.cuit_detectado and p.client and p.client.cuit == mov.cuit_detectado) else 0.0
        return 0.5 * importe_score + 0.3 * fecha_score + 0.2 * cuit_score

    pagos_ranked = sorted(pagos, key=_score, reverse=True)[:top_n]
    return [
        {
            "pago_id": p.id,
            "client_id": p.client_id,
            "client_name": p.client.name if p.client else None,
            "importe": p.importe,
            "fecha": p.fecha.isoformat(),
            "score": round(_score(p), 3),
        }
        for p in pagos_ranked
    ]
