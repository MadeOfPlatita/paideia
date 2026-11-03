# Paideia — pipeline de ingesta y calidad de datos

> **Integración:** véase `../19-integracion/CRITERIO-INTEGRACION.md`. Sigue pendiente adaptar `adapter.schema.json` para hechos desconocidos nullable con estado/motivo. El schema actual no es el contrato público final; siete fixtures correctas no resuelven ese hueco.

**Estado:** propuesta de contrato y operación; no implementada ni conectada a fuentes o PostgreSQL.  
**Ámbito:** cuentas y depósitos, deuda pública/series, fondos y ETF, listados de mercado e instituciones jurídicas.  
**Corte de la evidencia del proyecto:** 26-10-2026. Las cifras y entidades de `fixtures/` son exclusivamente sintéticas; no representan ofertas ni productos reales.

## 1. Principios y límites

1. **Leer, preservar, validar, revisar y publicar; nunca hacer scraping o promoción implícita.** Los conectores usan solo fuentes aprobadas y permitidas. Respuesta HTTP 200, página pública o archivo descargable no acredita permiso de almacenamiento o redistribución. Si el uso/licencia es desconocido, la salida queda bloqueada para publicación.
2. **La fecha de captura no equivale a fecha de observación ni a vigencia.** Se conservan separadas por campo. No se rellenan fechas faltantes con la fecha del proceso, una cadencia supuesta o la hora de consulta.
3. **Una cifra sin definición no es comparable.** Porcentaje, puntos porcentuales, razón decimal, dinero, precio por 100 nominales, NAV y cotización son unidades diferentes. Se conserva la etiqueta original del coste/tipo y su moneda.
4. **Identidad jurídica, producto/clase y línea de cotización son entidades distintas.** El ISIN identifica la clase/instrumento; ticker + MIC + moneda identifica una línea de cotización. Marca comercial no sustituye a la persona jurídica.
5. **No se sobrescribe el historial.** Un cambio de contenido genera una revisión/versionado nuevo. Reprocesar los mismos bytes y la misma transformación es un no-op idempotente.
6. **Sin promedio automático ni “último dato gana”.** Solo se comparan hechos con la misma semántica, periodo, instrumento, moneda y unidad. Conflictos, outliers o cambios de significado pasan a revisión.
7. **Ninguna extracción de IA publica por sí sola.** PDF/HTML extraídos por IA u OCR son candidatos no confiables; requieren contraste humano con el documento fuente y aprobación ligada al hash exacto.
8. **El catálogo publicado no constituye asesoramiento.** El pipeline transporta hechos y su procedencia; no ordena productos por perfil ni convierte datos incompletos en recomendaciones.

La síntesis de investigación encontró que las series del BdE/BCE no equivalen a ofertas bancarias particulares; el Tesoro publica resultados por subasta, y los proveedores de fondos distinguen clase, documentos, NAV y líneas de negociación. No se halló una fuente única que garantice cobertura diaria licenciada para todo el catálogo.[I01][I02][I03] La guía de rigor financiero pide conservar fuente/fecha y excluir comparaciones cuando la fuente caduque o falten costes; el informe de seguridad exige tratar extracción/salida externa como no confiable y no dar al LLM autoridad de escritura.[I09][I10]

## 2. Flujo propuesto

```text
Registro de fuentes y políticas
          │ allow-list + permiso + versión de adaptador
          ▼
Importador de solo lectura ── errores de fetch ──► registro de ejecución/alerta
          │ respuesta original + metadatos + SHA-256
          ▼
RAW inmutable (solo evidencia autorizada; sin secretos/PII)
          │ transformación pura y versionada por familia
          ▼
Candidato normalizado (adapter.schema.json)
          │ controles estructurales, semánticos, de tiempo, licencia y anomalías
          ├──► rechazado / cuarentena / cola de revisión humana
          ▼ aprobación ligada a hash, revisor y motivo
Publicador ── transacción atómica/idempotente ──► PostgreSQL: revisión publicada
```

Solo la última etapa puede cambiar la vista consumida por la app. La base de datos mantiene revisiones y linaje; el diseño SQL/entidades globales queda coordinado con el agente de esquema DB y no se fija aquí. No dar a importadores credenciales de escritura generales: publicador separado, mínimo privilegio y transacción limitada al candidato aprobado.

