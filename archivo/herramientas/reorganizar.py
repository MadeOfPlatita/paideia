"""Reorganiza el repositorio: app en la raíz, documentación separada y archivo.

Se ejecuta una vez. Usa `git mv` para conservar el historial y no borra nada:
lo que no es producto vigente se mueve a docs/historico o archivo/.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(r"C:/Users/aleja/Downloads/App Financiera")
DOCS = ROOT / "docs"

HISTORICO = [
    "catalogo-condiciones-20261103", "catalogo-hasta-bloqueo", "comparativa-producto-20261103",
    "contador-hasta-bloqueo", "correcciones-qa-20261103T172201", "demo-usuario-20261103",
    "diagnostico-movil-C", "diseno-hasta-bloqueo", "diseno-ideas", "ensayo-b5", "entrega-noche",
    "ia-calidad-estructurada", "ia-groq-estructurada", "informe-b6", "mision-4h30",
    "noche-funcional", "overnight-ampliado", "pai-calidad", "pai-catalogo-20261103",
    "privacidad-capacidad", "qa-usuarios-20261103T165536", "recorrido-escenarios-academico",
    "revision-manana-20261103", "robustez-accesibilidad",
]
HISTORICO_MD = [
    "CIERRE-4H30-20261104.md", "CIERRE-NOCHE-20261104.md", "CIERRE-PAIDEIA-HASTA-BLOQUEO.md",
    "DIARIO_DESARROLLO.md", "INFORME-NOCHE-20261105.md",
    "PAIDEIA-HASTA-BLOQUEO-SEGUIMIENTO.md", "PLAN-PAI-PENDIENTES.md", "PRIORIDAD-BACKEND.md",
    "IA-CALIDAD-OVERNIGHT-GOAL.md", "IA-CALIDAD-OVERNIGHT-PREPARACION.json", "IA-REAL-GOAL.md",
    "OVERNIGHT-AMPLIADO-GOAL.md", "OVERNIGHT-AMPLIADO-PREPARACION.md",
]
PRODUCTO = ["REQUISITOS.md", "ESTADO_Y_PLAN.md", "PAIDEIA-CUESTIONARIO-REVISION.md", "CUPO-Y-LIMITES.md"]
OPERACION = ["DESPLIEGUE-RENDER.md", "AUDITORIA-NOCHE-20261105.md"]


def run(*args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"falló {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def move(origin: Path, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    run("git", "mv", str(origin.relative_to(ROOT)), str(destination.relative_to(ROOT)))


def main():
    # 1. La aplicación pasa a `app/`; el resto se calcula desde ahí.
    if (ROOT / "prototipos" / "paideia-local").exists():
        move(ROOT / "prototipos" / "paideia-local", ROOT / "app")
        (ROOT / "prototipos").rmdir()

    # 2. Documentación: producto, operación e histórico.
    (DOCS / "historico").mkdir(exist_ok=True)
    (DOCS / "producto").mkdir(exist_ok=True)
    (DOCS / "operacion").mkdir(exist_ok=True)
    for name in HISTORICO:
        if (DOCS / name).exists():
            move(DOCS / name, DOCS / "historico" / name)
    for name in HISTORICO_MD + sorted(p.name for p in DOCS.glob("GOAL-*.md")):
        path = DOCS / name
        if path.exists():
            move(path, DOCS / "historico" / name)
    for name in PRODUCTO:
        if (DOCS / name).exists():
            move(DOCS / name, DOCS / "producto" / name)
    for name in OPERACION:
        if (DOCS / name).exists():
            move(DOCS / name, DOCS / "operacion" / name)
    if (DOCS / "seguridad").exists():
        move(DOCS / "seguridad", DOCS / "operacion" / "seguridad")
    if (DOCS / "set_goal_night.py").exists():
        move(DOCS / "set_goal_night.py", ROOT / "archivo" / "herramientas" / "set_goal_night.py")

    # 3. Archivo: intentos descartados y pruebas antiguas.
    for origin, destination in (("worker", "archivo/worker-cloudflare"), ("spikes", "archivo/spikes"),
                                ("tests", "archivo/pruebas-antiguas")):
        if (ROOT / origin).exists():
            move(ROOT / origin, ROOT / destination)
    for name in sorted(ROOT.glob("paideia-security-*.txt")):
        move(name, ROOT / "archivo" / "seguridad" / "referencias" / name.name)
    if (ROOT / "IDEA.md").exists():
        move(ROOT / "IDEA.md", DOCS / "producto" / "IDEA.md")

    # 4. Índice como README de docs.
    if (DOCS / "INDICE.md").exists():
        move(DOCS / "INDICE.md", DOCS / "README.md")

    print("movido")


if __name__ == "__main__":
    main()
