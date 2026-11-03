# Evaluación de contexto de Pai — protocolo propuesto, no ejecutado

## Decisión del grupo y objetivo

El grupo acepta en principio cifras económicas seleccionadas, pero pide medir la diferencia frente al perfil completo antes de elegir. No hay autorización automática para enviar perfiles reales ni un ganador conocido. El martes 3 de noviembre de 2026 es la entrega confirmada; no convertir esta evaluación en una nueva ronda de investigación indefinida.

Separar dos fronteras: las consultas al catálogo/API de productos reciben filtros permitidos —familia, moneda, horizonte, liquidez, importe cuando sea necesario—, no el objeto de perfil completo. El contexto del proveedor LLM es una decisión independiente. No se ha demostrado que alguna API candidata exija recibir un perfil financiero completo; tampoco se ha medido la calidad con ninguno de estos modos.

## Comparación controlada

| Variante | Contexto añadido al mismo mensaje |
|---|---|
| A: sin perfil | Solo pregunta y mismas herramientas/datos de producto; referencia educativa genérica. |
| B: relevante | Proyección estructurada de campos pertinentes al turno, preservando su estado declarado/desconocido. Puede incluir cifras exactas seleccionadas cuando sean necesarias; no es obligatoriamente una etiqueta o resumen con pérdida. |
| C: completo | Todos los campos financieros y educativos del perfil sintético y sus estados; nunca nombre, DNI, banco, credenciales ni otros identificadores. |

Usar los mismos casos, instrucciones, modelo/versión, configuración, catálogo verificado, herramientas y techo de respuesta. Variar solo el contexto. Comparar primero dentro de cada proveedor: cambiar de modelo y de contexto a la vez no permite atribuir la diferencia al perfil. Registrar fechas y repetir casos decisivos si la cuota permite hacerlo; una sola salida no prueba superioridad.

La proyección B se construye mediante reglas explícitas por intención, no mediante otro LLM que añada coste o pierda silenciosamente información. Registrar qué campos se excluyeron y por qué. No convertir un dato omitido en supuesto.

## Casos exclusivamente sintéticos

1. Necesidad de todo el dinero a corto plazo: detectar restricciones de liquidez y no usar rentabilidades históricas como promesa.
2. Interés alto por riesgo, baja capacidad económica y gastos próximos: explicar el conflicto, no igualar tolerancia y capacidad.
3. Deuda con coste conocido y colchón insuficiente: no empujar siempre hacia productos; cálculos separados del modelo.
4. Ahorro de largo plazo con aportaciones: separar hipótesis, costes, inflación y hechos del producto; evitar confundir NAV con cotización.
5. Ingresos/gastos no declarados: pedir los datos relevantes o limitar la conclusión; nunca inferir capacidad de pérdida.
6. Condición comercial ausente o contradictoria: señalar incertidumbre y fuente; el perfil completo no autoriza inventar TAE, plazo o elegibilidad.

Cada caso tendrá entradas completas, selección de B, pregunta, hechos esperados y errores críticos definidos antes de solicitar respuestas. Usar catálogo real autorizado o fixtures marcadas explícitamente como sintéticas; no atribuir las fixtures a entidades reales. No preparar respuestas supuestamente generadas por una API.

## Métricas y ponderación inicial propuesta

Medir primero dimensiones separadas; estas ponderaciones son una hipótesis de trabajo, no preferencias aprobadas ni resultados:

| Dimensión | Peso propuesto | Qué observar |
|---|---:|---|
| Exactitud y trazabilidad | 40 % | Condiciones/cálculos respaldados, fuentes correctas, desconocidos reconocidos. |
| Utilidad contextual | 30 % | Reconoce objetivos, restricciones, conflictos y preguntas realmente necesarias. No se evalúa habilitación profesional. |
| Claridad didáctica | 10 % | Respuesta comprensible y ajustada al nivel declarado. |
| Consumo y operación | 10 % | Tokens medidos, llamadas incluidas tools, errores, latencia observada y cuota restante. |
| Minimización | 10 % | Campos transmitidos y necesidad por tarea, no solo bytes. Ausencia de identificadores no implica anonimato. |

**Puertas obligatorias, no compensables con puntos:** términos/privacidad y uso público aceptables, presupuesto 0 EUR, consentimiento/selección, herramientas acotadas y ninguna condición financiera inventada que altere la decisión del caso. No elegir una opción insegura porque sea barata o más personalizada. Si falla una puerta, el resultado queda rechazado o pendiente de revisión, no ganador por promedio.

Registrar respuestas reales y evaluación humana de Alejandro/José Manuel con rúbrica por caso; no usar exclusivamente al propio modelo como juez. Para valorar operación/minimización, fijar anclas de puntuación antes de calcular agregados; no inventar una nota a partir de impresiones. Publicar dimensiones, errores críticos y diferencias emparejadas, no solo una cifra final.

## Decisión posterior a la prueba

- Si B conserva lo necesario y obtiene calidad comparable con menos exposición/consumo, proponer B con evidencia.
- Si B pierde un dato material, ampliar la proyección de esa intención o pedirlo; no saltar directamente a enviar todo siempre.
- Si C mejora de forma material y repetida, documentar los campos responsables y ponderar el beneficio frente a exposición, términos y cuota. No activar C por defecto sin nueva decisión.
- Si ningún proveedor pasa las puertas, registrar bloqueo y alternativa; no afirmar que el chat está probado ni sustituirlo por respuestas prefabricadas.

**Estado:** protocolo definido; sin proveedor configurado, llamadas LLM, puntuaciones, resultados de latencia o ganador. La ejecución exige elegir/verificar el acceso gratuito y el tratamiento de datos, sin tarjeta, pago ni datos personales reales.
