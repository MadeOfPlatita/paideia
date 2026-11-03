# Paideia frente a herramientas similares — brechas de producto y acabado

Fecha de consulta: 3 de noviembre de 2026. Referencias: páginas públicas de Finanzas para Todos, Investor.gov, Finect y justETF. Es una comparación de recorridos y capacidades documentadas, no una auditoría de cuentas, planes de pago ni calidad financiera de esos servicios. No se contrataron cuentas ni se ejecutaron inversiones.

**Base local:** demo utilizada por Alejandro y QA exploratoria en `../qa-usuarios-20261103T165536/INFORME-QA.md`. Las correcciones de guardado, móvil y claridad están en curso en `../correcciones-qa-20261103T172201/`; no se cuentan aquí como aceptadas antes de la verificación. Este análisis no autoriza cambios adicionales ni un rediseño general.

## Diagnóstico
Mi valoración: Paideia ya dispone de piezas útiles, pero todavía presenta demasiado la estructura interna del prototipo y poco el recorrido de una persona. La diferencia principal no es añadir más calculadoras o botones. Es ayudar al usuario a entender por dónde empezar, qué dato necesita, cómo interpretar un resultado, qué hacer después y cómo conservarlo.

Hay además una brecha funcional de datos: un catálogo de candidatos con condiciones pendientes no ofrece lo mismo que un comparador alimentado con información de productos. Esa distancia no se arregla con colores, una gráfica inventada o más filas vacías. No se deben rellenar comisiones, rentabilidades o riesgos sin fuente, identidad, vigencia y permisos.

Las pruebas ejecutadas respaldan comportamientos concretos; no demuestran que todo el producto resulte intuitivo. La QA de uso real encontró precisamente huecos en guardado, móvil y contexto de comparación. No tomo sus recuentos como medida de avance de producto.

## Referencias y qué aprender de cada una

| Referencia | Capacidad observada o documentada | Qué enseña para Paideia |
|---|---|---|
| Finanzas para Todos — Mis objetivos | Empieza preguntando el objetivo, importe necesario, ahorro inicial y plazo. La propia herramienta aclara su carácter didáctico y que no incluye inflación.[1] | Empezar por una necesidad reconocible, no por el nombre de un módulo. No copiar sus límites: Paideia ya distingue valor nominal y ajustado por inflación. |
| Investor.gov — Compound Interest Calculator | Divide el formulario en pasos y permite indicar un rango de variación de la tasa estimada.[2] | Ordenar la introducción de supuestos y hacer visible que variar una tasa cambia la hipótesis, no la certeza del resultado. |
| Finect — comparador de fondos | La página anuncia comparaciones guardadas, elección de clase y presenta productos con información de riesgo y gastos.[3] | Separar con claridad identidad, clase, características y consulta posterior. No confundir la presencia de datos allí con derecho a reutilizarlos aquí. |
| justETF — documentación del comparador | Describe selección desde resultados o ficha y comparación de rentabilidades por periodos definidos.[4] | Dar continuidad al recorrido buscar → seleccionar → comparar; aclarar fechas, periodos y significado de las columnas. |

No son equivalentes comerciales: un recurso educativo y un comparador de productos responden a necesidades distintas. Paideia puede tomar patrones de ambos sin intentar reproducir todos sus servicios.

## Qué falta o merece más acabado en Paideia

### 1. Una entrada que explique para qué sirve
**Observado:** hay navegación por Inicio, Tu mapa, Biblioteca, Comparar, Escenarios, Ensayo y Glosario. La demo muestra además estados técnicos y contexto ficticio del prototipo.

**Propuesta:** presentar tres tareas comprensibles: «Entender mis opciones», «Probar un plan de ahorro» y «Comparar candidatos». Un ejemplo breve que se pueda cargar sin responder un cuestionario. Mantener acceso libre sin perfil; Tu mapa ya existe y no debe reconstruirse.

**Criterio de acabado:** una persona nueva puede elegir su primera tarea sin necesitar que Alejandro le explique la arquitectura.

### 2. Conectar las piezas existentes
**Observado:** perfil, ayuda, simulación y biblioteca funcionan como módulos, pero todavía no forman de manera evidente un único recorrido educativo.

