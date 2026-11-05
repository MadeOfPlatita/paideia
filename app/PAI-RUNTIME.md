# ToolChatRunner de Pai — prototipo local

**Estado: implementación aislada, no integrada en HTTP.** Este módulo (`pai_runtime.py`) coordina un proveedor compatible con `providers.ChatResult` y un dispatcher `local-tools.v1`. No activa ni configura Groq.

## Frontera de entrada

`ToolChatRunner(provider, dispatcher, max_tool_rounds=2).run(messages)` recibe únicamente los mensajes ya validados y autorizados por el servicio. No interpreta ni decide consentimiento, no agrega perfil, historial externo, memoria, mensajes de sistema ni instrucciones de usuario. Copia el contexto antes de extenderlo y no muta el argumento recibido. El servicio que lo integre debe aplicar sus controles de consentimiento antes de llamarlo.

El dispatcher debe implementar exactamente:

- `definitions() -> list[OpenAI tool definition]`, con una definición única por cada herramienta permitida.
- `dispatch(name, arguments) -> dict` del contrato `local-tools.v1`: `schema_version`, `tool`, `status`, `data`, `sources`, `error`.

El runner falla cerrado si la registry no contiene exactamente las cinco herramientas, si la respuesta del dispatcher no cumple esa forma o si el proveedor/dispatcher falla. No acepta definiciones suministradas por el cliente.

## Registry y validación

El registro fijo es `search_products`, `get_product_detail`, `compare_products`, `calculate_scenario` y `get_sources`.

- `search_products`: `{query, family, limit}`; query de hasta 100 caracteres, family nula o familia local, limit entero 1..20.
- `get_product_detail`: `{product_id}` con forma de ID local del snapshot.
- `compare_products`: `{product_ids, criterion}`; 2..4 IDs locales únicos y criterio nulo o `deposit_tae_12m_eur`.
- `calculate_scenario`: exactamente `principal`, `annual_rate_percent`, `years`, `monthly_contribution`, `method`, `inflation_percent`, conforme a `domain.py`.
- `get_sources`: `{product_ids}`; 1..20 IDs locales únicos. La recuperación no acepta URL arbitraria.

El runner valida nombre, propiedades cerradas, tipos y límites antes de llamar a `dispatch`. El dispatcher conserva la validación de pertenencia/semántica del catálogo; la validación del runner no sustituye a la del dispatcher. El cálculo se ejecuta solo mediante `dispatch("calculate_scenario", ...)`; el runner no evalúa texto ni importa/llama directamente el motor. No hay herramienta SQL, compras ni herramientas generadas por el modelo.

## Presupuesto y ciclo

- Una llamada de herramienta como máximo por respuesta del modelo (el adaptador existente acepta cero o una).
- `max_tool_rounds` admite 0..2; con el valor predeterminado se ejecutan como máximo dos rondas y tres llamadas al modelo en total (inicial + dos continuaciones).
- IDs de llamada repetidos y firmas de herramienta/argumentos repetidas se rechazan. No se reintenta ni al proveedor ni al dispatcher.
- Unknown tools, argumentos no válidos, lotes con varias llamadas, IDs/ciclos repetidos y exceso de rondas terminan con un error/refusal fijo; no se revelan argumentos ni mensajes de excepción.
- Refusal explícito y truncado (`finish_reason="length"`) son terminales y no ejecutan llamadas de herramienta.

Para continuar una llamada, se añade un mensaje `assistant.tool_calls` y luego un mensaje `tool` que conserva el mismo `tool_call_id` y el nombre registrado. El resultado se serializa como JSON dentro de `untrusted_tool_result`; la siguiente petición se valida por el builder real del proveedor. El razonamiento separado de `ChatResult` se ignora: no se devuelve ni se incorpora al contexto posterior.

## DTO y procedencia

`run()` devuelve únicamente `answer`, `refusal`, `finish_reason`, `tool_events` y `sources`; no incluye `reasoning`. Cada fuente de salida se copia exclusivamente desde `sources` de un resultado válido del dispatcher y se envuelve con `tool_call_id` y nombre de herramienta. Las URLs/citas presentes solo en el texto del modelo no se convierten en fuentes. En particular, una fuente recuperada por `get_sources` es identidad/procedencia según el dispatcher y no prueba por sí sola que una oferta o condición esté verificada.

`tool_events` registra un estado terminal por llamada con `tool_call_id`, `name`, `state` y `status`; herramientas conocidas completadas se marcan `executed`, y rechazos/errores como `rejected`. Un nombre desconocido se normaliza a `null` en el evento.

`source_content` permanece en el resultado JSON del mensaje `tool`; no se promueve a `system` ni se concatena a instrucciones. Esto es aislamiento de roles/estructura, **no** una garantía de que el modelo ignore instrucciones hostiles: la prompt injection no se elimina mediante este mecanismo.

Los DTO de error usan mensajes fijos y finish reason `error` o `tool_error`; los detalles privados del proveedor, dispatcher y errores no se devuelven. Una respuesta del modelo con una URL inventada puede seguir apareciendo como texto de `answer`, pero nunca se incorpora a `sources`.

## Pruebas

`tests/test_pai_runtime.py` usa exclusivamente proveedor/dispatcher fake marcados `test_only`. Antes de devolver cada `ChatResult`, el fake llama a `providers.build_chat_request(messages, tools=tools)` y decodifica el cuerpo; no hace llamadas de red ni activa credenciales. Las respuestas sintéticas se etiquetan `TEST ONLY`.

## Pendiente de integración

Queda pendiente que el coordinador conecte el `ToolDispatcher` real y decida/documente el endpoint y su flujo de consentimiento antes de invocar el runner. Este cambio no habilita `/api/chat`, no cambia `app.py`, `backend_services.py`, `providers.py` ni UI, no configura cuentas/credenciales y no acredita chat real, contexto A/B/C ni datos de catálogo verificados.
