"""Provisiona el manifest de la misión de 4 h 30 min (windows/POSIX, sin secretos).

Uso:
    python scripts/provision_mission.py            # crea el manifest si no existe
    python scripts/provision_mission.py --status   # solo muestra el estado
    python scripts/provision_mission.py --close    # retira el manifest (fin de la misión)

El manifest vive en el directorio canónico por perfil
(`%LOCALAPPDATA%/Paideia/ledger-missions/<id>/MISSION.json`) y es lo que activa el contador
global de intentos reales. No contiene claves ni datos personales: misión, ventana y
cupo. Sin manifest activo, la app sigue con su cuota diaria normal.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mission_ledger  # noqa: E402

MISSION_ID = "paideia-mission-20261104-4h30"
# Corte de la misión: 4/11/2026 16:21:47 en Málaga (UTC+01:00) = 15:21:47Z.
CUTOFF = "2026-11-04T15:21:47+00:00"
CAP = 100


def _now():
    return datetime.now(timezone.utc)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Manifest del contador global de intentos reales")
    parser.add_argument("--status", action="store_true", help="muestra el estado y sale")
    parser.add_argument("--close", action="store_true", help="retira el manifest")
    parser.add_argument("--start", default=None, help="inicio UTC ISO (por defecto, ahora)")
    parser.add_argument("--cap", type=int, default=CAP)
    args = parser.parse_args(argv)

    directory = mission_ledger.mission_dir(MISSION_ID)
    manifest = directory / "MISSION.json"

    if args.status:
        config = mission_ledger.load_manifest(manifest)
        if config is None:
            print("sin misión provisionada")
            return 0
        state = mission_ledger.status(config, now=_now())
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0

    if args.close:
        if manifest.exists():
            manifest.unlink()
            print(f"manifest retirado: {manifest}")
        else:
            print("no había manifest")
        return 0

    if manifest.exists():
        print(f"ya existe: {manifest}")
        return 1

    start = args.start or _now().replace(microsecond=0).isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "schema": mission_ledger.SCHEMA,
        "mission_id": MISSION_ID,
        "start_utc": start,
        "cutoff_utc": CUTOFF,
        "cap": args.cap,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest creado: {manifest}")
    print(f"ventana: {start} → {CUTOFF} · cupo: {args.cap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
