# Pai — continuidad y pendientes, sin perder lo construido

## Actualización tras la misión de 4 h 30 min (4/11/2026)

La trazabilidad de las condiciones ya no se pierde en el camino: el registro de fuentes resuelve los ids del snapshot a URL con título y fecha, la ficha y el ensayo muestran esa fuente y el chat la enlaza. Un id sin resolver deja la condición en «desconocida» en lugar de publicar la cifra.

La prueba real de la rúbrica (diez preguntas ficticias, 15 intentos de 100, sin perfil) deja tres conclusiones que condicionan el siguiente paso: (1) el motor determinista responde bien y con supuestos visibles; (2) el filtro léxico suprime respuestas legítimas que mencionan cifras, fuentes oficiales o vigencia —cinco de diez— así que no basta con ajustar el proveedor: hay que decidir el criterio de supresión; (3) un turno de catálogo sin resultados ya no borra la explicación conceptual, pero la ausencia de fichas locales sigue impidiendo atribuir datos. No se presenta a Pai como asesor financiero validado y la muestra no permite inferir una tasa de error.

Pendiente inmediato, por orden: decidir el criterio de supresión con ejemplos revisados (falsos positivos documentados), completar la evaluación con proveedor y datos ficticios cuando el criterio esté aprobado, y solo después plantear publicación. El contador global (`mission_ledger.py`) queda disponible para la próxima ventana con cupo: se provisiona con `scripts/provision_mission.py` y se retira con `--close`.

## Cierre de correcciones QA, 3/11/2026

[Correcciones locales aprobadas independientemente](correcciones-qa-20261103T172201/RESULTADOS.md): informe HTML autónomo guardado desde Hermes y leído en disco; wrapping móvil, horizontes comparativos y aviso temporal de Biblioteca. No se construyó ni habilitó Pai, ni se envió perfil/informe/escenarios a proveedores. No hay nuevas fórmulas, persistencia automática ni despliegue. Impresión nativa/PDF y adjunto del chat no certificados. Se conserva el orden de construcción de Pai descrito abajo; este cierre no autoriza iniciarlo ni convierte las propuestas de comparación de producto en un encargo activo.

## Actualización tras diagnóstico móvil C

El diagnóstico autorizado por `docs/GOAL-DIAGNOSTICO-MOVIL-C-20261103.md` terminó con dictamen independiente favorable de C: `docs/diagnostico-movil-C/20261103T121105/independiente/REVISION-COMPLETA.json`. Los recorridos A/B conservan aprobación previa y C añade la verificación móvil independiente y la matriz de navegación/filtros que faltaban. No hubo cambios en producción ni en el test, ni ensamblaje adicional de Pai. La nueva evidencia supera el bloqueo de aceptación de mañana, sin reescribirlo ni resetear ciclos de corrección.

La siguiente tarea de Pai sigue siendo el ensamblaje estructurado desactivado del punto 1, con transporte existente instrumentado sin red y sus fronteras intactas, en un encargo separado. No habilitar llamadas reales ni enviar automáticamente perfil, escenarios o informe por tener A/B/C aprobados. Guion actual: `docs/diagnostico-movil-C/20261103T121105/GUIA-DEMO.md`.


## Construido y que se debe conservar

Según el resultado de la misión `docs/ia-groq-estructurada/ejecuciones/20261102T233227/RESULTADOS.md`:

