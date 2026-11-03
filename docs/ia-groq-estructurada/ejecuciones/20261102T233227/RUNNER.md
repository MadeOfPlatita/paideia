# Runner de regresión offline y sin GUI

Desde `prototipos/paideia-local`, ejecutar con un intérprete que ya tenga pytest. En esta máquina se comprobó pytest 9.1.1 en `C:/Users/aleja/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`; el `python` activo de la sesión no lo tenía. No se instala nada. Si falta pytest, el runner escribe JSON con error y sale con código 2: no sustituye la suite por unittest ni omite silenciosamente las funciones pytest.

## Comandos para coordinación (Git Bash en Windows)

Ejecutar **solo después de que terminen las ediciones concurrentes**. El primer comando es una línea base de **colección**, no una ejecución; el segundo ejecuta la regresión Python y conserva el código de salida de pytest. Crear nombres nuevos para cada ejecución: el JSON indicado se sobrescribe si ya existe. Una ruta relativa se interpreta desde el directorio actual.

```bash
cd 'C:/Users/aleja/Downloads/App Financiera/prototipos/paideia-local'
PY='C:/Users/aleja/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe'
OUT='C:/Users/aleja/Downloads/App Financiera/docs/ia-groq-estructurada/ejecuciones/20261102T233227'
export TMPDIR='C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/cache/scratch'
"$PY" scripts/run_offline_regression.py --collect-only --json "$OUT/baseline-collection.json"
"$PY" scripts/run_offline_regression.py --json "$OUT/regression-python.json"
```

El stdout coincide con el JSON. Los node IDs de selección, exclusiones GUI, deselecciones, errores de colección y resultados se representan como SHA-256; no se guardan nombres ni parámetros originales, tracebacks ni salida capturada de pytest. Los hashes son deterministas y pueden adivinarse por diccionario: no son anonimización fuerte. `phase_outcomes` conserva los resultados de setup, call y teardown que realmente ocurrieron; `outcomes` es un agregado con prioridad failed > xpassed > xfailed > skipped > passed. Cualquier failed, xfailed o xpassed en cualquier fase fuerza salida no cero. Un error real de setup o teardown es failed incluso si pytest lo transforma por una marca xfail. Si un test falla, investigar por separado con datos sintéticos en un entorno seguro; un informe sin traceback no prueba su causa. `--collect-only` no ejecuta tests, pero sí importa módulos de test; no usar tests que tengan efectos laterales al importar.

Para ejecutar solo pruebas concretas, añadir rutas o node IDs pytest tras `--json ruta.json`. El runner incluye las pruebas HTTP Python en la selección predeterminada; cada test es responsable de cerrar sus servidores. No lanza un servidor persistente ni las pruebas Node. Opcionalmente, tras revisar su seguridad y completar las ediciones, ejecutar la suite Node por separado desde el mismo directorio:

```bash
node --test tests/*.test.cjs
```

Node se ejecuta fuera del guard de Python: ese comando no ofrece bloqueo de red ni aislamiento de procesos. Su resultado es independiente del JSON Python y no debe sumarse automáticamente con pruebas/subtests históricos.

## Exclusiones GUI exactas

- `tests/test_secure_groq_smoke.py::TestSecureGroqSmoke::test_window_masks_key_and_does_not_submit_on_open` — crea ventana Tk real.
- `tests/test_secure_groq_smoke.py::TestSecureGroqSmoke::test_window_roundtrip_saves_sanitized_result_without_key` — crea ventana Tk real.
- `tests/test_session_ui_feedback.py::UIFeedbackTests::test_failed_start_is_terminal_and_explains_occupied_port` — crea ventana Tk real.
- `tests/test_session_ui_feedback.py::UIFeedbackTests::test_pending_expiry_erases_entry_and_disables_start` — crea ventana Tk real.
- `tests/test_session_ui_feedback.py::UIFeedbackTests::test_mission_cutoff_overrides_legacy_on_button_invoke` — crea ventana Tk real.
- `tests/test_session_ui_feedback.py::UIFeedbackTests::test_invalid_clock_fails_closed_without_leaking` — crea ventana Tk real.

Las seis pruebas anteriores se deseleccionan por node ID exacto, tras importar sus módulos; no hay módulos GUI ignorados automáticamente ni comprobación AST. Los tests generados dinámicamente o parametrizados no coinciden con esos IDs exactos y deben auditarse. Las pruebas vecinas permanecen seleccionadas. La importación puede fallar si falta tkinter; el guard impide construir Tk en este proceso, no en procesos hijos.

## Alcance y límites

El recolector usa pytest para unittest y tests de función, incluidos casos parametrizados; `unittest` cuenta casos `unittest.TestCase`, `pytest_other` cuenta todos los demás nodos de pytest. No suma subtests como tests independientes. Cualquier error de colección implica salida no exitosa; los recuentos son solo de lo efectivamente recolectado. Las 14 autopruebas sintéticas del runner pasaron en esta corrección; no se ejecutó la suite global ni Node. Los recuentos de colecciones anteriores corresponden a otros cortes y no demuestran cobertura completa.

El runner intercepta la creación de intérpretes `_tkinter` cuando existe y bloquea conexiones, DNS, envíos UDP y binds no-loopback mediante `socket` en el proceso de pytest; admite HTTP por loopback. No es un sandbox de seguridad: parches nativos, extensiones, procesos hijos y Node pueden eludir estos guardas. Hay tests existentes que crean subprocesos; deben mantenerse revisados como sintéticos, sin claves ni red externa. No cargar credenciales reales ni ejecutar pruebas no auditadas. Los tests con servidores propios deben cerrarlos en `finally`/cleanup; la prueba sintética del runner verifica servidor loopback con cierre y unión del hilo. El runner no gestiona procesos/servidores que tests ajenos dejen vivos.
