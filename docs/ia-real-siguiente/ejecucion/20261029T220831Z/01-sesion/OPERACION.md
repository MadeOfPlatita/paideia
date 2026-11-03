# Sesión de misión: contrato y límites

Misión: `paideia-ia-20261029T220831Z`; corte fijo 2026-10-29T23:08:31.985015Z, 24 intentos compartidos. No se ha abierto GUI ni consumido API externa en esta preparación.

Desde `prototipos/paideia-local`, tras revisión y pruebas offline del coordinador:

```text
python -B secure_groq_session.py --mission "C:/Users/aleja/Downloads/App Financiera/docs/ia-real-siguiente/ejecucion/20261029T220831Z/MISSION.json"
```

La clave se introduce exclusivamente en la ventana enmascarada, nunca por argumentos o chat. La casilla Free comienza desmarcada; no verifica la cuenta ni garantiza coste. La evaluación tiene casilla independiente y botón manual `Ejecutar evaluación A/B/C ahora`; no arrancarla antes de la revisión de calidad mínima.

READY es un JSON por stdout con `event`, `run_id` y `test_only`. Bajo esta carpeta de misión se generan `mission-ledger.json` y `mission-ledger.json.lock`; el segundo es simultáneamente bloqueo interproceso y diario de integridad. Cada arranque crea identificador `run-<hex>` y escribe `run-<hex>/session-status.json`; el informe, si se ejecuta, va a `run-<hex>/session-benchmark.json`. `calls` es de esa sesión, `mission_remaining` del ledger compartido. Nunca borrar, restaurar, editar ni sustituir ledger, lock o manifiesto: detenerse ante corrupción, pérdida o discrepancia; no hay reparación automática.

El registro confía en el operador y sistema local: detecta repetición del JSON mientras el diario permanece intacto, no puede detectar restauración coordinada de ambos archivos ni su eliminación conjunta. No es un almacenamiento resistente a un operador adversario. Las reservas se registran y sincronizan antes de TLS; interrupciones en la escritura bloquean la misión en vez de reponer cuota. Revocar o expirar bloquea el compromiso lógico tras TLS; no garantiza la cancelación de una petición ya comprometida ni el instante físico de transmisión.

Verificado offline: Python `unittest discover` 227 pruebas, Node 24 y sintaxis JS; transporte ficticio, sin clave real. Antes de fase real siguen pendientes revisión independiente y QA mínima; no inferir calidad real ni autorización de catálogo de estos resultados.
