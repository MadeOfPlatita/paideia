# Alternativas LLM adicionales para Paideia

> **Corrección del coordinador:** las afirmaciones originales sobre Mistral Experiment y exclusión de entrenamiento fueron revisadas mediante recuperación directa de las URLs oficiales. Véase [CONTRASTE-COORDINADOR.md](CONTRASTE-COORDINADOR.md), que prevalece para esos puntos. La candidatura de Mistral sigue abierta, no aprobada ni descartada.

**Revisión documental: 26-10-2026.** Se consultó documentación primaria de Cerebras, SambaNova, Mistral, Cohere y NVIDIA, además de documentación local de Mistral/Ollama. No se crearon cuentas, API keys ni pagos; no se instalaron ni ejecutaron modelos; no se mandaron prompts ni datos a endpoints. Estado: **documentado, no probado**. El público objetivo de Paideia es adulto y la aplicación es educativa; no se contempla asesoramiento profesional ni envío automático del perfil financiero completo. El contexto seleccionado requiere revisar el flujo de privacidad.

## Conclusión ejecutiva

**Ninguna opción ha sido validada operativamente para Paideia. Mistral permanece como candidato abierto tras el contraste directo del coordinador; no se descarta por una restricción de prototipado que la página actual no acredita.**

SambaNova Free tiene una cuota diaria de 20 solicitudes/modelo.[3] El alcance y los límites actuales de Mistral Free requieren revisión de cuenta y términos; el contraste del coordinador corrige la interpretación anterior de Experiment.

Cohere Trial limita Command A Reasoning a 20/min y sus claves Trial a 1.000 llamadas/mes.[13][16]

NVIDIA presenta NIM Free como prototipo; Cerebras exige método de pago verificado y sus créditos caducan a los 30 días.[17][1]

**Mejor candidata para una prueba técnica interna con datos sintéticos: Mistral API Experiment**, por el procesamiento API servido desde centros de datos de la UE por defecto.[8] El uso para mejora/entrenamiento depende de condiciones y controles que deben confirmarse, según el contraste directo del coordinador; no se afirma exclusión por defecto.

La guía documenta function calling con JSON Schema para modelos compatibles, pero no confirma esa capacidad en la ficha de `Mistral Small 4`; validarlo antes de elegir ese modelo.[9][26]

No es recomendación de despliegue: los límites exactos dependen del workspace y la disponibilidad de `Small 4` en el nivel gratis debe confirmarse antes de contar con su ventana de 256k.[7][8][26] La página actual de uso no permite concluir por sí sola una prohibición de demo pública.

**No se promete 100 simultáneos.** Las páginas consultadas publican cuotas y topes, no pruebas de carga ni garantías de 100 peticiones en vuelo.[1][3][13]

Para Mistral, los valores actuales de RPS/TPM por workspace se consultan en el panel.[7]

Ningún modelo se probó ni se midió latencia, concurrencia o disponibilidad.

## Matriz comparativa

