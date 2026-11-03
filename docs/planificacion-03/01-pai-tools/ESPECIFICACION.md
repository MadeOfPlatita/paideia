# Especificación propuesta: Pai ↔ backend ↔ PostgreSQL

**Estado:** contrato de diseño propuesto; no es código ejecutable ni decisión de proveedor. **Versión:** `pai-tools/0.1-draft`. **Fecha de contraste documental:** 26-10-2026.  
**Alcance:** chat con selección explícita de herramientas de solo lectura, catálogo PostgreSQL, procedencia/citas, perfil local con consentimiento y límites de contexto. Los contratos JSON completos están en [`contratos.json`](contratos.json); las pruebas de aceptación y fallos en [`ACEPTACION-FALLOS.md`](ACEPTACION-FALLOS.md).

## 1. Estado de las decisiones

- **Aprobado por el grupo (requisitos):** web pública sin login; perfil editable guardado localmente y borrable; productos reales en familias prioritarias; fuente y fecha para datos relevantes; escenarios calculados por código; simulación de contratación sin operaciones reales; no almacenar datos personales en el catálogo por defecto. Ver [REQUISITOS.md](../../REQUISITOS.md), en particular «Privacidad y operación» y «Alcance inicial aprobado».
- **Propuesta de este contrato:** el modelo solo propone una llamada de una lista cerrada; el backend la valida y ejecuta; PostgreSQL contiene únicamente el catálogo público y su procedencia; historial y perfil no se guardan en PostgreSQL; consentimiento diferenciado para procesamiento de chat, memoria local y transmisión del perfil al modelo.
- **No decidido / bloqueante para producción:** proveedor y modelo; alojador/base de datos; prueba de coste/capacidad para 100 usuarios; revisión legal y de privacidad; catálogo inicial y permisos de cada fuente; vigencia máxima por campo/producto; semántica final del perfil; límites de retención del proveedor. No se infieren de esta especificación.
- **No probado:** ninguna integración, carga, esquema desplegado, consulta de producción ni modelo se ha ejecutado. Las referencias técnicas citadas son documentación consultada, no una prueba de Pai.

> Coordinación entre frentes: este contrato no espera ni depende de los informes de APIs en curso. Supone que cada fuente que finalmente se apruebe entregará valores de catálogo con una identidad de producto, fuente primaria, fechas y estado de verificación; cuando un informe no cubra esos campos, se conserva `null`/`unknown` y se abre una incompatibilidad, no se inventa un valor. Los IDs y nombres JSON aquí definidos son propuestas internas, no se presentan como alineados ya con otros informes.

## 2. Arquitectura y límites de confianza

```text
Navegador (sin cuenta)
  ├─ estado de UI + perfil editable opcional + historial local opcional
  └─ HTTPS POST /v1/chat/turns
       Backend/orquestador (única frontera confiable)
         ├─ valida request, consentimiento, presupuesto y límites
         ├─ proveedor LLM intercambiable (selección pendiente; no recibe credenciales DB)
         ├─ registry de 5 herramientas permitidas, validación de argumentos/resultados
         ├─ calculadora determinista en código
         └─ conexión PostgreSQL con rol SELECT-only → catálogo y fuentes
```

La especificación usa JSON Schema Draft 2020-12 en `contratos.json`; JSON Schema define la estructura de datos que valida el contrato.[1] Los APIs de function/tool calling documentan el patrón de definir herramientas con JSON Schema, recibir del modelo una llamada con nombre/argumentos y ejecutar la función en la aplicación antes de devolver su resultado.[5] Los modos estructurados pueden restringir la forma del JSON, pero son dependientes del proveedor y admiten subconjuntos distintos de JSON Schema.[6] Por ello `contratos.json` es la autoridad del contrato de Pai; un adaptador futuro traducirá sus esquemas y **el backend volverá a validar siempre**. La lectura de esas guías no selecciona OpenAI ni otro proveedor.

