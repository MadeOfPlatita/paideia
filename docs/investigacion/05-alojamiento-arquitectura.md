# Paideia — alojamiento y arquitectura mínima sin coste

**Consulta de documentación oficial: 2026-10-26.** Investigación documental solamente: no se crearon cuentas, no se instaló ni ejecutó código remoto, no se desplegó y no se hizo una prueba de carga. El proyecto aún no tiene aplicación publicada.

## Dictamen

La recomendación mínima es **Cloudflare Pages para la SPA y el catálogo estático + Cloudflare Worker para `/api/chat` + Workers AI en un modelo habilitado en Free**.[1][5][28]
Pages sirve assets estáticos gratis e ilimitados.[28]
Pages Functions y Workers dinámicos sí comparten la cuota Workers Free de 100.000 solicitudes/día.[1][28]
Workers AI ofrece 10.000 Neurons/día.[5]
Su límite predeterminado de generación de texto es 300 solicitudes/minuto, sujeto a excepciones por modelo.[6]

Esto **no certifica 100 chats simultáneos**; la documentación de cuotas no es una prueba de carga de Paideia.[1][6]
El coste cero solo se mantiene dentro de los cupos Free y si no se activa Workers Paid ni un modelo de pago.[2][5][6]
Las páginas de precios consultadas no especifican si el alta exige tarjeta; no se ha verificado y no se debe asumir.[2][16][21]
Workers Paid tiene un mínimo de 5 USD/mes por cuenta.[2]

## Arquitectura propuesta para una semana

```text
GitHub Actions (repo público; ejecución diaria fuera del minuto :00)
  └─ consulta APIs oficiales autorizadas → valida → genera catalog.json
      └─ commit solo si el snapshot completo pasa validaciones
          └─ Cloudflare Pages Free: SPA responsive + /data/catalog.json
              └─ entrega estática global, compartida y cacheable

Navegador (perfil de Pai local, borrable)
  └─ POST /api/chat + token Turnstile → Cloudflare Worker
       ├─ valida origen permitido, esquema y tamaño de entrada
       ├─ valida token con Siteverify y aplica límite de uso
       └─ Workers AI binding (o proveedor externo con clave como Secret)
```

- **Catálogo y caché:** publicar el catálogo como un `catalog.json` estático de solo lectura; es la misma representación para todos, no una respuesta personalizada.[28] Para la primera versión no hace falta Redis ni una base de datos (decisión de alcance). Pages Free admite 500 builds/mes y un build simultáneo.[3] Una actualización diaria supone unos 30 builds/mes (6% del máximo), si cada actualización genera un build.[3] Los assets estáticos de Pages son gratuitos e ilimitados; las funciones dinámicas no lo son.[28]
- **Actualización diaria:** programar el workflow, por ejemplo, a las 03:17 UTC y no al inicio de la hora.[25] El job consultaría solo APIs con permiso y validaría esquema, identificador, valores, fuente, fecha efectiva y frescura (propuesta). Publicar solo si el snapshot queda completo; si falla, conservar el último bueno (propuesta). Los runners standard son gratis e ilimitados en repositorios públicos; en privados aplican cuotas del plan y el exceso puede facturarse.[24] GitHub advierte que `schedule` puede retrasarse o perderse con carga y se desactiva después de 60 días sin actividad del repo; monitorizar y reactivar cuando corresponda.[25]
- **Límite de lo anterior:** una automatización no crea una fuente fiable. En los requisitos del proyecto aún no se identifican APIs que cubran las familias de producto con permisos, cuotas y actualización diaria confirmados. Si no hay una fuente aceptable, el catálogo inicial debe marcarse como muestra/manual y su fecha, no anunciarse como actualizado.
- **Proxy LLM:** el Worker recibe solo el contexto mínimo que la persona decida enviar (diseño recomendado). Usar el binding de Workers AI mantiene la llamada del lado servidor.[5] Si se elige un LLM externo, guardar su API key como Secret del Worker, nunca en el bundle, repositorio o `localStorage`.[7] Cloudflare dice que el valor Secret queda oculto en Wrangler y en el dashboard.[7]
- **Privacidad:** mantener el perfil en el navegador y no guardar prompts, respuestas ni perfiles en un caché compartido. Informar antes del chat de qué campos se envían al modelo; omitir campos no necesarios y no incluir identificadores reales. Un endpoint proxy solo admite rutas/modelos esperados: no aceptar una URL arbitraria del cliente ni convertirse en un proxy abierto.
- **Alternativa al job de GitHub:** Cloudflare Cron Triggers ejecutan un handler en UTC y sirven para llamar APIs externas.[4]
Workers Free tiene 5 Cron Triggers por cuenta y 10 ms de CPU por invocación Cron.[1]
Si la validación o transformación supera ese tiempo, mover la preparación a Actions o reducirla a una descarga y escritura pequeñas (decisión de diseño).[1][4]

