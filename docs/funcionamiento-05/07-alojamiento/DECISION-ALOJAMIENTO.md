# Alojamiento 0 EUR con equipos apagados — decisión documental

**Estado:** recomendación condicional; no despliegue, alta de cuenta ni autorización para usar datos reales.  
**Consulta:** 2026-10-28. Siete páginas oficiales recuperadas; se intentó una octava (AUP de Cloudflare) sin recuperar su contenido.  
**Alcance:** máximo dos opciones; no cuentas, claves, pagos, llamadas autenticadas, instalaciones, DB, datos reales, dependencias nuevas ni parche de producción. No declarar disponibilidad online, 100 usuarios concurrentes, gratuidad perpetua o privacidad aprobada.

## Decisión breve

**No desplegar la app actual tal cual. No hacer PostgreSQL obligatorio.** Para un futuro piloto estrictamente gratuito con el PC apagado, priorizar como hipótesis **Cloudflare Workers Python Free con JSON versionado en el build**; añadir KV únicamente si una prueba demuestra que hace falta una caché compartida dinámica. Este es un camino de evaluación, no una selección final: el alta sin tarjeta, los términos de abuso, los detalles de privacidad/región EEE, la operación diaria de Cron y el alojamiento del frontend no quedaron aprobados ni probados. Cloudflare publica un plan Free y límites concretos, pero eso no confirma elegibilidad ni coste efectivo de esta cuenta.[4][5]

La propuesta anterior `docs/planificacion-03/13-despliegue-operacion/ESPECIFICACION.md` ya planteaba Pages + Worker y snapshot estático, con DB opcional. Esta revisión concreta las limitaciones de runtime, estado y cuotas del Worker; **no revalida Pages ni el build frontend**. Render Free es útil para ensayo/hobby, no es mi recomendación para servicio público: sus propios docs dicen que no se use Free para aplicaciones de producción, que duerme tras 15 min sin tráfico y tarda alrededor de un minuto en despertar.[1] Su ventaja es ejecutar Python como web service con menos cambio de modelo; su filesystem efímero invalida una caché que escriba JSON localmente.[1]

## Base local verificada (sin modificar)

| Parte | Estado encontrado | Implicación para alojamiento |
|---|---|---|
| Contrato y alcance | `docs/funcionamiento-05/00-CONTRATO.md`: presupuesto 0 EUR; sin cuentas, claves, DB real ni despliegue. PostgreSQL se cuestiona, no se ha aprobado quitarlo o crearlo. El catálogo incluye 20 candidatos y 0 ofertas cuantitativas publicables. | No conectar servicios ni inferir una necesidad de DB a partir de APIs. |
| Servidor | `prototipos/paideia-local/app.py`: `ThreadingHTTPServer`; `create_server` rechaza hosts distintos de `127.0.0.1`; `main` usa puerto CLI (por defecto 8765). Las comprobaciones Host/Origin también exigen loopback y origen HTTP local. | Un proxy/cloud no podrá acceder al listener ni pasar las comprobaciones públicas sin un diseño y pruebas expresos. Cambiar solo el bind no es suficiente ni autorizado aquí. |
| Catálogo | `SnapshotRepository` carga un JSON del repositorio al iniciar y conserva una vista de solo lectura en memoria. No hay caché central mutable ni persistencia de escrituras. | Un JSON revisado y empaquetado con una versión puede servir al catálogo actual sin PostgreSQL. |
| Chat/secretos | Chat deshabilitado por defecto (`CHAT_NOT_CONFIGURED`). `PROVEEDORES.md` indica opt-in y clave por entorno solo para un uso futuro autorizado; no se leyó ninguna clave ni se hizo llamada externa. | Mantener chat apagado. No pedir ni introducir credenciales ahora. |

## Matriz comparativa: Free documentado ≠ cuenta elegible

