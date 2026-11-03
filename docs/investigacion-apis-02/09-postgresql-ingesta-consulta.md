# 09 — PostgreSQL como catálogo de Pai: desarrollo, hosting, ingesta y consulta

## Decisión ejecutiva

**Usar PostgreSQL local solo para desarrollar/probar el esquema; no sirve como servicio público si el ordenador se apaga.** Para un piloto web de una semana y hasta 100 personas, la opción más directa es **Supabase Free + Data API/PostgREST**, con catálogo deliberadamente público en lectura, vistas/API de superficie pequeña y una función de servidor para la ingesta. La app y la base quedarían alojadas por el proveedor; no dependen del PC del desarrollador. El plan publica 500 MB de base, 5 GB de egress, 1 GB de archivos, 50.000 MAU y solicitudes API ilimitadas, pero los proyectos Free se pausan tras una semana de inactividad: no es garantía de servicio continuo ni una prueba de capacidad para 100 usuarios concurrentes.[7]

**Alternativa:** Neon Free para Postgres administrado cuando ya exista una función/backend donde ejecutar consultas con su driver serverless. Publica 100 CU-horas por proyecto/mes, 1 GB de almacenamiento por proyecto y 5 GB de transferencia por proyecto; el cómputo pasa a cero tras cinco minutos inactivo y despierta al recibir una conexión. Esto puede añadir latencia inicial; no se encontró SLA de disponibilidad en el plan Free.[14][15] La página de planes también publica un límite de 2 CU en Free.[14]

**No elegir todavía entre proveedores para producción:** no se ha creado cuenta/proyecto, no se han probado credenciales/API de aplicación, no se ha revisado la DPA/región concreta ni se ha hecho prueba de carga. Revisar las condiciones vigentes antes del piloto. Si Pai debe estar disponible sin interrupciones garantizadas, presupuestar un plan con SLA/soporte o acordar una alternativa; los dos Free tienen restricciones distintas.

## Local vs nube gratuita

| Opción | Lo que resuelve | Lo que no resuelve / límites relevantes | Encaje |
|---|---|---|---|
| PostgreSQL local | Desarrollo, pruebas de esquema, importadores y consultas sin publicar datos. | Solo es accesible mientras el equipo que lo hospeda esté encendido y conectado; no da URL pública, copias operativas ni un cron remoto por sí solo. | **Sí para desarrollo; no como hosting del piloto.** |
| Supabase Free | Postgres administrado más Data API REST basada en PostgREST, API key/JWT, RLS y Cron; sirve la app y los trabajos desde la nube.[8][9][11] | 500 MB DB, 5 GB egress y 1 GB de archivos; proyectos Free se pausan si están inactivos una semana. Las 50.000 MAU y “API requests ilimitadas” del plan no equivalen a 100 conexiones PostgreSQL simultáneas ni a una garantía de latencia/uptime.[7] Las Edge Functions Free tienen 150 s de duración máxima y 2 s de CPU por petición.[12] | **Mejor primer candidato para el piloto**, condicionado a pausa Free y comprobación real de uso. |
| Neon Free | Postgres administrado con pooler PgBouncer y driver JS/TS para consultas desde serverless/edge mediante HTTP o WebSockets.[15][16] | 100 CU-h/mes/proyecto, 1 GB/proyecto, 5 GB de transferencia y scale-to-zero tras cinco minutos; el primer acceso tras reposo puede tener cold start. Neon da Postgres, no se debe suponer una API REST PostgREST equivalente sin elegir/configurar esa capa.[14][15] | Buena alternativa si ya se adopta backend serverless. Hacer prueba del despertar y de cuota antes. |

Para 100 usuarios no se debe abrir una conexión TCP PostgreSQL por pestaña o usuario. El navegador llama a una **API HTTP**; PostgREST comparte conexiones reutilizables en un pool, y el pooler se usa para backend/serverless. PostgREST documenta un pool dinámico que atiende muchas peticiones HTTP con menos conexiones DB.[5] Supabase recomienda Data API para frontend y pooler de transacciones para funciones serverless.[10] Esto evita diseñar 100 conexiones permanentes; **no demuestra capacidad para 100 solicitudes simultáneas**, que requiere prueba de carga con los endpoints, planes y consultas concretos.

