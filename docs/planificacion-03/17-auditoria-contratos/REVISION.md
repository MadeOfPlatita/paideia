# Auditoría cruzada de contratos Paideia

**Alcance:** revisión documental estática de `01-pai-tools/contratos.json`, `05-perfil-conversacion/perfil.schema.json`, schemas/códigos de `07-comparador-reglas/`, `08-seguridad-arquitectura/`, `14-ingesta-calidad/` y `06-escenarios-visuales/`, contrastada con `docs/REQUISITOS.md` y los documentos de coordinación. No se ha probado una integración, aplicación, base de datos ni llamada a API. Todos los contratos están etiquetados como propuesta/diseño; la seguridad indica explícitamente que sus fixtures son inertes.

Se parsearon 10 JSON y `Draft202012Validator.check_schema` aceptó los seis schemas JSON revisados (contrato Pai, perfil, tres schemas del comparador y adapter). Esto valida sintaxis/meta-schema, **no** instancias, mapping ni interoperabilidad.

## Hallazgos priorizados

### 1. P0 — El payload de Pai puede transportar datos que la política de seguridad prohíbe enviar

`01-pai-tools/contratos.json:69-88,90-130` define `ProfileContext` con ingresos/gastos, activos/deuda, compromisos y etiquetas, y permite `profile_context` en el turno si `share_profile_with_model=true`. En cambio, `08-seguridad-arquitectura/controles.json:208-213` (C09) dice que el perfil/cifras no se envían al LLM y limita el contexto remoto a preferencias no financieras; `docs/REQUISITOS.md:45,55-57` pide perfil local y revisión del tratamiento antes de transmitir. Además, el schema Pai admite `accepted_chat_processing:false` y no exige `true` antes de un turno, aunque la capacidad siga apagada por política.

**Tipo:** conflicto real de política de datos, no una diferencia de idioma/schema. No demuestra filtración —no hay implementación—, pero la especificación permitiría una carga más amplia que la política.

**Propuesta:** conservar `perfil.schema.json` como estado local; definir DTO de proyección distinto con lista blanca explícita (p. ej. nivel de conocimiento/tema educativo, nunca importes/deuda en el MVP). El cliente/backend debe exigir aceptación de procesamiento para cualquier llamada y consentimiento separado para cada categoría transmitida. Con `share_profile_with_model=false`, no serializar contexto; no convertir consentimiento a «perfil completo compartido». La futura excepción para datos financieros requiere decisión y revisión del proveedor antes de cambiar la lista blanca.

### 2. P0 — La lista de tools de Pai no coincide con la allowlist de seguridad

`01-pai-tools/contratos.json:15-20,65-68` registra cinco tools en inglés: `search_products`, `get_product_detail`, `compare_products`, `calculate_scenario`, `get_sources`. `08-seguridad-arquitectura/controles.json:31-98,143-150` dice que tools están deshabilitadas en MVP (`habilitada_en_mvp:false`) y que, solo tras aprobación, podrían habilitarse dos tools de lectura con otros nombres y argumentos: `buscar_catalogo(q,categoria,limite)` y `obtener_ficha_producto(product_id)`. Difieren también los límites (20 vs 5), familias/categorías (p. ej. `government_bond` no está en la allowlist) y las formas de resultado. Una llamada/argumento válido para un contrato no es necesariamente válido para el otro.

**Tipo:** diferencia de fase intencional (apagado en MVP frente a registro futuro), pero falta contrato de activación/mapping; se convierte en incompatibilidad real si se habilitan las tools de Pai directamente en el proveedor.

**Propuesta:** mantener el off-switch y cero dispatch en MVP. Versionar un único manifest server-side; si se aprueba habilitar tools, exponer solo las dos lecturas de seguridad, validar y traducir aliases en el backend y limitar IDs a filas publicadas. Mantener comparación/cálculo como endpoints/servicios propios, no como agencia del LLM; `get_sources` puede ser detalle de salida de lectura o endpoint propio. No ampliar la allowlist por reflejo de `x-tool-registry`.

### 3. P1 — Identidad y familias no tienen una clave ni una conversión sin pérdida

`14-ingesta-calidad/adapter.schema.json:18-27,163-225,227-238` emite clases de entidad (`deposit_offer`, `public_debt_observation`, `fund_share_class`, `market_listing`, `legal_institution`) con identidades externas namespaced y `source_id` textual. No emite un `product_id` público. `07-comparador-reglas/product-record.schema.json:8-16` solo exige un `product_id` string; `01-pai-tools/contratos.json:23-27,57-63,173-188` exige UUIDv4 para `product_id`, `source_id` y `snapshot_id`; la salida mínima de seguridad admite ID textual con patrón diferente (`08-seguridad-arquitectura/controles.json:60-66,80-94`). Además, el comparador/contrato separa `remunerated_account` y `term_deposit`, mientras el adapter solo da `deposit_offer`; deuda pública puede ser evento de subasta/serie estadística/cotización, no siempre un producto; una línea de mercado no equivale automáticamente a un ETF/clase.

