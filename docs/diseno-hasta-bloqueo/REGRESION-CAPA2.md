# Regresión conductual tras la capa visual 2

Fecha de ejecución: 2026-11-04, 22:06–22:22 (Europe/Madrid).
Árbol: `C:/Users/aleja/Downloads/App Financiera`, prototipo `prototipos/paideia-local`.
Commit de la capa: `3b67737` («Lleva la jerarquia y las superficies de la maqueta a la app real»).
Capa medida: `prototipos/paideia-local/static/dark_theme.css`, sha256 `492c22cfe53884a8e26067184fbeb38e85b0929862cd80c5354e10a502bb6647` (idéntico a `api/_static/dark_theme.css`; ambas copias enlazadas desde su `index.html`).
Línea base declarada: **631 pruebas Python aprobadas + 1 omitida** y **95 comprobaciones Node**.

Durante la sesión, otro proceso hizo avanzar `HEAD` (`27f9476`, `c8acb3d`, `6ee2007`) y añadió `tests/test_claims_channel.py` a las 22:20:43. Ninguno de esos commits toca `static/` (`git diff --name-only 3b67737..HEAD | grep static/` → vacío) y las mediciones Python se hicieron antes de que apareciera el fichero nuevo, así que la comparación con 631+1 es válida para esta capa. El árbol de trabajo tenía además cambios sin confirmar ajenos a esta tarea (`mission_ledger.py`, `scripts/provision_mission.py`, dos tests del ledger y `test_mission_ledger_hardening.py`); no se tocaron.

## Cómo se ejecutó

- Python: `cd prototipos/paideia-local && python -m pytest tests -q`, sin red externa y sin Groq.
- Node: `node --test tests/*.test.cjs` y, aparte, `node tests/report_unit.js`.
- Navegador: Chromium real `Chrome/156.0.8078.80` en modo headless, una suite cada vez, por CDP (`Runtime.evaluate` con `awaitPromise`), sin caché y con almacenamiento limpiado entre suites. Cada fichero `tests/*.js` se evaluó tal cual, sin reescribirlo.
- Servidores locales, todos en `127.0.0.1`, arrancados para esta prueba:
  - `8772`: app real (`app.create_server`) con catálogo y condiciones reales del prototipo y chat sintético `FakeChatProvider(test_only=True)`; `/api/status` responde `test_only`. Nunca se llamó a Groq.
  - `8773`: fixture D (catálogo sintético `fixture-d`, sin persistencia).
  - `8774`: estático del prototipo para `tests/context_help_fixture.html`.
  - `8775`: `python app.py --port 8775` con `PAIDEIA_GROQ_ENABLED=0` para el estado «IA no configurada».
  - `8780`: copia del árbol **sin** la capa 2 (fuera del repositorio, en el directorio de trabajo temporal), para separar regresión de fallo preexistente.
- No se ejecutaron dos suites de navegador a la vez. Los servidores se cerraron al terminar.

## Python y Node

| Medición | Línea base | Observado | Veredicto |
|---|---|---|---|
| `pytest tests -q`, ejecución 1 | 631 + 1 omitida | 630 aprobadas, **1 fallo**, 1 omitida, 505 subtests (94,05 s) | fallo intermitente de Tk (ver abajo) |
| `pytest` del test fallido en aislamiento | — | 1 aprobada (0,34 s) | pasa |
| `pytest tests/test_secure_groq_smoke.py -q` | — | 4 aprobadas (0,44 s) | pasa |
| `pytest tests -q`, ejecución 2 completa | 631 + 1 omitida | **631 aprobadas, 1 omitida**, 505 subtests (93,15 s) | **igual a la línea base** |
| `node --test tests/*.test.cjs` | 95 | `tests 95 / pass 95 / fail 0` (1.349 ms) | **igual a la línea base** |
| `node tests/report_unit.js` | — | exit 0 | pasa |

