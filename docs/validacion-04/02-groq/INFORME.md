# Verificación de GroqCloud Free para Paideia

**Consulta documental:** 27 de octubre de 2026 · **Ámbito:** modelos, límites, uso de herramientas/JSON, términos, privacidad, ubicación y acceso gratuito. **Resultado:** análisis documental; no se creó cuenta, no se inició sesión, no se generó ni usó una API key y no se hicieron llamadas autenticadas.

## Veredicto

**Recomiendo probar `openai/gpt-oss-20b` como candidato inicial y `openai/gpt-oss-120b` como comparador A/B.** Groq los clasifica como modelos de producción; los dos figuran con uso de herramientas locales/remotas y JSON Mode. Ninguno permite uso paralelo de herramientas según la tabla de Groq.[1][2]
Ambos tienen una ventana publicada de 131.072 tokens y un máximo de salida de 65.536 tokens; esos máximos del modelo no equivalen a cuota gratuita disponible por petición.[1]

**El ajuste es prometedor para un prototipo educativo acotado, pero no queda validado para publicación pública ni para asesoramiento financiero**. Groq dice que sus modelos no deben usarse para consejo financiero o profesional.[5]
Para Paideia, limitaría el LLM a explicación didáctica de datos verificados y llamadas a herramientas de solo lectura; cálculo y reglas financieras deben seguir en código, sin recomendaciones personalizadas de compra/venta.[5]

No se verificó la calidad lingüística ni la utilidad de estos modelos para Paideia en español; debe probarse con casos sintéticos.[unverified]
`qwen/qwen3.8-27b` sí aparece con herramientas y JSON, pero está en la sección **Preview**, no en producción.[1][2]
Groq advierte que los modelos Preview pueden retirarse con poca antelación, así que no lo elegiría para la demo pública.[1]

## Modelos recomendados

| Modelo | Uso recomendado | Capacidades publicadas | Límites del modelo |
|---|---|---|---|
| `openai/gpt-oss-20b` | **Primero para el smoke**: más rápido de los dos en la tabla de Groq; la calidad en español no está comprobada. | Producción; herramientas locales/remotas; JSON Mode; sin herramientas paralelas. También aparece como compatible con salida JSON Schema estricta, pero no en la misma llamada que herramientas.[1][2][3] | 131.072 contexto; 65.536 máximo de salida.[1] |
| `openai/gpt-oss-120b` | **Segundo para comparar calidad**, sin asumir que será mejor hasta medirlo. | Producción; herramientas locales/remotas; JSON Mode; sin herramientas paralelas. La salida JSON Schema estricta requiere una llamada separada sin herramientas.[1][2][3] | 131.072 contexto; 65.536 máximo de salida.[1] |

Groq documenta `strict: true` para ambos modelos.[3]
También indica que Structured Outputs no admite actualmente llamadas a herramientas.[3]
En la práctica, usar la llamada con `tools` para pedir una función de Paideia y, si hace falta una salida final con JSON Schema estricto, hacerla en una segunda llamada sin herramientas; validar de todos modos la respuesta en el servidor.[3]
No activar las herramientas integradas de búsqueda web o ejecución de código para este caso: basta con una lista permitida de herramientas propias (`catalog_search`, `compare_products`, `calculate_scenario`, `source_lookup`) con argumentos y resultados acotados.[2]

## Cuota gratuita publicada y cuota real

La pestaña **Free Plan Limits** de la página oficial muestra estos límites para ambos modelos.[4]
La página define RPM/RPD/TPM/TPD como solicitudes por minuto/día y tokens por minuto/día, y dice que las cuotas son por organización, no por usuario.[4]

| Modelo | RPM | RPD | TPM | TPD | Contexto | Máx. salida |
|---|---:|---:|---:|---:|---:|---:|
| `openai/gpt-oss-20b` | 30 | 1.000 | 8.000 | 200.000 | 131.072 | 65.536 |
| `openai/gpt-oss-120b` | 30 | 1.000 | 8.000 | 200.000 | 131.072 | 65.536 |

**Cómo leer estos datos.** La página tiene pestañas separadas Free/Developer; guardé ambas vistas en `evidencia/04-rate-limits-tabs.txt`.[4]
La pestaña Free muestra la tabla anterior.[4]
La pestaña Developer muestra cifras distintas: para estos modelos, 1.000 RPM, 500.000 RPD y 250.000 TPM, con TPD sin valor mostrado.[4]
El texto explicativo también llama “base limits for the Developer plan” a los límites mostrados.[4]
Por eso la tabla anterior se atribuye solo a la pestaña Free observada, no se mezcla con la tabla Developer.[4]