## API consultable y piezas reutilizables

- **PostgREST:** expone tablas y vistas autorizadas como recursos GET, admite filtros/paginación y publica RPC bajo `/rpc/<función>`.[2][3] Su documentación enlaza una sección OpenAPI.[6] No se ha generado el OpenAPI de Pai. Úsese para exponer vistas curadas (p. ej. `catalog_listing_current`) y no toda la base.
- **Supabase Data API:** URL de forma `https://<project_ref>.supabase.co/rest/v1/`; es PostgREST autogenerado del esquema, con REST/GraphQL según configuración.[8] SDKs oficiales reutilizables: `supabase-js` para JavaScript/TypeScript y `supabase-py` para Python, además de Flutter/Dart y Swift.[18]
- **RPC de lectura:** una función PostgreSQL estrecha puede recibir parámetros tipados y devolver filas filtradas; PostgREST permite GET para funciones que no modifican datos.[3] En PostgREST, GET/HEAD son transacciones READ ONLY; una RPC invocada por GET es de solo lectura, y una función `STABLE` por POST también queda en modo READ ONLY.[4] Aun así, dar a la función solo `EXECUTE` necesario y evitar `SECURITY DEFINER` salvo revisión.
- **Neon serverless driver:** reutilizable desde JS/TS en funciones serverless/edge; su documentación recomienda HTTP para consultas simples y ofrece query parametrizada/tagged-template, además de WebSockets cuando se necesitan sesiones/transacciones interactivas.[16] Mantener `DATABASE_URL` solo en secreto del servidor; no incrustarla en el navegador.
- **No probado como servicio de aplicación:** se obtuvieron páginas de documentación públicas (ver `tests` en JSON), no se invocó una base desplegada ni una URL REST con credenciales. Las páginas de docs no prueban autenticación, cuotas efectivas, RLS ni rendimiento de Pai.

## Esquema mínimo propuesto

Separar identidad y dato observado: un producto canónico puede tener muchas ofertas/listings, condiciones, fuentes y documentos. No guardar el perfil financiero personal en estas tablas compartidas.

| Tabla | Campos clave / propósito |
|---|---|
| `entities` | `id`, tipo (emisor/proveedor/fabricante), nombre, país y claves externas. |
| `products` | `id`, nombre normalizado, marca/emisor, identificadores externos con namespace (p. ej. ISIN/GTIN cuando aplique), estado. No confundir producto con oferta. |
| `classes` + `product_classes` | Taxonomía jerárquica (`scheme`, código, etiqueta, `parent_id`) y relación N:M con productos. |
| `sources` | Proveedor/editor, API o página base, identificador externo, clave de adaptador, URL de términos, límites/rate policy documentados y estado de revisión de derechos. Las credenciales no se guardan aquí. |
| `listings` | Oferta/entrada publicada: producto, entidad oferente, fuente, `external_id`, mercado/país, URL, estado, primera/última observación. Clave única `(source_id, external_id)`. |
| `conditions` | Una fila por condición tipada de listing: `field_key`, valor numérico/texto, unidad/moneda, `valid_from`, `valid_to`; guardar términos distintos como filas, no como un único texto opaco. |
| `catalog_versions` | Snapshot/version de entidad, producto o listing: versión de origen, `source_published_at`, `retrieved_at`, hash de payload, payload normalizado y estado de validación. Append-only para auditoría/cambios. |
| `observations` | Historial append-only por campo, con FK opcional exactamente a uno de producto/listing/entidad, `field_key`, valor tipado/JSON, `source_id`, `document_id`, `observed_at`, fecha efectiva `as_of_at`, hash, estado y `ingest_run_id`. Mantener dos tiempos: cuándo se obtuvo y desde cuándo dice la fuente que vale. |
| `documents` | Metadatos y URL del documento, fecha de publicación/efectividad, MIME, hash, referencia a almacenamiento y estado de permiso. **No guardar el PDF completo** hasta confirmar permiso de copia/retención; por defecto guardar URL y metadatos. |
| `source_licenses` | Términos/licencia, atribución exigida, uso permitido, redistribución/almacenamiento (sí/no/desconocido), URL, responsable y fecha de revisión. `desconocido` bloquea descarga/redistribución; no es una conclusión legal. |
| `field_freshness_policy` + `ingest_runs` | Por campo/fuente: edad máxima aceptable, prioridad y verificación exigida. Cada ejecución: inicio/fin, cursor, recuentos, estado y error. Sirve para auditoría y aviso de datos obsoletos. |

