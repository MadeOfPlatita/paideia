"""Contador global de intentos reales de Pai para una misión concreta (sin secretos).

Por qué existe
--------------
La cuota diaria del adaptador vive en la sesión de la app y no impide que otra ruta,
otro proceso o un reinicio empiecen de cero. Esta misión tiene un cupo duro y único
(hasta 100 intentos HTTP reales) y el contador debe ser el mismo desde cualquier
copia del repositorio, cualquier proceso y cualquier reinicio del equipo.

Diseño
------
- Un directorio canónico por perfil del sistema operativo, **fuera** del checkout:
  Windows ``%LOCALAPPDATA%/Paideia/ledger-missions/<id>``; POSIX
  ``$XDG_STATE_HOME/Paideia/ledger-missions/<id>``. Todas las copias del árbol resuelven
  al mismo sitio.
- ``MISSION.json`` (manifest) se crea a mano, offline, y fija misión, inicio, corte y
  cupo. Mientras exista un manifest activo, **cualquier** proceso del mismo perfil
  que envíe por el transporte real queda contado, sin depender de variables de
  entorno. Sin manifest activo (o con la ventana cerrada) el contador no interviene
  y la ruta ordinaria conserva su propia cuota.
- ``attempts.jsonl`` es un diario append-only con ``flush`` + ``fsync`` antes de
  devolver el testigo: **se cuenta antes de enviar**, de modo que un cierre brusco
  no regala intentos. Un error de lectura del diario durante la misión bloquea el
  envío (fail closed); nunca se asume cero.
- Un lock de fichero evita carreras entre procesos; un lock obsoleto (más de 60 s)
  se puede recuperar, pero nunca se ignora el diario.

Cobertura
---------
Hay exactamente dos rutinas que abren una conexión HTTPS al proveedor y ambas reservan
antes de conectar: ``providers.GroqHTTPSJSONTransport._post`` y
``secure_groq_session._guarded_https_post``. El corte es un tope duro: mientras exista
un manifest, antes de su inicio y desde su corte el envío se bloquea hasta que el
coordinador retire el manifest (``scripts/provision_mission.py --close``). El estado
vive en ``Paideia/ledger-missions``, separado del mecanismo de la misión nocturna.

Límites explícitos
------------------
No es un sandbox: quien controle el proceso, el reloj o el sistema de archivos puede
**borrar el diario o el manifest, o mover la hora**. Un cliente que hable con el
proveedor sin pasar por esas dos rutinas no queda contado. Ejecutar la suite del
proyecto con la misión provisionada **consume cupo real**, porque se cuenta antes de
conectar y hay pruebas que usan el transporte real con la conexión sustituida: la
mitigación es no ejecutar pruebas dentro de la ventana y retirar el manifest al
terminar. Cubre el riesgo real de esta misión: rutas distintas, procesos nuevos,
reintentos y reinicios que comparten el mismo perfil.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "paideia-mission-manifest.v1"
JOURNAL_SCHEMA = "paideia-mission-attempt.v1"
NAMESPACE = "Paideia"
# Directorio propio: `Paideia/missions` lo usa el mecanismo de la misión nocturna y
# mezclar ambos espacios de nombres hacía que un manifest ajeno bloquease la app.
SUBDIR = "ledger-missions"
LOCK_STALE_SECONDS = 60.0
LOCK_TIMEOUT_SECONDS = 5.0


class MissionBlocked(RuntimeError):
    """El envío no está permitido: cupo agotado, corte alcanzado o estado ilegible."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def _state_root() -> Path:
    if os.name == "nt":
        configured = os.environ.get("LOCALAPPDATA")
        base = Path(configured) if configured and Path(configured).is_absolute() else Path.home() / "AppData" / "Local"
    else:
        configured = os.environ.get("XDG_STATE_HOME")
        base = Path(configured) if configured and Path(configured).is_absolute() else Path.home() / ".local" / "state"
    if not base.is_absolute():
        raise MissionBlocked("MISSION_UNAVAILABLE", "state root is not absolute")
    return base / NAMESPACE / SUBDIR