| Proveedor / candidato | Cuota gratis y contexto | Tools / JSON | Tarjeta, cuenta y uso público | EEE, licencia y finanzas | Veredicto para Paideia |
|---|---|---|---|---|---|
| **Cerebras Shared Inference — `gpt-oss-120b`** | La tabla general Free Trial da **5 RPM, 30k TPM sin caché, 90k TPM total y 1M TPD**; la ficha individual del mismo modelo publica 30 RPM y 60k tokens de entrada/min, una discrepancia que impide presupuestar la cifra mayor. Contexto: **65k** en trial, 131k de pago.[1][2] | La ficha del modelo documenta **Tool Calling** y **Structured Outputs**; no se probó la combinación elegida por Paideia.[2] | **Sí exige método de pago verificado** para activar los USD 5 de prueba; vencen en 30 días y al agotarse/caducar se detiene el acceso gratis. No es un nivel gratuito permanente.[1] | No se verificó residencia EEE, retención de prompts, permiso de servir una API pública ni una autorización financiera específica. El endpoint no sustituye la comprobación de licencia upstream del modelo.[1][2] | **Descartar**: tarjeta, crédito temporal, 5 RPM conservador y documentación de cuota contradictoria.[1][2] |
| **SambaNova SambaCloud — `gpt-oss-120b`** | Free Tier: **20 RPM, 20 RPD y 200k TPD por modelo**; contexto publicado: **128k**. Los límites Developer de 60 RPM/12.000 RPD para este modelo requieren nivel Developer; no contarlos como gratis.[3][4] | Responses API documenta function calls ejecutadas por el cliente y salida `json_schema`/`json_object`; `gpt-oss-120b` figura entre los modelos soportados.[6] | La documentación confirma un nivel Free, pero en esta revisión no se verificó el flujo de alta ni si siempre evita solicitar tarjeta. La designación “Production model” describe el modelo/tabla, no prueba capacidad para 100 usuarios.[3][4] | Un release note afirma que SambaNova “never stores your data”, pero no acredita residencia EEE ni sustituye un DPA aplicable. No se encontró en esta pasada una cláusula específica para asesoría financiera o permiso explícito para servir una app pública con el nivel Free. La licencia upstream debe verificarse por modelo.[5][3] | **Solo prueba interna**; 20 RPD no cubre una clase de 100 personas con una llamada cada una.[3] |
| **Mistral API Free — modelo elegible por confirmar** | La página actual describe consumo mensual incluido y límites por organización/modelo en el panel; sin cifras verificadas para esta cuenta. La ficha Small 4 anuncia 256k, no su disponibilidad Free.[7][26] | Tools y JSON dependen del modelo; no se ha probado la combinación.[9][26] | API key/cuenta necesarias; tarjeta y condiciones de uso público aún no comprobadas. No se deduce prohibición de demo de la página actual: ver CONTRASTE-COORDINADOR.md. | UE por defecto según documentación.[8] El contraste de privacidad exige revisar opt-out, retención y DPA; no afirmar ausencia de entrenamiento por defecto. | **Candidato abierto**, pendiente de cuota/modelo/contrato y smoke sintético. No garantiza cien usuarios ni producción gratuita. |
| **Cohere API — `Command A Reasoning`** | Trial: **20 req/min** para el modelo y límite de **1.000 llamadas/mes** para Trial keys (también afecta a modelos Chat nuevos con prod keys); el límite de producción de Command A Reasoning remite a ventas. Contexto **256.000**, salida máxima 32.000 tokens.[13][14] | El modelo documenta tool use. JSON Schema está documentado; **Structured Outputs (Tools)** con `strict_tools` solo se admite en Chat API V2. No se probó que el modelo, la cuota Trial y el esquema objetivo funcionen juntos.[14][15][25] | Cohere entrega una Trial key al registrarse; para “go live” describe una Production key. La documentación no confirma si hace falta tarjeta. Para casos que Cohere considere sensibles, la activación puede quedar limitada hasta revisión/aprobación humana; no se resolvió si la orientación educativa de Paideia entra en esa categoría.[16] | No se confirmó residencia/procesamiento EEE para la ruta Trial en las páginas consultadas. Uso financiero específico, retención y licencia de pesos no quedaron verificados; tratarlo como servicio API sujeto a sus términos, no como licencia de pesos reutilizable.[13][14][16] | **No sirve como base pública gratuita**: límite mensual bajo y ruta de producción/posible revisión pendiente.[13][16] |
| **NVIDIA NIM API Catalog — `Llama-3.3-Nemotron-Super-49B-v1.5`** | NVIDIA dice “hasta **40 RPM para la mayoría** de modelos, sin cobro por token”; el límite concreto es personal y visible en el panel. Contexto del modelo: **128k**.[17][19] | La ficha del modelo documenta tool calling y compatibilidad con español; no se encontró garantía de salida JSON Schema para este endpoint/modelo en las páginas consultadas, por lo que habría que validar parseo/schema.[19] | API key requiere cuenta NVIDIA; la guía no menciona tarjeta, pero tampoco certifica que nunca se pida. El endpoint gratis se ofrece para **prototipos**. Los términos exigen mayoría de edad para aceptar y, salvo acuerdo de producto distinto, conceden uso “for your use only”; no asumir permiso para alojar una app pública.[18][17][20] | La política general de NVIDIA dice que en la mayoría de casos la información se transfiere/almacena en EE. UU.; no es una declaración específica sobre retención del prompt de NIM ni residencia EEE.[21] No se verificó una licencia financiera específica ni derechos de redistribución del peso del modelo.[19][20] | **Solo prototipo aislado**; permiso de uso público, endpoint específico de datos y JSON Schema no aclarados.[17][20][21] |

## Lectura por requisitos críticos

### Cuotas y 100 usuarios

- **SambaNova:** la cuota Free diaria de 20 solicitudes por modelo descarta servir 100 conversaciones/turnos diarios desde ese tier, incluso antes de hablar de simultaneidad.[3]
- **Cohere:** 20 solicitudes/minuto y 1.000 llamadas al mes limitan una demo pública sostenida; para Command A Reasoning la tabla de producción remite a ventas.[13]
- **NVIDIA:** 40 RPM para la mayoría de modelos no certifica 40 en vuelo ni 100 concurrentes; el límite mostrado es personal.[17]
- **Mistral:** no se pudo dimensionar sin los valores del workspace. La URL oficial redirige a una página de uso/límites que describe Free con consumo mensual incluido; véase el contraste del coordinador, sin inferir permiso de producción ni prohibición de demo.
- **Cerebras:** usar 5 RPM como límite conservador del Free Trial hasta aclarar la contradicción con la ficha individual; requiere método de pago verificado.[1][2]