- Backend HTTP sin dependencia obligatoria de Tkinter.
- Frontera de procedencia cerrada: etiqueta test_only por sí sola no acredita ausencia de red; éxitos/errores no deben mentir sobre envío.
- Sesión temporal, consentimiento específico de chat, admisión/cola, singleflight, cuota persistente, plazo, revocación y estados not_started/unknown/completed. Las misiones antiguas están caducadas y no se reutilizan.
- Constructor estructurado candidato, parser puro de ChatResult y selección cerrada de IDs; rechazo de texto libre, duplicados, IDs inventados, refusal, truncado y herramientas.
- Textos educativos locales y motor determinista con supuestos explícitos del mismo turno; escenario local no añadido automáticamente al cuerpo remoto.
- Recorrido sintético contado conectado, sin envolver su resultado en FakeChatProvider; guardas tras admisión y pruebas de sustitución de proveedor/método/modo/misión.
- Runner persistente que recoge unittest y funciones pytest, resultados por fase y exclusiones GUI exactas; no es sandbox de procesos hijos.
- Históricamente hubo conectividad y turnos reales de Groq; no demuestran esta integración nueva, calidad sistemática, contexto o robustez.

Referencia histórica reciente:404Python/40Node/19HTTP con6GUIexcluidas; no presentarlo como prueba nueva ni cobertura completa. Pruebas sintéticas no certifican el proveedor.

## Siguiente construcción de Pai (orden)

1. **Ensamblaje real estructurado, desactivado:** unir constructor/parser/render con fachada contada y misión obligatoria, sin modos elegibles por cliente ni falsear metadatos. Probar el transporte HTTPS real del código con HTTPSConnection instrumentada sin red, no otra capa post falsa aislada. Mantener todos los controles existentes.
2. **Prueba real breve autorizada:** misión nueva válida y límite, confirmación humana de Free y clave voluntaria en ventana segura. Sin claves en chat/archivos/logs/entorno global ni perfiles reales. Confirmación no verifica facturación. No reintentos ocultos.
3. **Calidad y utilidad:** evaluar respuestas en español, relevancia de selección editorial, límites financieros, truncamientos, errores y explicaciones. ValidezJSON no prueba verdad financiera; filtro léxico no es verificador semántico. Conectividad no es producto terminado.
4. **Contexto e historial:** comparación con datos sintéticos de alternativas de contexto y exposición, consentimiento remoto separado y selección explícita. No enviar el perfil local automáticamente ni suponer autorización por guardarlo.
5. **Integración de producto:** Pai explica cálculos y comparaciones del servidor sin fabricar resultados, condiciones, fuentes o encaje profesional. Biblioteca y simuladores deben funcionar aunque la IA falle. Uso real depende también de catálogo verificado, alojamiento y capacidad.

## Límites todavía abiertos

Ruta estructurada real no ensamblada/habilitada/validada; calidad/contexto reales pendientes. Catálogo: candidatos no equivalen a condiciones cuantitativas vigentes y autorizadas. Hosting, carga y publicación pendientes. Control arbitrario del proceso Python no está aislado por la app ni por sus guardas de pruebas; no gastar ciclos indefinidos intentando prometer ese sandbox.

## Actualización de continuidad — B4 y B5

B9 tiene revisión local favorable acotada; queda el desplazamiento horizontal residual en escritorio a 320 px y la comprobación con lector de pantalla y dispositivo físico. No está publicado. Evidencia `robustez-accesibilidad/REVISION-CICLO-2.md`.

B1 sigue pendiente de calidad y evaluación real: el historial solo está verificado con proveedor sintético y el filtro no cubre todas las recomendaciones ni afirmaciones de riesgo. Rúbrica preparada pero no ejecutada (`pai-calidad/RUBRICA-DIEZ-PREGUNTAS.md`); ver también `pai-calidad/REVISION-FILTRO-Y-ERRORES.md`. No reabrir B4 dentro de esta misión.

Los avisos de error recibieron revisión favorable limitada a cuatro defectos (`pai-calidad/REVISION-ERRORES-CICLO-2.md`); queda una observación sin reproducir sobre volver al texto idéntico durante una petición. Eso no aprueba el conjunto de B1.

