"""Deja importables los módulos hermanos de prueba (`test_catalogue_facts`, etc.).

`tests` es un paquete (tiene `__init__.py`), así que pytest importa los módulos
como `tests.x` y no añade esta carpeta a `sys.path`. Varias pruebas hacen
`from test_catalogue_facts import ...` en tiempo de ejecución; sin esta línea
fallan con `ModuleNotFoundError` al lanzar un fichero suelto o con el entorno
saneado.
"""

import sys
from pathlib import Path

TESTS_DIR = str(Path(__file__).resolve().parent)
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)
