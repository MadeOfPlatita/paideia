# Paideia — misión nocturna de calidad estructurada, exclusivamente offline

ESTADO: PREPARADA, NO ACTIVADA. Guardar este archivo no activa un /goal, cron ni proceso independiente. El usuario activará el comando. Autorizó el cambio de enfoque y fijó el cierre a las 08:00 de hoy, 30 de octubre de 2026, hora peninsular.

## Contrato de terminación

**Resultado:** entregar una implementación local probada de respuestas educativas estructuradas y renderizadas por el servidor desde contenido revisado, en vez de usar expresiones regulares para decidir si la prosa financiera generada es verdadera. Debe funcionar una sección vertical completa backend→HTTP→frontend con proveedores ficticios; no basta un schema, un helper, un plan ni una demo desconectada. La integración real con Groq queda pendiente, no autorizada esta noche.

**Verificación:** contratos completos de entrada/salida, tests negativos/adversariales, regresión Python y Node, sintaxis JS, HTTP y navegador contra proceso propio con el código nuevo cargado, y revisión independiente de los límites de confianza. Guardar comandos, salidas reales y una matriz de aceptación. No declarar acabado con una regresión conocida fallida.

**Paradas:** terminar antes si se cumplen los criterios; o bloquear con evidencia si faltan permisos, se necesitan instalaciones/cuentas/modelos reales, se agota el presupuesto de Hermes o fallan dos ciclos de corrección y revisión. Corte absoluto **2026-10-30T08:00:00+01:00**, equivalente a **2026-10-30T07:00:00+00:00**. No extenderlo al recibir una delegación, reiniciar el proceso, reanudar un goal o introducir una clave. Si al activar ya ha vencido, no ejecutar y comunicarlo. No esperar hasta el corte para dar por terminado trabajo ya completado.

## 1. Workspace y permisos

Raíz: C:/Users/aleja/Downloads/App Financiera. Aplicación: app. Perfil Hermes: trabajos, sin tocar otros perfiles. Prioridad funcionamiento/backend; sin rediseño visual.

Permitido: código propio local, pruebas y procesos loopback temporales, ficheros de documentación y evidencia dentro del proyecto; scratch únicamente bajo TMPDIR de Hermes. Mantener los datos de prueba sintéticos. No asumir Git: si no lo hay, revisión de archivos concretos, sin inicializarlo ni crear commits.

**Prohibido:** llamadas a Groq o a cualquier proveedor de IA del prototipo, modelos locales para fingir esas llamadas, ventanas de entrada de claves, reutilizar credenciales, leerlas de archivos/entorno/historial/clipboard/procesos; pagos, facturación, altas, despliegues, DB, instalaciones o ejecución de código descargado; publicación del catálogo, permisos nuevos de fuentes y perfiles personales remotos. No iniciar pruebas financieras de red ni investigación web general: usar el código y la evidencia ya disponibles. Los modelos y herramientas de Hermes necesarios para realizar el trabajo consumen el usage disponible; no prometer que ese presupuesto sea ilimitado o gratuito.

No cambiar configuración, modelo, límites de turnos o mecanismos de permisos de Hermes. No crear cron, daemons ni jobs persistentes. Delegación limitada: máximo dos trabajadores simultáneos, archivos exclusivos; preferir una implementación vertical y una revisión, no rondas masivas. No sondear resultados de hijos: atender sus entregas. Mantener ordenador y Hermes activos es requisito; /goal no ejecuta trabajo mientras el host duerme o está apagado.

## 2. Hechos que NO deben repetirse ni maquillarse

- La sesión de proveedor de 20261030T005810Z se cerró tras una respuesta real que afirmaba ahorro sin riesgo de perder capital. Su ledger consumió un intento. No restaurarlo ni editar manifiesto/diario/corte. La misión nocturna no es una nueva autorización de llamadas: su cupo de proveedor es CERO.
- Ya se reforzó y compartió el prompt y se construyó un guard léxico. No está aprobado: repetidos problemas de negaciones mostraron sus límites. No dedicar la noche a ampliar regex o a resolver solo la última coma.
- Última suite completa previa al nuevo contraejemplo: 256 Python,24 Node,19 HTTP. Después se añadió una regresión que falla: `No es posible tener deudas, ahorrar es sin riesgo.`. En test_financial_quality_known_gap.py se verificaron dos pruebas: una pasó y otra falló. No presentar aquel verde anterior como estado actual.
- Existen pruebas HTTP y navegador de rechazo502 sin publicar el texto problemático, y de conservación de una respuesta ficticia correcta. Son test_only, no calidad de un modelo.
- A/B/C no tiene ganador aprobado. Contexto e historial externos siguen desactivados; esta noche no se cierran esas fases reales ni el punto1 completo.