**No es la cuota real de una cuenta de Paideia.** Groq dice que los valores exactos de cada organización se consultan en Console y que puede haber excepciones; no se comprobó ninguna cuenta de Alejandro/José Manuel.[4]
Para TPM, algunas organizaciones tienen topes separados de entrada y salida.[4]
La tabla Free fija 30 RPM por organización para estos modelos.[4]
Eso no garantiza 30 respuestas simultáneas: RPM mide solicitudes por minuto, no concurrencia.[4]
No prometería 100 respuestas IA en paralelo; mantener cupo y cola visibles y dejar catálogo, comparador y simuladores disponibles aunque el chat espere o se detenga.[4]

## España, publicación pública y uso financiero educativo

El Services Agreement, actualizado el 22 de junio de 2026, permite integrar las API en una aplicación del cliente y ponerlas a disposición de sus End Users.[5]
A la vez, dice que Cloud Services y AI Model Services “are not for consumer use”.[5]
La coexistencia de ambas frases no resuelve por sí sola si una demo web educativa abierta al público encaja.[5]
No encontré en las páginas revisadas una prohibición académica expresa, pero tampoco una autorización específica para Paideia; el acuerdo incorpora además una AUP separada que no se revisó dentro del límite de ocho páginas.[5]
**Antes de publicar, confirmar por escrito con Groq que una aplicación académica gratuita y pública de adultos está cubierta.**[5]

Para clientes domiciliados en el EEE, el acuerdo identifica a Groq UK Limited como parte contratante; eso sitúa a España en la región contractual descrita, pero no demuestra que el alta Free desde España esté disponible ni que se haya probado.[5]
El DPA permite tratamiento en Estados Unidos.[7]
También prevé las cláusulas contractuales tipo de la UE cuando sean legalmente exigibles.[7]
La ubicación estadounidense y el mecanismo contractual deben formar parte de la evaluación de privacidad de Paideia; no equivalen por sí solos a una validación legal del flujo.[7]

El acuerdo dice expresamente que el modelo no debe usarse para consejo financiero o profesional.[5]
Para no cruzar esa frontera, usaría el chat para educación general, explicación de términos, lectura de datos de catálogo con fuente/fecha y explicación de escenarios hipotéticos; evitaría que diga al usuario qué producto contratar o que formule asesoramiento personalizado.[5]
Mantendría los cálculos y criterios de elegibilidad en código, con fuentes y supuestos visibles, tal como ya prevé Paideia.[5]

## Privacidad, retención y entrenamiento

- **Entrenamiento:** Groq declara que no puede usar Inputs/Outputs para entrenar o afinar modelos salvo permiso o instrucción explícitos del cliente.[5]
- **Retención:** por defecto no retiene datos de inferencia, pero sí recoge metadatos de uso; puede registrar Inputs/Outputs por fiabilidad o investigación de abuso hasta 30 días. Groq ofrece activar Zero Data Retention (ZDR) desde Data Controls; no se comprobó ni cambió esa opción en una cuenta.[6]
- **Ubicación:** la documentación indica que los datos retenidos se guardan en buckets de Google Cloud Platform en Estados Unidos; el DPA contempla transferencias internacionales y SCC de la UE cuando corresponda.[6][7]

La retención por defecto limitada no convierte cifras de ingresos/gastos en anónimas.[6]
Mantener el perfil en el navegador y enviar solo la proyección B pertinente por turno; probar A/B/C exclusivamente con perfiles sintéticos; informar al usuario qué campos salen del dispositivo y obtener la decisión/consentimiento que Paideia aún debe definir.[5][6][7]

## Acceso gratuito, tarjeta y riesgo de pago

La FAQ oficial confirma una capa Free y dice que para **subir** de Free a Developer hace falta un método de pago válido: tarjeta, cuenta bancaria estadounidense o débito SEPA.[8]
También indica que Developer es pay-as-you-go y que los cobros se retiran automáticamente al alcanzarse umbrales de facturación o al cierre mensual.[8]