| Criterio | Render Free — runtime Python | Cloudflare Workers Free — Worker Python y KV opcional |
|---|---|---|
| **PC apagado / runtime** | Render ofrece web services gratuitos con apps Python, pero su documentación advierte que no se usen para producción; no se ha acreditado aquí una prohibición contractual.[1] | Python Worker recibe cada petición mediante un handler `fetch`; soporta bindings para estado/KV y variables/secrets.[3] Es un modelo distinto de ejecutar `ThreadingHTTPServer`. |
| **Sleep / cold start** | Duerme tras 15 min sin tráfico; volver a arrancar tarda alrededor de 1 min y muestra una pantalla de carga.[1] | Las páginas examinadas no documentan aquí una política de sleep ni una promesa de cold start para esta app; no afirmar “sin cold start” ni latencia. [unverified] |
| **Filesystem / JSON** | Free tiene filesystem efímero; cambios locales se pierden al dormir y en ciclos de servicio.[1] JSON incluido en el build es distinto de un fichero runtime modificado. | La documentación consultada ofrece KV como binding de almacenamiento y publica cuotas, pero no revisé consistencia, replicación ni garantías de backup/durabilidad. No basar estado en memoria de una instancia; validar KV o usar artefacto versionado de build.[3][5] |
| **Cuota vigente de Workers** | Página consultada confirma el servicio Free, pero el extracto revisado no aportó el cupo de horas ni el importe de ancho de banda; ambos quedan sin verificar en esta matriz. [unverified] | Página oficial, actualizada 2026-10-02: 100.000 solicitudes/día y 10 ms CPU por invocación en Free.[4] Son límites de requests/CPU, no una prueba de concurrencia, latencia, disponibilidad ni 100 usuarios. Workers Paid tiene mínimo publicado de 5 USD/mes por cuenta: queda fuera de 0 EUR.[4] |
| **KV compartido** | Un fichero JSON escrito durante la ejecución no es persistente en Free.[1] No propongo SQLite ni otra DB como atajo. | KV incluido en Free: página oficial actualizada 2026-04-21 publica 100.000 lecturas/día, 1.000 escrituras, borrados y listados/día y 1 GB almacenado; límites diarios y operaciones excedidas fallan.[5] La página consultada no prueba la semántica de consistencia ni la recuperación de datos; tratar esos puntos como pendientes. [unverified] |
| **Build, manual o diario** | Cambiar un snapshot empaquetado exige preparar y desplegar otra versión; los cambios de entorno pueden pedir rebuild/deploy o quedar pendientes del siguiente deploy.[2] La actualización diaria de datos no viene de tener JSON local. | Un snapshot versionado se actualiza al preparar/revisar y desplegar otro build. KV podría recibir una versión mediante operación autorizada manual o job; un Cron Trigger permite ejecución programada, pero el extracto no permite afirmar cuota, puntualidad/SLA ni una ingesta diaria probada.[6] |
| **Red saliente** | El tráfico saliente cuenta contra importes mensuales incluidos de ancho de banda; el límite concreto no quedó en el extracto consultado.[1] | Workers no factura sus subrequests por petición en la tabla consultada y KV indica sin cargo por egress; eso no concede acceso, licencia, cuota ni egress gratuito del API de origen.[4][5] |
| **Config y secretos** | Docs recomiendan variables de entorno para configuración y secretos; el cambio puede reconstruir, desplegar o esperar al siguiente deploy.[2] | Python Workers expone bindings de variables/secrets.[3] No se configuró nada; cualquier secreto futuro requeriría autorización del equipo y almacenamiento del proveedor, nunca código/cliente/prompts. |
| **EEE, abuso, tarjeta, cuenta** | Región, DPA, tratamiento EEE, AUP/abuso, requisitos de tarjeta y elegibilidad de esta cuenta no se verificaron. [unverified] | DPA v6.4 (vigente 2026-04-03) contempla transferencias desde EEE/Suiza/Reino Unido y SCC, pero requiere acuerdo principal; asigna al Customer responsabilidad por la legalidad de los datos.[7] No establece por sí sola residencia EEE ni aprobación para perfiles financieros. AUP no recuperada; tarjeta/cardless y aceptación de cuenta no probadas. [unverified] |

### 0 EUR publicado frente a lo que no se comprobó

| Opción | Lo publicado en docs oficiales | No verificado en esta cuenta |
|---|---|---|
| Render Free | Algunos web services Python se ofrecen gratis; el plan Free tiene límites y no se recomienda para producción.[1] | Si el alta es sin tarjeta, región aplicable, importe de ancho de banda/pipeline incluido, cargos/condiciones reales del workspace y cualquier permanencia del plan. [unverified] |
| Cloudflare Workers/KV Free | Existe plan Workers Free; KV figura incluido y tiene cuotas Free publicadas. Workers Paid tiene mínimo de 5 USD/mes/cuenta.[4][5] | Acceso efectivo sin tarjeta, requisitos de alta, límites/billing de esta cuenta, impuestos/moneda, cuenta gratis elegible, egress/fetch al origen, precio futuro o gratuidad perpetua. [unverified] |

**Lectura económica:** “Free” es coste publicado para los servicios/cuotas descritos, no confirmación de que el alta de esta cuenta sea sin tarjeta o sin condiciones. No se probó ni se presupone tarjeta, cargo, exención, acceso permanente o cambio futuro de términos.[1][4] La cuota publicada no equivale a capacidad probada ni a servicio gratuito perpetuo.

## Arquitectura de lectura: API directa frente a caché central

