# LLM con cuota gratuita para Paideia (España/EEE)

**Consulta documental:** 26-10-2026. Comparación de documentación primaria oficial; no se crearon cuentas, no se pidieron API keys y no se enviaron prompts a modelos. «Gratis» significa solo la cuota indicada por el proveedor: no implica SLA, capacidad reservada ni servicio sostenible para producción.

## Conclusión ejecutiva

- **Ninguna cuota publicada equivale a concurrencia reservada.** Las páginas de Gemini, Groq y Cloudflare describen cuotas de proyecto/organización, modelo o tareas, no una promesa de 100 sesiones en curso.[2][19][36]
  OpenRouter fija topes de solicitudes para sus modelos Free, no una garantía de concurrencia.[8]
  Por tanto, la disponibilidad para 100 solicitudes realmente simultáneas queda sin probar y no debe prometerse.[unverified]
- **Gemini API Free no es apto para servir una API Client a usuarios en España/EEE:** aunque España aparece como región disponible, sus términos exigen usar Paid Services al ofrecer una API Client a usuarios del EEE. El nivel gratuito no satisface esa condición.[4][10]
- **Cloudflare Workers AI es la opción provisional para un piloto muy limitado**, si se aprueban sus términos, se confirma el alta sin método de pago y las preguntas son genéricas/no personales.
  Ofrece 300 solicitudes/minuto de generación de texto y 10.000 Neurons/día.[6][19]
  Cloudflare dice que no entrena con el contenido; no encontré una promesa de inferencia solo en EEE.[20]
  El control regional documentado para Workers no se extiende a subrequests salientes.[32]
- **No enviar el perfil financiero local, nombres, DNI, credenciales, datos de cuenta ni información de pago.** Para consultas de finanzas, el LLM debe explicar contenido educativo y hechos recuperados de fuentes verificadas; no debe presentarse como asesor autorizado ni tomar decisiones financieras. Google prohíbe confiar en sus servicios para asesoramiento financiero, y la AUP de Groq requiere supervisión humana en decisiones financieras de alto impacto.[4][34]
- Si el requisito es residencia EEE estricta o disponibilidad garantizada, **no he encontrado una opción gratuita que lo demuestre**. La ruta regional de OpenRouter es de Business/Enterprise, no su ruta gratuita.[25][30]

## Comparación documental

### 1. Google Gemini Developer API — no elegible para una web pública gratuita en España/EEE

- **Modelos:** la documentación de precios ofrece algunos modelos con tokens gratuitos; por ejemplo, la familia Flash. La guía de function calling muestra `gemini-3.8-flash` y la guía de structured outputs documenta JSON Schema.[1][11][12]
- **Límites:** RPM, TPM de entrada y RPD, por proyecto (no por API key); varían por modelo y nivel. Los valores activos se consultan en AI Studio, pueden cambiar y no se garantizan. Los RPD se reinician a medianoche del Pacífico. No encontré un límite de concurrencia simultánea publicado.[2]
- **Tarjeta/pago:** la cualificación Free es proyecto activo o prueba gratuita y las cuentas nuevas empiezan en Free. La documentación no confirma el flujo de alta de tarjeta para cada cuenta; sí exige asociar billing para pasar a Paid, con un prepago mínimo documentado de USD 5.[3]
- **EEE, datos y región:** España figura en regiones disponibles, pero los términos dicen que una API Client dirigida a usuarios del EEE debe usar Paid Services. Para Paid Services Google declara que no usa prompts/respuestas para mejorar sus productos, aunque puede registrar datos temporalmente y almacenarlos/caché en cualquier país donde opere Google o sus agentes; no es una garantía de residencia EEE.[4][10]
- **Edad/uso:** mínimo 18 años y la web/API Client no puede estar dirigida a ni probablemente ser usada por menores de 18. El uso de AI Studio/API es para desarrolladores con fines profesionales o empresariales, no para uso de consumidor.[4]
- **Tools/JSON:** function calling y salidas estructuradas con JSON Schema están documentados; el soporte concreto depende del modelo y del flujo elegido. No se ha probado la integración.[11][12]

### 2. GroqCloud Free — buen modelo documentado, límite estrecho para un pico de clase

- **Modelo/cuota de referencia:** `openai/gpt-oss-20b`: **30 RPM, 1.000 RPD, 8.000 TPM y 200.000 TPD** en la tabla Free. Groq advierte que son límites resumidos, que se aplican a nivel de organización y que el límite exacto de una organización se consulta en su consola.[36]
  El catálogo de modelos lista `openai/gpt-oss-20b`; la página de límites advierte que las cuotas exactas pueden variar por organización.[5][18]