Lectura inicial mínima:
1. app/financial_quality.py y tests/test_financial_quality_known_gap.py.
2. docs/ia-real-siguiente/ejecucion/20261030T005810Z/quality-offline/EXPLICIT-FOLLOWUP-REVIEW.json y EXPLICIT-FOLLOWUP-BLOCKER.json.
3. backend_services.py, context_quality_benchmark.py y tests/test_financial_quality*.py.
4. pai_runtime.py/pai_tools.py, app.py y static/app.js solo en las secciones implicadas en la integración. Los contratos de privacidad existentes se conservan.

## 3. Nuevo límite de confianza: qué construir

### A. Contrato estructurado cerrado y validación servidor

Definir una proyección versionada con un esquema pequeño de temas/afirmaciones educativas registradas por el servidor. El proveedor ficticio puede seleccionar IDs permitidos y una intención acotada; no puede aportar texto financiero arbitrario que llegue a la UI como contenido revisado. Validar tipo completo, campos obligatorios, ausencia de adicionales, límites, cardinalidad, duplicados e IDs desconocidos. No convertir un booleano de «seguro» emitido por el modelo en garantía de veracidad.

La redacción de las afirmaciones sensibles se selecciona de contenido local revisado en esta misión, con procedencia editorial y limitaciones explícitas. Empezar con pocos temas: ahorro frente a inversión, riesgos nominales/custodia/entidad, inflación y poder adquisitivo, garantías condicionadas y límites de una simulación. No inventar ofertas, fuentes, umbrales legales ni aval profesional. No decir «revisado por un profesor/regulador»: eso no se ha hecho. Si no hay base suficiente para una afirmación, omitirla o responder de forma explícita que no se dispone de contenido validado para ella.

Rechazar texto libre, IDs y datos de procedencia que pretendan saltarse el contrato. No «aprobar» a partir de ausencia de una regex. Una explicación generativa adicional no puede reintroducir las mismas promesas: no mostrar prosa financiera libre no validada en la modalidad nueva. Si se conserva prosa experimental, mantenerla desactivada y fuera de la salida revisada.

### B. Cálculos y evidencia pertenecen al servidor

Conservar motor determinista, decimales y sus tests. Un resultado o referencia numérica debe proceder de una ejecución real de la herramienta local de ese turno y quedar vinculado por el servidor. El cliente o el proveedor no pueden fabricar un saldo, un éxito de herramienta, un ID de evidencia o la afirmación de que se calculó algo. Sin resultado válido, no mostrar números como verificados. No ampliar tools de catálogo ni permisos por añadir temas educativos.

### C. Integración y procedencia visibles

Implementar una modalidad experimental controlada por el servidor y un recorrido web completo. Compatibilidad del formato de petición y consentimiento existente; separar de forma explícita la salida estructurada nueva y la prosa heredada. No permitir al cliente ampliar permisos ni cambiar la política. Mantener IA no configurada por defecto y todos los envíos reales prohibidos en esta misión.

La UI distinguirá «contenido educativo de Paideia, no redacción libre del modelo», «resultado del motor determinista» y «ensayo con proveedor ficticio». No fingir IA real con tarjetas o plantillas. El intento estructurado no puede caer silenciosamente al camino legado no aprobado. El error de contrato debe mostrar un aviso claro y no ocasionar reintento o llamada extra.

Conservar privacidad: sin registro ni persistencia automática, perfil local solo opt-in/borrable, sin nombre/DNI/banco/credenciales; no adjuntar contexto/historial ni cambiar sus flags por desarrollar esta modalidad. El texto del usuario y del supuesto proveedor son datos no confiables, no instrucciones privilegiadas.

## 4. Ejecución ordenada, no otro plan general

