# Paideia — requisitos en definición

Este documento recoge decisiones del grupo y distingue propuestas y asuntos pendientes. No constituye una especificación técnica cerrada ni acredita funcionalidades implementadas.

## Contexto y entrega

- Equipo: Alejandro y José Manuel, estudiantes de tercero de Finanzas y Contabilidad de la UMA.
- Entrega/demo confirmada por el grupo: martes 3 de noviembre de 2026. Hora pendiente; no bloquea el trabajo preparatorio.
- Alejandro utiliza Hermes; José Manuel no tiene conocimientos técnicos.
- Presupuesto: gratuito. Pueden crear cuentas para los servicios necesarios. No se ha confirmado si aceptarían verificaciones con tarjeta.
- Entrega indicada en IDEA.md: web accesible online, enlace en Wiki del Campus Virtual, archivos fuente HTML/CSS/JS y diario de desarrollo en Moodle; demo presencial. Límite de entrega indicado: 1 GB.
- Se quiere publicar el código en GitHub como open source. Repositorio, titularidad y licencia pendientes.
- Prioridad expresada: sorprender a la clase y demostrar capacidad de creación de aplicaciones.

## Público y experiencia

- Personas mayores de edad sin formación financiera o con conocimientos básicos que quieren aprender.
- Mercado de referencia: España; idioma inicial: español; moneda de referencia: euro.
- Web adaptable a ordenador y móvil; no se solicita una aplicación móvil nativa.
- Nombre: Paideia. Mascota: Pai, un pequeño triángulo. Estilo general: moderno; dirección visual concreta pendiente.
- El grupo rechaza el diseño visual del prototipo actual. No está aprobado como identidad visual final. Prioridad vigente: backend y funcionamiento primero; rediseño al final. Mantener la interfaz actual solo como herramienta de prueba, sin dedicar esta fase a retoques estéticos.
- Inicio mediante conversación breve con botones, preguntas de una en una y resumen editable del perfil; después chat libre.
- Incluir «no lo sé» y «omitir». Si falta información relevante, pedirla o explicar qué falta y cómo limita la orientación. Nunca inventar un perfil.
- El chat puede concluir que conviene ahorrar un colchón, reducir deuda o no invertir todavía; no debe empujar siempre a un producto.

## Perfil

- Separar conocimientos y experiencia, tolerancia al riesgo y capacidad económica de asumir pérdidas.
- Considerar ingresos, gastos mensuales, situación personal y financiera, compromisos, activos/deudas, objetivo, horizonte y necesidad de liquidez. Campos y reglas exactos pendientes.
- El interés por alto riesgo no basta por sí solo para considerar que un producto encaja.
- No presentar la aplicación como asesor profesional autorizado porque el usuario demuestre conocimientos. El encaje normativo y el lenguaje de las salidas requieren revisión antes de publicar.

## Productos y datos

- Biblioteca amplia con información rápida; detalle y datos verificados al comparar o cuando el usuario lo solicite.
- Se quieren productos específicos de entidades reales, no solo categorías.
- Aspiración del grupo: cubrir «el 90% de los más populares». No es todavía un requisito medible: faltan universo, criterio de popularidad y fuentes.
- Familias iniciales aprobadas: cuentas remuneradas, depósitos, letras/deuda pública, fondos y ETF.
- Objetivo inicial aprobado: 20 productos reales, cuatro por familia, condicionado a datos y usos verificados. Es un primer hito, no un techo: el grupo insiste en ampliar el catálogo; cada incorporación pasa los mismos controles de identidad, condiciones, frescura y permisos.
- Se desea actualización diaria mediante API o MCP. Las rondas de investigación han identificado y probado descargas/endpoints concretos, pero no una fuente gratuita que cubra todas las condiciones, familias y derechos requeridos. Véanse `investigacion-apis-02/00-SINTESIS.md` y `ESTADO_Y_PLAN.md`; los candidatos aún no están integrados.
- Fuentes, fecha de consulta, fecha efectiva del dato, disponibilidad y condiciones deben ser explícitas. Una conexión técnica no demuestra actualidad o cobertura.
- Se aprueba una simulación de contratación dentro de Paideia. No debe ejecutar operaciones reales. La operación y los importes de ejemplo serán ficticios; los hechos del producto real seleccionado conservarán fuente, fecha y estado. No solicitar credenciales bancarias, documentos de identidad ni pagos; el flujo deberá indicar explícitamente que es una simulación.
- Si falla la actualización diaria, se acepta mostrar el último dato verificado con fecha, fuente y advertencia. Excluir de las comparaciones los datos cuya antigüedad pueda volverlas engañosas; el criterio de caducidad por tipo de dato está pendiente de definición.

