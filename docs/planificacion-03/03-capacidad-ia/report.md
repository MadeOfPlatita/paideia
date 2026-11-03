# Paideia — modelo reproducible de capacidad y coste de IA

**Ejecución del modelo:** 26-10-2026. Cloudflare indica que su página de precios se actualizó el 20-10-2026.[1] El cálculo compara dos tamaños de modelo por proveedor, pero es contabilidad de tokens/cuotas, no una prueba de rendimiento.

## Resultado ejecutivo

- Se generaron **432 escenarios** para 100 usuarios: Cloudflare Workers AI y GroqCloud, modelo pequeño y grande por proveedor, onboarding con botones o LLM, 3/5/10 turnos, tres perfiles de contexto, salida de 250/500 tokens y 0/1/2 loops de herramientas.
- Un caso austero de Cloudflare Llama 3.2 3B —100 usuarios, contexto lean, 3 turnos, respuestas de 250 tokens, sin loops y onboarding por botones— consume **4.186,5 Neurons/día** (41,9% de la cuota publicada de 10.000) y 300 solicitudes/día. Cabe aritméticamente en la asignación gratis, pero no demuestra que 100 peticiones en curso vayan a ser atendidas.
- Para el mismo caso, Cloudflare Llama 3.3 70B requiere **26.320,923 Neurons/día**, por encima de la cuota. Groq GPT-OSS 20B requiere 486.000 tokens/día, más del doble de los 200.000 tokens/día de referencia Free; el 120B comparte las mismas cuotas.
- **Presupuesto operativo recomendado: 0 € con degradación explícita**, no «chat IA ilimitado»: botones deterministas por defecto; limitar la IA a una ruta corta con el modelo pequeño; presupuesto diario global y equitativo; comparador, simulaciones y cálculo deterministas disponibles aunque la IA falle. La capacidad real, latencia y calidad siguen sin medir.

## Tarifas y cuotas oficiales usadas

