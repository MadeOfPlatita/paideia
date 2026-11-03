# MissionBudget: aislamiento de parches y regresión de orden

## Causa

En `test_window_requires_separate_confirmation_and_button_for_benchmark`, el parche de `launcher.MissionBudget` se iniciaba antes de `patch.dict(launcher.__dict__, ...)`. Este último tomaba una instantánea del diccionario ya contaminada por el `MagicMock`. La prueba detenía manualmente el parche de `MissionBudget` para que funcionara `isinstance`, pero en los cleanups LIFO `patch.dict.stop()` restauraba su instantánea y reintroducía el mock; la segunda llamada a `MissionBudget.stop()` ya no lo retiraba. Las pruebas posteriores fallaban en `Session.__init__` con `TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union`.

## Evidencia RED y corrección

- Nueva prueba de regresión ejecutada antes de corregir: **1 failed**, la aserción de identidad observó `MagicMock` en lugar de la clase real.
- Reproducción de orden con un probe temporal que sustituye en memoria únicamente el antiguo `patch.dict`, seguido de `tests/test_session_mission.py`: **4 failed, 7 passed**, salida 1. Los cuatro fallos fueron el `TypeError` anterior. El probe no modificó archivos de producción ni de pruebas.
- Sustitución de `patch.dict` por parches individuales de `tk` y `ttk`, conservando `addCleanup`, la restauración previa del tipo para `isinstance`, las comprobaciones de consentimiento/ledger y el join del hilo. `MissionBudget` usa ahora un context manager para cerrar también ante excepciones. Se añadieron regresiones para limpieza normal y tras excepción sintética.

## Verificación posterior

- `pytest tests/test_mission_session.py tests/test_session_send_boundary.py -q`: **16 passed** antes de añadir la segunda regresión de excepción.
- Runner offline, un intérprete, `tests/test_mission_session.py tests/test_session*.py`: **55 passed**, **4 deselected**, salida 0, sin errores de colección.
- Runner offline sobre la suite completa seleccionable: **398 passed** (369 unittest, 29 pytest), **6 deselected**, salida 0, sin errores de colección. Las seis exclusiones son casos que crean Tk real; no se evaluó esa cobertura.
- Informes JSON completos de estas dos ejecuciones: `mission-order-report.json` y `mission-full-report.json` en el scratch de la sesión. El runner bloquea Tk y conexiones externas en el proceso, pero no es sandbox y los procesos hijos no heredan estas barreras. Los transportes HTTPS de las pruebas son mocks; no se realizó una llamada real ni se usaron claves reales. Los ledgers usados en estas pruebas son temporales.
