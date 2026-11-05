"""Garantiza que el paquete `tests` sea importable al recolectar.

Varias pruebas hacen `from tests.x import ...`. Si el proceso se lanza con el
entorno saneado (PYTHONSAFEPATH) o desde otro directorio, el directorio de la
app no entra en sys.path y la recolección falla. Este conftest se carga antes
que los módulos de prueba, así que basta con declararlo aquí una vez.
"""

import sys
from pathlib import Path

APP_DIR = str(Path(__file__).resolve().parent)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
