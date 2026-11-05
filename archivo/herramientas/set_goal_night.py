"""Fija el objetivo persistente de la noche en esta sesión.

Se ejecuta con HERMES_HOME apuntando al perfil y la raíz de hermes-agent en sys.path.
"""

import os
import sys

HERMES_HOME = r"C:\Users\aleja\AppData\Local\hermes\profiles\trabajos"
AGENT_ROOT = r"C:\Users\aleja\AppData\Local\hermes\hermes-agent"
SESSION_ID = "local-ea17829b105a676cccedc27af178f99140c52a40622f1e9621dfe9b9e636b88e"

os.environ["HERMES_HOME"] = HERMES_HOME
sys.path.insert(0, AGENT_ROOT)

from hermes_cli.goals import GoalContract, GoalState, load_goal, save_goal  # noqa: E402

GOAL = (
    "Dejar Paideia en Render completa, honesta y probada: fichas de fondos y ETF con sus "
    "datos documentados, perfil conectado al chat con consentimiento por campo, cupo diario "
    "que sobreviva al redespliegue y defectos menores corregidos, todo con pruebas verdes y "
    "evidencia escrita."
)

CONTRACT = GoalContract(
    outcome=(
        "La app de Render (https://paideia-jg2n.onrender.com) muestra en cada ficha lo que la "
        "fuente documenta para fondos y ETF (TER, ISIN, comisiones, SRI, mínimos), el chat recibe "
        "solo los campos de perfil que el usuario autoriza uno a uno, el cupo diario no se reinicia "
        "al redesplegar, y los defectos menores detectados quedan corregidos o documentados como "
        "límite."
    ),
    verification=(
        "Ejecutar desde prototipos/paideia-local: `python -m pytest tests -q` y "
        "`node --test tests/*.test.cjs`, ambas con exit 0. Además, cada subobjetivo deja su "
        "evidencia en docs/ (captura, JSON o informe) y se comprueba el servicio real cuando "
        "aplique con curl o navegador."
    ),
    constraints=(
        "No tocar Vercel (queda congelado como escaparate). No reabrir el contador de misión ni "
        "N2. No inventar datos: lo que la fuente no publica se muestra como desconocido. Máximo 10 "
        "llamadas reales a Groq, con datos ficticios. Ninguna clave en el repositorio, en capturas "
        "ni en el chat. Los cambios se prueban antes de subirlos y se despliegan solo desde "
        "master."
    ),
    boundaries=(
        "prototipos/paideia-local (código, datos y pruebas), api/_static y api/_core regenerados "
        "con build_core, y docs/. No modificar mission_ledger.py, scripts/provision_mission.py ni "
        "sus pruebas."
    ),
    stop_when=(
        "Los seis subobjetivos están cumplidos con pruebas verdes y evidencia, o aparece una "
        "decisión de producto, una credencial o un pago que solo el usuario puede resolver."
    ),
)

SUBGOALS = [
    "Fichas de fondos y ETF: mostrar TER, ISIN, comisiones, SRI, mínimo y resto de datos "
    "documentados que hoy se transcriben pero no se ven, sin inventar y con su fuente.",
    "Perfil conectado: decidir y ejecutar para liquidez, tolerancia y capacidad de pérdida si se "
    "envían al chat con consentimiento por campo (DTO) o se dejan de preguntar.",
    "Cupo diario persistente: que el contador de llamadas sobreviva a un redespliegue de Render, "
    "o documentar con precisión por qué no puede y qué límite real queda.",
    "Defectos menores: lista corta de la auditoría Ponytail (código muerto, duplicación, "
    "validaciones ausentes) corregidos sin añadir capas nuevas.",
    "Evidencia: informe de la noche con qué se cambió, hashes, pruebas y límites reales, en "
    "docs/.",
    "Despliegue y comprobación en Render: push a master, espera de redespliegue y verificación "
    "del servicio con datos ficticios.",
]

state = load_goal(SESSION_ID)
if state is None:
    state = GoalState(goal=GOAL)
state.goal = GOAL
state.status = "active"
state.max_turns = 300
state.turns_used = 0
state.last_verdict = None
state.last_reason = None
state.paused_reason = None
state.consecutive_parse_failures = 0
state.consecutive_transport_failures = 0
state.contract = CONTRACT
state.subgoals = SUBGOALS
state.clear_wait()
save_goal(SESSION_ID, state)

print("guardado:", state.status, "| subobjetivos:", len(state.subgoals), "| turnos máx:", state.max_turns)