**Frontera inviolable:** el LLM no tiene conexión de red a PostgreSQL, credenciales, secretos, ejecución de SQL ni herramienta de escritura. Devuelve únicamente `tool name + arguments`; el backend aplica un `switch`/mapa literal por nombre, valida esquema y semántica, y llama a código fijo. Nombre desconocido, argumentos inválidos, llamadas múltiples no admitidas o intento de SQL se rechazan; nunca se concatenan argumentos en una consulta.

**Sin herramientas de efectos externos:** no hay compra, contratación real, transferencia, publicación, alta de usuario, pago ni modificación de catálogo. La simulación de contratación es una pantalla local y ficticia; no se convierte en herramienta LLM ni escribe en PostgreSQL.

## 3. Protocolo HTTP, IDs, fechas y citas

### Turno

- `POST /v1/chat/turns`, `Content-Type: application/json`, `Cache-Control: no-store`. Request y response se especifican en `ConversationTurnRequest` y `ConversationTurnResponse`.
- `conversation_id`, `turn_id` y `request_id`: UUID v4 creados por el cliente; `request_id` correlaciona un envío, no implica almacenamiento ni garantía de ejecución exactamente una vez. `provider_call_id` es un identificador opaco y efímero de la API seleccionada; `tool_call_id` es UUID v4 interno creado por el backend, no el ID del proveedor. `product_id`, `source_id` y `snapshot_id`: UUID estables del catálogo; no son IDs de persona.
- No guardar transcript, perfil, IDs de conversación ni llamadas a modelo en PostgreSQL. En logs operativos, omitir cuerpo, prompt, perfil, nombres de producto consultados e identificadores de conversación; conservar solo métricas agregadas y error técnico sin contenido. Este comportamiento requiere prueba de logging antes de publicar.
- Timestamps RFC 3339 UTC con `Z`; fechas de negocio `YYYY-MM-DD`; valores monetarios decimales como cadenas con moneda/campo unidad (no `float` para importes). No convertir fechas de observación a fechas de publicación.
- Cada dato de producto lleva `as_of` (fecha efectiva del dato, nullable si la fuente no la da), `observed_at` (fecha o timestamp de observación informada por fuente, si existe), `retrieved_at` (timestamp UTC de captura por el colector) y `source_ids`. Cada afirmación de catálogo que llegue al chat debe apuntar a una cita. Las citas incluyen editor/título/URL canónica, fecha de recuperación y referencia al campo respaldado. Los valores desconocidos son `null` + calidad explícita; no se fabrican fechas ni citas.

### Estado de conversación y ciclo de herramienta

El navegador mantiene el estado de UX; el backend procesa un turno sin persistir conversaciones. Estados internos de la máquina (el endpoint no transmite estados intermedios; `ConversationTurnResponse.state` sólo serializa estados terminales):

| Estado | Significado / siguiente transición |
|---|---|
| `profiling` | Recogida progresiva de preferencias por el cliente; puede responder «no lo sé» u «omitir». No se inventa perfil. |
| `ready` | Hay entrada suficiente para enviar un turno. |
| `validating` | Backend comprueba tamaño, UUID, consentimiento y schemas. |
| `model_pending` | Solicitud al proveedor seleccionado posteriormente; sin herramientas de escritura. |
| `tool_selected` | El modelo propone un nombre incluido en allowlist y argumentos JSON. No se ha ejecutado aún. |
| `tool_validating` | Validación estructural y reglas de negocio del backend. |
| `tool_running` | Ejecución de una herramienta registrada; consultas PostgreSQL parametrizadas o cálculo puro. |
| `model_resuming` | Resultado validado vuelve al modelo, con las citas intactas. |
| `complete` | Respuesta final disponible; termina este turno. |
| `clarification_required` | Se necesita un dato; preguntar una cosa concreta, no rellenarlo por inferencia. |
| `degraded` | Respuesta parcial por falta/desactualización/disputa de datos; se informa la limitación. Modelo no disponible se representa como `failed` para este turno; la UI puede conservar funciones locales. |
| `refused` | Negativa explícita del modelo/proveedor o bloqueo de seguridad; no convertirla en respuesta inventada. |
| `failed` | Error técnico terminal con `error.code` estable y opción de reintentar cuando proceda. |