El único fallo de la ejecución 1 fue `tests/test_secure_groq_smoke.py::TestSecureGroqSmoke::test_window_roundtrip_saves_sanitized_result_without_key`, que construye una ventana Tk real (está en la lista `GUI_EXCLUSIONS` de `scripts/run_offline_regression.py`). Pasó en aislamiento, pasó el fichero completo y pasó en la repetición de la suite completa. Hay precedente documentado del mismo fallo intermitente de Tk en `docs/PAIDEIA-HASTA-BLOQUEO-SEGUIMIENTO.md`. No es regresión de la capa: la capa es CSS y el test no carga el frontend.

## Suites de navegador

26 ficheros, 23 ejecuciones (cinco ficheros de perfil se encadenan con recargas reales, como exige su propio guion).

| # | Suite | Servidor / ruta | Comprobaciones | Resultado |
|---|---|---|---|---|
| 1 | `b6_blockers_browser.js` | 8772 `#inicio` | 18/18 | PASS |
| 2 | `b6_empty_rate_browser.js` | 8772 `#inicio` | 6/6 | PASS |
| 3 | `b6_journey_browser.js` | 8772 `#inicio` | 40/40 | PASS |
| 4 | `b6_recovery_browser.js` | 8772 `#inicio` | 7/7 | PASS |
| 5 | `c_integration_browser.js` | 8772 `#inicio` | 11 ejecutadas y correctas; aborta por timeout | **FAIL preexistente** |
| 6 | `context_help_test.js` | 8774 `context_help_fixture.html` | 6/6 | PASS |
| 7 | `d_fix2_simulation_ui.js` | 8773 `#simulacion` | bandera `pass` | PASS |
| 8 | `d_fix2_ui.js` | 8772 `#privacidad` | 2/2 | PASS |
| 9 | `d_profile_ui.js` | 8772 `#inicio` | bandera `pass` | PASS |
| 10 | `d_simulation_ui.js` | 8773 `#simulacion` | bandera `pass` | PASS |
| 11 | `dark_theme_goal_browser.js` | 8772 `#inicio` | fondo `[16,17,18]`, texto `[245,246,244]` | PASS |
| 12 | `profile_help_optin_ui.js` | 8772 `#perfil` | bandera `pass` | PASS |
| 13 | `profile_autosave_ui.js` (2 pasos con recarga) | 8772 `#perfil` | 2/2 pasos | PASS |
| 14 | `profile_autosave_failure_ui.js` → `profile_autosave_retry_ui.js` (3 pasos) | 8772 `#perfil` | 3/3 pasos | PASS |
| 15 | `profile_autosave_residue_ui.js` (2 pasos) | 8772 `#perfil` | 2/2 pasos | PASS |
| 16 | `profile_partial_ui.js` → `profile_partial_delete_ui.js` → `profile_partial_retry_ui.js` | 8772 `#perfil` | 3/3 pasos | PASS |
| 17 | `profile_partial_ui.js` → `profile_partial_delete_ui.js` → `profile_revocation_reload_ui.js` | 8772 `#perfil` | 3/3 pasos | PASS |
| 18 | `qa_layout_browser.js` | 8772 `#inicio` | 4/5 | **FAIL preexistente** |
| 19 | `report_browser.js` | 8772 `#escenarios` | 18/18 | PASS |
| 20 | `report_download_browser.js` | 8772 `#escenarios` (guard de impresión) | 14/14 | PASS |
| 21 | `scenario_browser.js` | 8772 `#escenarios` | 114/114 | PASS |
| 22 | `scenario_journey_browser.js` | 8772 `#escenarios` | 33/33 | PASS |
| 23 | `scenario_journey_focus_browser.js` | 8772 `#escenarios` | 9/9 | PASS |

Agregado: 282 comprobaciones correctas de 283 contabilizadas; el denominador no cierra solo porque `c_integration_browser.js` se detiene en la comprobación 11 y no llega a ejecutar las siguientes. 21 ejecuciones PASS, 2 FAIL, ambos preexistentes.

## Comprobaciones específicas del encargo

**Consentimiento y borrado del perfil.** `d_profile_ui.js` (origen limpio): sin consentimiento el chat no emite ninguna petición; con la casilla marcada se observa exactamente una `POST /api/chat` con cuerpo `consent,message` y nada de perfil; «Guardar perfil local» sin opt-in y marcar la casilla sin guardar dejan `localStorage` a 0; «Revocar y borrar copia» lo deja a 0. Las cadenas 13–17 reproducen con recargas reales los estados parciales: guardado que falla (aviso «no se pudo confirmar… podría ser una versión anterior»), residuo de claves antiguas, borrado que falla (dice «No se pudo borrar toda la copia local», nunca «copia borrada»), reintento que sí borra (0 claves) y permiso que no revive tras recargar. Todo PASS.