### Contrato de cada etapa

| Etapa | Entrada / salida mínima | Invariante / fallo |
|---|---|---|
| Registro de fuentes | `source_id`, propietario, familia/campos permitidos, URI aprobada, permiso/estado legal, cadencia declarada si la fuente la publica, política de consulta y adaptador versionado | `blocked` o `unknown` en licencia no publica. La cadencia de consulta del importador se registra aparte de la frecuencia de observación de la fuente. |
| Importador | GET/descarga permitida; `run_id`, `queried_at` UTC, estado HTTP, MIME, ETag/Last-Modified si existe, tamaño, URI final y SHA-256 de bytes | Solo lectura; límites de tamaño/tiempo; no seguir URL arbitraria entregada por un usuario. Reintentos acotados/backoff solo para errores transitorios; no repetir inmediatamente tras 429. |
| RAW | Referencia inmutable al cuerpo original autorizado + metadatos de captura | Repetir bytes conserva el mismo hash. No guardar cookies, tokens, datos de usuario ni contenido si la licencia/retención no lo permite. Un RAW no es una ficha publicada. |
| Adaptador | RAW + versión de parser/transformación → uno o más candidatos conforme a `adapter.schema.json` | Transformación determinista y pura. No completa con memoria, interpolación ni IA; desconocidos se representan como desconocidos. Un cambio de parser genera nueva versión. |
| Validación | Candidato + reglas aprobadas para fuente/campo/familia | Validación estructural, unidad, identidad, fechas, derechos, coherencia, rangos y frescura. Fallo = no pasa; anomalía = revisión, no corrección silenciosa. |
| Revisión | Diff frente a última versión aprobada, candidato y evidencia de origen | Primera alta, cambios materiales, identidad dudosa, conflictos, outliers, documento PDF/OCR/IA, cambio de estructura o dato stale requieren revisión. La aprobación firma (referencia lógica, `content_hash`, versiones de adaptador/esquema, revisor, instante UTC y motivo). |
| Publicador | Solo candidato validado y aprobación vigente para el mismo hash | Una transacción por unidad de publicación; `INSERT ... ON CONFLICT`/equivalente con clave lógica estable. Hash idéntico = no-op; hash nuevo = nueva versión y supersesión auditable, nunca borrado/actualización silenciosa. |

## 3. Contrato de adaptadores por familia

Todos los adaptadores emiten observaciones estrechas: **un hecho/campo por elemento**, con valor, unidad, moneda si aplica, identidad, temporalidad, referencia a evidencia y versión de adaptador. No se exige a cada fuente campos que no ofrece: se usan `null` + motivo/ausencia, nunca cero, estimación o valor heredado. El contrato máquina-legible está en [`adapter.schema.json`](adapter.schema.json).

| Familia / adaptador | Identidad primaria | Hechos y semántica que deben conservarse | Reglas de publicación |
|---|---|---|---|
| `deposit_offer` (cuenta/deposito) | `product_key` estable + identificador de **entidad jurídica**; marca solo como alias | TIN, TAE, tramos/promoción, importe mínimo/máximo, plazo, requisitos, comisiones, cancelación, garantía y documento, cada uno como campo separado; la condición se aplica al tramo/escenario exacto | Usar la ficha/condición oficial permitida. No convertir TIN en TAE, ni asumir que una página de banco se actualiza cada día. Cambio de tipo, condición, entidad o cancelación requiere diff/revisión. Estadística BdE/BCE agregada no se transforma en oferta de entidad.[I01] |
| `public_debt_observation` | `scope` + referencia `TREASURY_EVENT`, `BDE_SERIES`, `ECB_SDMX`, `ISIN` u otro identificador explícito | Separar resultado de subasta (evento), serie estadística/rendimiento por plazo y cotización de título. Precio, nominal, porcentaje/tipo, plazo y evento conservan unidades y periodo | Subasta es histórica por evento, no precio disponible hoy. Serie diaria/mensual se rige por metadatos de esa serie. Rendimiento agregado/curva no se asigna a ISIN ni se llama cotización ejecutable.[I02] |
| `fund_share_class` | ISIN de la **clase**; nombre del fondo/clase son atributos, no clave | Clase, acumulación/distribución, divisa base/clase, cobertura FX, UCITS, gestora, KID/DFI/folleto, riesgo y costes con su nombre documental (TER/OCF/ongoing costs/transaction costs), periodo y moneda | No fusionar costes con etiquetas distintas. Guardar versión/fecha de documento; no usar ticker como identidad de clase. La relación del ISIN debe verificarse contra fuente documental/registro y pasar formato/check digit antes de producción.[I03] |
| `market_listing` | `listing_key` + ticker + MIC (mercado) + moneda negociada | Precio/volumen y timestamp de mercado; moneda de cotización; relación opcional `related_class_isin` documentada | No inferir NAV, divisa de clase o exposición FX desde ticker/moneda de negociación. Un NAV y una cotización no se sustituyen entre sí. No publicar cotización sin fuente/licencia/frescura configuradas.[I03] |
| `legal_institution` | LEI o código de registro oficial con namespace; `brand_label` separado | País, nombre legal, marca, relación con oferta y sistema/garantía con evidencia, alcance y fecha | No inferir entidad o fondo de garantía por marca, dominio o país del usuario. Si no hay identificador o vínculo verificado, `identity_link_unresolved` y revisión; el registro de garantía no es una oferta de producto.[I01] |