Máquina propuesta por turno: `validating → model_pending → (tool_selected → tool_validating → tool_running → model_resuming →)* complete`. Se permite **una herramienta por respuesta del modelo y hasta 3 ejecuciones por turno**; la llamada final del modelo no cuenta como ejecución de herramienta. Si una respuesta incluye 0 herramientas, finaliza; si incluye más de 1, se rechaza el lote y se termina con `INVALID_TOOL_CALL`. El adaptador conserva `provider_call_id` sólo para completar el ciclo del proveedor; el backend genera su `tool_call_id` UUID. Todos los tools son de solo lectura o puros: los reintentos no causan escrituras, pero pueden repetir consultas/coste del modelo. El cliente no reenvía automáticamente un turno cuyo resultado sea desconocido por timeout; una repetición explícita genera un nuevo `request_id`. No se propone cachear contenido de chat para deduplicación.

## 4. Herramientas expuestas al modelo

Las definiciones completas de entrada/salida, límites de campos y enums están en `contratos.json` (`$defs`). `ModelToolCall` es la forma normalizada interna del adaptador, no un schema único que se envíe a cualquier proveedor: el adaptador registra por separado sólo los schemas de entrada habilitados y mapea la llamada devuelta. Solo se exponen las herramientas pertinentes al turno; en la adaptación al proveedor se activa selección de herramienta restringida/allowlist. La respuesta del modelo jamás decide SQL, nombre de columna, tabla, operador, orden SQL ni dirección URL de consulta. `search_products` usa `rate_field` explícito cuando se filtra por tasa; no interpreta un mínimo como TAE si el usuario no indicó qué métrica busca. Si no hay `query` ni `families`, el backend pide criterio en lugar de ejecutar una búsqueda vacía.

| Herramienta | Entrada / salida | Límite y fuente de verdad |
|---|---|---|
| `search_products` | Texto breve, familias permitidas, filtros tipados y `limit` acotado → productos/resumen de campos, calidad y citas | Consulta pública de catálogo. Sin filtro SQL libre; máximo 20 resultados. |
| `get_product_detail` | `product_id`, nivel y fecha opcional → ficha/campos versionados y citas | ID de producto existente; no recuperar documentos arbitrarios ni secretos. |
| `compare_products` | 2–4 `product_id`, lista de métricas permitidas y fecha de corte → matriz, faltantes, estado `comparable/partial/not_comparable` y citas | No personaliza ni afirma «mejor para ti». No rankea por defecto. La vigencia por tipo de dato sigue bloqueada hasta fijar criterios. |
| `calculate_scenario` | Principal, tasa anual hipotética, meses y método `simple/compound` → importes calculados por módulo determinista, fórmula/versión, redondeo y supuesto | Nunca inferir una tasa de producto; solo calcular los parámetros explícitos. Resultado rotulado `hypothetical`. Sin fuente de producto necesaria. |
| `get_sources` | 1–20 `source_id` devueltos previamente → citas verificadas | Recupera metadatos de fuentes del catálogo, no hace búsqueda web libre. |

### Semántica del cálculo

`r = annual_rate_percent / 100`; `t = duration_months / 12`. Simple: `A = P × (1 + r × t)`. Compuesto: `A = P × (1 + r/m)^(m × t)`, con `m ∈ {1,2,4,12}`; `compound_periods_per_year` debe ser `null` en simple y un valor permitido en compuesto. El backend admite tasa anual entre −100% y +100%, calcula en Decimal (precisión interna 34), redondea una sola vez los importes EUR finales a 2 decimales `ROUND_HALF_UP`, y separa interés de saldo final. No aplica impuestos, comisiones, inflación ni condiciones de producto.