**Propuesta:** al terminar cada paso, una siguiente acción pertinente y opcional: consultar un concepto, ajustar una hipótesis o revisar características. No trasladar datos del perfil al modelo ni tasas de candidatos a simulaciones sin autorización y etiqueta explícita.

**Criterio:** el usuario entiende por qué navega al siguiente módulo y qué información se conserva.

### 3. Hacer más cómoda la edición de escenarios
Paideia ya tiene dos escenarios independientes, gráficos, tablas, tasa negativa, cero, inflación e invalidación de resultados antiguos. No faltan esas funciones.

**Propuesta de acabado:** nombres editables como «Aportar 50 €/mes», duplicar una hipótesis para cambiar una sola variable y restablecer ejemplos con una acción explícita. Antes de añadir un tercer escenario, hacer cómodo comparar dos.

**Criterio:** probar una alternativa no exige volver a escribir todo ni deja dudas sobre qué se cambió.

### 4. Interpretar resultados en lenguaje cotidiano
El resumen ya muestra aportaciones, saldo e inflación, pero la demo necesitó explicación humana para comparar plazos distintos.

**Propuesta:** un resumen breve generado a partir de campos ya calculados: «Este escenario usa X años y Y de aportaciones; el saldo nominal es Z». Mostrar qué supuestos difieren, y aclarar que no se trata del mismo instante si cambian los plazos. La corrección del aviso de plazos ya está autorizada; esta explicación ampliada sería una propuesta aparte.

No declarar «mejor inversión», no transformar una diferencia final en rentabilidad anual y no usar un LLM para inventar el resultado.

### 5. Comparación visual realmente conjunta
Hoy cada escenario tiene su gráfico y hay una tabla comparativa. Eso no equivale a una gráfica conjunta que facilite ver diferencias a lo largo del tiempo.

**Propuesta opcional:** una vista conjunta de las series devueltas por el motor, con leyenda, selector nominal/real y tratamiento explícito de horizontes distintos. Evitar colores sin etiquetas, escalas incompatibles o extrapolar el escenario corto. Antes de implementarla, comprobar si mejora una tarea real de comparación.

### 6. Un recorrido por objetivo, no solo por saldo futuro
Las preguntas orientadas a objetivos y plazos aparecen en la herramienta de Finanzas para Todos.[1] Paideia puede aprovechar ese enfoque educativo sin copiar cálculos no verificados.

**Propuesta nueva:** «Quiero llegar a una cantidad en un plazo: ¿qué hipótesis de aportación necesitaría?». El formulario actual de escenarios calcula el resultado de unas entradas; un recorrido inverso requiere especificación y pruebas del motor, no una fórmula rápida en JavaScript. Separarlo del acabado inmediato.

### 7. Poder terminar y retomar el trabajo
El problema real de guardado es la prioridad: no basta tener un informe correcto si el usuario no consigue conservarlo.

**Ya autorizado:** salida de archivo compatible, explicación de impresión desactivada en Hermes y separación entre HTML descargable y PDF por impresión.

**Propuesta posterior:** guardar/reabrir una comparación con nombre mediante una proyección mínima, con acción explícita y explicación del almacenamiento. Finect anuncia comparaciones guardadas como parte de su recorrido.[3] Eso no obliga a añadir cuentas ni persistencia automática a Paideia.

**Criterio:** conseguir un archivo real y poder reconocer con qué supuestos y versión se produjo; no anunciar éxito solo por lanzar la descarga o la impresión.

### 8. Más utilidad en las fichas, sin fabricar datos
Paideia ya distingue candidatos, condiciones pendientes y motivos de bloqueo. Esa honestidad debe conservarse.

**Propuesta:** organizar cada ficha alrededor de «qué es», «cómo se dispone del dinero», «qué riesgos y costes conocemos», «qué falta verificar», «fuente y fecha». Mostrar «desconocido» cuando corresponda, no rellenar huecos para parecer Finect o justETF. Añadir filtros de coste o riesgo solo cuando esos campos existan y sean comparables.

Los servicios observados muestran criterios y periodos de comparación de producto; obtener información equivalente y utilizable es un trabajo de datos, no un detalle decorativo.[3][4]

