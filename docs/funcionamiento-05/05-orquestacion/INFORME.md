# Funcionamiento 05 — orquestación local de tools de Pai

## Alcance entregado

Se añadió `app/pai_runtime.py` con `ToolChatRunner(provider, dispatcher, max_tool_rounds=2)` y `run(messages)`. El runner consume únicamente el contexto que el servicio ya autorizó; no decide consentimiento ni incorpora perfiles/historial. Usa `definitions()` y `dispatch()` del contrato `local-tools.v1`, una allowlist fija de cinco tools, validación cerrada de argumentos, una tool por respuesta, máximo dos rondas (tres llamadas al modelo), rechazo de IDs/ciclos repetidos y errores sin reintentos.

El ciclo de cálculo llama al dispatcher con los seis campos vigentes de `domain.calculate_scenario`; el runner no ejecuta el motor ni interpreta texto. Las respuestas de herramientas vuelven como mensajes `assistant.tool_calls` + `tool` con el mismo ID, y resultado JSON marcado como dato no confiable. El razonamiento separado no forma parte del DTO ni de solicitudes posteriores. `sources` se deriva solamente de `sources` en salidas válidas del dispatcher; no se extraen citas del texto del modelo.

## Verificación aislada

- Comando: `python -m unittest tests.test_pai_runtime -v` (desde `app/`): **14 tests, OK, exit code 0**.
- También se reprodujeron en conjunto los tests del runtime y del dispatcher: **32 tests, OK**. Dos pruebas del runtime usan el `ToolDispatcher` real con repository sintético y proveedor fake: una recorre fuentes de identidad y otra el cálculo por el dispatcher/motor; el builder real valida las definiciones/messages antes de cada respuesta fake.
- Suite completa: `python -m unittest discover -s tests -q`: **135 tests, OK, exit code 0**.
- Los doubles de proveedor y dispatcher llevan `test_only=True`; el resto de datos de prueba son fixtures sintéticas. No se llamó a red, Groq, una cuenta ni una base de datos.
- Evidencia TDD: el test inicial falló por ausencia de `pai_runtime`; luego las regresiones de argumentos no hashables y DTO de error de dispatcher fallaron antes de sus arreglos. Tras los cambios, los tests pasan. La prueba de argumentos confirma que `family` no hashable se rechaza con respuesta segura y sin invocar dispatch.
- Casos cubiertos: pregunta→tool→respuesta, builder real y correlación de `tool_call_id`, contexto de entrada no mutado, dos tools secuenciales y límite de ronda, call ID/ciclo duplicado, múltiples/unknown/argumentos inválidos, refusal/truncation/errores sin reintentos, razonamiento no replay, fuente hostil en rol `tool`, y URLs del modelo excluidas de `sources`.

## Aislamiento frente a prompt injection

Una prueba coloca una instrucción hostil sintética en `data.source_content` del dispatcher. Comprueba que la instrucción aparece solo en el contenido JSON de un mensaje `tool`, que el mensaje `system` de entrada permanece intacto y que no se agrega razonamiento del modelo. Es una separación técnica de roles y datos; **no** se afirma garantía semántica total ni eliminación/detección de prompt injection. La prueba tampoco certifica que un modelo siga las instrucciones correctamente.

## Integración y pendientes del coordinador

La implementación no modifica `app.py`, `backend_services.py`, `providers.py` ni la UI. El endpoint de chat y el flujo de consentimiento antes de invocar el runner quedan pendientes del coordinador; el runtime por sí mismo no toma esa decisión. También queda pendiente probar el dispatcher real contra este contrato común. No se afirma chat real, activación de Groq, prueba A/B/C, ofertas cuantitativas verificadas ni integración global.

Fuentes devueltas por `get_sources` son de identidad conforme al dispatcher local y no certifican condiciones de una oferta. No hay SQL arbitrario, compra ni efecto externo en la registry.