## Cuotas y controles que condicionan el “gratis”

- **Workers Free:** 100.000 solicitudes dinámicas/día por cuenta.[1]
El CPU máximo es 10 ms por petición HTTP y cada isolate dispone de 128 MB.[1]
Cloudflare dice que escala automáticamente y que no hay un límite general de solicitudes/segundo.[1]
También indica que durante carga extremadamente alta puede cancelar algunas peticiones.[1]
El límite diario no es una cifra de concurrencia.[1]
- **Workers AI:** asigna 10.000 Neurons/día y reinicia a las 00:00 UTC.[5]
Al superar los límites Free, las operaciones posteriores fallan.[5]
Para generación de texto hay un límite predeterminado de 300 solicitudes/minuto, salvo modelos que exigen Workers Paid.[6]
Es una tasa, no una promesa de 300 ejecuciones simultáneas.[6]
Las páginas revisadas no publican un número de sesiones simultáneas admitidas para el modelo elegido.[6]
- **Turnstile + rate limit:** Turnstile Free permite 20 widgets por cuenta y desafíos ilimitados.[14]
La validación Siteverify en el Worker es obligatoria; cada token dura 300 segundos y es de un solo uso.[15]
El Rate Limiting API de Workers es aproximado, separado por ubicación y eventualmente consistente; puede exceder el umbral antes de sincronizar.[8]
La ventana soportada es de 10 o 60 segundos.[8]
Cloudflare desaconseja IP como identidad única porque se puede compartir entre usuarios.[8]
La página del binding no publica precio/cuota independiente; verificar su disponibilidad en el plan Free antes de depender de ella.[8]
- **Cuota estricta opcional:** para un límite global estricto por sesión/día, Cloudflare remite a Durable Objects.[8]
Workers Free incluye 100.000 solicitudes DO/día y 13.000 GB-s/día, solo con DO SQLite-backed.[9]
Añade una llamada y un punto caliente; probar concurrencia y latencia del objeto único antes de usarlo en el chat.[9]
- **KV si el catálogo pasa a ser mutable sin build:** Free incluye 100.000 lecturas/día, 1.000 escrituras/día y 1 GB.[10]
Los cambios pueden tardar 60 segundos o más en verse en otras ubicaciones y KV está orientado a muchas lecturas.[11]
D1 Free da 5 millones de filas leídas/día, 100.000 escritas y 5 GB totales.[12]
Cada base D1 individual procesa consultas de una en una.[13]
No elegir D1 para un JSON estático o un chat de 100 usuarios sin una prueba específica (decisión de diseño).[12][13]

**Mitigación mínima del abuso:** validar Siteverify en el servidor.[15]
Permitir solo el origen público de Paideia, limitar prompt/historial/salida y rechazar cuerpos inesperados (controles recomendados).
Imponer una cuota por sesión y un tope operativo diario; devolver 429 y apagar IA al alcanzar el cupo (controles recomendados).[8][9]
Sin login, una identidad de navegador puede reiniciarse y una IP puede compartirse, por lo que no hay un límite infalible por usuario.[8]
Mantener catálogo, simuladores y glosario visibles aunque la IA esté bloqueada (fallback recomendado).[28]
Si se usa Workers AI Free, el cupo diario de Neurons limita las operaciones del proveedor.[5]

## Comparación de alternativas oficiales