- **Prueba de capacidad, no benchmark:** suponiendo 200 tokens de entrada + 250 de salida por turno (450 total), el TPM permitiría como máximo **17 turnos/minuto** y el TPD, aproximadamente **444 turnos/día**; 100 turnos simultáneos representarían 45.000 tokens en el minuto. La cuota diaria de solicitudes de 1.000 no elimina el cuello de botella de TPM. Concurrencia/SLA no publicados.[36]
- **Tarjeta/pago:** Groq documenta que para actualizar de Free a Developer se necesita un método de pago. No confirma en esa página que el alta de una cuenta Free nunca solicite tarjeta; no se intentó el alta.[15]
- **Datos/región:** por defecto no retiene los datos de inferencia; puede registrar entradas/salidas hasta 30 días para fiabilidad/abuso, salvo activar Zero Data Retention. Groq sitúa los datos de cliente retenidos en buckets GCP de EE. UU.; su DPA permite procesar/transferir datos personales a EE. UU. y otros países. No es residencia EEE.[13][35]
- **Edad/uso:** Cloud Services tienen mínimo 18 años y no son para uso de consumidor. La AUP prohíbe decisiones automatizadas de alto impacto financiero sin supervisión humana.[14][34]
- **Tools/JSON:** `gpt-oss-20b` aparece con tool use y JSON Mode. Structured Outputs con JSON Schema está limitado a modelos compatibles y la documentación de Groq indica que **tool use no se admite a la vez que Structured Outputs**; hay que elegir/validar el flujo.[16][17]

### 3. Cloudflare Workers AI Free — mejor ajuste provisional, con presupuesto diario reducido

- **Modelo candidato:** `@cf/meta/llama-3.3-70b-instruct-fp8-fast` aparece con function calling y precio por token. El modelo está incluido en la lista de JSON Mode; ambos soportes constan por separado, pero no hay garantía documental de que tools y JSON Schema puedan combinarse en una misma petición.[22][33]
  No confundirlo con `@cf/meta/llama-3.1-8b-instruct`: su ficha actual lo marca como deprecated.[23]
- **Cuota:** la asignación gratuita es **10.000 Neurons/día**, reinicia a las 00:00 UTC; excederla en Workers Free hace fallar operaciones. Generación de texto tiene límite base de **300 solicitudes/minuto**, salvo modelos que exijan Workers Paid. La documentación no publica tokens/minuto ni concurrencia simultánea garantizada para el plan Free.[6][19]
- **Efecto orientativo del límite diario:** para el modelo candidato, la tabla muestra 26.668 Neurons/M tokens de entrada y 204.805/M tokens de salida. Con 200 tokens de entrada y 250 de salida serían ~56,53 Neurons/turno; 100 turnos, ~5.653 Neurons (56,5% del día), y ~176 turnos/día en total antes de añadir contexto, prompts de sistema o respuestas más largas. Es un escenario calculado, no una medición de rendimiento.[6]
- **Tarjeta/pago:** Workers AI tiene asignación gratuita; la misma documentación identifica ciertos modelos que sí requieren método de pago. No encontré confirmación explícita de que el alta de cuenta Free nunca pida tarjeta, por lo que hay que comprobarlo antes de elegirlo. El modelo candidato no figura en la lista de modelos que la página de precios marca como pagados obligatoriamente.[6]
- **Datos/región:** Cloudflare dice que no usa el contenido de Workers AI para entrenar o mejorar modelos/servicios; el contenido puede persistir si se usan servicios de almacenamiento como R2, KV, Durable Objects o Vectorize. La documentación consultada no ofrece una frontera de inferencia UE para el plan gratuito. La localización regional de Workers limita la ejecución del Worker, pero Cloudflare indica que no se extiende a subrequests salientes; eso no prueba que la inferencia de Workers AI ocurra solo en EEE.[20][32]
- **Edad/uso permitido:** no pude confirmar una edad mínima específica para Workers AI en la documentación/contrato consultados; es un dato pendiente, no autorización para usuarios menores.[unverified] Los términos de Free Services prohíben procesar o recopilar datos de tarjetas de crédito personales o empresariales en una propiedad que use esos servicios. También aplican licencia y términos del modelo seleccionado.[20][31][33]
- **Tools/JSON:** Workers AI documenta function calling y JSON Mode; JSON Mode no garantiza obediencia perfecta al esquema y no tiene streaming. Validar la respuesta y manejar error de esquema es obligatorio.[21][22]

