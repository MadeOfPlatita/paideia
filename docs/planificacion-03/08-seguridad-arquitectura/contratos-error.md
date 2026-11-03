# Contratos de error — API Paideia (propuesta)

**Estado:** contrato de diseño; no corresponde a endpoints implementados. Relacionado con C11/C12/C14 de [`controles.json`](./controles.json). El backend valida y devuelve el código; texto seguro en español para UI. Nunca reenviar el texto/JSON original del proveedor o del parser.

## Envolvente común

JSON UTF-8; respuestas de chat con `Cache-Control: no-store`; incluir `request_id` aleatorio no derivado de usuario/IP; no devolver stack, SQL, prompt, salida cruda, hostname privado, clave, cookie, cabecera ni contenido de fuente. El campo `message` se renderiza como texto, no Markdown confiable. `retry_after_seconds` sólo es entero no negativo cuando se conoce; `null` en otro caso.

```json
{
  "error": {
    "code": "CHAT_DISABLED",
    "message": "El asistente no está disponible ahora.",
    "request_id": "req_test_only_01",
    "retryable": false,
    "retry_after_seconds": null
  }
}
```

`req_test_only_01` es marcador ficticio del contrato, no identificador real. No aceptar un `request_id` del cliente como correlación de confianza. El ID no autoriza ni demuestra que el proveedor recibió una solicitud.

## Catálogo de errores

| HTTP | `code` | Mensaje de interfaz | `retryable` / detalle |
|---:|---|---|---|
| 400 | `INVALID_REQUEST` | «No se pudo interpretar la solicitud. Revisa los campos e inténtalo de nuevo.» | No reintentar la misma carga sin cambio. Sin revelar campo sensible. |
| 413 | `REQUEST_TOO_LARGE` | «El mensaje supera el límite permitido.» | No reintentar hasta reducirlo. |
| 422 | `TOOL_ARGUMENT_REJECTED` | «No se pudo procesar esta consulta; prueba con otra pregunta.» | Rechazo interno de tool/esquema; no incluir argumento/modelo. No hacer dispatch ni pedir al LLM que repare. |
| 422 | `SOURCE_REJECTED` | «La fuente no está permitida o no se pudo validar.» | Sólo ingesta interna; fuente/URL/razón técnica no se devuelve al público. |
| 429 | `SESSION_LIMIT` | «Has alcanzado el límite temporal del asistente. Puedes volver a intentarlo más tarde.» | `retry_after_seconds` y header `Retry-After` de la cuota **de esa sesión**, si está calculado. No aplicar por NAT compartida. |
| 503 | `CHAT_DISABLED` | «El asistente no está disponible ahora; el catálogo y el simulador siguen disponibles.» | Sin reintento automático. |
| 503 | `GLOBAL_BUDGET_EXHAUSTED` | «El asistente no está disponible ahora; el catálogo y el simulador siguen disponibles.» | Sin `Retry-After` salvo reapertura programada conocida. No informar saldo/coste interno. |
| 503 | `GLOBAL_CAPACITY` | «El asistente está ocupado ahora. Puedes continuar con el catálogo y el simulador.» | Limitación global, no IP. Sin retry automático; si hay ventana de espera segura, `Retry-After` opcional. |
| 503 | `PROVIDER_RATE_LIMIT` | «El asistente no está disponible ahora. Puedes volver a intentarlo manualmente más tarde.» | Mapear proveedor 429/503; se puede trasladar un intervalo `Retry-After` válido y acotado, nunca el body crudo. Ninguna repetición automática. |
| 504 | `PROVIDER_TIMEOUT` | «No se recibió respuesta a tiempo. No se reintentará automáticamente; puedes enviar una nueva solicitud manual.» | No afirmar que el proveedor no recibió el texto ni que no hubo coste. Una nueva petición consume cuota/budget. |
| 502 | `PROVIDER_RESPONSE_REJECTED` | «No se pudo validar la respuesta del asistente. Prueba más tarde o consulta el contenido educativo.» | JSON incompleto, salida fuera de esquema/tamaño o formato inválido: descartar entera; no ejecutar herramientas. |
| 500 | `INTERNAL_ERROR` | «Ha ocurrido un error. El catálogo y el simulador pueden seguir disponibles.» | `request_id` para soporte; sin excepción, consulta ni configuración en payload. |

El catálogo puede responder independientemente del chat; si los datos están caducados, indicar fuente/fecha/advertencia o excluir de comparaciones conforme a regla pendiente. No sustituir una respuesta rechazada del LLM por cifras inventadas.

## Reglas de transición

1. Validar tamaño, JSON, tipos, campos y cuota de sesión **antes** de llamar al proveedor. Reservar budget global atómicamente antes de cada solicitud.
2. `PAIDEIA_CHAT_ENABLED=false`, proveedor no seleccionado, términos/retención sin revisar, límite de gasto ausente o breaker abierto: no realizar salida de red y responder `CHAT_DISABLED`/`GLOBAL_BUDGET_EXHAUSTED` según causa.
3. Por petición de chat, máximo una llamada upstream. Configurar reintentos automáticos del SDK, proxy y cliente en cero. Sólo el usuario puede iniciar otra petición nueva; timeout tras envío es resultado incierto.
4. Validar tools/salida del proveedor con esquema cerrado. Tool desconocida o malformada: descartar, registrar sólo código `TOOL_ARGUMENT_REJECTED` y request_id, y no tocar BD.
5. Respuesta visible no contiene campos internos, prompt de sistema, extractos privados, clave, URL de origen interna, SQL, token de proveedor, stack ni texto de excepción.
6. Una excepción nunca degrada cálculo/catalogación local ni crea usuario, lead, solicitud, contratación o transacción.

## Aceptación del contrato

- Test automático por fila de la tabla: status, código, `message`, booleano `retryable`, forma de `retry_after_seconds`, `request_id`, `Cache-Control` y ausencia de campos extra.
- Inyectar errores simulados 429/503/timeout/esquema inválido del proveedor: exactamente cero reintentos automáticos y cero secretos/prompt en respuesta/log.
- Confirmar 429 sólo por cuota de sesión; 100 sesiones desde misma IP no se clasifican como una sola sesión. Límite global usa 503 y no bloquea endpoints sin LLM.
- Criterios aún no ejecutados; casos inertes listados en `fixtures/seguridad-inerte.json`.