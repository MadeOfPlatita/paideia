"""Genera api/_core/ para el despliegue en Vercel.

El runtime de Vercel empaqueta el código de la función; para no depender de rutas
del repositorio, el catálogo y los módulos puros se copian dentro de la función.
"""

from __future__ import annotations

import json
import pprint
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "validacion-04" / "05-catalogo" / "candidatos.json"
CURATED = ROOT / "prototipos" / "paideia-local" / "data" / "condiciones.json"
TARGET_DIR = Path(__file__).resolve().parent / "_core"

KEEP = ("candidate_id", "family", "candidate_state", "name_literal", "issuer_manager",
        "isin", "primary_url", "dates", "conflicts", "unknown_fields")
SHARED = ("domain.py", "catalogue_conditions.py")


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    candidates = [{key: item.get(key) for key in KEEP} for item in snapshot.get("candidates", [])]
    curated = json.loads(CURATED.read_text(encoding="utf-8"))
    body = (
        '"""Datos empaquetados para Vercel. Generado por api/build_core.py."""\n\n'
        f"CANDIDATES = {pprint.pformat(candidates, width=110, sort_dicts=False)}\n\n"
        f"CURATED = {pprint.pformat(curated, width=110, sort_dicts=False)}\n"
    )
    (TARGET_DIR / "catalogue_data.py").write_text(body, encoding="utf-8")
    source_dir = ROOT / "prototipos" / "paideia-local"
    for name in SHARED:
        text = (source_dir / name).read_text(encoding="utf-8")
        header = f"# Copia generada por api/build_core.py desde prototipos/paideia-local/{name}. No editar aquí.\n"
        (TARGET_DIR / name).write_text(header + text, encoding="utf-8")
    (TARGET_DIR / "__init__.py").write_text("", encoding="utf-8")
    static_source = ROOT / "prototipos" / "paideia-local" / "static"
    static_target = TARGET_DIR.parent / "_static"
    static_target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for path in static_source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(static_source)
        destination = static_target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())
        copied += 1
    print(f"api/_core listo: {len(candidates)} candidatos, {len(curated.get('records', []))} transcritos, {copied} archivos estáticos")


if __name__ == "__main__":
    main()