### Identificadores y relaciones

- **ISIN:** se aplica a instrumento/clase cuando la fuente lo identifica; se conserva literalmente (mayúsculas, 12 caracteres) y se valida el check digit como control, nunca se “repara” una cadena mal formada. En `synthetic_fixture` se acepta solo el namespace reservado `TEST-ISIN-nnnn`, que el publicador debe rechazar.
- **Listing:** clave independiente `(ticker, MIC, trading_currency)`; relacionarla con ISIN solo si evidencia oficial la sustenta. Un ticker puede referirse a listados distintos y una clase puede tener varias líneas.
- **Entidad jurídica:** LEI/código de registro y jurisdicción como identidad; nombre/marca no determinan entidad. Se permite identificador local namespaced si no existe LEI, con evidencia y revisión explícitas.
- **Instrumentos sin identificador estable:** guardar `scheme + value + source_id`; no construir identidad por nombre/tasa ni fusionar homónimos. Asignar `product_key` interno solo bajo control de catálogo y guardar los alias/versiones.

## 4. Unidades, monedas y valores

- Serializar decimales como **cadenas decimales base 10** (`"1234.50"`), sin separador de miles, coma, exponente ni `NaN`/infinito; PostgreSQL debe usar `NUMERIC`, no `float`. Redondeo pertenece al cálculo/visualización, no al dato importado.
- `MONEY` exige moneda ISO 4217 en `currency`; no se asume EUR por el país, símbolo `€` o contexto. Importes y comisiones expresan si son totales, por periodo o por operación en `field_path`/definición del campo.
- `PERCENT`: el valor es porcentaje sobre 100; `"0.05"` significa 0,05 %, no 5 % ni 0,0005. `PERCENTAGE_POINT` = puntos porcentuales; `BASIS_POINT` = puntos básicos; `DECIMAL_RATIO` = razón fraccionaria. No convertir sin registrar unidad original y fórmula.
- `PRICE_PER_100_NOMINAL` requiere moneda asociada y no es una cantidad de dinero. Precio de mercado, NAV por participación y reembolso nominal son medidas diferentes.
- Las definiciones/escala de cada campo son parte del catálogo de validación; una unidad faltante, moneda desconocida o coste de nomenclatura ambigua detiene la comparación. La moneda no se deduce desde el ticker ni de la moneda base de otra entidad.

## 5. Tiempo, validez y frescura

El adaptador separa en cada `fact`:

1. `validity.valid_from` / `valid_to`: intervalo de vigencia contractual/documental explícito, en fechas ISO y con semántica **[desde, hasta)**; `source_explicit=false` implica ambos `null`. No calcular la fecha de fin por costumbre.
2. `observation.observed_at`: fecha/hora a la que se refiere el valor (día de NAV, subasta, observación de serie, timestamp de cotización o versión de documento). Conserva precisión `date`, `datetime` o `not_stated`; si falta, es `null`, no `queried_at`.
3. `source.retrieved_at`: instante UTC en que se consultó/descargó la fuente (`queried_at`). No es hora de actualización de la fuente.

`source_published_at` puede guardarse cuando la fuente lo da. Fechas calendario sin hora se conservan como `date`; timestamps llevan offset explícito/UTC. En límites de periodo, respetar zona horaria declarada por la fuente, convertir el instante a UTC sin perder el original.

