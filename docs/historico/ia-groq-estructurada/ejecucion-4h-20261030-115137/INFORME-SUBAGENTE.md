# Integración parcial sintética — subagente

Inicio comprobado: 2026-10-30T11:51:54+01:00. Corte: 2026-10-30T15:50:34+01:00. Última comprobación antes del informe: 2026-10-30T11:58:36+01:00.

## Resultado

Implementado únicamente ensamblaje explícito de servidor `structured_test_only=True`, prohibido para sesión real, con transporte de clase ficticia exacta, misión con digest, admisión existente, single-flight, reserva `MissionBudget` real, guarda final, petición `strict:false`, parser cerrado y render/cálculo local. Prueba HTTP loopback usa manifiesto sintético en directorio efímero y parche temporal de `NEW_MANIFEST` solo en el proceso de pruebas, sin alterar whitelist ni misiones productivas. Escenario separado no entra en el cuerpo; no se garantiza que el usuario no escriba datos en el propio mensaje. No prueba proveedor externo ni calidad del modelo.

## Evidencia ejecutada

- RED: `python -B -m unittest tests.test_session_structured_integration -v`: error esperado `Session.start_server() got an unexpected keyword argument 'structured_test_only'`; GREEN tras implementación: 1 OK.
- RED→GREEN de revocación tras conexión simulada y revocación tras POST simulado: cada test falló por atributo de fixture ausente y luego pasó; sincronización en memoria, sin socket externo.
- `python -B -m unittest tests.test_session_structured_integration tests.test_session_structured_security tests.test_session_send_boundary tests.test_session_mission tests.test_mission_journal_integrity tests.test_structured_counted_provider -q`: 36 OK. Incluye cuota persistente 24, ticket cerrado, consentimiento y campos extra, revocación antes/después de guardia, corte/corrupción durante conexión simulada, 429, duplicados, refusal, length, tool calls, sin reintento; sin afirmar que cada negativa tuvo su propio RED.
- `python -B -m unittest discover -s tests -p 'test_*.py' -q`: 317 OK en una versión intermedia antes de los últimos tests/cambios. **Incidente de alcance:** esa ejecución incluye `test_session_ui_feedback` y otros tests Tk que crean ventanas reales ocultas con credenciales ficticias; contravino la prohibición de GUI. Se cerraron en los propios tests; no se repetirán. Ninguna clave real ni GUI de credenciales reales se usó. No se debe presentar esa ejecución como totalmente conforme a las restricciones.

## Límites

No implementado modo real ensamblable: sigue bloqueado explícitamente; falta política de autorización para misión nueva, marcador de estado externo `not_started`/`sent`/`unknown`, aislamiento de excepciones y revisión independiente. El modo sintético usa metadatos `test_only`, `external_sent:false` correctamente por su transporte cerrado; errores genéricos no exponen estado de envío externo. No afirmar cancelación física ni protección antirrollback coordinado. Sin revisión independiente de estos cambios. Resta prueba específica conjunta de single-flight y fallo ambiguo, regresión sin GUI y revisión de seguridad/integración; no considerar hitos completos.