| Proveedor / modelo | Tamaño | Precio publicado por millón de tokens (entrada / salida) | Cuota gratis de referencia | Contexto / herramientas |
|---|---:|---:|---|---|
| Cloudflare `@cf/meta/llama-3.2-3b-instruct` | 3B | $0,051 / $0,335 | 10.000 Neurons/día por Workers AI; generación de texto 300 req/min salvo modelos que requieren plan Paid | 80.000 tokens; la ficha del modelo no lista function calling |
| Cloudflare `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 70B | $0,293 / $2,253 | Igual asignación y límite base de generación de texto | 24.000 tokens; ficha marca function calling |
| Groq `openai/gpt-oss-20b` | 20B | $0,075 / $0,30 | Referencia de Free: 30 RPM, 1.000 RPD, 8.000 TPM, 200.000 TPD | 131.072 tokens; tool use documentado |
| Groq `openai/gpt-oss-120b` | 120B | $0,15 / $0,60 | La misma referencia de Free que el 20B | 131.072 tokens; tool use documentado |

Cloudflare publica una asignación gratis diaria de 10.000 Neurons; el plan Paid cobra $0,011 por cada 1.000 Neurons que excedan esa asignación.[1]

La tarifa de texto es 300 solicitudes/minuto excepto modelos que requieren Workers Paid.[2]

La página de precios contiene las tarifas por token y Neurons de ambos modelos.[1]

Las fichas por modelo documentan ventanas de contexto; la 70B marca function calling y la 3B no lista esa función.[3][4]

Groq publica los límites de referencia para esos dos modelos en la vista Free y advierte que los topes exactos se aplican a nivel de organización y deben confirmarse en la consola; no son una promesa de concurrencia.[5]

El catálogo y las fichas oficiales documentan precio y soporte de uso de herramientas para GPT-OSS 20B y 120B.[6][7][8]

No apliqué descuentos por caché ni trasladé precios USD a EUR.

## Supuestos del cálculo

Una fila es **una cohorte de 100 personas, una conversación por usuario en un día UTC**, no 100 conversaciones concurrentes medidas. Contextos estáticos por llamada (tokens):

| Perfil | Instrucciones | Definiciones de herramientas | Perfil | Productos | Total estático |
|---|---:|---:|---:|---:|---:|
| Lean | 400 | 250 | 100 | 250 | 1.000 |
| Típico | 700 | 500 | 250 | 900 | 2.350 |
| Heavy | 1.200 | 900 | 400 | 1.800 | 4.300 |

Cada turno añade una pregunta de 60 tokens. El historial previo crece en 60 tokens del usuario + la respuesta final seleccionada (250 o 500) + 170 tokens por loop previo (mensaje de llamada a herramienta de 50 y resultado de herramienta de 120). Cada llamada de seguimiento repite contexto e historial y añade pares de llamada/resultado anteriores; un loop añade una llamada LLM secuencial. La ejecución de la herramienta se trata como determinista y sin coste de tokens. Esto es una cota de consumo basada en una aplicación que reenvía el contexto; no se supone caché.

Onboarding con botones: cero llamadas LLM. Onboarding LLM: **una llamada por usuario**, con 600 tokens de entrada y 120 de salida (supuesto de diseño). Por tanto añade 100 solicitudes, 60.000 tokens de entrada y 12.000 de salida al día para la cohorte. En el caso lean de 3 turnos con Cloudflare 3B, pasa de 4.186,5 a 4.829,7 Neurons/día. El uso posterior del perfil dentro del chat ya está contado en el componente «perfil» del contexto.

El número de requests es `turnos × (1 + loops)` más onboarding LLM opcional. El coste publicado de la tabla CSV/JSON es una estimación sin caché a tarifas de token; para Cloudflare también se calcula el exceso teórico sobre la asignación gratuita si se habilitara Paid. En Free, superar la cuota no habilita el exceso: las operaciones fallan según la documentación.[1]

## Escenarios representativos

Consumo agregado de los 100 usuarios, onboarding por botones, respuestas de 250 tokens y sin loops salvo que se indique:

| Proveedor/modelo | Configuración | Requests/día | Tokens entrada + salida/día | Neurons/día | Situación frente a cuota diaria | Coste de tokens a tarifa publicada, sin caché |
|---|---|---:|---:|---:|---|---:|
| Cloudflare Llama 3.2 3B | Lean, 3 turnos | 300 | 411.000 + 75.000 | 4.186,5 | Dentro de 10.000 | $0,0461 |
| Cloudflare Llama 3.3 70B | Lean, 3 turnos | 300 | 411.000 + 75.000 | 26.320,9 | Excede; caben 37 usuarios a este uso | $0,2894 |
| Groq GPT-OSS 20B | Lean, 3 turnos | 300 | 411.000 + 75.000 | — | Excede 200.000 TPD; caben 41 usuarios a este uso | $0,0533 |
| Cloudflare Llama 3.2 3B | Típico, 5 turnos | 500 | 1.515.000 + 125.000 | 10.816,3 | Excede por 816,3; caben 92 usuarios | $0,1191 |
| Cloudflare Llama 3.3 70B | Típico, 5 turnos | 500 | 1.515.000 + 125.000 | 66.002,6 | Excede; caben 15 usuarios | $0,7255 |
| Groq GPT-OSS 20B | Típico, 5 turnos | 500 | 1.515.000 + 125.000 | — | Excede 200.000 TPD; caben 12 usuarios | $0,1511 |

«Caben N usuarios» escala solo los topes diarios por el consumo de una persona; **no** descuenta picos/minuto, reserva ni fallos. Los importes en USD son valor de lista de todos los tokens, no el cobro real de un plan gratuito; en Cloudflare la asignación de Neurons y el requisito de Paid cambian la factura efectiva.[1]

En el caso típico de cinco turnos, Groq queda bajo 1.000 solicitudes/día pero genera 1,64 millones de tokens, 8,2 veces los 200.000 TPD de referencia. Su mayor tamaño no aumenta las cuotas publicadas: solo eleva el precio por token. En Cloudflare, el 3B también deja de caber por poco y el 70B excede la asignación ampliamente.

## Casos de cuota, cola, rate limit y latencia

- **Cuota agotada:** Cloudflare 70B con contexto heavy, 10 turnos, 500 tokens de salida y 2 loops demanda 809.317,32 Neurons frente a 10.000 gratis. La simulación marca `exhausted`; en producción debe cortarse el gasto gratis al alcanzar el límite y ofrecer fallback, no continuar suponiendo que el proveedor dará servicio.[1]
- **Cola:** 100 peticiones iniciales Groq 20B con contexto típico y respuesta de 250 tokens producen un lote de 266.000 tokens. Sin cola supera 30 RPM y 8.000 TPM; el drenaje inferior por cuotas es **34 ventanas de un minuto** (el límite de tokens domina), no una predicción de tiempo de respuesta.[5]
- **429/rate limit:** 100 llamadas iniciales con contexto lean generan 131.000 tokens y superan los límites Free de Groq si se lanzan sin cola. La política propuesta limita globalmente, usa cola acotada, obedece `Retry-After` si viene, aplica backoff con jitter y después usa fallback; no hace retries apretados.[5]
- **Latencia desconocida:** `latency_ms = null` en todos los escenarios y en el caso de prueba. No se enviaron prompts ni se hicieron pruebas de carga. Los tokens/segundo de una ficha no equivalen a latencia extremo a extremo y aquí no se usan como benchmark.

Cloudflare deja 100 solicitudes dentro de su límite nominal de 300 req/min, pero el límite por minuto no promete 100 solicitudes simultáneas; no se encontró un límite TPM publicado para esta ruta.[2] El cálculo, por tanto, informa capacidad de cuota, no throughput real.

## Recomendación de 0 € y reparto justo

1. Mantener onboarding por botones y dejar búsqueda, filtros, comparador, simulaciones y cálculos financieros en lógica determinista. No gastar tokens en tareas que no requieren generación.
2. Si se acepta un piloto gratuito, probar una ruta acotada con Llama 3.2 3B en el caso lean de 3 turnos/250 tokens, sin loops LLM. El chat con IA sigue siendo un requisito del proyecto; acotar disponibilidad no lo convierte en una función opcional ni autoriza sustituirlo definitivamente por FAQ. Esa combinación consume 4.186,5 Neurons para 100 personas, por debajo de una reserva operativa ilustrativa del 10% (9.000 Neurons asignadas a usuarios). Esto es una hipótesis aritmética de coste, no garantía de calidad en español, latencia, disponibilidad o concurrencia. Su ficha no lista function calling; no basar la integración de herramientas en esa capacidad no documentada.[1][3]
3. Presupuesto global por proveedor/modelo con contador atómico compartido. Reservar 10% de cuota y distribuir el 90% restante equitativamente: Cloudflare ≈90 Neurons por usuario/día; Groq ≈9 solicitudes y 1.800 tokens por usuario/día sobre los topes de referencia Free. En Groq, incluso el escenario lean de tres turnos usa 4.860 tokens por persona, por lo que no cabe en ese reparto.[1][5]
4. La identidad de cuota debe ser la cuenta autenticada o una sesión firmada, con límite secundario de abuso por IP; **no** usar IP como cuota primaria ni penalizar a usuarios legítimos por compartir NAT. Usar ronda justa por usuario en cola, límite de concurrencia por usuario y contador global por organización. No repartir cuota entre cuentas o claves para eludir los topes.
5. Cuando se agote la cuota o llegue un 429, parar intentos LLM, comunicar que Pai IA no está disponible y ofrecer fallback determinista. No prometer ETA mientras no se midan latencias. Nunca activar pagos ni un plan superior automáticamente.

**Conclusión:** 0 € es realista como presupuesto para una beta de 100 usuarios solo si «100 usuarios» no significa acceso ilimitado ni respuesta garantizada: el onboarding es determinista, los contextos/salidas se limitan, la IA pequeña es best-effort y la aplicación funciona sin ella. Para cinco turnos típicos por usuario o uso de modelo grande, el modelo calculado no respalda una promesa gratuita fiable.

## Correcciones de revisión del coordinador

Se restauró el ledger tras detectar una sobrescritura entre tareas: se descargaron de nuevo las ocho fuentes oficiales, se verificó la correspondencia URL → texto y se regeneró este bloque de fuentes. Evidencias en `restauracion/`; el archivo `INCIDENTE-ledger-corrupto-NO-USAR.json` conserva únicamente el incidente y no debe usarse como bibliografía.

Se corrigió además la estimación del burst inicial con loops: incluía resultados de herramientas que aún no existían en esa primera solicitud. Una regresión falló con 145.000 frente a 111.000 tokens para el caso de prueba; tras corregir el cálculo pasan seis tests y se regeneraron los 432 escenarios. La contabilidad diaria de ese modelo no cambió.

## Límites y reproducibilidad

No se crearon cuentas, API keys ni pagos; no se ejecutó ninguna petición a un proveedor ni carga externa. Las cuotas son las publicadas consultadas el 26-10-2026; la cuota Free real puede depender de la cuenta y cambiar. No se demuestra throughput, latencia, calidad de respuestas, disponibilidad, residencia de datos, elegibilidad de uso ni encaje jurídico.

Reproducir en este directorio: `python capacity_model.py` para regenerar `scenarios.csv` y `scenarios.json`; `python -m unittest test_capacity_model.py -v` ejecuta las pruebas locales de fórmulas, cuadrícula, onboarding y casos límite. Solo se usa la biblioteca estándar de Python.

## Sources

[1] https://developers.cloudflare.com/workers-ai/platform/pricing
[2] https://developers.cloudflare.com/workers-ai/platform/limits
[3] https://developers.cloudflare.com/workers-ai/models/llama-3.2-3b-instruct
[4] https://developers.cloudflare.com/workers-ai/models/llama-3.3-70b-instruct-fp8-fast
[5] https://console.groq.com/docs/rate-limits?plan=free
[6] https://console.groq.com/docs/models
[7] https://console.groq.com/docs/model/openai/gpt-oss-20b
[8] https://console.groq.com/docs/model/openai/gpt-oss-120b