### Matriz propuesta de cadencia y caducidad por campo

**Son políticas operativas iniciales de Paideia, pendientes de aprobación/calibración; no son SLA de las fuentes ni afirmaciones de que todas publiquen a diario.** La “frecuencia observada” se copia de metadatos/documento por fuente/serie; la frecuencia de comprobación es una decisión nuestra. Sin frecuencia/umbral configurado, el campo no se presenta como actual ni participa en comparación actual.

| Fuente/familia y campo | Frecuencia conocida por la evidencia del proyecto | Comprobación propia propuesta | Regla de frescura y efecto por campo |
|---|---|---|---|
| Ficha bancaria: tipo, TAE/TIN, comisiones y requisitos | No se encontró feed público que garantice actualización diaria; los documentos oficiales tienen sus propias fechas/condiciones.[I01] | Releer diariamente solo fuentes autorizadas del catálogo acotado (objetivo de proceso, no cadencia del banco). | “Verificado reciente” solo con revisión exitosa en las últimas 24 h (umbral propuesto). Si supera 24 h, retener último valor bueno como `stale`; excluir campo de comparación vigente; no borrar la ficha ni su historia. Fecha de vigencia del documento prevalece si es explícita. |
| Tesoro: resultado de subasta | Por evento/subasta, no diario.[I02] | Importar tras publicación oficial/evento, con verificación de resolución/fecha. | Es dato histórico asociado a su evento; no caduca como hecho histórico ni se marca cotización actual. No se extrapola a vencimiento o precio posterior. |
| BdE/BCE: series estadísticas | Depende de la serie: hay frecuencias diarias y mensuales documentadas; conservar metadata exacta por serie.[I01][I02] | Consultar cada día es una comprobación técnica posible, no significa que haya una observación nueva cada día. | Mostrar `observed_at` real y unidad/serie; no sustituir ausencias por cero. Umbral máximo de observación se configura por serie y uso; si no está acordado, etiqueta “referencia histórica” y no se presenta como dato diario/quote. La estadística agregada nunca se usa como precio individual. |
| KID/DFI, costes y características de clase | Documentos fechados; no hay feed agregado diario probado.[I03] | Revalidar URL/versión de documentos seleccionados semanalmente como objetivo operativo, sujeto a permisos. | Conservar la fecha del documento y vigencia explícita. Si la última revisión de disponibilidad/versión supera 7 días (umbral propuesto), marcar la ficha `stale` hasta revisión; el umbral no cambia la vigencia jurídica/documental. Costes sin documento vigente: fuera de comparativa. |
| NAV/valor liquidativo | Cadencia propia del producto/fuente; un documento puede declarar diaria, pero no generalizarla a todo el universo.[I03] | Según frecuencia declarada del proveedor elegido; ninguna frecuencia general asumida. | Aplicar umbral por feed + clase; `null` sin observación. No rellenar NAV con precio de bolsa. Si no hay SLA/frescura acordados, no titular “NAV actual”. |
| Cotización de listing | No se confirmó feed abierto/licenciado general por ISIN en la investigación.[I02][I03] | Sin fuente aprobada, no activar importación de cotizaciones. Al seleccionar proveedor, definir consulta, licencia, mercado y máximo de edad para esa fuente. | Falta de feed/umbral = no publicar como actual ni comparar con NAV. Superar el umbral configurado = `stale`, excluido de cálculos actuales; preservar historia si se permite. |
| Institución jurídica/garantía | Registros y fuentes de cobertura no son feeds diarios; la periodicidad depende de cada registro.[I01] | Comprobación al alta y revalidación trimestral como objetivo de revisión (propuesta, no frecuencia de la fuente). | Tras 90 días sin revisión (umbral propuesto), `stale` la relación entidad/garantía y bloquear afirmación vigente; no caduca el hecho histórico. Si el proveedor publica periodo/versionado, usarlo en lugar del umbral genérico. |

La evaluación de stale se aplica **a cada campo y uso**: un identificador de clase puede seguir válido aunque su precio esté obsoleto. `valid_to` vencida = dato expirado; TTL desde última consulta = falta de verificación reciente; ambas cosas no son sinónimos. Un producto solo se excluye de comparaciones actuales si un campo necesario es stale/expirado o falta; otros campos e historial permanecen visibles con su estado y fecha.