### Contrato de selección y validación

1. El adaptador solo recibe la lista de herramientas habilitada para esta solicitud; sus argumentos se parsean como JSON y validan contra el `$defs` exacto correspondiente (no contra un schema redactado por el propio modelo).
2. Backend comprueba límites semánticos: cantidad de productos, filtros de tasa sólo con `rate_field` explícito (TAE/tasa nominal/rendimiento), coherencia mínimo/máximo, tasa hipotética entre −100% y 100%, `compound_periods_per_year=null` si método simple y no nulo si compuesto, enums, campos por familia, existencia/estado de IDs, consentimiento y validez de datos. `additionalProperties:false` y campos permitidos se mantienen para impedir expansión silenciosa.
3. Ejecutar con repositorio/capa de acceso que solo implemente consultas nominadas, con parámetros separados. PostgreSQL documenta `PQexecParams` como separación de valores y texto SQL, evitando interpolación y ayudando contra inyección.[2] Los nombres/columnas/orden no son valores parametrizables: se eligen solo de mapas estáticos allowlisted.
4. Validar la salida interna antes de enviarla al modelo y al cliente. Una salida de catálogo debe incluir calidad, fecha y citas; si falta procedencia, degradar/omitir el campo, no pedir al modelo que invente la cita.
5. Resultados de catálogo y páginas de fuente son datos no confiables (pueden contener instrucciones adversarias); se presentan como datos y nunca anulan instrucciones del sistema. Escape de HTML en UI; no confiar en `ts_headline` como sanitizador: la documentación PostgreSQL advierte que su salida no garantiza seguridad XSS.[3]

## 5. Perfil, consentimiento y memoria

Tres decisiones independientes y visibles, no un consentimiento agregado:

1. **Enviar el mensaje al servicio de IA:** aviso claro antes del primer uso; cada mensaje enviado se procesa externamente según el proveedor finalmente aprobado. No afirmar privacidad/retención hasta verificar los términos del proveedor.
2. **Guardar perfil local:** opt-in; guardado en `localStorage`/IndexedDB del navegador. El usuario puede editar/borrar con botón «Borrar perfil y memoria local». Nunca se guarda en PostgreSQL.
3. **Enviar campos del perfil al modelo:** opt-in separado, revocable y por petición. Si no se concede, el request omite `profile_context`; backend rechaza perfil presente con consentimiento falso. Enviar solo campos necesarios para esa consulta. Evitar nombre, DNI, email, cuenta bancaria, credenciales, documentos, dirección y texto libre identificable; no solicitar secretos.

La estructura de perfil permite progreso parcial, valores `unknown` o campos omitidos para «no lo sé»/«omitir». Un campo desconocido no es cero ni «bajo». Las cantidades personales, si se habilitan tras revisión de privacidad, se envían solo con consentimiento y como decimal EUR explícito; el backend no las retiene. La aplicación debe informar de que almacenamiento local no significa que el proveedor no procese el mensaje.

### Presupuesto de contexto (propuesta, no benchmark)

- Máximo inicial por invocación: **6.000 tokens de entrada y 700 de salida**, contados por adaptador/tokenizador del proveedor elegido. Máximo **3 llamadas a herramientas por turno**, 4 invocaciones de modelo (inicial + tras cada resultado + final), 4 turnos previos usuario/asistente, 20 resultados de búsqueda/turno, 4 fichas completas, 20 citas y 1.500 tokens por salida de herramienta. Son guardrails propuestos y requieren ensayo de latencia/coste/100 concurrencias; no garantizan capacidad gratuita.
- Orden de inclusión: instrucciones y schemas habilitados → mensaje actual → perfil consentido y solo pertinente → últimos turnos completos → resultado mínimo/citas. Para liberar espacio se descarta primero el turno más antiguo; nunca se corta ni altera en silencio el mensaje actual. Resumir filtros/campos en código, no pedir al modelo que resuma números críticos. Si no cabe, devolver `CONTEXT_LIMIT` con degradación clara y no llamar al modelo.
- Si el backend no puede calcular tokens para el proveedor concreto, falla cerrado (o configura un límite conservador documentado por bytes probado); no envía contexto sin límite. Herramientas devuelven sólo campos solicitados y citas necesarias.