Una cola acotada y fallback determinista serían obligatorios si se autorizara una futura prueba. No repartir cuota entre claves/cuentas ni cambiar de plan automáticamente. La API key, si alguna vez se autoriza integración, no debe ir en el JavaScript público; el perfil completo no debe adjuntarse automáticamente; cualquier contexto seleccionado se rige por la propuesta de privacidad y la decisión informada del usuario.

### Público, licencias y finanzas

- **Uso público:** Mistral requiere comprobar términos aplicables y límites reales. La afirmación anterior de exclusividad de evaluación/prototipado no queda respaldada por la página actual; véase el contraste del coordinador.

NVIDIA describe NIM Free como prototipo, y los términos base limitan el acceso a “your use only” salvo acuerdo de producto distinto.[17][20]

Cohere separa Trial de “go live”/Production y contempla revisión de casos sensibles.[16]

Estos textos no acreditan por sí solos permiso para desplegar una app pública gratuita; pedir confirmación del proveedor.[7][16][17]
- **Licencias:** no se infiere de las páginas de API una licencia para redistribuir pesos; revisar por separado el modelo upstream antes de descargarlo o autoalojarlo.[11][20]

La ficha de `Mistral Small 4` publica Apache 2.0 para el modelo; eso no determina condiciones, cuota ni aptitud del servicio API gratuito.[26][7]

Como alternativa local, **Mistral Nemo** aparece bajo Apache 2; la documentación advierte que los pesos listados no vienen ajustados para seguridad.[22]
- **Uso financiero:** no se encontró una autorización explícita para recomendaciones de inversión personalizadas en las páginas revisadas. Cohere exige declarar casos sensibles y puede requerir aprobación; Mistral hace responsable al cliente de evaluar exactitud y adecuación del output.[16][11] Paideia debe mantener la IA en explicación educativa, usar reglas/código deterministas para cálculos y no presentar el resultado como asesoramiento autorizado, conforme a `docs/REQUISITOS.md`.

### EEE y privacidad

- **Mejor evidencia regional:** Mistral dice que su API se sirve por defecto desde centros de datos de la UE.[8] El contraste directo de la URL de privacidad describe controles de opt-out específicos para Studio/API. Deben confirmarse ajustes y contrato antes de afirmar exclusión de entrenamiento; véase el documento del coordinador. El DPA contempla transferencias a países fuera del EEE que no tengan decisión de adecuación.[12]
- **SambaNova:** la afirmación de no almacenar datos no aporta localización; no enviar perfiles financieros hasta verificar región, DPA y alcance del endpoint.[5]
- **Cohere y Cerebras:** residencia EEE/retención de la ruta gratuita no quedaron acreditadas en las fuentes consultadas; marcarlo como **pendiente**, no como “EEE seguro”.[13][1]
- **NVIDIA:** su política de privacidad general contempla en la mayoría de casos transferencia y almacenamiento en EE. UU.; buscar condiciones específicas del API Catalog antes de mandar cualquier dato personal.[21]
- Para pruebas internas aún sin proveedor/privacidad aprobados, usar preguntas sintéticas sin perfil real. Esto no retira el requisito de chat contextual: el contexto mínimo y su selección se resolverán con la propuesta de privacidad.

## Contingencia local (y por qué no satisface “PC apagado”)

Un modelo local evita enviar prompts a un proveedor solo si inferencia, historial, herramientas y logs quedan realmente locales.[24]

Ollama indica que, al ejecutar localmente, no ve los prompts; también usa **4.096 tokens** de contexto por defecto, ajustables por configuración.[24]

Mistral Nemo 12B es un candidato con licencia Apache 2 y contexto publicado de 128k, pero los pesos no están ajustados para seguridad; guardrails y validación siguen siendo necesarios.[22][8]

**Un servidor en el ordenador del equipo deja de servir cuando ese PC está apagado.** Para mantener disponibilidad, el modelo tendría que correr en una máquina propia siempre encendida y con acceso de red seguro, o en alojamiento GPU remoto; en este último caso hay coste, operación y revisión de residencia que no se han comprobado aquí. Como referencia de hardware distinta (Devstral Small 2, 24B), Mistral cita GPU de 24 GB para 4-bit/32k o A100/H100 para FP8/128k; CPU offload funciona pero es significativamente más lento. No se afirma que los equipos de Alejandro/José Manuel puedan ejecutarlo.[23]