### 9. Coherencia de interacción y estados
**Observado en QA:** Inicio móvil desborda por cadenas de contexto, hay estado temporal que desaparece al recargar y el guardado no explica suficientemente lo que ocurre. Los tres asuntos ya están autorizados o identificados; no se necesita esperar a la IA.

**Propuesta:** mismo patrón para pendiente, error, resultado actualizado y acción no disponible; foco y teclado coherentes; botones que expliquen su alcance; advertencias importantes junto a la acción pertinente. La jerarquía visual debe distinguir «prototipo», «hipótesis» y «bloqueo» sin que todos los avisos compitan por atención.

### 10. Confianza y continuidad de Pai
La explicación educativa local y el motor ya son útiles sin IA. Pai no debe ocupar una posición que sugiera un acompañamiento conectado cuando no lo está.

**Propuesta:** explicar con precisión qué funciona ahora y qué aportará Pai después. Conservar el plan `../PLAN-PAI-PENDIENTES.md`: integración estructurada desactivada, calidad real, contexto y consentimiento siguen separados. No llenar el hueco con respuestas simuladas que parezcan reales.

## Orden recomendado

### Primero: terminar el recorrido que ya estamos probando
Guardado real y explicación del formato; Inicio móvil legible; plazos claros en el resumen; estado temporal explicado. Las correcciones ya están en marcha y requieren prueba desde el entorno real y revisión independiente.

### Después: una capa de acabado funcional
Entrada por tareas, ejemplo inicial, nombre/duplicado de escenarios y explicación corta del resultado. Guardado/reapertura explícitos si el equipo lo prioriza. No hace falta una cuenta, una DB o un proveedor real para especificar esa experiencia.

### Más adelante: ampliar el producto
Recorrido inverso por objetivo, catálogo verificable y comparaciones de producto con datos útiles, y Pai integrado con sus controles. Estas piezas sí pueden exigir nuevas pruebas matemáticas, derechos sobre datos o autorización de proveedor. No prometer que se resuelven con un retoque de interfaz.

## Qué no copiaría ahora
- Más ratios o filtros solo para llenar pantalla.
- Rentabilidades de páginas públicas pegadas sin verificar instrumento, fecha y permiso.
- Cuenta obligatoria para usar herramientas que pueden ser locales.
- Ranking de «mejor producto» con campos incompletos.
- Gráficas de mercado que en realidad representen tasas manuales.
- Una gran renovación estética antes de que guardar y completar la demo sea fiable.

## Límites de la investigación
Se consultaron páginas públicas, no se abrió cuenta ni se probó el servicio completo de cada competidor. Algunas extracciones contienen elipsis: solo se usan los apartados efectivamente recuperados. La página adicional de objetivo de ahorro de Investor.gov no expuso el formulario en la extracción y el navegador devolvió Access Denied; no se usó como evidencia funcional ni se intentó eludir la protección.[5] No se copiaron cifras de rentabilidad, precios, tasas fiscales o promesas de esos servicios.

Evidencia y procedencia: `retrieval.json`, `evidence-1.txt` a `evidence-4.txt` y ledger `sources.json`. Las citas describen al competidor; el diagnóstico y el orden de trabajo son recomendaciones propias basadas en la demo y QA local.

**Conclusión:** la prioridad no es que Paideia tenga tantas funciones como un portal financiero maduro. Es que una persona pueda entrar con una pregunta, recorrer dos o tres pasos claros, entender un resultado honesto y conservarlo sin ayuda. Hoy faltan detalles de continuidad y acabado, además de datos verificables para la parte de productos. Son problemas diferentes y conviene planificarlos por separado.

**Siguiente paso:** terminar las correcciones autorizadas y decidir una única siguiente rebanada de acabado funcional. Este documento no inicia nuevas implementaciones.

**Qué tenéis que hacer:** nada para completar la comparación; revisar después qué recorrido queréis priorizar, sin perder el plan de Pai ni las restricciones actuales.

## Sources

[1] https://www.finanzasparatodos.es/herramientas/mis-objetivos
[2] https://www.investor.gov/financial-tools-calculators/calculators/compound-interest-calculator
[3] https://www.finect.com/fondos-inversion/comparador
[4] https://justetf.com/en/tutorial/etf-search/compare-etfs-in-etf-screener.html
[5] https://www.investor.gov/financial-tools-calculators/calculators/calculadora-de-objetivo-de-ahorro