**Tarjeta en el alta Free: no comprobado.**
La documentación revisada no dice expresamente si el formulario de alta gratuita solicita tarjeta; tampoco se hizo una inscripción.[8]
El método de pago queda documentado como requisito para el upgrade, no como requisito confirmado de la cuenta Free.[8]
Flujo seguro cuando el usuario decida configurarlo: crear la cuenta en Groq Console, permanecer en **Free**, crear la API key allí y guardarla solo como secreto de backend (nunca en el navegador ni en el chat).
Si el alta Free pide tarjeta, detenerse y no continuar hasta confirmar que puede mantenerse sin pago.
No cambiar a Developer, no introducir método de pago ni confiar en un supuesto auto-overage; al alcanzar un límite, pausar/encolar y mostrar el estado, sin reintentos en bucle.[8]

## Smoke pequeño y comparación A/B/C

**Smoke posterior — no ejecutado en este informe.** Cuando el usuario configure la key de forma segura, ejecutar primero `gpt-oss-20b` y luego, si la cuota lo permite, repetir el mismo smoke en `gpt-oss-120b`. Usar fixtures marcadas como sintéticas y no incluir datos personales, perfiles reales ni condiciones comerciales atribuidas a una entidad.

1. **Español y límites:** pedir una explicación didáctica breve de interés simple frente a compuesto; comprobar claridad, tono educativo y que no invente supuestos.
2. **Herramienta acotada:** solicitar una búsqueda en un catálogo fixture de dos productos ficticios; comprobar que solo emite la función permitida y argumentos válidos, y que la respuesta cita los campos recibidos.
3. **Cálculo:** llamar a `calculate_scenario` con capital, plazo y tipo sintéticos; comparar el resultado de la herramienta con el cálculo determinista local y pedir al modelo que explique supuestos, no que calcule por su cuenta.
4. **JSON separado:** en una llamada sin herramientas pedir un objeto JSON/JSON Schema sencillo, validarlo en backend y comprobar la ruta de error/refusal. Tope práctico de salida: 256 tokens, una llamada a herramienta por turno y sin paralelismo; no intentar consumir los máximos publicados de 65.536 tokens.

Parar ante 429, petición de pago, herramienta fuera de allowlist, argumentos que no validan, dato financiero inventado o salida que se convierta en consejo.[4][5]
No ejecutar ahora estas pruebas: no hay cuenta ni key disponible, y el usuario pidió no hacer llamadas autenticadas.

Después, aplicar el protocolo ya definido en `docs/planificacion-03/19-integracion/EVALUACION-CONTEXTO.md`: comparar A (sin perfil), B (solo campos pertinentes) y C (perfil sintético completo), sin identificadores. Dentro de cada modelo, mantener iguales casos, prompt, fixtures, herramientas y techo de salida; variar solo el contexto. Luego, comparar 20B frente a 120B con el mismo contexto elegido. Registrar exactitud/trazabilidad, utilidad contextual, claridad, tokens, errores/latencia y campos enviados; revisión humana de los dos estudiantes y puertas no compensables de privacidad/uso/presupuesto. No elegir C por defecto ni declarar ganador con una sola salida.

## Estado y decisión pendiente

**Documentado, no integrado ni probado.** No se verificaron alta desde España, requisito de tarjeta en Free, cuota real de organización, calidad en español, latencia ni capacidad concurrente; no hubo llamada API, no se creó key y no se cambió ninguna opción de datos. Mi recomendación es autorizar únicamente el smoke sintético en Free tras la configuración segura; decidir sobre publicación después de resolver la ambigüedad de uso público/financiero y comprobar la política AUP, el alta sin pago y la cuota real.

## Sources

[1] https://console.groq.com/docs/models — Supported Models - GroqDocs
[2] https://console.groq.com/docs/tool-use/overview — Tool Use Overview - GroqDocs
[3] https://console.groq.com/docs/structured-outputs — Structured Outputs - GroqDocs
[4] https://console.groq.com/docs/rate-limits — Rate Limits - GroqDocs
[5] https://console.groq.com/docs/legal/services-agreement — Groq Services Agreement
[6] https://console.groq.com/docs/your-data — Your Data in GroqCloud
[7] https://console.groq.com/docs/legal/customer-data-processing-addendum — Data Processing Addendum for GroqCloud Services
[8] https://console.groq.com/docs/billing-faqs — Billing FAQs - GroqDocs