## Recomendación provisional vs. prueba decisiva

**Provisional:** mantener candidatos abiertos y comparar sus condiciones reales antes de decidir. Workers AI sigue siendo candidato; Mistral no queda descartado por la antigua etiqueta de Experiment. No hay proveedor aprobado.

No se ha validado una cuota suficiente ni el encaje contractual para la web pública de Paideia. NVIDIA presenta su endpoint como prototipo.[17] Para Mistral, consultar el contraste directo antes de interpretar su Free.

Cohere separa Trial de la ruta de producción y prevé revisión de casos sensibles.[16]

SambaNova Free queda en 20 solicitudes/día y no acredita capacidad para 100 simultáneos.[3]

Si el grupo autoriza una comparación técnica, incluir Mistral Free en la prueba interna sintética por la evidencia regional, verificando antes cuota, modelo, controles de datos y términos; no inferir permiso de despliegue.[8][10][12]

**Prueba decisiva, solo tras autorización explícita para cuenta/clave y sin datos reales:** (1) confirmar por escrito tier/modelo exactos, tarjeta, uso de API pública y contrato; (2) verificar DPA/retención/región EEE y licencia upstream; (3) enviar prompts sintéticos con tools + JSON Schema, validar argumentos y fallback ante 429/timeout; (4) medir consumo/latencia y realizar prueba de carga autorizada hasta 100 solicitudes concurrentes. Hasta superar esos pasos, no prometer 100 simultáneos ni mostrar “respuestas IA” si el proveedor falla.

**No ejecutado:** alta, aceptación de términos, key, llamada a modelo, instalación local, prueba concurrente, despliegue o comprobación de tarjeta. La matriz refleja documentación consultada, no aprobación legal, integración funcional ni SLA.

## Sources

[1] https://inference-docs.cerebras.ai/support/rate-limits — Cerebras — rate limits and free trial
[2] https://inference-docs.cerebras.ai/models/openai-oss — Cerebras — OpenAI GPT OSS model card
[3] https://docs.sambanova.ai/docs/en/models/rate-limits — SambaNova — model rate limits
[4] https://docs.sambanova.ai/docs/en/models/sambacloud-models — SambaNova — SambaCloud models
[5] https://docs.sambanova.ai/docs/en/release-notes/sambacloud — SambaNova — SambaCloud release notes/data use
[6] https://docs.sambanova.ai/docs/en/features/responses.md — SambaNova — Responses API
[7] https://docs.mistral.ai/admin/user-management-finops/tier — Mistral — usage and limits
[8] https://docs.mistral.ai/resources/known-limitations — Mistral — known limitations
[9] https://docs.mistral.ai/studio/conversations/function-calling — Mistral — function calling
[10] https://docs.mistral.ai/admin/monitor-comply/privacy-data-controls — Mistral — privacy and data controls
[11] https://legal.mistral.ai/terms/commercial-terms-of-service — Mistral — commercial terms
[12] https://legal.mistral.ai/terms/data-processing-addendum — Mistral — data processing addendum
[13] https://docs.cohere.com/docs/rate-limits — Cohere — API keys and rate limits
[14] https://docs.cohere.com/v1/docs/command-a-reasoning — Cohere — Command A Reasoning
[15] https://docs.cohere.com/v1/docs/structured-outputs — Cohere — structured outputs
[16] https://docs.cohere.com/docs/going-live — Cohere — going live
[17] https://build.nvidia.com/overview — NVIDIA — NIM prototype endpoints
[18] https://docs.api.nvidia.com/nim/docs/api-quickstart — NVIDIA — API Catalog quickstart
[19] https://docs.api.nvidia.com/nim/reference/nvidia-llama-3_3-nemotron-super-49b-v1_5 — NVIDIA — Llama 3.3 Nemotron Super 49B v1.5 model card
[20] https://developer.nvidia.com/legal/terms — NVIDIA — Terms of Use
[21] https://www.nvidia.com/en-us/about-nvidia/privacy-policy — NVIDIA — privacy policy
[22] https://docs.mistral.ai/getting-started/models/weights — Mistral — model weights and licenses
[23] https://docs.mistral.ai/vibe/code/cli/offline-models — Mistral — offline model hardware guidance
[24] https://docs.ollama.com/faq — Ollama — FAQ/local data handling
[25] https://docs.cohere.com/docs/structured-outputs — Cohere — structured outputs V2/strict_tools
[26] https://docs.mistral.ai/models/mistral-small-4-0-26-03 — Mistral — Small 4 model card