## 6. Versionado, deduplicación, hashes y upsert

- Guardar cada ejecución con `run_id`, `source_id`, URI, `queried_at`, status/MIME, digest de bytes y `adapter_id@version` + `contract_version`. El RAW conserva cada snapshot autorizado con referencia inmutable y SHA-256.
- La clave idempotente lógica se construye desde identidad namespaced + `family` + `field_path` + scope/condiciones + `observed_at` + intervalo de validez. No incluir `queried_at` en la identidad lógica; una nueva consulta del mismo dato no crea una nueva observación lógica.
- Calcular `content_hash = SHA-256(canonical_json)` downstream sobre identidad, campo, valor, unidad, moneda, temporalidad y referencia/versión documental estable; serialización UTF-8 determinista, claves ordenadas y normalización decimal definida. Excluir `run_id`, hora de ingesta, reintentos y demás metadatos volátiles. Guardar algoritmo/versión para poder reproducirlo. El hash recibido del importador nunca se considera autoridad.
- **Misma clave + mismo content_hash:** no-op idempotente, conservar la primera evidencia y añadir referencia a la ejecución repetida si se necesita auditoría.
- **Misma clave + hash distinto:** insertar revisión nueva, mantener la anterior y registrar `supersedes`; no mutar el pasado. Cambios de documento fuente se enlazan por versión/fecha.
- Cambios de ISIN, entidad, moneda, frecuencia o significado no se tratan como simple cambio de valor: crean nueva relación/revisión y revisión humana.
- `ON CONFLICT` debe tener una clave única acordada en el esquema DB. En una transacción, insertar revisión, linaje, estado de aprobación y actualizar el puntero `current` solo si el hash aprobado coincide. Reintentos de transacción no duplican historia.

## 7. Validación, anomalías y conflicto de fuentes

### Gates obligatorios

1. **Estructural:** JSON Schema 2020-12; campos conocidos, tipos, fechas RFC3339/ISO, URI, hash con longitud correcta y versión admitida. Rechazar valores NaN/infinitos, números como float, unidades desconocidas y propiedades extra.
2. **Identidad:** sintaxis/validación de ISIN y check digit en producción; claves jurídicas namespaced; ticker con MIC y moneda. Verificar relaciones ISIN↔listing y producto↔entidad con evidencia, no con similaridad de nombre.
3. **Semántica/unidad:** rango plausible definido por campo/familia; `valid_from < valid_to`; porcentaje compatible con concepto; `MONEY` con ISO currency; precio por 100 nominales nunca convertido en dinero. Rangos y reglas financieros los debe aprobar el responsable de dominio; este documento no inventa límites universales.
4. **Tiempo:** observar antes de comparar; validez, observación, publicación y consulta no se confunden. Fechas ausentes se conservan como ausentes y disparan la política correspondiente.
5. **Derechos/procedencia:** solo `license_status=allowed` permite avanzar; `unknown`/`review_required` a cuarentena; `blocked` rechazo de publicación y borrado de RAW si el régimen aplicable lo exige. La evidencia mínima es URI, título/fragmento o locator, digest, fecha y permiso.
6. **Duplicados:** clave lógica/hashes y versiones. Mismo hecho repetido no se suma ni sobreescribe; dos hechos solo son el mismo scope si identidad, periodo, definición, unidad y moneda coinciden.
7. **Outliers:** nunca winsorizar, recortar, interpolar ni elegir el dato más cercano automáticamente. Usar umbrales por campo expresamente aprobados; si no existen, registrar `OUTLIER_THRESHOLD_UNSET` y pedir revisión. Diferencia grande frente al último bueno puede ser un cambio real.
8. **Conflictos:** agrupar fuentes por el mismo hecho temporal/semántico; mostrar valores/evidencias lado a lado. Fuente primaria de una entidad prevalece solo para los campos que esa fuente acredita y con política documentada. No escoger automáticamente la fuente más reciente ni calcular promedio. Discrepancia de fuentes primarias, definiciones incompatibles o scope incierto = revisión.

### Errores y cambios de estructura

