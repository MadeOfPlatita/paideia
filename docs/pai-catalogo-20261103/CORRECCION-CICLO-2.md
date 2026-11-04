# B4 — corrección del ciclo 2 (atribución, estado y texto)

Fecha de trabajo: 4/11/2026, antes del corte de las 09:00 (UTC+01:00).
Alcance: corrección local del bloque B4 tras la revisión `deleg_b93dc16b` (dictamen
desfavorable). No hay revisión independiente nueva ni aprobación de B4; B6 y el resto
de bloques no se tocan.

## Qué se corrigió

- **Sin texto libre cuando el turno consulta el catálogo.** `ToolChatRunner` conserva
  los datos locales del resultado de la herramienta (`catalogue.used` y fichas con
  condiciones, estado, clase, fechas, límites y tramos) y entrega `answer: ""` con
  `answer_text_state: withheld_catalogue_evidence`. El servicio refuerza la regla: si
  `catalogue.used` es cierto, no devuelve prosa aunque un runner alternativo la incluya.
- **Sin afirmaciones oficiales/vigentes sin respaldo.** En turnos conceptuales, un
  detector léxico estrecho retira el texto que atribuye una fuente oficial o una tasa
  vigente sin datos locales (`withheld_unbacked_claim`). Las definiciones conceptuales
  sin esas atribuciones conservan su texto y su aviso de no validación.
- **Clase incoherente.** Si el motivo de una condición y el registro de la fuente
  declaran clases distintas, se retiran las citas de esa condición, `source_class`
  queda `unknown`, `source_resolution` no se presenta como resuelta y
  `attribution_state` pasa a `inconsistent`. Una fuente con id pero sin URL tampoco se
  declara oficial.
- **Estado `documented` más estricto.** Exige valor conocido, fuente resoluble con
  clase oficial o secundaria, fecha de referencia y vigencia no terminada. Se añaden
  `documented_unattributed`, `documented_not_current` y motivos visibles. Una fecha
  `effective_to` vencida convierte la condición en `stale`.
- **Error del servicio de condiciones.** `CatalogueWithConditions` ya no devuelve
  `{"products": []}`: lanza `ConditionsUnavailable`, la herramienta responde
  `CONDITIONS_UNAVAILABLE` y el chat termina en `CHAT_TOOL_ERROR` (HTTP 502) sin
  inventar un catálogo vacío.
- **Identificadores literales.** Se eliminó la normalización de espacios y guiones
  tipográficos en `pai_tools` y `pai_runtime`; un ID no literal se rechaza antes de
  consultar el repositorio.
- **Fechas de identidad.** La cita de identidad incluye `retrieved_at` cuando existe y
  `date_state` (`documented`/`unknown`) cuando no; nunca se inventa una fecha.
- **Tramos incoherentes.** Se rechazan duplicados de condición, importes fuera de
  rango y TAE inferior al TIN del mismo tramo (`rate_tiers_state: inconsistent`), sin
  mostrar sus valores.
- **UI del chat.** La sección de chat muestra las fichas locales con clase de fuente,
  fecha de consulta, vigencia, atribución, límites y tramos; muestra las citas con su
  clase y fecha; y presenta `answer_provenance.limitations`. Si el texto está retenido,
  no se renderiza en ningún caso, aunque el payload traiga prosa.

## Pruebas ejecutadas

- Suite B4/HTTP/chat (19 módulos: B4, herramientas, runtime, adaptador, backend,
  contexto, comparación, structured y regresión offline): **205 pruebas correctas**,
  ejecutadas con `python -m unittest …` en `prototipos/paideia-local`.
- `node --test tests/*.test.cjs`: **63 pruebas correctas**, incluidas las 6 nuevas de UI.
- Nuevas pruebas Python: `tests/test_b4_cycle2_provenance.py` (26 casos), con
  proveedor sintético, adaptador sintético, servicio local y HTTP loopback.
- Nuevas pruebas de UI: `tests/b4_chat_provenance.test.cjs`, con respuestas sintéticas
  y el shim DOM usado por el contrato de chat existente.
- La discovery completa se volvió a ejecutar durante el trabajo y en ese momento
  incluía archivos de misión/sesión que otro agente estaba editando
  (`test_pai_setup_integration`, `test_night_mission_budget`, `test_guarded_send_connect`,
  `test_mission_canonical_state`) y pruebas de sesión afectadas por esos cambios. Sus
  errores (`chat_enabled(now=…)`, `build_chat_service(test_only=…)`, manifiesto de
  misión) no provienen de los archivos de B4 y no se tocaron.

## Límites y lo que no se verificó

- No se llamó a Groq ni a ningún proveedor real; no se usó `.env`, red externa ni
  credenciales. Las pruebas con proveedor son sintéticas y no acreditan calidad del
  modelo.
- No se probó en navegador real ni en móvil; la UI se verificó con el shim DOM del
  contrato de chat y los casos HTTP con servidor loopback.
- El detector léxico de afirmaciones oficiales/vigentes es estrecho y no sustituye una
  validación semántica; puede retirar alguna frase segura y no detectar paráfrasis.
- No se modificaron `catalogue_conditions.py`, la UI de biblioteca/comparador/informes,
  `api/index.py`, `pai_setup.py`, `mission_budget.py` ni documentos de estado.
  `api/_static/app.js` se sincronizó desde `prototipos/paideia-local/static/app.js`.
- B4 sigue pendiente de revisión independiente y no se declara aprobado.
