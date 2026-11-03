# Diagnóstico móvil C — resultado final

**Estado: completado en el alcance solicitado. C tiene aceptación independiente favorable.** No se modificó producción ni el script existente de integración. Este encargo nuevo resolvió un bloqueo de verificación; no abrió un tercer ciclo de corrección de la aplicación.

## Qué se diagnosticó
El experimento mínimo reprodujo el límite de evaluación del navegador sin ejecutar código de Paideia:
- Esperar una promesa de 6,5 segundos dentro de `Runtime.evaluate` falló a los 5,026 segundos.
- Lanzar la misma promesa, devolver `started` y recoger el resultado después retornó en 0,016 segundos y obtuvo `finished`.

Evidencia: `EXPERIMENTO-1.json` y `DIAGNOSTICO.md`. Esto demuestra un mecanismo capaz de producir los timeouts anteriores, no cada detalle de su causa histórica. No fue necesario cambiar la aplicación ni ampliar un timeout de Hermes. Un único experimento fue suficiente; no se gastó el segundo por rutina.

El primer resultado recogido por el coordinador a los 8 segundos seguía pendiente y una aserción prematura falló. Se conservó en `coordinator-mobile.json`. La segunda recogida del mismo lanzamiento terminó 27/27 en `coordinator-mobile-final.json`; un estado pendiente no es un defecto de aplicación.

## Verificación independiente completada
El primer revisor ejecutó el test intacto con servidor/API normales en documentos nuevos y sesión aislada:

| Recorrido | Resultado | Métricas finales client / scroll / visual |
|---|---|---|
| Escritorio solicitado 1440×900 | 27/27 | 1440 / 1440 / 1440 |
| Móvil emulado solicitado 390×844 | 27/27 | 390 / 390 / 390 |

Archivos: `independiente/desktop.json`, `mobile.json`. Incluyen búsqueda, ficha, diagnóstico con respuesta HTTP real retenida, navegación con los mismos IDs sin petición automática y reintento manual, descarte al cambiar selección, ayudas, glosario y bloqueo de familias mixtas. Los cuerpos observados de comparación contienen únicamente IDs y criterio. Las razones explican por qué no se puede comparar cuantitativamente; no inventan tasas ni ranking.

`independiente/probes.json` añade nueve comprobaciones propias de límites/consultas válidas y prueba de teclado CDP en escritorio. El primer intento de teclado quedó fallido y se conserva; el reintento completo abre con Enter, mueve foco con Tab y cierra con Escape devolviendo foco. No certifica todas las combinaciones de teclado ni lectores de pantalla.

## Matriz suplementaria y dictamen combinado
El primer dictamen de este diagnóstico quedó pendiente porque no cubría toda la matriz exigida. Se conserva en `independiente/REVISION-INDEPENDIENTE.json`; no se cambió a mano a aprobado.

Un suplemento independiente completó cuatro valores: 101 letras, 100 letras más espacio final, espacio inicial más 100 letras y 101 espacios. Para cada uno comprobó cinco etapas: entrada, salida/vuelta con filtro depósito, cambio de filtro a ETF mientras es inválido, nueva salida/vuelta y restauración de depósito. Las **20/20 etapas** preservan texto literal, filtro, error y aria-invalid sin nuevas peticiones de catálogo. Al borrar el texto se realiza una petición válida y vuelve la carga local.

Dictamen combinado: `independiente/REVISION-COMPLETA.json`, **passed:true**, security_concerns, logic_errors y verification_blockers vacías. Distingue las pruebas integradas independientes anteriores que leyó del suplemento que ejecutó. La coordinación verificó programáticamente los dos resultados completos, cada etapa y sus contadores; no se acepta solo la narrativa del agente.

## Archivos y pruebas conservados
Los SHA256 de app.py, app.js, context_help.js, context_help.css y c_integration_browser.js coinciden con `SOURCE-HASHES.json` al cierre. No hubo correcciones de producción, nuevas dependencias, wrappers permanentes ni cambios a assertions/esperas. Solo se escribieron documentos y evidencias nuevas en esta carpeta y referencias de estado/demo/continuidad.

No se repitieron suites Python/Node intactas. Sus resultados anteriores mantienen su alcance histórico y no se presentan como pruebas de este encargo. No se forzó una consulta Qwen: el comportamiento temporal se pudo medir directamente; el modelo no habría añadido evidencia a ese experimento. Ponytail se aplicó conservando el código y evitando capas innecesarias.

## Límites que siguen vigentes
- Emulación CDP, no dispositivo móvil físico ni auditoría integral de seguridad, accesibilidad o diseño.
- Inicio móvil registró inicialmente client 390, scroll/inner 448 y visual 390; al terminar C las medidas fueron 390. La causa de esa diferencia no está establecida. No se certifica toda la aplicación como libre de desbordamiento.
- C sigue siendo biblioteca de candidatos, comparación de metadatos y explicaciones. No se aprobó catálogo cuantitativo ni condiciones vigentes de productos.
- No se activó ni validó IA real en Paideia, no se ensambló Pai, no hubo claves, datos personales, pagos, instalaciones, bases de datos, despliegue o commits.

## Limpieza y entrega
Servidores propios 18874, 18875 y 18876 detenidos. La comprobación final no encontró listeners y los tres GET /api/status fueron rechazados con WinError 10061. Evidencia del suplemento en `independiente/CIERRE-SUPLEMENTO.json`; del coordinador en `COORDINADOR-CIERRE.json`. LM Studio, Hermes y servicios ajenos no se detuvieron.

Los dictámenes desfavorables anteriores no se borraron ni se reescribieron. El estado actual favorable enlaza este diagnóstico nuevo. A y B conservan sus aprobaciones anteriores; C añade ahora la aceptación que faltaba.

**Siguiente paso:** utilizar `GUIA-DEMO.md` para mostrar escenarios, informe y biblioteca con sus límites. El siguiente desarrollo de Pai requiere un encargo separado; no se inicia automáticamente.

**Qué tenéis que hacer:** no hace falta intervención para cerrar este diagnóstico. Podéis revisar la demo cuando os venga bien.