**Frescura por campo:** no actualizar `updated_at` al recoger una fila si la fecha efectiva del valor no cambió. En cada lectura devolver valor, fuente, `as_of_at`, `observed_at`, URL/documento y bandera `fresh/stale/unknown`, calculada con `field_freshness_policy`. Mantener todas las observaciones; escoger la última vigente según prioridad/validación, no simplemente la más reciente descarga. Si hay conflicto o falta fecha, presentar ambas/indicar incertidumbre. Las condiciones deben mostrar fecha de vigencia y no parecer actuales porque el crawler pasó hoy.

## Ingesta diaria incremental — arquitectura, no implementación

1. Ejecutar un cron alojado (por ejemplo, Supabase Cron puede ejecutar SQL o invocar por HTTP una Edge Function); el ordenador local no participa.[11] Mantener el importador como función/backend en nube y guardar secretos en el almacén de secretos del proveedor.
2. Añadir un adaptador por proveedor: `fetch` con cursor o `ETag`/`Last-Modified` si la fuente los ofrece; validar código/respuesta/esquema; normalizar IDs/fechas/unidades; comprobar cuota y derechos antes de persistir. Registrar proveedor, fecha efectiva, fecha recuperada, atribución y hash.
3. Hacer upsert idempotente por `(source_id, external_id)`, insertar versión/observación solo si cambió el dato, y guardar el cursor solo al completar la transacción. Registrar fallos y reintentar con backoff limitado. Un fallo conserva el último dato bueno y lo marca stale; una ausencia en respuesta parcial no borra una oferta.
4. Dividir trabajo largo por fuente/lotes: Supabase Edge Function Free limita duración a 150 s y CPU a 2 s por solicitud, por lo que conviene que el trabajo sea mayoritariamente I/O y no recorrer grandes corpus de PDFs en una ejecución.[12] Almacenar documentos aparte solo con derecho verificado.
5. Medir ejecuciones, tamaño de datos y egress; mantener página/UI con fuente y frescura visibles. Añadir cada futura API mediante adaptador, sin acoplar su formato ni autenticación al cliente/LLM.

La DB no incorpora datos de Internet por existir ni actualiza por sí sola el contenido: se necesita una fuente, permisos, un adaptador y una planificación. Los proveedores de datos deben evaluarse uno por uno: la API/servidor de consulta no concede derecho a copiar, conservar o redistribuir la respuesta ni resuelve derechos de PDFs.

## Consultas parametrizadas, read-only y seguridad

1. Exponer esquema API dedicado y vistas `catalog_listing_current`, `product_detail`, `field_provenance`; conceder al rol público solo `SELECT` sobre esas vistas. Para catálogo intencionalmente público, acceso anónimo de lectura puede ser suficiente; RLS/grants deben seguir activos y explícitos.
2. Mantener la parte de escritura/ingesta únicamente en función del servidor con rol de mínimo privilegio. En tabla de perfiles (si se centraliza en futuro), activar RLS y filtrar `owner_id` al usuario autenticado; preferible conservar perfil local y borrable, separado de catálogo compartido.
3. No dar consultas SQL arbitrarias generadas por LLM, ni `INSERT/UPDATE/DELETE` o DDL al rol de lectura. Usar filtros sobre columnas permitidas y RPC de consulta con parámetros tipados, límites `LIMIT`, `statement_timeout` y lista blanca de ordenación/filtros. Si el backend ejecuta SQL, enlazar valores como parámetros (`$1`, `$2`), nunca interpolar entradas en el texto SQL.
4. Supabase documenta que grants determinan qué objetos puede alcanzar un rol y RLS qué filas puede leer/modificar; recomienda RLS en objetos expuestos y control explícito de `EXECUTE` en funciones.[9] PostgreSQL aplica denegación por defecto cuando RLS está habilitada sin política; roles `BYPASSRLS`, superusuario y, normalmente, propietario la saltan.[1] Mantener separadas funciones y tablas internas, y no confiar en RLS si se usa una clave privilegiada.
5. La clave publishable/anon solo se expone si las políticas permiten exactamente lo que se publica; clave `service_role`, contraseña DB y URL de conexión permanecen secretas en servidor. Supabase avisa que los grants predeterminados de proyectos existentes pueden dejar tablas/funciones de `public` expuestas: revisar y revocar defaults o usar esquema API dedicado antes de añadir tablas.[9][10]