- **Lectura directa del API público desde cada navegador:** evita alojar una copia compartida, pero cada visitante genera sus propias lecturas y depende directamente de disponibilidad, CORS, cuotas, atribución/licencia y frescura de la fuente. Solo sería admisible para una API expresamente pública, de lectura y autorizada para uso desde navegador; nunca poner una clave privada allí. Esta vía no crea un estado común “último bueno” ni una fecha común de actualización.
- **Snapshot JSON dentro del build:** una persona/equipo obtiene y valida el lote permitido, conserva fuente, fecha efectiva y fecha de consulta, y publica una nueva versión. Todos leen la misma revisión del catálogo; no hay DB ni escritura runtime. Un push/build puede automatizar la publicación de código, pero no equivale a refrescar datos cada día.
- **Caché central compartida en KV:** Worker obtiene una vez una respuesta permitida y escribe un snapshot/versionado compartido; visitantes leen esa versión común. Aísla claves de servidor y reduce lecturas repetidas a fuentes, pero añade límites de KV, permisos de escritura, frescura, errores y responsabilidad operativa. Las cuotas publicadas no prueban consistencia/durabilidad, disponibilidad ni que el fetch diario quepa en el límite.[4][5]
- **Actualización automática diaria:** requiere cron remoto, fuente/API y derechos aprobados, adaptador, validación, límites, política de “último bueno” y estado/alerta de antigüedad. La página de Cron recuperada solo confirma la primitiva de ejecución programada, no su cuota Free, puntualidad o éxito.[6] Sin esos elementos, etiquetar el dato como manual/versionado, no “actualizado diariamente”.

La API no implica PostgreSQL: es fuente, mientras que el caché, normalización, historial y consultas son decisiones separadas. Para los metadatos de solo lectura actuales, JSON versionado es la mínima arquitectura; KV es una opción de caché compartida, no una DB SQL. PostgreSQL se justificaría si una prueba de requisitos demuestra consultas relacionales/joins e historial con consultas que ya no se pueden servir de forma fiable con snapshots, o escrituras concurrentes/transaccionales que necesiten consistencia y auditoría. No se justifica por tener APIs o por hospedar el prototipo. No se propone SQLite, D1, ni otra base como workaround.

## Adaptación mínima antes de cualquier cloud

1. **Render:** separar las funciones de aplicación de `BaseHTTPRequestHandler`, decidir cómo escuchar en el puerto/interfaz que asigne el servicio y revisar el esquema Host/Origin/HTTPS detrás del proxy. No relajar controles de origen por conveniencia; probarlos con el host real y errores de seguridad. El servidor local no cumple esos contratos ahora.
2. **Cloudflare Python Worker:** conservar dominio, validadores, contratos y lógica existente; añadir en el futuro un adaptador pequeño del modelo `fetch` a la aplicación/rutas. El handler `fetch` de Cloudflare no es el socket HTTP local y `app.py` limita el bind a loopback.[3] La guía usa `WorkerEntrypoint` del módulo `workers` y exige la bandera de compatibilidad `python_workers`; reservar cualquier herramienta/dependencia de desarrollo para autorización futura, sin instalarla aquí.[3] Decidir cómo empaquetar estáticos y el snapshot o leer una clave KV. No portar el negocio entero ni introducir FastAPI/otro framework sin necesidad demostrada.
3. **Persistencia y privacidad:** no escribir caché de catálogo en el filesystem efímero de Render. Mantener perfiles en navegador; no enviar perfil/prompt a cloud/LLM ahora. Para cualquier futuro secret, usar variables/bindings del servidor tras aprobación; jamás incluirlo en JS, JSON publicado, repo o log.[2][3]
4. **Pruebas obligatorias:** smoke test sintético de rutas/rendimiento/errores, origen y secretos; test de lectura después de reinicios/redeploy, límites y comportamiento de KV; ejecutar una vez el cron autorizado y verificar su resultado/caducidad. La prueba debe ser desde cliente externo con el PC del desarrollador apagado; no representa una prueba de carga de 100 usuarios.

## Recomendación condicional y prueba decisiva

**Recomendación:** conservar PostgreSQL como herramienta local opcional de desarrollo, sin hacerlo requisito de servicio. Para el siguiente ensayo de alojamiento, comparar Cloudflare Worker Python + JSON de build primero y añadir KV solo para una necesidad demostrada de actualización central compartida. No seleccionar Render Free como servicio público estable por su propia advertencia de no producción y por el sleep/cold start.[1] No aprobar producción todavía: el front-end/Pages y el proceso de build no formaron parte de las páginas auditadas aquí; privacidad EEE, AUP y alta sin tarjeta siguen bloqueos.

**Prueba decisiva futura (con autorización explícita del equipo, cuenta Free confirmada y solo datos sintéticos):** desplegar un adaptador mínimo que devuelva una versión JSON sintética desde el Worker; con el PC apagado, leerlo desde otro cliente, escribir/publicar una nueva versión KV si se necesita, leerla desde una petición independiente y comprobar tras reinicio/redeploy; invocar el cron de prueba y verificar la marca de última ejecución, el límite de cuota, fallo y conservación del último bueno. Antes de iniciarla, el equipo debe confirmar en el panel y términos que el plan permanece a 0 EUR para el uso y que no exige una tarjeta que no se quiera aportar, revisar AUP/DPA y aprobar región/privacidad. No usar claves, datos reales, carga concurrente ni activar chat en esta prueba.