**Tipo:** separar identidad de entidad, oferta, clase y listing es intencional y correcto; la ausencia de un mapping de IDs/familias es la incompatibilidad real.

**Propuesta:** persistir claves externas namespaced (`scheme + value + source_id`) y asignar en DB un UUID estable a cada entidad/producto/listing; convertirlo a UUID textual en API/tools. Mantener `source_id` del adapter como alias de catálogo de fuentes y asignar ID público estable aparte. Mapping con evidencia: `deposit_offer` → cuenta o depósito solo por naturaleza contractual; `public_debt_observation` → métrica/evento/serie histórica, y `treasury_bill` solo si el instrumento/evento está identificado; `fund_share_class` → `mutual_fund`; `market_listing` → listing hijo, enlazado a clase/ETF solo con evidencia; `legal_institution` → emisor/entidad, nunca producto. No fusionar por nombre, ticker o marca.

### 4. P1 — La unidad de porcentaje cambia de escala entre ingesta, perfil y escenarios

La especificación de ingesta define `PERCENT` como porcentaje sobre 100: `0.05` significa `0,05 %`, no `5 %` (`14-ingesta-calidad/ESPECIFICACION.md:72-78`; schema: `adapter.schema.json:234-237`). El perfil representa bandas `min_pct/max_pct` entre 0 y 100 (`05-perfil-conversacion/perfil.schema.json:176-203`). Los escenarios usan razones fraccionarias: `inflacion_efectiva_anual_supuesta: 0.03` y rendimientos `0.04`/`0.08` significan 3/4/8 % (`06-escenarios-visuales/escenarios-ejemplo.json:12-13,48-68`). Pai llama `annual_rate_percent` al parámetro pero no fija si `4` o `0.04` es 4 %, y la fórmula usa `r` sin indicar conversión (`01-pai-tools/contratos.json:285-309`). Hay riesgo de factor 100 si se pasa directamente de adapter o escenario a la herramienta. Los importes también cambian de cadenas decimales en adapter/Pai a números JSON en perfil/fixtures; eso es admisible solo con conversión explícita.

**Tipo:** falta de definición de unidad/escala en el contrato de cálculo; no prueba que una cifra ya se calcule mal.

**Propuesta:** fijar por campo una unidad y escala, sin deducir por nombre. En catálogo, conservar el valor fuente como decimal string + `unit_code`; para `PERCENT`, `3.00` significa 3 %. En el motor didáctico usar campo explícito `annual_rate_ratio` (`0.04` = 4 %) o aceptar `annual_rate_percent` (`4.00` = 4 %) y dividir por 100 exactamente una vez. Renombrar el dato de inflación/retorno de fixture si se versiona ese DTO. Usar `NUMERIC`/decimal en DB y cadenas decimales en APIs financieras; los números flotantes de UI/fixtures no son entrada canónica de producción.

### 5. P1 — Tiempo/frescura/nulos no son representables de manera uniforme; el schema de adapter contradice su política de unknown

La ingesta separa validez, observación con precisión `date|datetime|not_stated` y consulta (`retrieved_at`) y prohíbe sustituir observación ausente por fecha de consulta (`14-ingesta-calidad/ESPECIFICACION.md:82-104`). Sin embargo, el schema adapter exige `fact.value` y solo permite string/boolean, no `null`, y no incluye `fact.state` (`adapter.schema.json:227-238`); la especificación dice que se usan `null` + motivo y que desconocidos se conservan (`ESPECIFICACION.md:48,55`). En contraste, el comparador permite métrica `value:null` con estado (`07-comparador-reglas/product-record.schema.json:87-102,119-134`), y Pai tiene `value:null`/`quality` (`01-pai-tools/contratos.json:159-171`).

También hay precisión temporal distinta: adapter permite observación día o timestamp (`adapter.schema.json:249-270`), pero `07` usa `date-time` para métrica `as_of` y request `as_of` (`product-record.schema.json:97`; `comparison-request.schema.json:11,15`); Pai usa fecha de negocio para `GetProductDetailInput.as_of`/`CompareProductsInput.as_of` y permite fecha o timestamp en `observed_at` (`contratos.json:40-46,230-260,159-171`). El output 07 versiona política de frescura, pero la respuesta Pai no identifica una versión de esa política.

