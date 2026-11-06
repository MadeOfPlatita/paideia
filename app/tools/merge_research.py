"""Incorpora al catálogo condiciones documentadas en una investigación externa.

Entrada: un JSON con {"products": [{"candidate_id", "conditions": [...]}]} donde
cada condición trae metric (clave en español de la transcripción), value,
value_literal, source_url, source_title y accessed. Solo se añaden métricas que
el registro no tenga ya: nunca se sobrescribe un dato existente ni se rellena un
hueco sin fuente. Si una condición no trae URL, se descarta y se informa.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
APP = Path(__file__).resolve().parents[1]
CATALOGO = APP / "data" / "condiciones.json"
sys.path.insert(0, str(APP))
from catalogue_conditions import DOCUMENTED_METRICS  # noqa: E402


def unidad(metric: str) -> str:
    return DOCUMENTED_METRICS.get(metric, (metric, "TEXT"))[1]


def normaliza(valor):
    """El catálogo guarda literales de texto: la proyección valida cadenas."""
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    if isinstance(valor, float):
        return str(valor)
    if isinstance(valor, int):
        return str(valor)
    return str(valor).strip()


def main(entrada: Path) -> int:
    datos = json.loads(entrada.read_text(encoding="utf-8"))
    documento = json.loads(CATALOGO.read_text(encoding="utf-8"))
    registros = {r["candidate_id"]: r for r in documento["records"]}
    añadidas = descartadas = 0
    for producto in datos.get("products", []):
        pid = producto.get("candidate_id")
        registro = registros.get(pid)
        if registro is None:
            print(f"[aviso] {pid}: no está en el catálogo; se omite")
            continue
        existentes = {d.get("metric") for d in registro.get("documented") or []}
        for cond in producto.get("conditions", []):
            metric = cond.get("metric")
            url = (cond.get("source_url") or "").strip()
            valor = cond.get("value")
            if metric not in DOCUMENTED_METRICS:
                print(f"[aviso] {pid}/{metric}: clave no reconocida; se omite")
                descartadas += 1
                continue
            if not url.startswith("http") or valor in (None, ""):
                print(f"[aviso] {pid}/{metric}: sin fuente o sin valor; se omite")
                descartadas += 1
                continue
            if metric in existentes:
                continue
            registro.setdefault("documented", []).append({
                "metric": metric,
                "value": normaliza(valor),
                "unit": unidad(metric),
                "literal": str(cond.get("value_literal") or "")[:180],
                "source_url": url,
                "source_title": str(cond.get("source_title") or "")[:180],
                "accessed": str(cond.get("accessed") or "2026-11-06"),
            })
            existentes.add(metric)
            añadidas += 1
    CATALOGO.write_text(json.dumps(documento, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"añadidas {añadidas} condiciones; descartadas {descartadas}; fichero {CATALOGO}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: merge_research.py <investigacion.json>")
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1])))