## Registro de intentos y pendientes

- Recuperadas 7 páginas oficiales: Render Free y variables/secretos; Cloudflare Python Workers, pricing, KV, Cron y DPA. Sus citas y extractos literales están en `sources-ledger.json` y `evidence/`.
- AUP oficial de Cloudflare: primer intento con `web_extract` devolvió `http_error`; el segundo intento de navegador no llegó a la página (`await outside function`). Se detuvo al llegar al límite de dos intentos fallidos. No se usa como evidencia y no se afirma que el uso esté permitido o prohibido.
- No se recuperaron páginas de privacidad/AUP de Render, Pages hosting, los términos específicos de la cuenta, prueba de tarjeta, calidad de servicio, disponibilidad, precio futuro, cron diario real, backup/consistencia de KV o capacidad para 100 usuarios. Permanecen sin verificar.

## Sources

[1] https://render.com/docs/free — Deploy for Free — Render docs
    > "Do not use them for production applications."
    > "Render spins down a Free web service that goes 15 minutes without receiving any inbound traffic."
    > "This process takes about one minute."
    > "Like all Render services, Free web services have an ephemeral filesystem."
    > "Web services and static sites count against your monthly included amounts of outbound bandwidth and pipeline minutes."
    > "Web services (web apps in Node.js, Python, Rails, etc.)"
[2] https://render.com/docs/configure-environment-variables — Environment Variables and Secrets — Render docs
    > "You can (and should!) use environment variables to configure your Render services:"
    > "They also protect you from committing secret credentials (such as API keys or database connection strings) to your application source."
    > "Save, rebuild, and deploy: Render triggers a new build for your service and deploys it with the new environment variables."
    > "Your service will not use the new variables until its next deploy."
[3] https://developers.cloudflare.com/workers/languages/python — Write Cloudflare Workers in Python
    > "the main entry point for a Python worker is the `fetch` handler which handles incoming requests sent to the Worker."
    > "State storage and databases like KV, D1, Durable Objects"
    > "Access to Environment Variables, Secrets, and other Workers using Service Bindings"
    > "In a Python Worker, this handler is placed in a `Default` class that extends the `WorkerEntrypoint` class (which you can import from the `workers` SDK module)."
    > "You must add the `python_workers` compatibility flag to your Worker."
[4] https://developers.cloudflare.com/workers/platform/pricing — Cloudflare Workers pricing
    > "By default, users have access to the Workers Free plan."
    > "Free | 100,000 per day | No charge for duration | 10 milliseconds of CPU time per invocation"
    > "The Workers Paid plan includes Workers, Pages Functions, Workers KV, Hyperdrive, and Durable Objects usage for a minimum charge of $5 USD per month for an account."
    > "Cloudflare does not bill for subrequests you make from your Worker."
[5] https://developers.cloudflare.com/kv/platform/pricing — Cloudflare Workers KV pricing
    > "Workers KV is included in both the Free and Paid Workers plans."
    > "The Workers Free plan includes limited Workers KV usage. All limits reset daily at 00:00 UTC."
    > "If you exceed any one of these limits, further operations of that type will fail with an error."
    > "Keys read | 100,000 / day | 10 million/month, + $0.50/million"
    > "Keys written | 1,000 / day | 1 million/month, + $5.00/million"
    > "Stored data | 1 GB | 1 GB, + $0.50/ GB-month"
    > "Does Workers KV charge for data transfer / egress? No."
[6] https://developers.cloudflare.com/workers/configuration/cron-triggers — Cron Triggers — Cloudflare Workers docs
    > "Enable your Worker to be executed on a schedule."
[7] https://www.cloudflare.com/cloudflare-customer-dpa — Cloudflare Data Processing Addendum
    > "This DPA applies where Cloudflare processes Personal Data as a Processor (or sub-Processor as applicable) on behalf of Customer to provide the Services and such Personal Data is subject to Applicable Data Protection Laws (as defined below)."
    > "the Customer shall have sole responsibility for the accuracy, quality, and legality of Personal Data and the means by which the Customer acquired Personal Data."
    > "Data transfers from the EEA, Switzerland, and the UK"
    > "Version 6.4, effective April 3, 2026"
    > "Cloudflare, Inc. (“Cloudflare”) and the counterparty agreeing to these terms (“Customer”) have entered into an Enterprise Subscription Agreement, Self-Serve Subscription Agreement or other written or electronic agreement for the Services provided by Cloudflare (the “Main Agreement”)."
