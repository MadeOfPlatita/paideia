# Funcionamiento 05 — dispatcher de tools de Pai

## Entrega

Se implementó `app/pai_tools.py` como `ToolDispatcher(repository, comparison_service)`, sin importar `app.py`. Expone `definitions()` para el builder OpenAI local y `dispatch(name, arguments)` en el contrato `local-tools.v1`. Los nombres aprobados se conservan literalmente: `search_products`, `get_product_detail`, `compare_products`, `calculate_scenario` y `get_sources`.

Las entradas son cerradas, con validación de tipos estrictos, campos desconocidos, familias, IDs locales literales, unicidad, cotas, nulos, NaN/Infinity y valores booleanos. Los errores tienen códigos fijos, mensajes sin datos de entrada ni excepción y DTO compatible con el `ToolChatRunner` coordinado (`data: {}` en error). La búsqueda aplica `limit` por respuesta; no fija el tamaño máximo del catálogo.

## Límites de dominio y fuentes

- Los productos se devuelven como candidatos internos de investigación, no publicables y con condiciones pendientes. El dispatcher solo proyecta metadatos permitidos del repositorio.
- La comparación de metadatos no invoca el servicio. Si se pide el criterio permitido, se delega en `comparison_service.compare` sin reproducir reglas de comparabilidad; un bloqueo sigue sin valor numérico. `calculate_scenario` usa directamente `domain.calculate_scenario` y sus seis campos/unidades.
- Las fuentes identifican producto solamente. Sus URLs proceden del repositorio; no se aceptan URLs en argumentos ni se hacen fetch. `source_ref` declara `namespace: local-tools.v1` e ID `identity:<ID-local>` (no UUID); las citas no acreditan condiciones.
- No se añadieron SQL, escrituras, compras, pagos, LLM, datos reales, dependencias ni acceso de red.

## Evidencia de pruebas

- `python -m unittest tests.test_pai_tools -v`: **20 tests, OK**.
- `python -m unittest tests.test_pai_runtime -v`: **14 tests, OK**; los casos con dispatcher real verifican la definición, citas de identidad y cálculo con fake provider.
- `python -m py_compile pai_tools.py tests/test_pai_tools.py`: OK.
- `python -m unittest discover -s tests -q`: **143 tests, OK** en la última ejecución. Una ejecución anterior de la suite registró un fallo transitorio en `tests.test_chat_admission.ChatAdmissionTests.test_lifecycle_calls_report_expired_instead_of_duplicate_for_timed_out_ticket` (esperado `expired`, recibido `duplicate`); la prueba individual y su módulo aislado pasan. Ese frente no se modificó aquí.

Las pruebas positivas de herramientas usan solo repository `SYN-*` sintético en memoria. Hay cobertura de comparabilidad no publicable/bloqueada y verificación de que argumentos/resultados no mutan el repositorio. No se declara integración HTTP ni chat real.
