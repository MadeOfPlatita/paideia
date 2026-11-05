# Nuevo encargo: diagnóstico de automatización móvil y aceptación de C

## Preparación, no activación
Preparado a petición de Alejandro el 03/11/2026. Este archivo no activa /goal ni inicia procesos. Se ejecuta cuando el usuario envíe el comando correspondiente. Es un diagnóstico separado del arnés de pruebas; no reabre ni prolonga los tramos nocturno o de mañana, ni reinicia sus contadores de corrección de la aplicación. No se ha acordado otro plazo de tres horas: no asumirlo. Parar al completar aceptación, necesitar intervención, agotar cuota o persistir el bloqueo tras los dos experimentos acotados descritos abajo. Registrar inicio y cierre reales; no llenar horas ni prometer continuidad.

## Fuentes y ámbito
Raíz: C:/Users/aleja/Downloads/App Financiera. Aplicación: app. Solo perfil Hermes trabajos. Leer docs/revision-manana-20261103/{CIERRE.json,RESULTADOS.md,REGRESION-FRONTEND.json}, C/ciclo2-revision/{REVISION-INDEPENDIENTE.json,mobile.json,mobile-attempt1.json,desktop.json,probes.json} y docs/PLAN-PAI-PENDIENTES.md.

A/B tienen revisión favorable y regresión frontend nueva. C fue corregido en dos ciclos; su integración móvil pasó al coordinador, pero no al revisor independiente: Runtime.evaluate agotó tiempo dos veces. El dictamen final es passed:false con listas de lógica/seguridad vacías y bloqueo de verificación. No inferir un defecto de app, causa de harness ni un aprobado a partir de esos datos. Conservar evidencia histórica intacta.

## Objetivo concreto
Obtener una explicación reproducible del bloqueo de automatización y, si se puede sin más cambios de app, una revisión independiente completa de C en móvil. No construir funciones nuevas, refactorizar Paideia ni lanzar un tercer ciclo de corrección de la app con otro nombre. Si aparece un defecto de aplicación nuevo, documentar el caso y parar para autorización específica.

## Procedimiento: señal pequeña antes de repetir la integración
1. Cargar systematic-debugging, requesting-code-review, ponytail y ponytail-review; test-driven-development si se modifica un arnés. Inspeccionar las llamadas reales del revisor y coordinador; recuperar el tramo relevante del transcript solo si los archivos no bastan. Revisar especialmente si Runtime.evaluate esperaba toda la promesa, si el helper limita el tiempo y si el comando etiquetado asíncrono se ejecutó realmente sin esperar. No culpar al código de aplicación sin prueba.
2. Usar navegador aislado con nombre propio y documentos nuevos, sin perfil real ni localStorage del usuario. Crear servidor propio app.py en puerto loopback libre, registrar PID y comprobar /api/status: IA no conectada. No detener servicios ajenos.
3. Construir un experimento mínimo que discrimine hipótesis: readiness/URL, CDP viewport, una promesa corta que termine después del límite observado y la recogida posterior. Máximo dos experimentos de diagnóstico con hipótesis y resultado persistidos; no repetir la misma llamada o abrir pestañas en bucle. Conservar fallos. Si la primera evidencia es concluyente, no gastar el segundo por rutina.
4. Para scripts browser.js, no usar Node. Lanzar sin esperar la promesa completa, por ejemplo: window.__result=null; (SCRIPT_IIFE).then(r=>{window.__result=r},e=>{window.__result={ok:false,error:String(e)}}); 'started'. La llamada inicial debe retornar enseguida; recoger después con evaluación corta y esperar mediante plazo de test definido, no polling sin límite. En cada llamada CDP registrar lo solicitado y medir documentElement.clientWidth, scrollWidth, innerWidth, devicePixelRatio y visualViewport. No exigir clientWidth idéntico al ancho solicitado si hay scrollbar: explicar la diferencia observada. Un nombre mobile.json no acredita tamaño móvil.
5. Solo tras un mecanismo mínimo fiable, ejecutar tests/c_integration_browser.js en documento limpio con viewport solicitado 390x844 y medir métricas efectivas; contrastar escritorio1440x900 si el arnés también cambió. No alterar esperas, assertions, viewport ni script para ocultar un defecto. Si se cambia un runner, observar RED con el caso reducido antes y GREEN después; cambios exclusivos a artefactos/arnés bajo el nuevo directorio, sin tocar producción.

