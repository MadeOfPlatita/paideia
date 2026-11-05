# Ensayo local del contrato Groq/educación

Este adaptador es una **costura sintética aislada**, no una conexión con Groq. El constructor solo admite exactamente `FakeChatProvider`, no acepta transporte ni credenciales y no consulta el entorno. Usa `build_chat_request` para serializar en memoria y descarta los bytes; llama una vez al proveedor ficticio existente y valida la selección mediante `StructuredProviderAdapter`. No realiza HTTP ni reintentos. El servicio estructurado actual rechaza este adaptador: no cambia sus barreras ni habilita integración externa.

La salida admitida contiene exclusivamente `version`, `intent` y `claim_ids` válidos. Se rechazan duplicados, campos adicionales (incluido un escenario), IDs desconocidos o repetidos, JSON inválido, UTF-8 inválido o más de 4096 bytes, negativas, herramientas y cualquier `finish_reason` distinto de `stop`. Los errores expuestos se reducen a `invalid_response` sin retener el contexto de la excepción. El fixture puede guardar los mensajes de ensayo en memoria; no introducir secretos ni datos reales.

El cálculo es responsabilidad del renderizador local con el escenario del mismo turno; el modelo no suministra valores ni resultado. El test del renderizador prueba la exigencia de escenario, no la integración de esta costura en el servicio.

## Límites de compatibilidad

El builder existente no admite `response_format`. La función pura `build_structured_request` primero lo ejecuta con sus valores fijos y después añade al JSON el esquema cerrado `paideia_education_v1`, con `strict: false`, y vuelve a comprobar el límite total de 16 KiB. Conserva los campos actuales del builder: `model=openai/gpt-oss-20b`, `max_tokens=256`, `reasoning_effort=low` e `include_reasoning=false`; no se añadieron parámetros de razonamiento adicionales. No admite controles del usuario, tools, stream, escenario, campos de perfil ni historial estructurado. El texto libre del usuario no se anonimiza: no introducir datos privados. Un roundtrip JSON local no demuestra aceptación remota. El `ChatResult` es un DTO fabricado, no una respuesta HTTP real.

**Bloqueo de integración:** este cuerpo candidato se descarta, no se entrega a un transporte. `GroqProvider.chat` vuelve a llamar su builder ordinario, que no acepta el esquema; el servicio rechaza este adaptador. Por tanto no existe una captura integrada del cuerpo de salida estructurado y no se debe liberar ni saltar la guardia para forzarla. Se requiere diseñar y revisar una costura de transporte de confianza antes de esa prueba.

Según la inspección aportada de [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs), GPT-OSS 20B figura como best-effort (`strict: false`), mientras un ejemplo en la misma página usa `strict: true`; existe una contradicción documental y no se afirma soporte de `strict: true`. La página indica que streaming y tool use no son compatibles con Structured Outputs. Una futura integración necesita resolver documentación, diseñar y revisar builder/parser, guardia cerrada, autorización y límites de gasto por separado; no se ha activado ni autorizado una prueba real.

Prueba sin red: `python -m unittest discover -s tests -p 'test_groq_structured_adapter.py' -v` desde la raíz del prototipo. Fixtures exclusivamente sintéticos.