1. Al activar, comprobar reloj, registrar el inicio efectivo y el corte fijo en una carpeta NUEVA bajo docs/ia-calidad-estructurada/ejecucion/. Guardar estado y pruebas por hitos; no usar ficheros antiguos como prueba nueva. Identificar procesos/puertos propios y comprobar baseline focalizada. No matar procesos ajenos ni leer contenido de entradas secretas.
2. Cargar skills pertinentes: TDD, debugging, dogfood y revisión independiente. Escribir una prueba roja del nuevo límite de confianza; implementar la sección vertical mínima. Iterar pruebas y código, sin redactar primero decenas de tests hipotéticos.
3. Añadir adversariales: prosa peligrosa en answer/refusal, citas/negaciones y comas, texto correcto libre que NO se presenta como estructurado revisado, IDs inventados, schema incompleto/tipos erróneos, extras, duplicados, Unicode, referencias numéricas falsas, datos de tools simulados por el proveedor, intento del cliente de cambiar modalidad y resultados de un turno ajeno. Reutilizar el corpus de20frases como texto no confiable; el objetivo no es que un clasificador léxico adivine su semántica.
4. Integrar UI+HTTP con proveedor ficticio explícito. Probar resultado correcto desde IDs autorizados, error sin filtrar texto arbitrario, cálculo contra motor y un flujo de consentimiento. Iniciar proceso propio nuevo para que cargue el código actual; el normal8765 antiguo no demuestra integración del cambio. Recoger red/DOM antes de capturas opcionales y detener el fixture al terminar.
5. Actualizar la evaluación offline: probar el contrato, no inventar respuestas de Groq ni puntuaciones de calidad. Si se adapta el benchmark, conservar fase/versionado, ganador nulo y separar comparabilidad de las antiguas variantes. No ejecutar sus18llamadas. Mantener modelo/salida/consumo existentes para cualquier futura propuesta, sin activarlos.
6. Retirar el guard léxico como autoridad de aprobación de esta modalidad. Se permite deprecar o sustituir sus contratos/tests obsoletos como parte del cambio arquitectónico, **solo con un mapa explícito de cada prueba retirada al nuevo criterio que la sustituye**. Conservar evidencia roja y contraejemplos. No borrar, saltar, marcar expectedFailure, rebajar aserciones o mover tests fuera del descubrimiento solo para obtener verde. Los contratos no afectados deben seguir pasando.
7. Ejecutar regresión Python unittest, Node, sintaxis JS, HTTP y navegador. Registrar número real y exit code; separar fallos de infraestructura de fallos de código. Suite completa al terminar cambios relevantes, no en bucle. Revisar DTO completo y no solo nombres de campos. Si falta herramienta instalada, no instalar: alternativa existente o bloqueo honesto.
8. Revisión independiente de archivos actuales, pruebas y límites de confianza. Máximo dos ciclos de corrección y nueva revisión. Si no se obtiene un pase, parar con el candidato no aprobado y la función real desactivada; no generar nuevas rondas de regex ni solicitar autorizaciones en cadena durante la ausencia del usuario.
9. Entregar o parar al corte: cerrar procesos temporales propios y comprobar sus puertos; conservar uso de misiones anteriores; guardar checkpoint y pendientes. No iniciar nuevas tareas largas cerca del corte ni dejar trabajadores ejecutándose después. No esperar ni rellenar la noche si el objetivo se logra antes.

## 5. Entrega y criterios exactos de aceptación

Crear en la carpeta de ejecución:
- CONTRATO.md y schemas/versiones/ejemplos claramente sintéticos.
- README-PRUEBA-LOCAL.md con comandos reales de arranque, puerto y cómo parar, sin instalaciones ni claves.
- RESULTADOS.json/MD: comandos, salidas y conteos de tests; qué procesos cargaron el código nuevo; evidencia HTTP y navegador; revisión independiente y matriz de aceptación.
- MIGRACION-TESTS.md si cambian tests del clasificador antiguo, con correspondencia y motivo, no ocultamiento de fallos.
- PENDIENTE-GROQ.md: qué hipótesis solo puede probar el modelo real, mensajes previstos, criterios y consumo esperado; no una autorización para hacerlo.

Aceptación del trabajo nocturno: una sección vertical nueva funciona solo con fixtures explícitos; texto/claims/evidencia numérica no autorizados no llegan como contenido revisado; motor, permisos y privacidad preservados; pruebas y revisión favorables, o informe de bloqueo explícito. No confundir «bloqueo documentado» con «implementación aprobada». No declarar punto1 terminado: quedan validación real del modelo, calidad contextual, A/B/C y demás fases pendientes.

Informe final breve al equipo: cambios, alcance probado, incidencias, límites y cómo probarlo. Especificar si hace falta autorización futura para Groq. **No pedir una clave mientras el equipo está ausente.**

## Comandos base existentes (detectar primero el estado real)

Desde app:

    python -B -m unittest discover -s tests -p 'test_*.py' -q
    node --test tests/*.test.cjs
    node --check static/app.js
    python -B verify_http.py

verify_http.py presupone servidor8765; si se usa otro proceso propio, adaptar el harness de forma explícita o utilizar integración equivalente y registrar su URL. No presentar19HTTP sobre servidor antiguo como prueba de la nueva modalidad. No declarar disponible un comando que no se haya ejercitado.

## Mecanismo de activación

La documentación oficial consultada confirma /goal <texto> y contratos inline. /goal conserva el objetivo en esta sesión; no crea un cron ni un proceso independiente y puede pausarse por límite de turnos/usage. No modificar ese límite para seguir. Fuente: https://hermes-agent.nousresearch.com/docs/user-guide/features/goals .

El comando preparado se entrega por chat. Hasta que el usuario lo envíe, este documento no activa trabajo nocturno. Si ya ha vencido el corte, pedir una nueva ventana, no trasladarlo automáticamente a otro día.
