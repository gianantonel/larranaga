"""Precios de referencia del día desde fuentes externas (para R-03, productos).

Fuente principal: **Cámara Arbitral de Cereales de la Bolsa de Comercio de Rosario**
(pizarra de granos), que publica el precio del día por tonelada en pesos.

Todo es *best-effort*: si la fuente no responde o cambia el HTML, se devuelve
`disponible=False` y la UI cae a la carga manual (nunca rompe). Cache en memoria de
30 min para no pegarle a la fuente en cada request.
"""
from __future__ import annotations

import re
import time
from typing import Optional

import httpx

# Fuentes soportadas: clave estable -> (etiqueta visible, término a buscar en la pizarra)
FUENTES_BCR = {
    "bcr_soja":    ("Soja · Bolsa de Rosario",    "Soja"),
    "bcr_maiz":    ("Maíz · Bolsa de Rosario",    "Maíz"),
    "bcr_trigo":   ("Trigo · Bolsa de Rosario",   "Trigo"),
    "bcr_girasol": ("Girasol · Bolsa de Rosario", "Girasol"),
    "bcr_sorgo":   ("Sorgo · Bolsa de Rosario",   "Sorgo"),
}
FUENTES = dict(FUENTES_BCR)  # espacio para sumar MAG (hacienda) en el futuro

_PIZARRA_URL = "https://www.cac.bcr.com.ar/es/precios-de-pizarra"
_CACHE_TTL = 1800  # 30 min
_cache: dict = {"ts": 0.0, "precios": {}}


def fuentes_disponibles() -> list[dict]:
    """Lista de fuentes para poblar el selector del front."""
    return [{"clave": k, "label": v[0]} for k, v in FUENTES.items()]


def _parse_pizarra(html: str) -> dict:
    """Extrae {término: precio_float} de la pizarra. Precio en formato '$475.000,00'."""
    precios: dict[str, float] = {}
    for _clave, (_label, termino) in FUENTES_BCR.items():
        idx = html.find(termino)
        if idx < 0:
            continue
        m = re.search(r"\$\s?([\d.]+,\d{2})", html[idx: idx + 240])
        if not m:
            continue
        crudo = m.group(1).replace(".", "").replace(",", ".")
        try:
            precios[termino] = round(float(crudo), 2)
        except ValueError:
            continue
    return precios


def _pizarra_precios() -> dict:
    """Precios de la pizarra BCR con cache de 30 min."""
    ahora = time.time()
    if _cache["precios"] and (ahora - _cache["ts"] < _CACHE_TTL):
        return _cache["precios"]
    resp = httpx.get(_PIZARRA_URL, timeout=10.0, follow_redirects=True,
                     headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    precios = _parse_pizarra(resp.text)
    if precios:
        _cache["precios"] = precios
        _cache["ts"] = ahora
    return precios


def precio_sugerido(fuente: str) -> dict:
    """Devuelve el precio sugerido del día para una fuente. Nunca lanza: ante error
    devuelve {disponible: False, ...} para que la UI use carga manual."""
    if fuente not in FUENTES:
        return {"disponible": False, "error": f"fuente desconocida: {fuente}"}
    label, termino = FUENTES[fuente]
    try:
        precios = _pizarra_precios()
        precio = precios.get(termino)
        if precio is None:
            return {"disponible": False, "fuente": label,
                    "error": "la fuente no publicó precio para este producto hoy"}
        return {"disponible": True, "fuente": label, "precio": precio,
                "unidad": "tonelada", "moneda": "ARS"}
    except Exception as e:  # noqa: BLE001 — best effort, la UI sigue con carga manual
        return {"disponible": False, "fuente": label, "error": str(e)[:200]}