def mission_dir(mission_id: str) -> Path:
    if not isinstance(mission_id, str) or not mission_id or not mission_id.replace("-", "").replace("_", "").isalnum():
        raise MissionBlocked("MISSION_UNAVAILABLE", "invalid mission id")
    return _state_root() / mission_id


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise MissionBlocked("MISSION_CORRUPT", f"{field} missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise MissionBlocked("MISSION_CORRUPT", f"{field} invalid") from error
    if parsed.tzinfo is None:
        raise MissionBlocked("MISSION_CORRUPT", f"{field} without timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class MissionConfig:
    mission_id: str
    start: datetime
    cutoff: datetime
    cap: int
    directory: Path

    def active(self, now: datetime) -> bool:
        return self.start <= now < self.cutoff

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "start_utc": self.start.isoformat(),
            "cutoff_utc": self.cutoff.isoformat(),
            "cap": self.cap,
            "state_dir": str(self.directory),
        }


def load_manifest(path: str | os.PathLike | None = None) -> MissionConfig | None:
    """Carga el manifest de la misión. ``None`` si no hay misión provisionada."""
    manifest = Path(path) if path is not None else None
    if manifest is None:
        return None
    try:
        raw = manifest.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as error:
        raise MissionBlocked("MISSION_UNAVAILABLE", f"manifest unreadable: {error.errno}") from error
    try:
        document = json.loads(raw)
    except ValueError as error:
        raise MissionBlocked("MISSION_CORRUPT", "manifest is not JSON") from error
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise MissionBlocked("MISSION_CORRUPT", "manifest schema mismatch")
    mission_id = document.get("mission_id")
    cap = document.get("cap")
    if not isinstance(mission_id, str) or not mission_id:
        raise MissionBlocked("MISSION_CORRUPT", "mission_id missing")
    if type(cap) is not int or cap <= 0:
        raise MissionBlocked("MISSION_CORRUPT", "cap invalid")
    start = _parse_utc(document.get("start_utc"), "start_utc")
    cutoff = _parse_utc(document.get("cutoff_utc"), "cutoff_utc")
    if cutoff <= start:
        raise MissionBlocked("MISSION_CORRUPT", "cutoff before start")
    directory = mission_dir(mission_id)
    expected = (directory / "MISSION.json").resolve()
    if manifest.resolve() != expected:
        raise MissionBlocked("MISSION_UNAVAILABLE", "manifest outside the canonical mission directory")
    return MissionConfig(mission_id, start, cutoff, cap, directory)


class _Lock:
    """Lock entre procesos sobre ``<state>/lock``; nunca bloquea indefinidamente."""

    def __init__(self, directory: Path):
        self.path = directory / "lock"
        self.acquired = False

    def __enter__(self):
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if self._break_if_stale():
                    continue
                if time.monotonic() >= deadline:
                    raise MissionBlocked("MISSION_UNAVAILABLE", "ledger lock is held")
                time.sleep(0.02)
                continue
            try:
                os.write(fd, f"{os.getpid()} {time.time():.3f}".encode("ascii"))
            finally:
                os.close(fd)
            self.acquired = True
            return self

    def _break_if_stale(self) -> bool:
        try:
            age = time.time() - self.path.stat().st_mtime
        except OSError:
            return True
        if age <= LOCK_STALE_SECONDS:
            return False
        try:
            self.path.unlink()
        except OSError:
            return False
        return True

    def __exit__(self, *_exc):
        if self.acquired:
            try:
                self.path.unlink()
            except OSError:
                pass
            self.acquired = False
        return False


def read_attempts(directory: Path) -> list[dict]:
    """Lee el diario. Un diario malformado es un error, no un cero silencioso."""
    journal = directory / "attempts.jsonl"
    try:
        raw = journal.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError as error:
        raise MissionBlocked("MISSION_UNAVAILABLE", f"journal unreadable: {error.errno}") from error
    records = []
    for number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise MissionBlocked("MISSION_CORRUPT", f"journal line {number} is not JSON") from error
        if not isinstance(record, dict) or record.get("schema") != JOURNAL_SCHEMA or type(record.get("n")) is not int:
            raise MissionBlocked("MISSION_CORRUPT", f"journal line {number} is not an attempt")
        records.append(record)
    return records


def status(config: MissionConfig, now: datetime | None = None) -> dict:
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    used = len(read_attempts(config.directory))
    return {
        **config.to_dict(),
        "now_utc": moment.isoformat(),
        "active": config.active(moment),
        "used": used,
        "remaining": max(config.cap - used, 0),
    }


def reserve(config: MissionConfig, route: str, now: datetime | None = None) -> dict:
    """Reserva un intento **antes** de enviar y devuelve el testigo.

    Fuera de la ventana de la misión no reserva: devuelve el estado sin consumir cupo
    para que la ruta ordinaria conserve su propio límite.
    """
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if not config.active(moment):
        raise MissionBlocked("MISSION_CLOSED", "outside mission window")
    directory = config.directory
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise MissionBlocked("MISSION_UNAVAILABLE", f"state dir unavailable: {error.errno}") from error
    label = route if isinstance(route, str) and route else "unknown"
    label = "".join(character for character in label if character.isalnum() or character in "-_./")[:40] or "unknown"
    with _Lock(directory):
        used = len(read_attempts(directory))
        if used >= config.cap:
            raise MissionBlocked("MISSION_EXHAUSTED", f"{used}/{config.cap}")
        record = {
            "schema": JOURNAL_SCHEMA,
            "n": used + 1,
            "at": moment.isoformat(),
            "pid": os.getpid(),
            "route": label,
        }
        journal = directory / "attempts.jsonl"
        try:
            with journal.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as error:
            raise MissionBlocked("MISSION_UNAVAILABLE", f"journal not writable: {error.errno}") from error
    return {
        "attempt": record["n"],
        "used": record["n"],
        "cap": config.cap,
        "remaining": max(config.cap - record["n"], 0),
        "cutoff_utc": config.cutoff.isoformat(),
        "mission_id": config.mission_id,
    }


def reserve_attempt(route: str, *, manifest_path: str | os.PathLike | None = None,
                    now: datetime | None = None) -> dict | None:
    """Punto de entrada del transporte: ``None`` si no hay misión provisionada."""
    config = load_manifest(manifest_path)
    if config is None:
        return None
    return reserve(config, route, now=now)


def active_manifests(now: datetime | None = None) -> list[MissionConfig]:
    """Manifests existentes bajo el directorio canónico, estén activos o no."""
    root = _state_root()
    try:
        children = sorted(path for path in root.iterdir() if path.is_dir())
    except FileNotFoundError:
        return []
    except OSError as error:
        raise MissionBlocked("MISSION_UNAVAILABLE", f"state root unreadable: {error.errno}") from error
    found = []
    for child in children:
        config = load_manifest(child / "MISSION.json")
        if config is not None:
            found.append(config)
    return found


def active_mission(now: datetime | None = None) -> MissionConfig | None:
    """La misión vigente en este instante, si hay alguna provisionada."""
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    active = [config for config in active_manifests(moment) if config.active(moment)]
    if not active:
        return None
    if len(active) > 1:
        # Dos misiones activas a la vez serían cupos paralelos: se falla cerrado.
        raise MissionBlocked("MISSION_CORRUPT", "more than one active mission manifest")
    return active[0]


def reserve_for_active_mission(route: str, now: datetime | None = None) -> dict | None:
    """Reserva en la misión provisionada. ``None`` solo si no hay ningún manifest.

    Mientras exista un manifest en el directorio canónico, el corte es un tope duro:
    antes del inicio y a partir del corte se bloquea (`MISSION_CLOSED`) hasta que el
    coordinador retire el manifest (`scripts/provision_mission.py --close`). Así el
    corte no se convierte en «dejar de contar y seguir enviando».
    """
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    configs = active_manifests(moment)
    if not configs:
        return None
    if any(moment >= config.cutoff for config in configs):
        raise MissionBlocked("MISSION_CLOSED", "mission cutoff reached; close the manifest")
    if any(moment < config.start for config in configs):
        raise MissionBlocked("MISSION_CLOSED", "mission has not started")
    if len(configs) > 1:
        raise MissionBlocked("MISSION_CORRUPT", "more than one mission manifest")
    return reserve(configs[0], route, now=moment)
