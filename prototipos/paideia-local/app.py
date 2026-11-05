"""Lanzador heredado: el servicio de Render todavía arranca esta ruta.

El código vive en `app/`. Cuando el Start Command del servicio pase a
`python app/app.py` (ver `docs/operacion/DESPLIEGUE-RENDER.md`), este archivo
puede borrarse sin tocar nada más.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2] / "app"
sys.path.insert(0, str(APP_DIR))
runpy.run_path(str(APP_DIR / "app.py"), run_name="__main__")