## 6. PostgreSQL: catálogo, procedencia y consultas

### Datos propuestos (sin tablas personales)

- `products(product_id, family, issuer, name, external_id, issuer_country, currency, active, current_snapshot_id, search_text, search_vector, updated_at)`; `product_id` estable y `external_id` opcional (p. ej. ISIN cuando proceda).
- `product_snapshots(snapshot_id, product_id, captured_at, source_version, status)`; cada actualización produce snapshot/versionado trazable, sin sobrescribir evidencia histórica.
- `product_fields(snapshot_id, field_key, value_json, value_numeric, value_text, value_bool, value_date, unit, as_of, observed_at, quality)`; `field_key` sólo de enum/backend allowlist. `value_json` conserva el valor serializable y su forma decimal string; columnas tipadas sirven a filtros/indexes y se validan mutuamente al ingerir. Tasas/importes no se convierten a `float`.
- `sources(source_id, publisher, title, canonical_url, source_type, published_at, retrieved_at, reuse_status)` y `field_sources(snapshot_id, field_key, source_id, evidence_ref)`; una relación por dato, no una cita genérica para toda la ficha.
- `product_embeddings(product_id, snapshot_id, embedding)` opcional y futuro, solo para texto público del catálogo. **No guardar** usuarios, chats, perfiles, consentimiento, prompts ni trazas de herramientas en esta DB.

El catálogo parte de valores curados con procedencia; estadísticas agregadas no se reinterpretan como ofertas comerciales. Un campo con frescura no evaluada se etiqueta `unknown`; los datos `stale` se muestran con advertencia o se excluyen de comparaciones que puedan inducir a error. La regla de caducidad y criterios por familia siguen siendo una decisión pendiente de requisitos.

### Búsqueda lexical primero; pgvector sólo como re-ranking opcional

1. Canonicalizar/capar query y resolver identificador exacto (p. ej. ISIN/ID) con consulta parametrizada.
2. Ejecutar búsqueda textual PostgreSQL en español (`tsvector`/GIN y `websearch_to_tsquery` o `plainto_tsquery`) y filtros de familia de enum; ordenar por rank y limitar candidatos, por ejemplo top 50. PostgreSQL provee funciones para `tsvector`, `tsquery` y ranking.[3]
3. **Sólo si** hay candidatos léxicos y la extensión/vector se valida después, calcular similitud pgvector exclusivamente para esos IDs acotados y reordenar; nunca devolver por semejanza vectorial un producto que no apareció en el conjunto textual inicial. pgvector documenta combinación con full-text search.[4] Para la primera versión, PostgreSQL FTS basta y pgvector es opcional, no dependencia.
4. Si no hay candidatos textuales, devolver “sin resultados” o pedir términos/familia; no ejecutar vector search global como fallback. No enviar prompts/perfil a embeddings.

### Plantillas parametrizadas (ejemplo fijo, no salida del modelo)

La consulta de búsqueda usa una plantilla fija con parámetros ligados: `$1=query`, `$2=families[]` (array vacío significa sin filtro), `$3=limit`, `$4=currency?`, `$5=issuer_country?`, `$6=rate_field?`, `$7=minimum_rate?`, `$8=maximum_rate?`, `$9=maximum_term_months?`. La selección de campos numéricos queda en filas de `product_fields`; `field_key` es un parámetro de texto validado, no un identificador SQL.

