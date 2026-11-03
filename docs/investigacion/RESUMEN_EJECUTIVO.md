# Paideia — resultado ejecutivo de la investigación

La investigación está cerrada: diez áreas cubiertas, diez informes y ocho repositorios seleccionados. Se agregaron 290 registros de fuentes, correspondientes a 284 URLs distintas. Este recuento mide referencias recopiladas, no afirmaciones independientemente corroboradas.

## Lo más aprovechable

| Recurso | Qué aprovechar | Qué no asumir |
|---|---|---|
| [Portugal Term Deposit Comparator](https://github.com/ricardoserodio/portugal-term-deposit-comparator) | Modelo de productos, filtros y revisión de condiciones con trazabilidad.[4] | Datos y fiscalidad portugueses no sirven directamente para España.[4] |
| [Which ETF?](https://github.com/violettance/etf-dashboard) | Interacción de selección/comparación y visibilidad de campos sin verificar.[5] | Su directorio es histórico, no una fuente actual de cotizaciones.[5] |
| [FinGenius](https://github.com/anujdevsingh/financial_genius_agent) | Separación entre herramientas de cálculo y explicación del LLM.[6] | Requiere OpenAI para su configuración de arranque; no es coste cero listo para usar.[6] |

Estos proyectos son referencias documentales; no se han instalado ni ejecutado. Las licencias y otros cinco repositorios están en el informe 07 y en la síntesis.

## Hallazgos que afectan al proyecto

1. **No hemos validado una API gratuita universal de productos españoles.** Los endpoints BdE/BCE probados dan estadísticas agregadas, no ofertas contractuales individuales.[14][15] La propuesta viable es un catálogo inicial acotado, fuentes oficiales, fechas por campo y automatización donde esté permitida.
2. **Sí hay datos de mercado accesibles técnicamente, pero acceso no es licencia.** La prueba de Yahoo para VWCE.DE respondió con JSON de cotizaciones; no resuelve permisos, KID, costes o distribución en España.[19]
3. **MCP no elimina el problema de los datos.** Es un estándar de conexión con sistemas externos.[7] Para una semana proponemos APIs directas y herramientas propias pequeñas, no desplegar un agregador solo por usar MCP.
4. **La IA gratuita sigue siendo el cuello de botella.** Los términos Gemini restringen a Paid Services los API Clients dirigidos a usuarios del EEE.[1] Workers AI tiene cuota gratuita, pero no debemos confundirla con chat ilimitado o capacidad probada para cien personas.[2]
5. **La web puede plantearse sin servidor doméstico.** Cloudflare Pages es un candidato para frontend y catálogo; sus assets estáticos tienen solicitudes gratuitas e ilimitadas, separadas de las funciones dinámicas.[16] Aún no hay cuentas ni despliegue.

## Recomendación concreta

- Base propia ligera, tomando patrones de los repos anteriores y revisando la licencia de cualquier código copiado.
- Pai, perfil editable, catálogo real verificado, comparación y escenarios como recorrido principal.
- Cálculos deterministas; IA para conversación y explicación, sin inventar condiciones.
- Comparador y simuladores independientes de la disponibilidad del chat.
- Contratación ficticia claramente señalizada, sin pagos ni identificadores bancarios reales.
- Antes de fijar modelo: prueba con contexto realista, consumo, calidad en español, límites y fallback explícito.

No se han reducido unilateralmente los requisitos: productos reales no se sustituyen por un catálogo totalmente inventado y la IA no se reemplaza definitivamente por FAQ.

## Qué queda abierto

Selección final del catálogo y permisos de fuentes; proveedor/modelo real y su presupuesto gratuito; prueba operativa para cien usuarios; revisión del encaje de las recomendaciones personalizadas; implementación y despliegue. La investigación no certifica rendimiento ni cumplimiento jurídico.

Ver [00-SINTESIS.md](00-SINTESIS.md) para el contraste y [README.md](README.md) para los diez informes.

## Sources

[1] https://ai.google.dev/gemini-api/terms
[2] https://developers.cloudflare.com/workers-ai/platform/pricing
[4] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/README.md
[5] https://raw.githubusercontent.com/violettance/etf-dashboard/main/README.md
[6] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/README.md
[7] https://modelcontextprotocol.io/introduction
[14] https://app.bde.es/bierest/resources/srdatosapp/favoritas?idioma=es&series=DN_1TI2T0026
[15] https://data-api.ecb.europa.eu/service/data/MIR/M.ES.B.L22.A.R.A.2250.EUR.N?lastNObservations=1&format=csvdata
[16] https://developers.cloudflare.com/pages/functions/pricing
[19] https://query1.finance.yahoo.com/v8/finance/chart/VWCE.DE?range=5d&interval=1d
