"""Genera src/catalogue_data.py a partir de los JSON del proyecto.

Cloudflare Workers no lee ficheros en tiempo de ejecución, así que el catálogo y
las condiciones transcritas se empaquetan como constantes de Python. El script se
ejecuta en local; el Worker solo importa el resultado.
"""

from __future__ import annotations

import json
import pprint
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "validacion-04" / "05-catalogo" / "candidatos.json"
CURATED = ROOT / "prototipos" / "paideia-local" / "data" / "condiciones.json"
TARGET = Path(__file__).resolve().parent / "src" / "catalogue_data.py"

KEEP = ("candidate_id", "family", "candidate_state", "name_literal", "issuer_manager",
        "isin", "primary_url", "dates", "conflicts", "unknown_fields")
SHARED = ("domain.py", "catalogue_conditions.py")


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    candidates = []
    for item in snapshot.get("candidates", []):
        candidates.append({key: item.get(key) for key in KEEP})
    curated = json.loads(CURATED.read_text(encoding="utf-8"))
    body = (
        '"""Datos empaquetados para el Worker. Generado por build_data.py; no editar a mano."""\n\n'
        f"CANDIDATES = {pprint.pformat(candidates, width=110, sort_dicts=False)}\n\n"
        f"CURATED = {pprint.pformat(curated, width=110, sort_dicts=False)}\n"
    )
    TARGET.write_text(body, encoding="utf-8")
    print(f"escrito {TARGET.name}: {len(candidates)} candidatos")
    source_dir = ROOT / "prototipos" / "paideia-local"
    for name in SHARED:
        text = (source_dir / name).read_text(encoding="utf-8")
        header = f"# Copia generada por worker/build_data.py desde prototipos/paideia-local/{name}. No editar aquí.\n"
        (TARGET.parent / name).write_text(header + text, encoding="utf-8")
        print(f"copiado {name}")


if __name__ == "__main__":
    main()
