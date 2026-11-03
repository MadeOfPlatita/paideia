# Paideia — síntesis y contraste de la investigación

**Investigación cerrada:** diez informes y diez JSON de fuentes recibidos y comprobados. Fue necesario un subagente adicional para recuperar fondos/ETF tras fallar su primer intento. Consulta y contraste: 26 de octubre de 2026.

## Resultado ejecutivo

Sí hay proyectos similares aprovechables. No se ha identificado una base lista para desplegar que resuelva simultáneamente catálogo español de productos reales, condiciones contractuales diarias, chat gratuito suficiente para la clase y personalización financiera con encaje jurídico revisado. Esto es un resultado de la búsqueda realizada, no una demostración de inexistencia.

La propuesta de este documento no modifica por sí sola los requisitos aprobados. Especialmente, convertir todos los productos en ficticios o sustituir definitivamente la IA por FAQ serían cambios de alcance que requieren aprobación del grupo.

## 1. Repositorios que más aportan

| Proyecto | Lo aprovechable | Límite importante |
|---|---|---|
| [Portugal Term Deposit Comparator](https://github.com/ricardoserodio/portugal-term-deposit-comparator) | Esquema de productos, requisitos de elegibilidad, trazabilidad, revisión humana antes de publicar cambios. Su README describe el flujo.[4] | Sus datos y la hipótesis tributaria son portugueses; no importar la fiscalidad ni las condiciones para España.[4] |
| [Which ETF?](https://github.com/violettance/etf-dashboard) | Búsqueda, selección y comparación con fecha de captura y campos desconocidos explícitos.[5] | Su directorio se capturó el 25 de mayo de 2025; no es un feed vigente ni acredita cobertura de ETF UCITS accesibles desde España.[5] |
| [FinGenius](https://github.com/anujdevsingh/financial_genius_agent) | Separación entre calculadoras y texto del LLM; ejemplo de herramientas financieras.[6] | El arranque pide una clave de OpenAI y no acredita coste cero. Sus ejemplos se centran en finanzas personales y extractos de India.[6] |

Las tres licencias de código comprobadas son MIT.[11][12][13] Esto no acredita automáticamente derechos sobre datos financieros, marcas o servicios asociados.

Otros proyectos estudiados en el informe 07: RukiAI, FinRobot, Wealthfolio, Ghostfolio y Actual Budget. No se ha ejecutado ninguno; la revisión fue documental y de archivos concretos.

**Recomendación de diseño:** implementar una base pequeña propia, aprovechar patrones y, si se copia código, identificar archivos y conservar sus avisos. No adoptar de golpe varios backends y frameworks de agentes.

## 2. Datos: qué funciona y qué no

### Cuentas y depósitos

El BdE documenta un servicio web JSON de series estadísticas.[8]

La petición pública del BdE probada directamente devolvió HTTP 200 y una serie `TEDR. Depósitos de hogares e ISFLSH. De 1 a 2 años`, con frecuencia `M` y fecha de observación de agosto de 2026.[14] El endpoint MIR del BCE probado devolvió CSV HTTP 200 y datos AAR/NDER mensuales agregados.[15]

**No son TAE vigentes de productos de bancos concretos.** La búsqueda no encontró una API gratuita abierta suficiente para todo el catálogo contractual deseado. Las fichas oficiales de bancos siguen siendo candidatas para un catálogo curado; el informe 01 documenta sus campos y limitaciones.

**Decisión propuesta:** empezar con pocos productos reales, cada campo vinculado a una fuente primaria y su fecha. Automatizar únicamente lo que permitan las fuentes y pasar cambios relevantes por validación antes de publicar. No anunciar cobertura del 90 % sin definir y medir el universo.

### Deuda pública

La página oficial del Tesoro contrastada devuelve resultados por plazo, fecha de subasta, vencimiento, precio medio y tipos; es información de subastas concretas.[9] No debe presentarse como una cotización de compra disponible hoy. El informe 02 diferencia calendario, resultado de subasta y series de rendimiento agregadas.

### Fondos y ETF

El informe 03 ya está incorporado. La página CNMV contrastada identifica el fondo y su ISIN y distingue gastos corrientes y comisiones.[18] Se han localizado documentos oficiales de gestoras, pero no se ha validado un feed agregado autorizado que reúna catálogo, costes, riesgo y precios diarios para todo el universo deseado.

También he probado directamente Yahoo Finance para `VWCE.DE`: HTTP 200, JSON de un ETF en EUR con cinco observaciones; la respuesta no identifica por sí sola ISIN, KID o comisiones contractuales.[19] Es una prueba técnica, no verificación de permisos de publicación ni de redistribución.

**Propuesta:** registrar clases por ISIN; separar coste documental, indicador de riesgo y fecha del documento de NAV y cotización por bolsa. No usar fichas reservadas a profesionales como documentación minorista ni confundir una clase que cotiza en EUR con exposición sin riesgo de divisa. El informe 03 detalla límites y fuentes.

Which ETF? reconoce que su dataset es histórico y que parte de las comisiones se verifican manualmente.[5]

### Corrección entre informes: reutilización del BdE

Los informes 01 y 06 dejaron la licencia del BdE sin confirmar; el 02 localizó términos oficiales. Los he leído directamente: permiten reutilización de estadísticas, condicionada a integridad, atribución y otras obligaciones, con excepción de datos de terceros.[10] Por tanto, ya no debe figurar como desconocida en la decisión conjunta. Esto no transforma estadísticas en ofertas comerciales.

## 3. MCP frente a API directa

La documentación oficial define MCP como un estándar de conexión de aplicaciones de IA con sistemas externos.[7] No aporta por sí solo un catálogo, actualización, permisos de datos o alojamiento.

**Propuesta para esta semana:** API HTTP directa cuando exista una fuente válida; catálogo versionado para los demás campos. El informe 06 evalúa OpenBB y wrappers financieros, pero no demuestra que alguno resuelva el catálogo español completo de coste cero. No desplegar un MCP solo por añadir esa etiqueta técnica.

## 4. IA gratuita: el principal cuello de botella

### Gemini: restricción confirmada, no solo privacidad

He descargado directamente el texto completo de sus términos. Contiene literalmente: “You may use only Paid Services when making API Clients available to users in the European Economic Area, Switzerland, or the United Kingdom.”[1]

El mismo documento explica que en el EEE las condiciones de tratamiento de datos de Paid Services también se aplican a la cuota gratuita; esa regla de privacidad no elimina la restricción anterior sobre API Clients.[1] **No elegir Gemini Free para esta web española sobre la base de que aparece España como región disponible.**

### Workers AI: candidato de prueba, no solución aprobada

Cloudflare documenta 10.000 Neurons gratuitas por día y un límite base de generación de texto de 300 solicitudes por minuto, con excepciones para modelos que requieren plan de pago.[2][3] Ni una cuota diaria ni una tasa por minuto prueban que cien chats simultáneos funcionen.

Para `@cf/meta/llama-3.3-70b-instruct-fp8-fast`, los coeficientes publicados son 26.668 Neurons por millón de tokens de entrada y 204.805 por millón de salida.[2] Cálculo realizado en Python sobre esas tarifas —no benchmark, sin llamadas a modelos—:

| Supuesto por turno | Consumo calculado | Máximo teórico dentro de 10.000/día |
|---|---:|---:|
| 200 tokens entrada + 250 salida | 56,5348 Neurons | 176 turnos |
| 1.500 entrada + 300 salida | 101,4435 Neurons | 98 turnos |
| 3.000 entrada + 500 salida | 182,4065 Neurons | 54 turnos |

Cada turno puede incluir instrucciones, historial, productos y varias llamadas; no equivale a una conversación completa. **Recomendar un modelo 70B como resuelto para cien compañeros sería prematuro.** Hay que medir uno o varios modelos aptos para Free con contexto realista, calidad en español, control de herramientas y consumo.

El informe 04 compara además Groq y OpenRouter y conserva sus fuentes. Ninguno ha sido probado con credenciales. No hay garantía comprobada de chat gratuito ilimitado ni de cien inferencias simultáneas.

**Propuesta:** backend intercambiable, límites explícitos, contexto breve y cálculo determinista. Si no se puede servir IA, mostrarlo y conservar comparador/simuladores; nunca fingir respuestas del modelo. La IA sigue siendo un requisito deseado, no se sustituye silenciosamente por un guion.

## 5. Alojamiento provisional

La documentación de Cloudflare Pages confirma que los assets estáticos tienen solicitudes gratuitas e ilimitadas, mientras que Pages Functions consume la cuota de Workers.[16] Por eso separar catálogo, cálculos y gráficos locales del chat remoto evita gastar inferencia en tareas que no la necesitan.

**Arquitectura candidata, aún no desplegada:** GitHub público para código → frontend estático en Cloudflare Pages → Worker para chat protegido → proveedor IA que supere las pruebas. Preparación del catálogo por tarea programada solo donde haya fuentes y permisos suficientes. Las condiciones específicas de Actions y límites de build se documentan en el informe 05; no hay cuentas ni despliegue creados.

## 6. Rigor, diseño y simulación

La CNMV define asesoramiento de inversiones como recomendaciones personalizadas sobre productos concretos y explica que la idoneidad incluye conocimientos, situación financiera y objetivos.[17] Adaptar explicaciones al nivel del usuario no habilita a Paideia como asesor autorizado. La conclusión jurídica de un servicio concreto requiere revisión profesional; no está resuelta por esta investigación.

**Propuesta prudente:** perfil para adaptar explicaciones, filtros elegidos por el usuario y comparación trazable, sin prometer “el mejor producto para ti”. Mantener productos reales cuando haya datos verificados; escenarios y contratación deben identificarse claramente como simulados. No confundir “escenario ficticio” con “dato contractual inventado”.

Los informes 08 y 10 incluyen propuestas más conservadoras, como dataset totalmente sintético o chat inicial apagado. Son alternativas de reducción de alcance, no decisiones ya aceptadas por Alejandro y José Manuel.

Recursos de diseño investigados en 08: Chart.js o ECharts, iconos Lucide, animación CSS o Motion y PDF con impresión o jsPDF. La propuesta visual de Pai es original; no se han creado assets ni prototipo. Las licencias observadas están en el informe, pero deben revisarse para las versiones que finalmente se incorporen.

## 7. Qué está probado y qué falta

**Comprobado por el coordinador:** archivos de diez informes y sus diez JSON; 290 registros de fuentes, 284 URLs únicas sin normalizar variantes; revisión de los diez informes; 19 solicitudes HTTP públicas de contraste con resultado 200; tres archivos LICENSE MIT; dos endpoints estadísticos y uno de mercado; texto completo de términos Gemini y cuotas Cloudflare. Los textos y metadatos están en `evidencia-parental/`. El recuento de URLs no equivale a corroboración independiente de cada afirmación.

**No probado:** ninguna app ejecutada, integración de LLM, cuenta gratuita sin tarjeta, carga de cien usuarios, actualización diaria completa, cobertura de mercado o autorización/revisión jurídica. No se ha instalado ni ejecutado código de los repos encontrados ni se ha publicado nada.

**Pendiente de implementación:** elegir un catálogo inicial medible y ejecutar pruebas técnicas pequeñas antes de fijar proveedor y arquitectura. La investigación está entregada; la viabilidad operativa conjunta de gratuidad, cobertura amplia y chat para cien personas sigue abierta.

## Sources

[1] https://ai.google.dev/gemini-api/terms
[2] https://developers.cloudflare.com/workers-ai/platform/pricing
[3] https://developers.cloudflare.com/workers-ai/platform/limits
[4] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/README.md
[5] https://raw.githubusercontent.com/violettance/etf-dashboard/main/README.md
[6] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/README.md
[7] https://modelcontextprotocol.io/introduction
[8] https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html
[9] https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/letras-del-tesoro
[10] https://bde.es/wbe/en/estadisticas/recursos/terminos/terminos-de-uso.html
[11] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/LICENSE
[12] https://raw.githubusercontent.com/violettance/etf-dashboard/main/LICENSE
[13] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/LICENSE
[14] https://app.bde.es/bierest/resources/srdatosapp/favoritas?idioma=es&series=DN_1TI2T0026
[15] https://data-api.ecb.europa.eu/service/data/MIR/M.ES.B.L22.A.R.A.2250.EUR.N?lastNObservations=1&format=csvdata
[16] https://developers.cloudflare.com/pages/functions/pricing
[17] https://cnmv.es/portal/inversor/idoneidad?lang=es
[18] https://www.cnmv.es/portal/inversor/fondos-dfi?lang=es
[19] https://query1.finance.yahoo.com/v8/finance/chart/VWCE.DE?range=5d&interval=1d