- Clasificar fallo como `FETCH_TRANSIENT`, `FETCH_FORBIDDEN`, `SOURCE_UNAVAILABLE`, `FORMAT_CHANGED`, `PARSE_ERROR`, `SCHEMA_ERROR`, `SEMANTIC_ERROR`, `RIGHTS_UNRESOLVED`, `IDENTITY_UNRESOLVED`, `STALE`, `SOURCE_CONFLICT` o `OUTLIER_REVIEW`.
- Timeout/5xx/429 se registran con intento y se reprograman con backoff acotado según política; 403/licencia no reintenta en bucle. Un cambio de content-type, estructura/selector, encabezado o fingerprint detiene el adaptador, conserva el último bueno y abre revisión. Nunca interpretar parseo vacío como lista vacía de productos ni publicar ceros.
- Adapter nuevo o cambio de mapping incrementa su versión; reproducir fixture de regresión y comparar diff. No autoactualizar selectores/modelos ni aceptar un esquema nuevo remotamente.
- El lote publica atómicamente por producto/revisión; errores parciales no marcan el lote entero como completo. Mantener contadores por importados, rechazados, en revisión y publicados.

## 8. PDF, OCR e IA

1. Conservar PDF/HTML original solo en cuanto los permisos lo permitan; limitar tamaño/tipo, calcular SHA-256 y registrar páginas/fragmentos de origen para cada campo.
2. Extracción determinista/tabla primero. OCR o IA puede proponer campos, jamás autoridad de valor/fecha/entidad ni decisión de publicación. Señalar `extraction.method=pdf_ocr|llm_assisted` y `human_verified=false`.
3. Revisor compara cada cifra, etiqueta/unidad, clase, periodo y condición con el documento visible y marca cada campo verificado. La aprobación se vincula al hash exacto del documento y del candidato; si cualquiera cambia, expira.
4. Conflicto entre texto/tablas, mala calidad OCR, documento escaneado, idioma/unidad desconocidos o páginas incompletas = cuarentena. No resolver contradicciones con lenguaje generado ni corregir el documento por contexto.
5. No enviar datos financieros personales al servicio IA; no usar IA para importar usuarios, cuentas, operaciones o decisiones. El LLM no tiene herramientas de escritura/SQL ni puede sortear gates. El informe de seguridad define las respuestas de IA y salida externa como no confiables y exige validación y revisión humana.[I10]

## 9. Revisión humana y publicación PostgreSQL

| Decisión | Condición | Efecto |
|---|---|---|
| `ACCEPT` | Estructura/unidades/identidad/frescura/derechos pasan; política del campo está configurada; revisión requerida completada | Publicador inserta versión y deja estado actual solo para el hash aprobado. |
| `REVIEW` | Primera alta/cambio material; source conflict; posible outlier; fuente/cadencia/licencia dudosa; vínculo jurídico o ISIN no verificado; PDF/OCR/IA; estructura alterada | No visible como dato vigente ni comparable. Revisor aprueba/deniega o pide fuente. |
| `REJECT` | Documento no permitido, identidad errónea, formato no recuperable o semántica incompatible | No publica. Mantener log mínimo; eliminar artefacto si permiso/retención lo exige. |
| `STALE` / `EXPIRED` | TTL de verificación vencido o intervalo explícito vencido | Mantener último bueno/historia y fecha; excluir el campo de comparación vigente; no sustituir por otro producto/fuente sin revisión. |
| `TOMBSTONE` | Fuente oficial confirma discontinuación o responsable confirma retirada | Ocultar producto de selección actual, conservar historial y motivo; no hard-delete/cascade automático. |

El control de publicación vuelve a comprobar justo antes del upsert que: `classification=production_candidate`, licencia `allowed`, validaciones vigentes, revisión firmada sobre el mismo `content_hash`, frescura aceptable para el campo, y ninguna supersesión posterior. Las fixtures `synthetic_fixture` se rechazan sin excepción en publisher. El estado de producción y el registro de pruebas permanecen separados.

### Borrado y caducidad por campo/producto

