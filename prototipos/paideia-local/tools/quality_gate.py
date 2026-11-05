"""Puerta de calidad del objetivo: pruebas Python y Node en un solo comando.

Se ejecuta sin depender del shell (cmd, PowerShell o bash): cambia de directorio
él mismo y lanza las dos suites. Devuelve 0 solo si ambas pasan.
"""

from __future__ import annotations

import glob
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]


def run(command, label):
    print(f"== {label}: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=APP_DIR)
    print(f"== {label}: exit {completed.returncode}", flush=True)
    return completed.returncode


def main() -> int:
    python_code = run([sys.executable, "-m", "pytest", "tests", "-q"], "pytest")
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
