# Adaptador de proveedores IA — interfaz y límites

**Estado actualizado:** adaptador revisado y conectado a `app.py` a través de `backend_services.LocalChatService`, con el servicio apagado por defecto. El arranque normal mantiene `CHAT_NOT_CONFIGURED`. La integración HTTP se ha probado solo con transportes de test explícitos; ver `BACKEND-INTEGRACION.md`. No se creó cuenta, no se leyó ninguna clave del entorno durante esta entrega y no se hizo una llamada externa. La API no está probada con Groq; no se afirma calidad, capacidad, latencia ni disponibilidad.

## Interfaz

Desde `app/`, el adaptador expone:

```python
from providers import GroqHTTPSJSONTransport, GroqProvider

provider = GroqProvider.from_environment(
    GroqHTTPSJSONTransport(),
    model="openai/gpt-oss-20b",
)
messages = [
    {"role": "system", "content": "Explica únicamente información validada."},
    {"role": "user", "content": "Pregunta sintética de ejemplo."},
]
result = provider.chat(messages)  # solo tras autorización; sin opt-in devuelve disabled
```

`chat()` devuelve `ChatResult(answer, reasoning, tool_calls, finish_reason, refusal)`. `answer` y `reasoning` son campos separados cuando la API envía un campo explícito `reasoning` o `reasoning_content`; el adaptador no intenta inferir ni extraer razonamiento embebido en `content`, no concatena campos ni genera una respuesta de respaldo. No devuelve el secreto, el cuerpo bruto, el nombre/modelo informado por el proveedor ni métricas de uso.

`build_chat_request(...)` es un constructor puro: no lee el entorno, no abre conexiones y devuelve bytes JSON. Acepta solo mensajes `system`, `user`, `assistant` y `tool`; restringe los campos por rol, valida JSON de argumentos de herramientas y exige que cada respuesta `tool` apunte a un `tool_call_id` previo. Las definiciones de función se reciben del servidor. No implementa `response_format`/Structured Outputs; el informe local advierte que Structured Outputs estrictos y tool use no se combinan en una misma llamada.

El transporte inyectable implementa `post(*, host, path, headers, body, timeout) -> TransportResponse(status, body)`. `GroqHTTPSJSONTransport` fija el destino a `api.groq.com/openai/v1/chat/completions` y usa HTTPS de la biblioteca estándar. El fake `TestOnlyFakeTransport` vive solo en `tests/test_providers.py`, está marcado `test_only` y no afirma ser un proveedor ni un endpoint real.

## Opt-in y credenciales

El proveedor está deshabilitado por defecto. `GroqProvider.from_environment(...)` habilita solo si `PAIDEIA_GROQ_ENABLED` vale exactamente `1`; `chat()` lee entonces `GROQ_API_KEY` del entorno del proceso. Primero valida la solicitud; con opt-in apagado o clave ausente/inválida no invoca el transporte. No pasar claves en argumentos de línea de comandos, navegador, prompts o logs. La clave solo se incorpora a la cabecera `Authorization` durante el envío autorizado; no se conserva en el resultado.

Este código no configura ninguna variable, cuenta o clave por sí mismo. La configuración queda deshabilitada en ausencia de opt-in explícito y autorización separada. La bandera no comprueba el nivel Free ni controla facturación; con presupuesto actual de 0 EUR, no activar ni llamar al proveedor hasta confirmar autorización y que no genere coste.

## Límites y validación

- Allowlist local de modelos: `openai/gpt-oss-20b` (predeterminado) y `openai/gpt-oss-120b`; no acepta alias ni modelos arbitrarios.
- Salida: 256 tokens por defecto; ampliable solo por configuración validada hasta 900. El chat local usa 800 (`PAIDEIA_GROQ_MAX_TOKENS`).
- Request: 16 KiB máximo. Response: 64 KiB máximo; la lectura HTTPS se corta en 64 KiB + 1 byte para detectar exceso.
- Timeout predeterminado: 5 segundos, configurable solo entre 0,1 y 20 segundos.
- Cero reintentos. Errores de timeout, 401, 429, 5xx, otros estados no exitosos, respuesta JSON inválida o sobrelímite se convierten en códigos genéricos sin reflejar cuerpo, secreto ni excepción interna.
- Admite como máximo una llamada de herramienta por respuesta; no ejecuta herramientas.
- Las llamadas devueltas se entregan al servidor como nombre y argumentos JSON ya parseados. El dispatcher del servidor debe comprobar allowlist, schema exacto y reglas semánticas, y rechazar herramienta desconocida o argumentos inválidos antes de ejecutar. Este módulo no sustituye ni implementa ese dispatcher; mientras no se integre y pruebe esa frontera, no se debe ejecutar `tool_calls`.

## Contrato de mensajes y evidencia

La forma de `messages`, `tool_calls` y el enlace `tool_call_id` sigue la evidencia local capturada en `docs/validacion-04/02-groq/evidencia/02-tool-use-browser.txt`. El informe `docs/validacion-04/02-groq/INFORME.md` recomienda estos dos IDs canónicos, registra que no admiten uso paralelo de herramientas y propone un techo práctico de 256 tokens. Es evidencia documental, no una prueba de API, cuenta ni calidad.

El contrato de Pai ubica la allowlist, la validación de argumentos y el rechazo de nombres desconocidos en el backend (`docs/planificacion-03/01-pai-tools/ESPECIFICACION.md`, apartados 2, 3 y 4). La aplicación local integra el adaptador, pero no el dispatcher: en esta fase no anuncia tools y rechaza cualquier tool_call recibido sin ejecutarlo.

## Pruebas

`python -B -m unittest discover -s tests -p test_providers.py -v` es offline. Usa un fake marcado test-only para verificar payload, cabeceras, opt-in, ausencia de eco del secreto, errores y ausencia de reintentos. La prueba del transporte HTTPS sustituye `HTTPSConnection` por un fake; no abre sockets. Ninguna de estas pruebas determina la calidad o capacidad de un modelo.