| Opción | Precio y límites publicados relevantes | Evaluación para Paideia |
|---|---|---|
| **Cloudflare Pages + Worker + Workers AI** | Pages assets estáticos sin límite de peticiones; Workers Free 100.000 solicitudes/día, 10 ms CPU por invocación; Workers AI 10.000 Neurons/día y 300 solicitudes/minuto de generación de texto por defecto.[1][5][6][28] | **Recomendación.** Cubre frontend, proxy, CDN y mitigación básica sin servidor doméstico. La cuota de IA/modelo, no el contador diario, es el riesgo de la demo. No se ha verificado requisito de tarjeta ni concurrencia real. |
| **Vercel Hobby** | 0 USD con 100 GB de transferencia rápida y 1 millón de invocaciones de Functions incluidos; Vercel publica autoescalado de Functions hasta 30.000 concurrencias en Hobby/Pro. Sus Cron en Hobby solo corren una vez al día con precisión horaria de ±59 min.[16][18][19] | Alternativa si sus términos y límites de cuenta encajan. Hobby se restringe a uso personal no comercial; la clasificación de un proyecto público colaborativo se debe confirmar. La capacidad de Vercel no dimensiona al proveedor LLM. No hacer load test en Vercel sin autorización.[17] |
| **Netlify Free** | 300 créditos/mes, con límite duro; 15 créditos por deploy de producción, 2 por cada 10.000 peticiones web, 20 por GB de bandwidth y 10 por GB-hora de compute. Scheduled Functions disponibles en todos los planes, con máximo de 30 s.[20][21][22] | No elegir para un rebuild diario del catálogo: 30 deploys de producción consumirían 450 créditos/mes, antes de tráfico, más que los 300 Free; al agotarse, los proyectos se pausan.[22] |
| **GitHub Pages + Actions** | Pages: tamaño publicado máximo 1 GB, límite blando de 100 GB/mes y rate limits posibles. GitHub dice que Pages no está destinado ni permitido como hosting gratuito de un sitio cuya finalidad principal sea prestar SaaS comercial. Actions standard runners son gratis e ilimitados en repos públicos; `schedule` puede retrasarse/perderse con carga y se desactiva tras 60 días sin actividad del repo.[23][24][25] | **Actions sí** como job de ingesta si el repo es público; programar fuera de `:00` y vigilar fallos. **Pages no** como primera opción para la app interactiva: es estático, no hace proxy LLM y sus términos requieren revisar la frontera del proyecto. |
| **Supabase Free** | 50.000 MAU, 500 MB DB, 5 GB egress y pausa por inactividad de una semana; MAU no equivale a 50.000 personas simultáneas.[26][27] | Alternativa para datos relacionales si realmente se necesitan; añade otra cuenta, pausa y no resuelve el proxy LLM. Innecesario para catálogo estático. |

Las asignaciones publicadas de Vercel y Supabase no prueban la capacidad de toda la cadena LLM.[16][19][26]
No se debe mezclar MAU, solicitudes diarias, requests/minuto y concurrencia: son métricas distintas.[1][6][26]

## 100 usuarios concurrentes: lectura correcta y prueba requerida

Cloudflare documenta autoescalado y ausencia de un límite general de RPS.[1]
Eso no certifica la app, el Worker, la región, el modelo, la latencia ni 100 respuestas de IA simultáneas.[1][6]
Vercel publica hasta 30.000 concurrencias de Functions en Hobby/Pro.[19]
Ese valor tampoco es una garantía de throughput del modelo externo.[19]

Ejemplo para separar magnitudes: **100 usuarios × 10 turnos = 1.000 llamadas al chat en total**, el 1% de 100.000 solicitudes Workers/día si cada turno produce una invocación.[1]
Eso no equivale a 1.000 simultáneas (distinción entre volumen diario y burst).[1]
El caso crítico separado es un burst de 100 `POST /api/chat` al mismo tiempo.[1]
Las 100 solicitudes serían carga instantánea, aunque el cupo diario apenas se consuma.[1]
La tasa publicada de 300/min para Workers AI tampoco prueba que se acepten 100 en paralelo.[6]

Antes de anunciar compatibilidad, prueba en staging y con permiso del proveedor:

1. **Frontend y catálogo:** 100 VUs, rampa de 1 a 100 durante 1–2 minutos y 5 minutos sostenidos (plan de prueba). Cargar SPA y `catalog.json`; medir errores, TTFB, p50/p95 y ancho de banda (métricas sugeridas). Son assets estáticos y no llamadas al Worker si las rutas no invocan Function.[28]
2. **API con proveedor simulado:** 100 solicitudes simultáneas y una sesión de varios turnos por VU. Medir p50/p95, 429/5xx, memoria/CPU Worker, CORS, comportamiento de Turnstile y que perfiles/prompt no aparecen en logs.
3. **IA real, escalonada:** primero pocas llamadas y luego 10/25/50/100 concurrencias, con prompts sintéticos cortos y `max_tokens` acotado (plan de prueba).
Registrar latencia, 429, modelo exacto y Neurons consumidas; comprobar que el presupuesto diario Free no se agota.[5][6]
No lanzar el burst completo hasta verificar que el modelo está en Free y que la prueba está permitida (control recomendado).
Vercel menciona expresamente load testing sin autorización entre usos no aceptables.[17]
4. **Fallo controlado:** API de catálogo caída, snapshot caducado, token inválido, cuota de IA agotada y respuesta 429. Confirmar que no se publica dato parcial, que se informa fecha/fuente y que el resto de la web sigue usable.

