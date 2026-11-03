# Paideia — noche funcional hasta las 08:00

## Prioridad y activación

Este encargo **sustituye el orden del borrador GOAL-NOCHE-20261103.md**. El equipo ha confirmado: escenarios y comparación visual → informe descargable/imprimible → biblioteca/comparador y explicaciones. Pai se conserva y mantiene un plan pendiente, pero no monopoliza la noche. Las pruebas respaldan entregas, no son el producto.

Preparar este archivo no activa /goal ni procesos. Al recibir orden de ejecución, consulta el reloj y registra inicio/corte en un directorio nuevo bajo docs. Corte inmutable: **2026-11-03T08:00:00+01:00**. Reserva desde07:40 para regresión, informe y cierre; no ampliar por reinicios, notificaciones, delegaciones o espera humana. Si ya venció, no iniciar. Terminar antes por hitos viables logrados, bloqueo humano, límite de uso o dos ciclos de revisión fallidos por bloqueo. No llenar horas artificialmente. Requiere equipo despierto, Hermes abierto y conexión; los límites de turnos/uso pueden detenerlo antes.

## Estado y ámbito que conservar

Raíz C:/Users/aleja/Downloads/App Financiera/; app prototipos/paideia-local/; solo perfil Hermes trabajos. Leer docs/REQUISITOS.md, docs/PLAN-PAI-PENDIENTES.md y docs/ia-groq-estructurada/ejecuciones/20261102T233227/RESULTADOS.md. Contrastar con el código, sin reconstruir lo existente. La misión previa terminó y su corte00:32:27 no se reabre.

Base histórica reciente:404Python(375unittest+29otrosnodospytest),6GUIexcluidos,40Node,19HTTPloopback; no contarlos como ejecución nueva. Ya existen motor financiero determinista, perfil local, candidatos de catálogo, simulación y recorrido estructurado sintético. Backend sinTkobligatorio y procedencia cerrada revisados; no hay ensamblaje estructuradoHTTPS/Groqreal ni calidad del modelo validada. Diseño final pospuesto: se permiten mejoras funcionales de organización/legibilidad/accesibilidad, no un rediseño estético global.

## Arranque acotado

En los primeros20minutos inspeccionar domain.calculate_scenario, API/api/calculate, pantallas de escenarios, gráficos, comparaciones e impresión. Definir diferencias concretas que falten respecto a A/B/C y empezar una rebanada utilizable. Si algo ya cumple aceptación, no reconstruirlo ni contarlo como función nueva. No cambiar el motor correcto para ajustar un gráfico. Mantener cero/desconocido/omitido/no preguntado.

## A — comparación de escenarios completa (principal)

Completar un recorrido sin IA ni claves que permita:

- Introducir/editar capital, aportación mensual, plazo, tasa hipotética, interés simple/compuesto e inflación con supuestos explícitos y validación comprensible.
- Comparar al menos dos escenarios editables. Evitar mostrar resultados de entradas anteriores durante edición/peticiones pendientes: invalidación, estado pendiente y coincidencia de supuestos verificable.
- Gráfico de evolución y tabla accesible alimentados por el resultado/serie del motor existente del servidor, sin fórmulas alternativas de JavaScript. Unidades y aportaciones claras; nominal/real ajustado por inflación si el motor lo soporta. Métrica nueva exige TDD del motor o no se muestra.
- Mostrar ceros, pérdidas y tasas negativas válidas sin ocultarlas. Aclarar periodicidad de aportaciones y costes/impuestos excluidos. No prometer rentabilidad ni convertir tasa manual en oferta real.
- Funcionar en escritorio y móvil sin necesitar perfil guardado o procesamiento remoto.

Aceptación: navegador loopback aislado crea dos escenarios, edita uno y comprueba tabla/gráfico/resumen contra el motor, incluyendo edición mientras una respuesta está pendiente y error sin pérdida indebida del otro escenario. Evidencia del recorrido real, tests y revisión independiente. Un helper aislado o gráfico con datos inventados no cumple.

## B — resumen descargable o imprimible (segunda prioridad)

Desde A, botón para obtener informe con escenarios, supuestos, resultados, diferencias, unidades, fecha de generación y advertencias. Fuentes solo si existen; generación del informe no equivale a vigencia de una oferta. No exportar el perfil completo ni datos innecesarios, solo información de esa comparación mostrada/seleccionada explícitamente. Sin identificadores, credenciales ni envío comercial.

Usar capacidades instaladas y cargar skill del formato que corresponda. Si solo se implementa impresión/guardar comoPDF del navegador, etiquetarlo así: no afirmar descargaPDFautomática. Si se genera archivo, abrir y comprobar contenido. Revisar saltos de página y legibilidad, sin menús invadiendo documento. No exportar resultados obsoletos respecto a entradas ni mezclar gráfico/tabla de versiones distintas.

Aceptación: obtener un informe utilizable desde el recorrido de comparación, con cifras y supuestos exactos, prueba tras edición y de falta/error de resultado, sin fuga de perfil. Declarar si solo se comprobó CSS/vista de impresión y no el diálogo o guardado físico.