**Aviso de simulación.** En `8773 #simulacion` el `warning-note` visible dice «ENSAYO FICTICIO · No se enviará nada ni se moverá dinero. No introduzcas identificadores, credenciales, cuenta, tarjeta ni datos de pago.», y el `persistent-notice` recuerda que escenarios y ensayo son simulados. `d_simulation_ui.js` termina el ensayo y comprueba que el justificante incluye «ENSAYO FICTICIO», el importe ficticio y «no es un contrato», con `localStorage` y `sessionStorage` a 0.

**Aviso de IA no configurada.** Con `PAIDEIA_GROQ_ENABLED=0` (`8775`) `/api/status` devuelve `ai.status = not_configured`. El panel contextual muestra, visible y sin recorte, «Chat IA no conectado. Los cálculos, la biblioteca y el glosario funcionan igual.» y el chip «Prototipo local · IA no conectada». Al pulsar «Enviar pregunta» con consentimiento marcado: **0 peticiones** a `/api/chat` y aviso «Chat IA no configurado o no verificable: la pregunta no se ha enviado y no se hará ninguna petición de chat al servidor…».

**Descarga del informe de comparación.** `report_download_browser.js` 14/14 (botón deshabilitado hasta que ambos escenarios están actualizados, fallo transitorio con reintento, rechazo de supuestos manipulados). `b6_journey_browser.js` captura el HTML descargado (6.702 caracteres): empieza por `<!doctype html>`, **no referencia `dark_theme.css`**, no contiene `#101112`, usa `body{color:#111}` y no incluye perfil ni correo. El informe descargado sigue siendo la hoja clara.

**Impresión del informe (debe seguir clara).** `report_browser.js` 18/18 con `window.print` interceptado, más emulación de medio `print` por CDP sobre el informe ya generado: `body` `rgb(255,255,255)` sobre texto `rgb(0,0,0)`, `--paper` cae al valor claro `#F7F5EF`, `#comparison-report-print` en `display:block`, navegación lateral `display:none`, botones del panel `display:none`, bordes de tabla `rgb(119,119,119)`. La captura `print-emulado.png` (evidencia de sesión) muestra la hoja en blanco, legible y sin navegación. La capa está dentro de `@media screen`, así que no alcanza la impresión.

**Navegación por teclado.** `scenario_journey_focus_browser.js` 9/9 (foco a `#scenario-start`, `#scenario-comparison-summary` y `#scenario-report-host`, sin cambiar de ruta ni emitir peticiones). Recorrido real con `Tab` por CDP: primer foco en «Saltar al contenido», después marca, «Revisar estado», «Borrar mi perfil local» y los enlaces 00–03; todos dentro del viewport y con anillo de foco visible `3px solid rgb(169,216,255)` (`#a9d8ff`, el color que fija la capa). `c_integration_browser.js` valida además que `Escape` cierra la ayuda contextual y devuelve el foco al disparador.

**Extra de maquetación.** A 390 px de ancho, las siete rutas (`#inicio`, `#biblioteca`, `#comparar`, `#escenarios`, `#perfil`, `#privacidad`, `#simulacion`) dan `scrollWidth == clientWidth` (375 px) sin elementos desbordados: los rellenos nuevos de la capa no abren scroll horizontal.

## Los dos fallos, y por qué no son de la capa

**`qa_layout_browser.js` — comprobación «home bounds».** `bounds` sale vacío: la prueba busca en `#chat-panel .choice span` etiquetas con el patrón `respuestas.objetivo:` / `detalle_economico.importe_objetivo:`, pero la interfaz ya las rotula como «Objetivo: sin responder en tu mapa», «Horizonte: …», «Importe objetivo: …». El desbordamiento en sí no ocurre (`clientWidth == scrollWidth == 1265`, y a 390 px tampoco). Es desfase entre la prueba y un cambio de copy anterior a esta capa.

