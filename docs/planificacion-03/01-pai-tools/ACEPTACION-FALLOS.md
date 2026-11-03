# Aceptación y fallos — contrato Pai tools 0.1

**Estado:** criterios propuestos para implementación; no ejecutados. La app aún no existe. “Aceptado” significa que la prueba pasa cuando se implemente, no que ya esté verificada. Umbrales indicados son contratos de diseño y necesitan revisión con el proveedor y el catálogo escogidos.

## Tabla de aceptación

| ID | Criterio observable | Prueba reproducible / aserción | Prioridad / estado |
|---|---|---|---|
| A01 | Contratos legibles por máquina | Parsear `contratos.json`; validar cada `$defs` con Draft 2020-12; validar ejemplos válidos y rechazar campos extra, enums inválidos, UUID/fecha incorrectos y límites excedidos. Comprobar referencias `$ref` locales. | Bloqueante; pendiente |
| A02 | Selección de herramienta restringida | Simular cada una de las 5 herramientas admitidas; comprobar que el backend despacha sólo el nombre exacto y valida argumentos con su schema y reglas semánticas. Nombre desconocido o llamada múltiple en una respuesta → `INVALID_TOOL_CALL`; cero efectos. | Bloqueante; pendiente |
| A03 | No se ejecuta SQL del modelo | Enviar argumentos con `sql`, `where`, `table`, operador, comentario SQL e inyección como texto de búsqueda; comprobar que los extra se rechazan y el texto permitido sólo viaja como valor ligado a plantilla fija. Revisar código/telemetría: ninguna cadena de SQL proviene de respuesta del modelo. | Bloqueante; pendiente |
| A04 | Aislamiento de PostgreSQL | Ejecutar la app con rol `pai_chat_readonly`; `SELECT` permitido, `INSERT/UPDATE/DELETE/DDL` denegado. La base no contiene tablas de perfil, usuario, conversación, historial, consentimiento o tool-call. Credenciales sólo en backend y separadas de ingestión/migraciones. | Bloqueante; pendiente |
| A05 | Fechas, precisión y evidencia | Cada campo material devuelto contiene `quality`, `as_of`/`observed_at` (o `null` explícito), `source_ids`; toda cita resuelve a título, editor, URL HTTPS y `retrieved_at`. No hay `float` para tasas/importes de catálogo ni timestamps locales sin zona. | Bloqueante; pendiente |
| A06 | Consentimiento de chat y perfil | Con `accepted_chat_processing=false` no se llama al proveedor. Con `share_profile_with_model=false`, `profile_context` es rechazado/omitido y el mock del proveedor no recibe valores del perfil. Rechazar el request si incluye contexto de perfil sin consentimiento. | Bloqueante; pendiente |
| A07 | Memoria local revocable | Con `store_local_profile=false`, recargar no recupera perfil; con opt-in, editar y borrar elimina perfil e historial local pertinente. Verificar manualmente DevTools/localStorage/IndexedDB y confirmar que borrar no implica borrar datos del catálogo. | Bloqueante; pendiente |
| A08 | Presupuesto de contexto | Medir con tokenizador del proveedor concreto: nunca exceder 6.000 tokens de entrada ni 700 de salida; máximo 4 llamadas de modelo, 3 tools, 8 mensajes previos, 20 resultados, 4 fichas y 20 citas. Caso sobredimensionado descarta historial viejo primero; mensaje actual intacto; si no cabe → `CONTEXT_LIMIT` sin llamada al modelo. | Bloqueante; pendiente |
| A09 | FTS antes de vector | Instrumentar SQL: cada búsqueda ejecuta exact match/FTS primero; si pgvector está habilitado, su consulta recibe exclusivamente IDs del top-K lexical (máximo propuesto 50). Query sin candidatos lexicales no dispara vector search global. Confirmar que embeddings no incluyen perfil, chat ni prompts. | Bloqueante si se activa vector; pendiente |
| A10 | Cálculo no delegado al LLM | Golden test con principal `1000.00 EUR`, tasa anual `10%`, 12 meses: simple devuelve interés `100.00`, saldo `1100.00`; compuesto mensual devuelve interés `104.71`, saldo `1104.71`, con `ROUND_HALF_UP`. Las cifras fueron calculadas con Decimal, precisión 34, en la preparación de este contrato. Una tasa de producto no se infiere del texto; sólo se calcula si llega como parámetro explícito. | Bloqueante; pendiente |
| A11 | Comparación honesta | Con datos completos y compatibles retorna `comparable`; con campo ausente/desactualizado/disputado retorna `partial`/`not_comparable`, explica exclusiones y conserva citas de cada campo; jamás presenta un orden “mejor para ti”. | Bloqueante; pendiente |
| A12 | Fallos de proveedor/catálogo | Simular timeouts y 5xx por separado; error estructurado, sin respuesta financiera inventada ni cita fabricada. El modelo no disponible no impide usar simuladores locales; no hay fallback que se haga pasar por LLM. | Bloqueante; pendiente |
| A13 | Prompt injection en catálogo | Poner instrucciones hostiles en nombre/descripción/extracto de una ficha; el modelo las trata como texto no confiable, no amplía tools ni el acceso a datos. En UI el contenido se escapa como texto, nunca HTML confiable. | Bloqueante; pendiente |
| A14 | Sin operaciones reales | Recorrer demo de contratación: usa datos ficticios y mensajes visibles de simulación; no solicita credenciales bancarias/DNI/pago, no invoca proveedor bancario y no escribe en catálogo. | Bloqueante; pendiente |
| A15 | Reintentos y concurrencia | Repetir una petición sólo puede volver a ejecutar lecturas/cálculo puro; no hay exactamente-una-vez ni caché persistente de chat. El cliente no auto-reintenta un timeout de resultado incierto y usa nuevo `request_id` al reintentar explícitamente. Dos turnos distintos no mezclan contexto; probar ráfaga concurrente con objetivo medido de hasta 100 usuarios. El éxito requiere latencia, error, tokens y coste; la cuota documentada no basta. | Bloqueante para publicar; pendiente |

