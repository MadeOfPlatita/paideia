"""Provisiona el manifest del contador global de intentos reales (windows/POSIX, sin secretos).

Uso:
    python scripts/provision_mission.py --mission-id <id> --cutoff <ISO UTC> [--cap N] [--start ISO]
    python scripts/provision_mission.py --status [--mission-id <id>]
    python scripts/provision_mission.py --close --mission-id <id>

El manifest vive en el directorio canónico por perfil
(`%LOCALAPPDATA%/Paideia/ledger-missions/<id>/MISSION.json` en Windows,
`$XDG_STATE_HOME/Paideia/ledger-missions/<id>/` en POSIX) y es lo que activa el contador
global. No contiene claves ni datos personales: misión, ventana y cupo.

Reglas (una revisión independiente encontró que la versión anterior escribía manifests
inválidos y aun así salía con código 0):

- `--cap` debe ser un entero entre 1 y 100: el máximo autorizado por el equipo.
- `--cutoff` es obligatorio al crear, debe quedar en el futuro y después de `--start`.
- No se crea un segundo manifest si ya hay otro provisionado en el directorio canónico:
  dos misiones activas serían dos cupos en paralelo y el ledger las rechaza.
- El manifest se escribe de forma atómica y se valida con `load_manifest` antes de dar
  éxito; si no carga, se retira y se sale con código distinto de cero.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mission_ledger  # noqa: E402

MAX_CAP = 100


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _parse_iso(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as error:
        raise ValueError(f"{label} no es una fecha ISO válida: {value!r}") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{label} necesita zona horaria (por ejemplo +00:00)")
    return parsed.astimezone(timezone.utc)


def _existing_manifests() -> list[Path]:
    root = mission_ledger._state_root()  # noqa: SLF001 - misma unidad de estado
    try:
        children = sorted(path for path in root.iterdir() if path.is_dir())
    except FileNotFoundError:
        return []
    except OSError as error:
        # Un estado ilegible no es «sin misión»: el ledger bloquearía cada envío.
        raise mission_ledger.MissionBlocked(
            "MISSION_UNAVAILABLE", f"state root unreadable: {error.errno}") from error
    return [child / "MISSION.json" for child in children if (child / "MISSION.json").is_file()]


def _print_status(mission_id: str | None) -> int:
    try:
        manifests = _existing_manifests()
    except mission_ledger.MissionBlocked as error:
        print(f"el estado del contador no es legible ({error}); el chat quedaría bloqueado",
              file=sys.stderr)
        return 1
    if mission_id:
        manifests = [path for path in manifests if path.parent.name == mission_id]
    if not manifests:
        legacy = mission_ledger._legacy_manifests()  # noqa: SLF001
        if legacy:
            print("hay un manifest del contador en la ruta heredada Paideia/missions; "
                  "muévelo a Paideia/ledger-missions antes de usar el contador")
            return 1
        print("sin misión provisionada")
        return 0
    exit_code = 0
    for manifest in manifests:
        try:
            config = mission_ledger.load_manifest(manifest)
            if config is None:
                raise mission_ledger.MissionBlocked("MISSION_UNAVAILABLE", "manifest sin contenido")
            state = mission_ledger.status(config, now=_now())
        except mission_ledger.MissionBlocked as error:
            print(f"{manifest}: manifest inválido ({error})")
            exit_code = 1
            continue
        print(json.dumps(state, ensure_ascii=False, indent=2))
    return exit_code


def _close(mission_id: str) -> int:
    manifest = mission_ledger.mission_dir(mission_id) / "MISSION.json"
    if manifest.exists():
        manifest.unlink()
        print(f"manifest retirado: {manifest}")
    else:
        print(f"no había manifest para {mission_id}")
    return 0


def _provision(args) -> int:
    cap = MAX_CAP if args.cap is None else args.cap
    if type(cap) is not int or not 1 <= cap <= MAX_CAP:
        print(f"error: --cap debe estar entre 1 y {MAX_CAP} (recibido {cap!r})", file=sys.stderr)
        return 2
    if not args.cutoff:
        print("error: --cutoff es obligatorio para crear una misión", file=sys.stderr)
        return 2
    try:
        start = _parse_iso(args.start, "--start") if args.start else _now()
        cutoff = _parse_iso(args.cutoff, "--cutoff")
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if cutoff <= start:
        print(f"error: el corte ({cutoff.isoformat()}) debe ser posterior al inicio "
              f"({start.isoformat()})", file=sys.stderr)
        return 2
    if cutoff <= _now():
        print(f"error: el corte ({cutoff.isoformat()}) ya pasó; una ventana vencida no "
              "autoriza envíos", file=sys.stderr)
        return 2

    try:
        directory = mission_ledger.mission_dir(args.mission_id)
    except mission_ledger.MissionBlocked as error:
        print(f"error: identificador de misión no válido ({error})", file=sys.stderr)
        return 2

    existing = [path for path in _existing_manifests() if path.parent != directory]
    if existing:
        print("error: ya hay otra misión provisionada; retírala con --close antes de crear otra:",
              file=sys.stderr)
        for path in existing:
            print(f"  {path}", file=sys.stderr)
        return 2
    legacy = mission_ledger._legacy_manifests()  # noqa: SLF001
    if legacy:
        print("error: hay un manifest del contador en la ruta heredada Paideia/missions; "
              "muévelo a Paideia/ledger-missions antes de provisionar:", file=sys.stderr)
        for path in legacy:
            print(f"  {path}", file=sys.stderr)
        return 2

    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory / "MISSION.json"
    document = {
        "schema": mission_ledger.SCHEMA,
        "mission_id": args.mission_id,
        "start_utc": start.isoformat(),
        "cutoff_utc": cutoff.isoformat(),
        "cap": cap,
    }
    temporary = directory / "MISSION.json.tmp"
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, manifest)
    try:
        config = mission_ledger.load_manifest(manifest)
        if config is None:
            raise mission_ledger.MissionBlocked("MISSION_UNAVAILABLE", "manifest sin contenido")
        state = mission_ledger.status(config, now=_now())
    except mission_ledger.MissionBlocked as error:
        try:
            manifest.unlink()
        except OSError:
            pass
        print(f"error: el manifest no se puede cargar ({error}); se ha retirado", file=sys.stderr)
        return 2
    print(f"manifest creado: {manifest}")
    print(f"ventana: {state['start_utc']} → {state['cutoff_utc']} · cupo: {state['cap']} "
          f"· usado: {state['used']}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Manifest del contador global de intentos reales")
    parser.add_argument("--mission-id", default=None, help="identificador de la misión")
    parser.add_argument("--start", default=None, help="inicio UTC ISO (por defecto, ahora)")
    parser.add_argument("--cutoff", default=None, help="corte UTC ISO (obligatorio al crear)")
    parser.add_argument("--cap", type=int, default=None, help=f"cupo de intentos (1..{MAX_CAP})")
    parser.add_argument("--status", action="store_true", help="muestra el estado y sale")
    parser.add_argument("--close", action="store_true", help="retira el manifest")
    args = parser.parse_args(argv)

    if args.status:
        return _print_status(args.mission_id)
    if args.close:
        if not args.mission_id:
            print("error: --close necesita --mission-id", file=sys.stderr)
            return 2
        try:
            return _close(args.mission_id)
        except mission_ledger.MissionBlocked as error:
            print(f"error: identificador de misión no válido ({error})", file=sys.stderr)
            return 2
    if not args.mission_id:
        print("error: --mission-id es obligatorio para crear una misión", file=sys.stderr)
        return 2
    return _provision(args)


if __name__ == "__main__":
    raise SystemExit(main())