**`c_integration_browser.js` — timeout tras 11 comprobaciones.** Espera que el diagnóstico contenga «política» (código `FRESHNESS_POLICY_NOT_CONFIGURED`), pero el servicio devuelve para DEP-01 `PERIOD_MISMATCH` + `METRIC_MISSING` y para DEP-02 `PERIOD_MISMATCH`; el panel se pinta correctamente con esos motivos. La prueba sigue esperando un motivo que el catálogo actual ya no produce.

**Comparación sin la capa.** Se copió el árbol fuera del repositorio, se eliminó `static/dark_theme.css` y su `<link>` en `index.html`, y se sirvió en `8780`. Verificación de que la copia no tiene la capa: `GET /dark_theme.css` → 404 y `dark_theme_goal_browser.js` devuelve fondo `[247,245,239]` (claro), es decir, la capa no está. En esa copia, **`qa_layout_browser.js` falla igual (4/5, mismo «home bounds») y `c_integration_browser.js` falla igual (timeout en el mismo punto, mismas 11 comprobaciones)**. Ambos son fallos preexistentes, no regresiones de la capa 2. Ninguna propiedad CSS puede cambiar códigos de motivo del servicio ni el texto de las etiquetas del chat.

## Veredicto

**Sin regresiones atribuibles a la capa visual 2.** Python 631+1 y Node 95/95 igualan la línea base; 21 de 23 ejecuciones de navegador pasan y las 2 restantes fallan idénticamente sin la capa (desfase prueba-interfaz y expectativa de diagnóstico obsoleta). Consentimiento, borrado, aviso de simulación, aviso de IA no configurada, descarga e impresión clara del informe, foco visible y navegación por teclado se comportan como antes.

## Evidencia

```
$ python -m pytest tests -q            # ejecución 1
1 failed, 630 passed, 1 skipped, 6 warnings, 505 subtests passed in 94.05s

$ python -m pytest "tests/test_secure_groq_smoke.py::TestSecureGroqSmoke::test_window_roundtrip_saves_sanitized_result_without_key" -q
1 passed in 0.34s
$ python -m pytest tests/test_secure_groq_smoke.py -q
4 passed in 0.44s

$ python -m pytest tests -q            # ejecución 2, completa
631 passed, 1 skipped, 7 warnings, 505 subtests passed in 93.15s (0:01:33)

$ node --test tests/*.test.cjs
ℹ tests 95   ℹ pass 95   ℹ fail 0

$ node tests/report_unit.js
report unit: exact cents, whitelist, mismatch, dirty/pending/error and invalid data passed
```

Salidas de navegador (una línea por suite, resumen):

```
b6_blockers 18/18 · b6_empty_rate 6/6 · b6_journey 40/40 · b6_recovery 7/7
scenario_browser 114/114 · scenario_journey 33/33 · scenario_journey_focus 9/9
report_browser 18/18 · report_download 14/14 · d_fix2_ui 2/2 · context_help 6/6
dark_theme_goal: background [16,17,18], text [245,246,244]
c_integration: 11 correctas, timeout en el diagnóstico   (también sin capa)
qa_layout: 4/5, «home bounds» con bounds=[]              (también sin capa)
sin capa: dark_theme_goal background [247,245,239]  ·  qa_layout 4/5  ·  c_integration timeout
```

Los JSON completos de esta sesión (resultado por suite, cadenas de perfil, capturas de impresión y de la IA no configurada) quedaron en el directorio de trabajo temporal del agente, no en el repositorio.

## Límites

- Chromium headless; la impresión se comprobó con emulación de medio `print` por CDP y captura, no con diálogo nativo ni PDF.
- La descarga se verificó por el contenido del `Blob` generado en la página, no por el fichero escrito en disco por el navegador.
- Los servidores son fixtures locales con chat sintético; no se usó Groq, red externa ni datos reales. No se probó el despliegue de `api/` (solo se comprobó que su copia del CSS es idéntica por sha256).
- El árbol se movió durante la sesión (commits y un test nuevos ajenos a la capa); las cifras Python corresponden al estado 631+1 y a los commits sin cambios en `static/`.