### 4. OpenRouter Free — demostración/volumen bajo, no 100 usuarios

- **Modelo:** `openrouter/free` selecciona aleatoriamente un modelo gratuito disponible. Puede filtrar el conjunto por capacidades solicitadas (por ejemplo, tools o structured outputs), pero la selección de modelo/proveedor puede variar entre solicitudes.[24]
- **Cuota sin compras:** **20 RPM y 50 RPD**. Con compras acumuladas de créditos de al menos USD 10, la cuota gratuita sube a 1.000 RPD, pero deja de ser coste cero. 100 peticiones al máximo de 20 RPM tardarían 5 minutos en drenarse si se encolan; además, con 50 RPD no todos los 100 usuarios pueden recibir una llamada gratuita ese día.[8]
- **Tarjeta/pago:** cuenta y API key; el router gratuito no cobra inferencia, pero no encontré una afirmación oficial inequívoca de que el proceso de registro nunca solicite tarjeta. No se compraron créditos ni se creó una cuenta.[7][24]
- **Datos/región:** OpenRouter dice que no registra prompts/completions por defecto, pero el proveedor de modelo tiene su propia política de retención/entrenamiento. La ruta `eu.openrouter.ai` con procesamiento de prompts/completions en endpoints europeos solo se ofrece en Business/Enterprise; Business añade una comisión del 8% sobre compras de créditos. El dominio por defecto enruta globalmente, por lo que Free no garantiza región UE.[7][25][30]
- **Edad/uso:** términos de OpenRouter requieren 18 años y obligan a respetar los términos del proveedor/modelo elegido.[29]
- **Tools/JSON:** el API normaliza tool calling, pero la disponibilidad de structured outputs es por modelo **y endpoint/proveedor**, y puede cambiar. Hay que fijar proveedor/modelo compatible, no dar por sentado que el router aleatorio siempre podrá combinar ambos.[26][27][28]

**Opción no priorizada:** Hugging Face Inference Providers documenta USD 0,10/mes de crédito para Free Users, sujeto a cambio; lo tomaría como saldo de prueba, no como base de capacidad para 100 usuarios.[9]

## Viabilidad para 100 usuarios y medidas honestas

| Proveedor | Qué dicen las cuotas frente a 100 usuarios | Veredicto |
|---|---|---|
| Gemini Free | Cuota por proyecto/modelo, valores activos variables; además, Free no sirve para una API Client a usuarios EEE según sus términos. | **Descartado para España/EEE en Free.** |
| Groq Free | El TPM de `gpt-oss-20b` permite ~17 turnos/min con el supuesto anterior; 100 simultáneos no caben en ese minuto. | **No**, salvo cola lenta/limitación estricta; no garantiza simultaneidad. |
| Cloudflare Workers AI Free | 300 solicitudes/minuto nominales permiten 100 solicitudes dentro de una ventana de minuto, pero no certifican 100 in-flight. El límite de 10k Neurons/día es el cuello de botella; el ejemplo de 100 turnos usa ~56,5% del día. | **Sí para piloto de una interacción corta**, no como capacidad garantizada ni chat ilimitado. |
| OpenRouter Free | 20 RPM y 50 RPD; cola de 100 tarda al menos 5 min y 50 llamadas gratuitas/día. | **No**, salvo demo con cupos muy bajos. |

Los topes publicados son límites de cuota, no una prueba de carga simultánea.[2][19][36]

OpenRouter Free añade su propio límite de 20 RPM/50 RPD.[8]

Tratar cualquier pico de 100 como **degradación prevista**, no como disponibilidad cubierta por el proveedor.[unverified]

Mitigaciones para Paideia:

1. Mantener el perfil financiero en el navegador; enviar solo la pregunta necesaria tras avisar qué proveedor recibe el texto y obtener consentimiento. No enviar identificadores, perfil personal ni datos bancarios/de tarjeta; aplicar minimización también a logs.
2. Guardar la API key solo en servidor/secret manager, nunca en JavaScript público. Usar un contador global compartido, cuota por usuario, límite de tokens de entrada/salida, contextos cortos, y limitar el número de llamadas de herramientas. No repartir la cuota entre claves o cuentas distintas para evadir límites.
3. Usar el catálogo diario compartido y fuentes verificadas del proyecto como datos de herramientas; la IA explica esos datos, pero no inventa cotizaciones, cálculos ni citas. Cálculos financieros y validaciones deben ser deterministas y comprobables.
4. Ante 429, timeout, cuota agotada o modelo indisponible: cola acotada con backoff, luego **circuit breaker** y fallback determinista (FAQ, buscador del catálogo, calculadora y material estático actualizado). No generar una respuesta “como si fuera IA”. Rotularla, por ejemplo: **“Asistente IA no disponible; respuesta estática/cálculo determinista”**. Si falta un dato verificado: decir que no se puede responder y mostrar la fuente disponible.
5. Mostrar límites de uso y un aviso de finalidad educativa/no asesoramiento autorizado. No personalizar decisiones de inversión ni ejecutar operaciones.