Acordar antes una latencia p95 y tasa de errores aceptables para la demo y guardar resultados. **No se ejecutó esta prueba**: no hay aplicación ni despliegue, y esta investigación no autoriza ni requiere generar tráfico contra proveedores.

## Fallback y decisiones pendientes

- Si falla la actualización diaria, mantener el último catálogo validado, mostrar fecha de consulta/fuente/aviso de antigüedad y excluir de comparación lo que ya no sea apropiado según reglas de Paideia. No rellenar valores faltantes con IA.
- Si Workers AI supera cuota, sus operaciones Free fallan.[5]
Desactivar chat temporalmente y mantener simuladores, comparador, glosario, ejemplos preescritos y respuestas educativas estáticas (fallback recomendado).
Si el modelo no cumple español, aplicar el mismo fallback (decisión de producto).
No convertir automáticamente la cuenta a Workers Paid ni añadir un proveedor con facturación no verificada.[2]
- Pendiente antes de construir: proveedor/modelo LLM exacto y términos de uso de los datos enviados; coste por conversación y Neurons por prompt típico; APIs reales del catálogo, licencias y cuotas; prueba de 100 chat requests; requisito de tarjeta al crear cuentas; repositorio público, permisos mínimos de Actions y política de privacidad.
- Estado verificado del workspace: esta carpeta no tiene metadatos Git (`git status` devolvió “not a git repository”). Antes de configurar Actions/Pages hay que crear o ubicar el repositorio público real y definir titularidad/licencia.
- Si el job de GitHub se vuelve poco fiable o se necesita ingesta sin actividad del repo, probar Cloudflare Cron+KV como alternativa.[4][10]
Respetar cuotas y consistencia eventual de KV.[10][11]
Ningún cron elimina el problema de que aún no hay fuente de datos seleccionada (alcance pendiente).

## Sources

[1] https://developers.cloudflare.com/workers/platform/limits — Cloudflare Workers limits
[2] https://developers.cloudflare.com/workers/platform/pricing — Cloudflare Workers pricing
[3] https://developers.cloudflare.com/pages/platform/limits — Cloudflare Pages limits
[4] https://developers.cloudflare.com/workers/configuration/cron-triggers — Cloudflare Cron Triggers
[5] https://developers.cloudflare.com/workers-ai/platform/pricing — Cloudflare Workers AI pricing
[6] https://developers.cloudflare.com/workers-ai/platform/limits — Cloudflare Workers AI limits
[7] https://developers.cloudflare.com/workers/configuration/secrets — Cloudflare Workers Secrets
[8] https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit — Cloudflare Workers Rate Limiting API
[9] https://developers.cloudflare.com/durable-objects/platform/pricing — Cloudflare Durable Objects pricing
[10] https://developers.cloudflare.com/kv/platform/pricing — Cloudflare Workers KV pricing
[11] https://developers.cloudflare.com/kv/concepts/how-kv-works — How Cloudflare KV works
[12] https://developers.cloudflare.com/d1/platform/pricing — Cloudflare D1 pricing
[13] https://developers.cloudflare.com/d1/platform/limits — Cloudflare D1 limits
[14] https://developers.cloudflare.com/turnstile/plans — Cloudflare Turnstile plans
[15] https://developers.cloudflare.com/turnstile/get-started/server-side-validation — Cloudflare Turnstile server-side validation
[16] https://vercel.com/docs/plans/hobby — Vercel Hobby plan
[17] https://vercel.com/docs/limits/fair-use-guidelines — Vercel Fair Use Guidelines
[18] https://vercel.com/docs/cron-jobs/usage-and-pricing — Vercel Cron Jobs usage and pricing
[19] https://vercel.com/docs/functions/limitations — Vercel Functions limitations
[20] https://docs.netlify.com/build/functions/scheduled-functions — Netlify Scheduled Functions
[21] https://www.netlify.com/pricing — Netlify plans and pricing
[22] https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/how-credits-work — Netlify credit usage
[23] https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits — GitHub Pages limits
[24] https://docs.github.com/en/actions/reference/usage-limits-billing-and-administration — GitHub Actions usage and billing
[25] https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows — GitHub Actions scheduled workflow events
[26] https://supabase.com/pricing — Supabase pricing
[27] https://supabase.com/docs/guides/platform/free-project-pausing — Supabase Free project pausing
[28] https://developers.cloudflare.com/pages/functions/pricing — Cloudflare Pages Functions pricing