## Tabla de estados de fallo y respuesta

| Condición | HTTP propuesto | `state` / `error.code` | Comportamiento exigido |
|---|---:|---|---|
| JSON inválido, schema/UUID/enum/límite incorrectos | 400 | `failed` / `INVALID_REQUEST` | No llamar modelo ni DB; texto de error sin reflejar secretos. |
| Aviso/consentimiento IA no aceptado | 409 | `failed` / `CONSENT_REQUIRED` | No enviar cuerpo al proveedor. |
| Perfil incluido sin permiso explícito | 409 | `failed` / `PROFILE_CONSENT_MISMATCH` | No enviar perfil; solicitar decisión separada. |
| Herramienta no permitida, JSON inválido, más de una llamada o salida incompatible | 422 | `failed` / `INVALID_TOOL_CALL` | No ejecutar ninguna del lote; registrar sólo métrica sin payload. |
| Contexto excede límites tras truncar turnos previos | 413 | `failed` / `CONTEXT_LIMIT` | No enviar contexto parcialmente mutilado ni llamar modelo. |
| Producto o fuente inexistente/retirada | 404 | `clarification_required` / `PRODUCT_NOT_FOUND` o `SOURCE_NOT_FOUND` | Explicar que no se encontró y permitir corregir ID/criterio. |
| Sin resultados léxicos | 200 | `complete` | Respuesta explícita “sin resultados”; no iniciar vector global ni inventar fichas. |
| Datos obsoletos, parciales o disputados | 200 | `degraded` | Marcar calidad y fecha; excluir campos incompatibles; no describir como actual. |
| Catálogo PostgreSQL no disponible | 503 | `failed` / `CATALOG_UNAVAILABLE` | No fingir búsqueda; ofrecer reintento. Cálculo local puede seguir por UI. |
| Proveedor IA saturado, timeout o cuota agotada | 503 | `failed` / `MODEL_UNAVAILABLE` | No fingir respuesta ni ocultar indisponibilidad; función local sigue disponible. |
| Rechazo explícito del proveedor | 200 | `refused` / `MODEL_REFUSAL` | Mostrar rechazo; no fabricar respuesta alternativa. |
| Respuesta final del proveedor no parseable/no validable | 502 | `failed` / `INVALID_MODEL_RESPONSE` | No mostrar como respuesta válida; permitir como máximo un reintento si todavía queda presupuesto de llamadas; si no, fallar cerrado. |
| Rate limit de abuso | 429 | `failed` / `RATE_LIMITED` | Aplicar backoff; sin identificación persistente ni bloqueo de usuarios legítimos no revisado. |
| Error no clasificado | 500 | `failed` / `INTERNAL_ERROR` | Mensaje genérico; ID de petición; sin stack trace/secretos al cliente. |

### Puertas de cierre

1. Validar JSON Schema de entrada/salida y export de schemas compatibles con el proveedor elegido (no elegir proveedor hasta PoC).
2. Decidir caducidad por tipo/familia, criterios para comparar y campos que necesitan fuente primaria antes del alta del catálogo.
3. Revisar aviso de consentimiento, transferencia/retención de datos y redacción financiera con responsables adecuados.
4. Ejecutar las pruebas A01–A15 en integración y medir la carga de 100 usuarios; publicar solo después de guardar evidencia real de los resultados.

**Resultado actual:** ninguna A01–A15 ha sido ejecutada sobre una aplicación, porque no hay aplicación implementada. En este paquete sólo se verificará la sintaxis/estructura de los contratos y documentos.