```sql
SELECT p.product_id, p.current_snapshot_id AS snapshot_id,
       p.family, p.issuer, p.name, p.currency,
       CASE WHEN NULLIF($1, '') IS NULL THEN 0
            ELSE ts_rank_cd(p.search_vector, websearch_to_tsquery('spanish', $1))
       END AS rank
FROM products AS p
WHERE p.active = TRUE
  AND (cardinality($2::text[]) = 0 OR p.family = ANY($2::text[]))
  AND ($4::text IS NULL OR p.currency = $4)
  AND ($5::text IS NULL OR p.issuer_country = $5)
  AND (NULLIF($1, '') IS NULL OR p.external_id = $1
       OR p.search_vector @@ websearch_to_tsquery('spanish', $1))
  AND ($6::text IS NULL OR EXISTS (
        SELECT 1 FROM product_fields AS rf
        WHERE rf.snapshot_id = p.current_snapshot_id
          AND rf.field_key = $6
          AND ($7::numeric IS NULL OR rf.value_numeric >= $7)
          AND ($8::numeric IS NULL OR rf.value_numeric <= $8)
      ))
  AND ($9::integer IS NULL OR EXISTS (
        SELECT 1 FROM product_fields AS tf
        WHERE tf.snapshot_id = p.current_snapshot_id
          AND tf.field_key = 'term_months'
          AND tf.value_numeric <= $9
      ))
ORDER BY CASE WHEN NULLIF($1, '') IS NOT NULL AND p.external_id = $1 THEN 1 ELSE 0 END DESC,
         rank DESC, p.product_id
LIMIT $3;
```

La aplicación prepara esta plantilla o su equivalente mediante driver (`$1…$9`/bind parameters). Si un límite de tasa está presente, el backend exige `rate_field`; nunca se concatenan valores. No aceptar `sql`, `where`, `sort`, operadores, nombres de columna/tabla ni `limit` sin clamp. Detalle/compare/fuentes usan otras plantillas fijas. El rol de chat se limita a `SELECT`; colector/migración tienen credenciales aisladas fuera del runtime de conversación.

## 7. Proveedor, privacidad y puertas de publicación

No se selecciona proveedor por disponer de function calling o Structured Outputs. Antes de fijarlo: comparar esquema/estrictitud y recusas; confirmar términos para EEE, retención/entrenamiento y transferencia; medir español y fidelidad de citas; probar límites y latencia con contexto medido; probar el escenario de hasta 100 usuarios concurrentes y consumo real con las cuotas que se usarían. La [síntesis de investigación § 4–5 y 7](../../investigacion/00-SINTESIS.md) señala que cuotas por minuto/día no prueban 100 conversaciones concurrentes, y que proveedor/alojamiento siguen pendientes.

**Gate prepublicación:** resolver caducidad de datos y revisión de lenguaje financiero; validar permiso de reutilización para cada campo/fuente; implementar consentimiento/revocación/limpieza; confirmar que los logs no incluyen datos; generar migración con rol de solo lectura; pasar tabla `ACEPTACION-FALLOS.md`; ensayar alternativa cuando modelo o catálogo no estén disponibles. Esta especificación no autoriza crear cuentas, instalar, desplegar ni publicar.

## 8. Referencias técnicas consultadas

Las referencias informan el patrón general y la sintaxis/funciones descritas; no son pruebas de integración ni recomendación de proveedor.

## Sources

[1] https://json-schema.org/draft/2020-12/json-schema-core.html — JSON Schema Core 2020-12
[2] https://www.postgresql.org/docs/current/libpq-exec.html — PostgreSQL libpq command execution
[3] https://www.postgresql.org/docs/current/textsearch-controls.html — PostgreSQL text search controls
[4] https://github.com/pgvector/pgvector/blob/master/README.md — pgvector README hybrid search
[5] https://developers.openai.com/api/docs/guides/function-calling — Function calling | OpenAI API
[6] https://developers.openai.com/api/docs/guides/structured-outputs — Structured model outputs | OpenAI API