- **Caducidad del campo:** depende de `valid_to` explícita y TTL/umbral acordado por `source_id + family + field_path + uso`. Si falta un umbral, no declarar actual; conservar último bueno como stale y bloquear ese campo en comparaciones.
- **Ausencia en una captura:** una ficha que desaparece una vez no se considera retirada. Crear alerta y revisión; solo una fuente oficial explícita o confirmación humana crea `TOMBSTONE`.
- **Producto retirado:** desactivar para catálogo actual y preservar revisiones/linaje según derechos. Los enlaces a listas, costes, NAV y cotizaciones no se borran en cascada; cada uno conserva su ciclo de vida independiente.
- **Eliminación por licencia/privacidad/solicitud:** política específica de retención define si se borran bytes y valores o se conservan solo datos mínimos de auditoría (p. ej., digest/estado). No se promete conservar RAW cuando la fuente no lo autoriza.
- **Revisión del catálogo:** reactivar exige nueva evidencia/validación/aprobación. Ningún stale/expired/withdrawn se “arregla” editando in-place.

## 10. Política de comparabilidad

Un campo participa solo si tiene identidad resuelta, unidad/moneda compatibles, fecha de observación adecuada, vigencia aplicable, permiso, calidad y freshness válidas. Comparar fondos exige clase/periodo/definición de coste compatibles; deuda primaria, serie agregada y quote son tipos distintos; depósito se compara bajo mismas condiciones/saldo/plazo. Cuando falte un dato esencial o esté stale, mostrar “no disponible/no verificado” y excluirlo del orden/comparación actual, sin completar desde modelos de lenguaje. Las comparaciones deben ser neutrales y los cálculos deterministas.[I09]

## 11. Pruebas de aceptación y límites

Los casos de [`fixtures/casos.json`](fixtures/casos.json) son sintéticos: cambio contractual sin fecha observada, listing separado de clase, serie mensual histórica, extracción PDF asistida por IA, conflicto/outlier/stale, replay idempotente y error de moneda. `verifica_fixtures.py` valida JSON Schema, hashes de las cadenas sintéticas y esas invariantes mínimas.

Antes de conectar una fuente real, ejecutar —solo en entorno propio y con permisos—: replay del mismo RAW, cambio de documento, tasa ausente, estructura HTML/CSV cambiada, 403/429/timeouts, hash idéntico/cambiado, ISIN inválido/check digit, MIC/ticker duplicado, divisa ausente, moneda/porcentaje incompatibles, fechas inválidas, PDF con tabla/texto contradictorio, fuente stale, conflicto, outlier, retiro confirmado y rollback de transacción. Ninguna prueba externa de carga ni servicios se ejecutó para este entregable.

**No verificado / pendiente:** licencia de redistribución de cada fuente/campo; SLA/cadencia y cuotas de feeds futuros; umbrales de freshness por serie/proveedor/campo; límites de outlier por definición; esquema físico y constraints PostgreSQL; almacenamiento permitido de RAW; revisión jurídica y acceso minorista por producto. Los valores 24 h, 7 días y 90 días de la matriz son propuestas de política Paideia para pilotaje, no datos o compromisos de fuentes.

## 12. Evidencia consultada en el proyecto

Estas referencias apuntan a los informes de investigación ya entregados; sus secciones `Sources` contienen enlaces y notas de contraste de fuente primaria. Las decisiones operativas marcadas como propuestas son diseño de Paideia, no hechos extraídos.

- [I01] [`../../investigacion/01-cuentas-depositos.md`](../../investigacion/01-cuentas-depositos.md) — API BdE/BCE agregada, ficha contractual del banco, garantía y ausencia de una API gratuita universal con cadencia diaria confirmada.
- [I02] [`../../investigacion/02-deuda-publica.md`](../../investigacion/02-deuda-publica.md) — Tesoro/BOE por evento; series BdE diarias o mensuales según catálogo; no equiparar rendimiento agregado a quote por ISIN.
- [I03] [`../../investigacion/03-fondos-etf.md`](../../investigacion/03-fondos-etf.md) — ISIN de clase, costes/documentos, NAV vs precio negociado y límites de feeds públicos.
- [I09] [`../../investigacion/09-rigor-financiero.md`](../../investigacion/09-rigor-financiero.md) — unidad, coste, stale data, comparaciones neutrales y límites del LLM en datos financieros.
- [I10] [`../../investigacion/10-seguridad-calidad.md`](../../investigacion/10-seguridad-calidad.md) — extracción no confiable, control de salidas, revisión humana y no contratación.
- [I00] [`../../investigacion/00-SINTESIS.md`](../../investigacion/00-SINTESIS.md) — alcance/limitaciones de las pruebas documentales y advertencia de que cobertura diaria integral no está demostrada.