B4 está detenido y no aceptado tras dos ciclos y revisión independiente desfavorable (`pai-catalogo-20261103/REVISION-CICLO-2.md`); no abrir un tercero en esta misión. B6 está detenido tras dos ciclos y dictamen desfavorable (`informe-b6/REVISION-CICLO-2.md`).
B8 (privacidad y capacidad del chat) quedó aceptado el 4/11/2026 con revisión independiente favorable; evidencia en `privacidad-capacidad/EVIDENCIA.md`. Falta decidir si se publica, porque la web pública conserva la versión anterior. B5 solo está acreditado para Openbank: el mismo dictamen halló condiciones falsamente ausentes para ACC-01. Ninguno de estos cambios se ha desplegado. Continuar únicamente con trabajo independiente que no dependa de B6, sin rediseño. Los apartados anteriores y posteriores conservan su contexto histórico.

## Prioridad actual del equipo (histórica)

Ejecución de `docs/GOAL-PENDIENTES-20261103.md` (sin diseño). Cerrados B0, B1.1-B1.2, B2 y B3. El catálogo ya tiene condiciones con fuente y fecha, la biblioteca y la ficha las muestran con su estado, y el comparador compara TAE a 12 meses entre EBN (3,10 %) y Self Bank (2,75 %), con salto a Escenarios desde cada ficha. Siguiente en el orden: **B7 (publicación)**, bloqueado hasta que el equipo decida visibilidad y licencia del repositorio y la cuenta de hosting. De Pai quedan historial, filtro de calidad, errores reales y rúbrica (B1.3-B1.6), y la decisión sobre el catálogo por el modelo (B4).

El plan siguiente impide olvidar Pai, pero no autoriza llamadas reales fuera de las ya configuradas ni adelanta su trabajo por encima de esas entregas. Al cierre de cada bloque actualizar solo lo realmente avanzado, con evidencias y próximo paso concreto; conservar los informes históricos.

## Revisión funcional de mañana, 3 de noviembre

Nuevo tramo documentado en `docs/GOAL-REVISION-MANANA-20261103.md`; resultados en `docs/revision-manana-20261103/RESULTADOS.md`. A/B conservan aprobación previa y pasan nueva regresión navegador escritorio/móvil. C sigue **no aprobado**: corrección ciclo2 pasa al coordinador y los probes independientes, pero la revisión móvil independiente queda sin resultado por dos timeouts; no se hace un tercer ciclo automático. No se ha construido ni habilitado integración adicional de Pai. La inferencia Qwen local usada para auditoría de código es una herramienta de desarrollo, no la IA de Paideia ni una prueba de su calidad. El siguiente ensamblaje de Pai permanece en el punto1 y condicionado a un encargo separado; no queda autorizado por cerrar documentación.

## Entrega funcional de la noche del 3 de noviembre

Se han construido dos escenarios editables con resultados, gráficos y tablas del motor local; informe imprimible desde una comparación vigente; ayudas educativas compartidas con el glosario y diagnóstico explícito de comparabilidad por depósito. Son funciones independientes de la IA. Evidencia, incidencias y dictámenes en `docs/noche-funcional/20261103T003723/`; consultar el resultado final de esa ejecución antes de dar todos los hitos por aceptados. No se han añadido productos cuantitativos aprobados ni publicado la aplicación.

No se ha construido ni activado otro ensamblaje de Pai esta noche: se priorizaron las funciones solicitadas y el cierre ante el margen de cuota comunicado. Se conservan las capas y fronteras enumeradas arriba. El próximo trabajo de Pai es el punto1, en un encargo separado: un único recorrido que conecte el constructor estructurado existente, la fachada contada con misión, el transporte HTTPS existente instrumentado sin sockets externos y el parser/render. Debe probar revocación y corte durante admisión/envío, consumo durable sin reintentos ocultos y metadatos veraces de envío. No basta otro wrapper fake ni se habilita el proveedor real por pasar esos tests.

Contexto futuro: no transmitir automáticamente el snapshot de escenarios, el informe ni el perfil. Acordar una proyección mínima y autorización remota explícita antes de conectar estas funciones con Pai. La prueba real breve, la calidad financiera, el historial, el catálogo verificable y el alojamiento siguen siendo tareas distintas. No reabrir las misiones antiguas.