## C — biblioteca/comparador y ayuda contextual (tercera prioridad)

Después de A/B, o tarea independiente si uno se bloquea:

- Completar filtros/fichas de candidatos existentes con estados claros: desconocido, histórico, contradictorio o no verificado; fuentes y fechas reales cuando existan. No inventar tasas actuales.
- Explicar por qué una comparación cuantitativa está bloqueada; permitir comparación legítima de características sin ranking inventado ni confundir métricas/familias.
- Conectar definiciones locales de TAE/TIN, liquidez, riesgo, inflación e interés compuesto desde sus pantallas. Contenido educativo, no asesoramiento profesional ni necesidad de LLM.
- Si hace falta reconciliar evidencia local, Openbank/YieldMeister6vs12meses permanece contradictorio/en cuarentena hasta resolverlo con evidencia. No inventar TTL/permisos ni igualar display con app_display. No buscar datos masivamente sin entregar funcionalidad.

Aceptación: usuario filtra, abre ficha y entiende una comparación bloqueada o una definición en la aplicación real. Pruebas y revisión; candidatos investigados no son ofertas cuantitativas aprobadas.

## D — demo y continuidad de Pai

Guion corto para Alejandro/JoséManuel: arrancar, crear comparación, modificar supuestos, interpretar gráfico y obtener informe; límites visibles. No fingir IA ni datos aprobados. Instrucciones para personas no técnicas.

Actualizar docs/PLAN-PAI-PENDIENTES.md: preservar todo lo construido y concretar próximos pasos. Solo si A/B/C están completos y revisados y sobra tiempo suficiente, elegir una integración genuina y acotada hacia Pai estructurada, desactivada, con conexiónHTTPSinstrumentada y sin red externa; no más capasfakeaisladas. No reabrir misiones antiguas ni aflojar consentimiento, admisión, cuota durable, revocación, plazo, singleflight, parser o metadatos. Si no es viable, dejar bloqueo preciso y siguiente tarea. La conexión real, evaluación de calidad, contexto y consentimiento remoto siguen pendientes separados.

## Pruebas y revisión al servicio de entregas

TDD RED→GREEN por comportamiento, tests de motor/contratos/API y navegador según hito. Contexto independiente revisa funcionalidad y fronteras; archivos exclusivos por agente, contratos compartidos coordinados. Máximo2ciclosporbloqueo, sin resetear límite con otro agente/nombre. Si persiste, mantener afectado desactivado y pasar solo a tarea independiente o cerrar. No perseguir sandbox contra código con control arbitrario de Python: declarar límites, no prometer invulnerabilidad.

Base inicial acotada, pruebas decisivas por hito y regresión final tras cambios; no repetir suites completas sin cambios relevantes ni consumir la noche en checks. Usar scripts/run_offline_regression.py con pytestya instalado; intérprete comprobado C:/Users/aleja/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe, verificar/no instalar. Recoger funcionespytestyunittest,6exclusionesGUIexactas,estadosporfase y fallos reales. Guardas en proceso no son sandbox heredado por hijos: auditar subprocesos propios.

Guardar evidencia RED/GREEN, screenshots propios sintéticos y artefactos en directorio nuevo del proyecto, no solo scratch. Contar resultados en código. Conservar fallos previos. Cerrar servidores/hilos propios en finally y comprobar endpoints; no parar servicios ajenos. Registrar hora real de cierre incluso si excede corte. No dejar servidor expuesto.

## Privacidad, restricciones y permisos

Permite código propio del proyecto/perfiltrabajos, fixtures/ledgers sintéticos efímeros y navegador/servidores loopback aislados. Sin llamadas reales de la app a Groq/otrosproveedores,clavesreales,datospersonales,lecturadesecretosdeentorno/portapapeles/memoriaajena,ventanasTk/credenciales,cuentas,pagos,instalaciones,códigodescargado,DBnuevas,despliegues,auth/WAFbypass,Gitinit/commits. Presupuesto0€. No resetear ledger ni ampliar misionescaducadas.

Perfil local: recuperar copia tras recarga no reactiva autoguardado; casilla sola no escribe, Guardar explícito sí. No borrar/migrar datos reales del navegador del equipo para probar. Permiso local no es permiso de envío remoto.

Una futura prueba real requiere autorización concreta, misión nueva vigente, confirmación humanaFree y clave voluntaria por ventana segura; checkbox no verifica facturación. No se necesita intervención para A/B/C.

## Entrega y finalización

Cada hito completo exige función integrada utilizable, pruebas ejecutadas y revisión favorable. Informe final: qué puede hacer el usuario mañana que antes no podía, archivos/informe producido, guiondemo, pruebas, limitaciones y próximos pasosPai. No medir avance funcional por aumento de tests. Actualizar estado general sin reescribir informes históricos. Separar completo/parcial/bloqueado/norealizado. No afirmar Paideia final, publicación ni IArealvalidada.

Parar por entregasviableslogradas,bloqueo,usooalas08:00+01. Terminar con Siguiente paso y Qué tenéis que hacer; decir si no requiere intervención.