## SQL para catálogo vs RAG textual

- **SQL es el camino principal** para comparaciones cuantitativas y filtrables: producto/clase/país, importe, tipo de condición, vigencia, ordenación, límites, joins y agrupaciones. El resultado mantiene valores tipados y trazables a una fuente. El LLM puede redactar una explicación sobre esas filas, pero no debe inventar condiciones ni cambiar unidades.
- **RAG** es útil para preguntas sobre contenido no estructurado de folletos, condiciones extensas, preguntas frecuentes o documentos: extraer texto con página/sección, recuperar los fragmentos pertinentes y pasar al modelo solo esos fragmentos con URL/fecha/citas. Es complementario: un fragmento no sustituye una consulta SQL para comparar números, ni prueba que un documento pueda redistribuirse.
- **No hace falta pgvector al principio** si Pai consulta campos estructurados y el corpus documental es pequeño o se puede seleccionar por producto/fecha/keywords; la primera versión puede devolver enlaces y metadatos, y el LLM leer un número acotado de fragmentos autorizados. `pgvector` sirve para guardar/buscar embeddings de similitud; obtenerlos exige un modelo de embeddings/proceso explícito.[13][17] Añadirlo cuando una prueba muestre que la búsqueda semántica aporta mejores documentos que filtros/búsqueda lexical y se haya aprobado proveedor, coste, privacidad y mantenimiento de embeddings.

**La base no alimenta ni entrena automáticamente un LLM.** Solo si la aplicación hace explícitamente la consulta, selecciona resultados y los envía en contexto a un servicio LLM existe retrieval en tiempo de consulta; guardar filas o activar pgvector no equivale a entrenamiento. El uso y retención de esos datos en el proveedor LLM debe revisarse aparte. Ni Postgres, ni PostgREST, ni RLS deciden si se pueden copiar o mostrar documentos; derechos y atribución se resuelven por fuente/licencia antes de ingestarlos.

## Fuentes y verificación

Los límites son los publicados en las páginas oficiales consultadas y pueden cambiar. Se hicieron GET de páginas de documentación públicas, no llamadas a una instancia propia de la API. El JSON adjunto conserva URLs, evidencia y las cinco comprobaciones HTTP con archivos de evidencia. `tests` distingue página documental de prueba funcional; no se registró cuenta, no se guardaron secretos, no se instaló software ni se creó una base.

## Sources

[1] https://www.postgresql.org/docs/current/ddl-rowsecurity.html
[2] https://docs.postgrest.org/en/stable/references/api/tables_views.html
[3] https://docs.postgrest.org/en/stable/references/api/functions.html
[4] https://docs.postgrest.org/en/stable/references/transactions.html
[5] https://docs.postgrest.org/en/stable/references/connection_pool.html
[6] https://docs.postgrest.org/en/stable/references/api.html
[7] https://supabase.com/pricing
[8] https://supabase.com/docs/guides/api
[9] https://supabase.com/docs/guides/api/securing-your-api
[10] https://supabase.com/docs/guides/database/connecting-to-postgres
[11] https://supabase.com/docs/guides/cron
[12] https://supabase.com/docs/guides/functions/limits
[13] https://supabase.com/docs/guides/database/extensions/pgvector
[14] https://neon.com/docs/introduction/plans
[15] https://neon.com/pricing
[16] https://neon.com/docs/serverless/serverless-driver
[17] https://github.com/pgvector/pgvector
[18] https://supabase.com/docs/guides/api/rest/client-libs
