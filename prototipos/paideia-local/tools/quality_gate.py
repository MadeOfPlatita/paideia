"""Puerta de calidad del objetivo: pruebas Python y Node en un solo comando.

Se ejecuta sin depender del shell (cmd, PowerShell o bash): cambia de directorio
él mismo y lanza las dos suites. Devuelve 0 solo si ambas pasan.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]

# Interpretes candidatos: el que lanzó el script, el que declare el entorno y las
# instalaciones conocidas de esta máquina (el Python del agente no trae pytest).
_FIJOS = (
    r"C:\Users\aleja\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe",
    r"C:\Users\aleja\AppData\Local\Programs\Python\Python311\python.exe",
)


def _candidatos():
    yield os.environ.get("PAIDEIA_PYTHON", "")
    yield sys.executable
    for ruta in _FIJOS:
        yield ruta
    for nombre in ("python", "python3", "python3.11"):
        encontrado = shutil.which(nombre)
        if encontrado:
            yield encontrado


def _tiene_pytest(interprete):
    try:
        prueba = subprocess.run([interprete, "-c", "import pytest"],
                                capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False
    return prueba.returncode == 0


def elegir_python():
    vistos = set()
    for candidato in _candidatos():
        if not candidato or candidato in vistos:
            continue
        vistos.add(candidato)
        if not Path(candidato).is_file() and not shutil.which(candidato):
            continue
        if _tiene_pytest(candidato):
            return candidato
    return None


def run(command, label):
    print(f"== {label}: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=APP_DIR)
    print(f"== {label}: exit {completed.returncode}", flush=True)
    return completed.returncode


def main() -> int:
    interprete = elegir_python()
    if interprete is None:
        print("== pytest: no hay ningún Python con pytest instalado", flush=True)
        return 1
    print(f"== pytest: intérprete {interprete}", flush=True)
    python_code = run([interprete, "-m", "pytest", "tests", "-q"], "pytest")
    if python_code != 0:
        return python_code
    tests = sorted(glob.glob(str(APP_DIR / "tests" / "*.test.cjs")))
    if not tests:
        print("== node: no se encontraron pruebas", flush=True)
        return 1
    node_code = run(["node", "--test", *tests], "node")
    return node_code


if __name__ == "__main__":
    raise SystemExit(main())