## Funciones solicitadas

- Chat con LLM y perfil contextual.
- Biblioteca de productos y comparador.
- Simuladores de interés simple y compuesto.
- Gráficos de escenarios.
- Glosario.
- PDF descargable opcional.
- La distribución de decisiones entre LLM y reglas financieras requiere concreción; el grupo desea tanto interpretación y explicación como recomendaciones con controles.

## Privacidad y operación

- Aceptada la propuesta de uso sin registro, perfil local en el navegador y botón para borrarlo.
- No solicitar nombre real, DNI, credenciales bancarias ni otros identificadores innecesarios.
- Si se usa IA externa, informar de los datos transmitidos y revisar las condiciones del proveedor. Almacenamiento local y procesamiento externo son cuestiones distintas.
- El grupo acepta en principio el envío de cifras económicas seleccionadas, pero exige comparar antes calidad, utilidad, coste y exposición frente a enviar el perfil completo. No se ha aprobado como opción definitiva el resumen ni el perfil completo. Pruebas comparativas con perfiles sintéticos; revisión del proveedor y selección/consentimiento del usuario final antes de datos reales. No implica autorización para transmitir perfiles ahora.
- Dimensionar pruebas para hasta 100 usuarios concurrentes como peor caso. Capacidad real no comprobada. El grupo acepta cupo y cola visibles del chat real, con biblioteca/comparador/simuladores independientes; no exige prometer 100 respuestas IA simultáneas.
- La web debe funcionar aunque los ordenadores del grupo estén apagados; no depender de un servidor doméstico para el servicio publicado.
- Proveedor LLM, alojamiento, límites, protección de claves, protección frente a abuso y alternativa ante fallos: pendientes de validar.

## Escena central de la demo

Un usuario compara alternativas y ve cómo cambian los escenarios con sus decisiones.

## Alcance inicial aprobado y criterios técnicos propuestos

- Aprobado por el grupo: dar prioridad a cuentas remuneradas, depósitos, letras/deuda pública, fondos y ETF para el comparador. Ampliaciones posteriores sujetas a viabilidad.
- Mostrar otras familias en la biblioteca con alcance y nivel de actualización explícitos.
- Calcular importes y escenarios mediante código y supuestos visibles; usar la IA para interpretar preguntas y explicar resultados sin inventar condiciones.
- Mostrar fecha y fuente por campo relevante; diferenciar tipos actuales de escenarios hipotéticos.

## Aprobación funcional y almacenamiento por validar

El grupo confirma las prioridades de completar el recorrido perfil → Pai → catálogo → comparación → cálculo → explicación, con IA real, perfil completo, datos verificables y funcionamiento online; diseño al final. Pregunta si PostgreSQL es necesario al utilizar APIs. **PostgreSQL no queda fijado como requisito**: se evaluará qué persistencia/caché hace falta y si una solución sin DB cubre integridad, actualización, consultas y fallos. La aprobación no autoriza por sí sola cuentas, pagos, instalaciones, despliegues ni transmisión de datos reales. Trabajo delegado y contratos en `funcionamiento-05/`.

## Validaciones y definiciones aún necesarias

1. Fuentes de datos por familia, permisos de uso, cobertura y posibilidad real de actualización diaria gratuita.
2. Proveedor de IA y alojamiento gratuitos; cuotas, privacidad, protección frente a abuso y prueba de capacidad para el peor caso de 100 usuarios concurrentes.
3. Reglas de caducidad de datos y de elegibilidad para comparación.
4. Diseño detallado del flujo de simulación y sus límites; sin operaciones ni documentación personal reales.
5. Criterios financieros del perfil y lenguaje de orientación educativa; no atribuir habilitación profesional al sistema.

## Material pendiente

- Ejemplos de trabajos de compañeros ofrecidos por Alejandro.
- Posibles aclaraciones de la profesora sobre GitHub, alojamiento, criterios de evaluación y formato del diario.
