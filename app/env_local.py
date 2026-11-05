"""Carga local de variables desde `.env`, sin dependencias externas.

Lee solo pares CLAVE=VALOR del archivo `.env` que está junto a este módulo.
No sobrescribe variables ya presentes en el entorno del proceso, ignora
comentarios y líneas mal formadas, y nunca registra ni devuelve valores.
"""

from pathlib import Path
import os

ENV_PATH = Path(__file__).with_name(".env")


def load_env(path=None):
    """Carga el `.env` indicado y devuelve cuántas claves se añadieron."""
    target = Path(path) if path is not None else ENV_PATH
    try:
        if not target.is_file():
            return 0
        lines = target.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return 0
    loaded = 0
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key or not key.replace("_", "").isalnum():
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key in os.environ:
            continue
        os.environ[key] = value
        loaded += 1
    return loaded