## Elección provisional y prueba pendiente

**Provisional: Workers AI Free, `@cf/meta/llama-3.3-70b-instruct-fp8-fast`, solo como piloto adulto, con preguntas genéricas, datos no personales, presupuesto global y fallback visible.**

La razón es la combinación más útil documentada: 300 RPM, 10.000 Neurons/día y no uso del contenido para entrenamiento/mejora.[6][19][20]

La ficha marca function calling y la lista de JSON Mode incluye el modelo; no asegura que ambas funciones combinadas estén validadas.[22][33]

**No es aprobación para publicar:** residencia EEE de inferencia, tarjeta de alta y combinación `tools + JSON Schema` siguen pendientes.[20][32]

Si el tratamiento regional es requisito, pausar la IA gratuita hasta tener una garantía documentada. Gemini Free no sirve para una API Client EEE y el endpoint UE de OpenRouter es Business/Enterprise, no Free.[4][30]

**Pendiente (sin ejecutar aquí):** confirmar edad/condiciones de Cloudflare, método de pago de alta, modelo activo y su licencia; después de aprobación, probar con payload sintético sin datos personales: tools + JSON Schema, 100 solicitudes concurrentes, 429/timeout, consumo real de Neurons, tiempos p50/p95 y comportamiento exacto del fallback. Mantener el presupuesto en cero y no aceptar una migración a plan de pago sin autorización.

**Estado de verificación:** solo documentación primaria vigente; no se crearon cuentas, no se usaron claves y no se llamó ningún modelo. Cuotas, latencia, tarjetas, carga real y residencia de la inferencia quedan pendientes de validación operativa.

## Sources

[1] https://ai.google.dev/gemini-api/docs/pricing
[2] https://ai.google.dev/gemini-api/docs/rate-limits
[3] https://ai.google.dev/gemini-api/docs/billing
[4] https://ai.google.dev/gemini-api/terms
[5] https://console.groq.com/docs/rate-limits
[6] https://developers.cloudflare.com/workers-ai/platform/pricing
[7] https://openrouter.ai/docs/faq
[8] https://openrouter.ai/docs/api_reference/limits
[9] https://huggingface.co/docs/inference-providers/en/pricing
[10] https://ai.google.dev/gemini-api/docs/available-regions
[11] https://ai.google.dev/gemini-api/docs/generate-content/function-calling
[12] https://ai.google.dev/gemini-api/docs/structured-output
[13] https://console.groq.com/docs/your-data
[14] https://console.groq.com/docs/legal/services-agreement
[15] https://console.groq.com/docs/billing-faqs
[16] https://console.groq.com/docs/structured-outputs
[17] https://console.groq.com/docs/tool-use/overview
[18] https://console.groq.com/docs/models
[19] https://developers.cloudflare.com/workers-ai/platform/limits
[20] https://developers.cloudflare.com/workers-ai/platform/data-usage
[21] https://developers.cloudflare.com/workers-ai/features/function-calling
[22] https://developers.cloudflare.com/workers-ai/features/json-mode
[23] https://developers.cloudflare.com/workers-ai/models/llama-3.1-8b-instruct
[24] https://openrouter.ai/docs/guides/routing/routers/free-router
[25] https://openrouter.ai/docs/guides/privacy/provider-logging
[26] https://openrouter.ai/docs/guides/features/tool-calling
[27] https://openrouter.ai/docs/guides/features/structured-outputs
[28] https://openrouter.ai/docs/api/reference/overview
[29] https://openrouter.ai/terms
[30] https://openrouter.ai/business/eu
[31] https://www.cloudflare.com/terms
[32] https://developers.cloudflare.com/data-localization/how-to/workers
[33] https://developers.cloudflare.com/workers-ai/models/llama-3.3-70b-instruct-fp8-fast
[34] https://console.groq.com/docs/legal/ai-policy
[35] https://console.groq.com/docs/legal/customer-data-processing-addendum
[36] https://console.groq.com/docs/rate-limits?plan=free