**Tipo:** falta real de interoperabilidad y contradicción interna adapter-especificación; distinguir fecha de negocio, instante consultado y vigencia es una decisión deliberada, no algo que deba homogeneizarse a timestamps.

**Propuesta:** canonicalizar cada observación como `{value|null, state, unit, currency, observed_at, observed_precision, valid_from, valid_to, retrieved_at, source_refs}`. `observed_at` mantiene fecha si la fuente solo da día; nunca fabricar medianoche. `retrieved_at` es instante UTC; vigencia contractual se conserva como fecha/intervalo declarado. Añadir estado al adapter y permitir valor null, con reglas de coherencia (unknown/no aplicable/conflicto no equivale a cero). Frescura se calcula por campo/uso usando `freshness_policy_version` explícita; mapearla luego a `quality` Pai o `freshness_state` del comparador.

### 6. P1 — Citas/evidencias y namespaces de reason codes no enlazan campo → prueba → decisión

El adapter tiene `source_ref` textual hacia evidencia, pero no `fact_id` ni estado por hecho (`14-ingesta-calidad/adapter.schema.json:227-238`). El producto del comparador sí exige `fact_id`, `field_path`, estado y fuente (`07-comparador-reglas/product-record.schema.json:119-134`), y las razones requieren `field_path`, `source_ids`, regla/fórmula y fecha (`comparison-result.schema.json:22-33`). Pai conserva `source_ids` por campo y citas con `field_keys`/URL/fecha, pero no `fact_id`, locator ni vínculo inequívoco por afirmación (`01-pai-tools/contratos.json:142-171`). Seguridad reduce el resultado a `source_id` y `fecha_efectiva` (`08-seguridad-arquitectura/controles.json:49-70`), insuficiente para reconstruir la evidencia de una razón. Además, `comparador-trazable.md:97` prescribe namespaces `EDU_*` y `CONTROL_*`, mientras que `result-reason-codes.json:5-29` y el enum de `comparison-result.schema.json:26` usan códigos de control sin prefijo `CONTROL_` (la clase se separa del código). El catálogo y el enum coinciden en los códigos listados, pero no con la regla de namespaces del documento.

**Tipo:** intención correcta de separar razones de control y avisos educativos; inconsistencia literal de namespace y pérdida de trazabilidad en los DTOs.

**Propuesta:** guardar `source_id` + `source_revision/content_hash` + `fact_id` + `locator` y asociar cada `FieldValue`/métrica y razón con esos refs. API pública puede presentar citas compactas; no tiene que exponer la fila DB. Enmendar el texto para decir “clase CONTROL/EDUCATIONAL” conservando códigos existentes, o migrar el catálogo y enum juntos con versión nueva. Los tools deben devolver el subset citado que el publicador validó, no sintetizar fuentes.

### 7. P1 — Errores HTTP de seguridad y errores del contrato de chat son dos formatos incompatibles

`08-seguridad-arquitectura/contratos-error.md:5-18,23-48` propone cuerpo `{error:{code,message,request_id,retryable,retry_after_seconds}}` y códigos como `CHAT_DISABLED`, `SESSION_LIMIT`, `GLOBAL_CAPACITY`, `PROVIDER_TIMEOUT`, `PROVIDER_RESPONSE_REJECTED`. `01-pai-tools/contratos.json:132-141` define `Error` plano, sin `request_id` ni `retry_after_seconds`, con códigos distintos (`RATE_LIMITED`, `MODEL_UNAVAILABLE`, etc.); su respuesta normal exige otros campos (`ConversationTurnResponse`, líneas 379-395). Un cliente que trate siempre los errores HTTP como `ConversationTurnResponse` no puede validar el envelope de seguridad, y no hay tabla de traducción ni de status HTTP.

**Tipo:** podría ser una separación intencional entre respuesta normal y error HTTP; falta definir el adaptador público y equivalencias de códigos/reintentos.

**Propuesta:** un envelope HTTP común versionado con `request_id`, `code`, `message`, `retryable` y `retry_after_seconds|null`; mapear errores de seguridad a la taxonomía pública sin incluir texto upstream. Mantener `ConversationTurnResponse` solo para respuestas 2xx. Definir tabla code→HTTP status→retry semántico. El marcador `req_test_only_01` de seguridad está etiquetado como fixture; no usarlo como ID real ni exigir que el ejemplo cumpla UUIDv4 de producción.

### 8. P1 — El contrato de escenario de Pai no puede describir el laboratorio 06; sus fixtures no son productos