## Revisión independiente: aceptación por comportamiento
Un contexto distinto debe ejecutar y examinar la aplicación con el mecanismo ya demostrado. No repetir la amplia investigación en cada worker ni atribuirle Qwen por haber fallback configurado. Exigir:
- Búsqueda DOM maxLength100; 101 letras, 100letras+espacio, espacio+100letras y101espacios inyectados: sin fetch, texto/filtro/error/aria-invalid preservados, también al salir y volver. Consulta válida100, recorte para q con longitud válida, filtro y vaciado siguen funcionando.
- Filtro/ficha y motivos explícitos de bloqueo; comparación no inventa ranking o tasas y cuerpos contienen solo product_ids y criterion.
- Retener respuesta HTTP REAL de diagnóstico; Comparar→Inicio→Comparar con mismosIDs: descartar respuesta, no autofetch y permitir reintento manual. Cambio de selección invalida.
- Ayudas locales y glosario compartidos, teclado/Escape/foco y familias mixtas bloqueadas. Declarar alcance exacto de accesibilidad, sin certificar auditoría completa.
- Documento nuevo por tamaño, resultados completos, métricas y endpoints de prueba reales. Pasar solo si no hay fallos y la evidencia móvil independiente se completa. No sustituirla por el móvil verde del coordinador.

## Qwen local y Ponytail
Preferir Qwen local para una pregunta estática pequeña o contraste de una función. Endpoint127.0.0.1:1234/v1, modelo qwen3.6-35b-a3b; verificar disponibilidad sin leer secretos. La inferencia local es herramienta de desarrollo, no habilita IA en Paideia. Un archivo pequeño por solicitud y una pregunta concreta; máximo una llamada y un reintento solo con alcance menor, timeout y presupuesto de salida definidos. Registrar finish_reason y contenido utilizable, no razonamiento privado. Si termina length o contenido vacío, no contar auditoría como completada. No conceder ejecución de herramientas ni aplicar código generado sin comprobarlo. No repetir una auditoría amplia que ya falló ni consumir llamadas por llenar el tiempo. Si Qwen no aporta nada al diagnóstico, no forzar su uso.

Ponytail: el menor cambio completo; no wrappers, capas, dependencias o opciones especulativas. No cortar validación, accesibilidad, privacidad, error handling ni contratos para reducir líneas. Auditoría y sugerencias no son permiso para limpieza masiva.

## Regresión proporcional
Si solo cambian runners/documentación, no repetir automáticamente Python/Node enteros ni atribuir pruebas históricas a la revisión nueva. Si no cambia la app, mantener sus resultados previos con alcance explícito. Verificar el runner corregido y la integración afectada; cualquier necesidad de modificar producción queda fuera y se comunica. No instalar paquetes para resolver un harness sin comprobar herramientas ya disponibles.

## Artefactos y final
Crear directorio nuevo docs/diagnostico-movil-C/<inicio>/ con START.json, experimento(s), resultados desktop/mobile con métricas, dictamen independiente, RESULTADOS.md y cierre de servidor. Añadir referencia actual a docs/ESTADO_Y_PLAN.md, sin reescribir dictámenes históricos. Si aprobado, enlazar la nueva evidencia y actualizar guion de demo y estado C. Si bloqueado, conservar C como no aprobado, causa conocida/desconocida precisa y una única siguiente tarea. No iniciar ensamblaje Pai, nuevos productos o auditoría repo-wide al terminar: entregar este diagnóstico y parar.

Cerrar servidores/procesos propios en finally, verificar netstat y petición rechazada; no parar LMStudio, Hermes ni servicios ajenos. Registrar hora real y estado runtime. El objetivo no está hecho por completar un plan o subir tests: requiere evidencia y dictamen favorable; si no, informar parcial/bloqueado.

## Restricciones conservadas
Sin llamadas de la app a proveedores reales, claves, datos personales, Tk, pagos, instalaciones, bases de datos nuevas, despliegues, Git init/commits ni ampliaciones de misiones caducadas. Presupuesto0€. No leer .env, portapapeles o memoria de otros procesos. No tocar perfiles reales para probar borrado/migración. Solo código propio, datos sintéticos y loopback. La conexión de desarrollo Qwen local es la excepción explícita ya autorizada; ninguna otra inferencia/proveedor se autoriza desde Paideia.

## Entrega al equipo
Respuesta final: causa probada o límite aún desconocido; cambios exactos si los hubo; revisión móvil aceptada o bloqueada; rutas de evidencia y cierre; siguiente paso. Terminar con Siguiente paso y Qué tenéis que hacer, indicando si no necesitan intervenir. Distinguir el archivo preparado, /goal activado y cualquier proceso realmente lanzado.