`01-pai-tools/contratos.json:285-315` solo admite un principal, una tasa anual, plazo y método simple/compuesto, y devuelve principal/interés/saldo final. `06-escenarios-visuales/escenarios-ejemplo.json:5-70,73-125,127-167` incluye flujo contractual con fechas exactas, aportes periódicos, rutas de rendimientos por año, costes, inflación, retiradas, importes no cubiertos y valores reales/nominales. No existe una conversión sin pérdida entre esos DTOs. El propio laboratorio declara dos motores separados y los datos sintéticos aislados de hechos de producto (`06-escenarios-visuales/laboratorio-escenarios.md:5-10,29-45`); las fixtures de ingesta también son `synthetic_fixture` y nunca publicables (`14-ingesta-calidad/ESPECIFICACION.md:170,154`; `fixtures/casos.json:2-4`).

**Tipo:** la separación de motores y de sintético vs real es intencional. La incompatibilidad real sería conectar la UI avanzada al tool simple o incluir esos ejemplos en el catálogo, sin contrato ni clasificación explícitos.

**Propuesta:** conservar `calculate_scenario` como calculadora de interés simple/compuesto. Crear, si se decide conectar el laboratorio, otro DTO/versionado de escenarios con `scenario_kind`, calendario de flujos, unidades y método, y salida `hypothetical:true` + supuestos/versión; no enviarlo al modelo para calcular. Mantener ejemplos bajo namespace/almacenamiento de fixtures y bloquear publicación por clasificación, nunca reetiquetarlos como productos o quotes.

## Mapping canónico propuesto por frontera

No igualar todos los schemas. Compartir semántica y adaptadores explícitos; cada frontera conserva su propósito.

| Frontera | Contrato recomendado | Conversión / control |
|---|---|---|
| **Adapter → DB (candidato)** | Envelope versionado de ingesta: clasificación, familia de origen, identidad namespaced, fuente/revisión/raw hash, hechos tipados con valor nullable/estado/unidad, vigencia/observación/consulta e idempotency key. | No publicar desde adapter. Crear `fact_id` al aceptar el candidato; preservar la clave externa literal. `synthetic_fixture`, licencias no aprobadas, desconocidos o conflictos quedan en cuarentena. |
| **DB (modelo canónico)** | Entidades separadas `issuer`, `product/offer/share_class`, `listing`, `source_revision`, `fact` y `publication`; claves UUID internas + identificador externo namespaced; `NUMERIC`, moneda y código de unidad; historial inmutable. | FK `fact→source_revision`; guardar `content_hash`, versión de adapter/política y estado de revisión/publicación. `DATE` para día/validez de negocio, `TIMESTAMPTZ` para instantes; no inventar observación. Publisher con rol separado sólo publica candidatos aprobados. |
| **DB → Public API** | DTOs de lectura por uso: `ProductSummary/Detail`, `ComparisonRequest/Result`, `ScenarioRequest/Result`, `Citation`, `Error`. IDs de producto y fuente opacos estables; familias públicas; `as_of_date` separado de `generated_at`; estado/frescura/citas por campo. | Mapeo explícito desde familia/origen a `ProductFamily`; omitir de catálogo de productos series estadísticas y entidades jurídicas; no mezclar listing con clase; unidad/período/basis en cada métrica. Añadir policy-version y refs citables en comparación. |
| **Public API → Tools del modelo** | Manifest cerrado, versionado y deshabilitado por defecto; DTOs delgados de lectura con límites. Contexto del perfil se proyecta con consentimiento separado. | Si se habilitan, sólo handlers expresamente aprobados por 08; validar input/ID, dispatch por mapa, lectura de filas publicadas, resultado no confiable. No tool SQL, escritura, fetch o contratación; cálculo/comparador pueden permanecer locales/API y no ser tools del LLM. |

### Diferencias intencionales que no deben “arreglarse” igualando schemas

- Perfil español/local en 05 y `ProfileContext` inglés de Pai son modelos de capas distintas: hace falta proyección consentida, no copiar el objeto completo ni reemplazar el perfil local.
- Adapter 14 modela observaciones fuente/entidad; 07/01 modelan producto público/comparación/chat. La jerarquía cambia legítimamente, pero debe existir mapping de identidad, familia y evidencia.
- Tools desactivadas para el MVP (08) y cinco tools descritas como catálogo futuro (01) pueden coexistir por fase; el runtime debe respetar la desactivación y el manifest aprobado.
- Los escenarios 06 son supuestos sintéticos; los hechos de producto real permanecen reales. No usar fixtures como catálogo de demo que aparente ofertas reales.

## Artefactos

- `REVISION.md`: auditoría, severidad, propuestas y mapping por frontera.
- `hallazgos.json`: la misma lista en forma estructurada para integración/seguimiento.

No se modificó ningún otro archivo ni se ejecutó una integración remota.