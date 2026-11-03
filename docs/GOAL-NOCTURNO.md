# Goal de Paideia — prototipo local ejecutado; producción pendiente

## Resultado de ejecución del encargo

El usuario autorizó y solicitó explícitamente ejecutar este encargo como mensaje de trabajo. El prototipo local se verificó con 39 tests, 17 comprobaciones HTTP y ocho rutas en escritorio/móvil; informe en `../prototipos/paideia-local/VERIFICACION.md` y evidencia `../prototipos/paideia-local/evidence/FINAL.json`. El servidor local permanece disponible mientras siga activo su proceso. No se afirma activación del registro nativo `/goal`, autonomía nocturna garantizada ni producto de producción completo.

Los criterios siguientes se marcan únicamente para el prototipo local, con chat no conectado y catálogo contractual bloqueado explícitamente. La ejecución se detiene antes de cuentas, datos reales, pagos, PostgreSQL o publicación.

## Estado histórico y condición de inicio

Solicitud del grupo: «Prepárate un slash goal cuando acaben los subagentes».

Se recibió y revisó la unidad `deleg_2d7b1900`. Se reprodujeron siete tests del arnés y veintiuno de proyección, se validaron seis casos y dieciocho requests, y se recontaron veinte candidatos de catálogo con doce ISIN válidos. Evidencias: `validacion-04/00-VERIFICACION-COORDINADOR.json` y `validacion-04/00-REVISION-COORDINADOR.md`. Este archivo es el comando preparado: NO demuestra que `/goal` esté activado, que exista una tarea nocturna programada o que haya un proceso autónomo en marcha.

Resultados incorporados: Groq GPT-OSS 20B es el primer candidato de smoke interno, no proveedor probado; 120B es comparador posterior. Gemini Free no se considera aprobado para backend público EEE por su cláusula Paid Services. No hay cuenta ni llamadas LLM; sin acceso, continuar las partes locales sin fingir chat. El catálogo tiene catorce identidades verificadas por evidencia previa y seis propuestas; ninguno de los veinte está marcado publicable. La proyección y el arnés usan formatos distintos: el adaptador y sus tests conjuntos forman parte del encargo, no una integración ya conseguida.

## Comando preparado

El siguiente bloque es un único comando `/goal` con el encargo; no es una orden de shell. Está listo para introducir en esta conversación. Guardarlo en este archivo no ejecuta el comando ni activa una sesión autónoma.

```text
/goal Aplicar primero los resultados y límites de docs/validacion-04/00-REVISION-COORDINADOR.md. Crear y probar el adaptador entre perfil local05, proyector04-contexto y arnés03-benchmark antes de afirmar integración. Considerar Groq GPT-OSS20B solo para un smoke posterior autorizado; no hay calidad IA ni cuenta verificadas. Construir y verificar un prototipo local navegable de Paideia para la entrega del martes 3 de noviembre de 2026, usando los resultados auditados de docs/validacion-04 y los requisitos vigentes. Priorizar un recorrido completo Pai → perfil editable → biblioteca → comparación → escenarios → contratación explícitamente ficticia. Trabajar en prototipos/paideia-local/ sin pisar entregas de agentes ni archivos del usuario. Inspeccionar antes el proyecto y las herramientas instaladas; reutilizar lo disponible y no instalar dependencias ni ejecutar código descargado sin autorización. Implementar frontend adaptable a móvil/ordenador, backend local con API de lectura y cálculos deterministas, selección explícita de contexto y manejo de errores. Mantener PostgreSQL como arquitectura propuesta del catálogo; si el prototipo usa snapshot o repositorio en memoria, identificarlo como adaptador local temporal, no DB creada ni cambio de alcance. Primer objetivo de catálogo: 20 productos reales, cuatro por familia, ampliable, solo con campos y usos respaldados; candidatos incompletos no se convierten en ofertas verificadas. Datos sintéticos únicamente en tests y demostraciones inequívocamente rotuladas, nunca atribuidos a entidades reales. Conservar IA real como requisito: sin acceso autorizado, mostrar chat no conectado y probar con dobles inertes identificados; no fingir conversaciones de un proveedor. Ejecutar tests de cálculo, validación, consentimiento, proyección y desconocidos, integración HTTP local y smoke del recorrido en navegador cuando esté disponible. Corregir los fallos encontrados, volver a probar y conservar evidencia de comandos y resultados. No crear cuentas, claves, facturación, pagos, servicios cloud, DB externas ni despliegues; no enviar datos personales ni ejecutar cargas contra terceros. Llamadas externas LLM solo si existe autorización y acceso gratuito seguro verificado, con datos sintéticos y límite explícito; en caso contrario dejar ese test pendiente. Guardar avances y decisiones por hitos, no repetir investigación ya cerrada. Parar cuando los criterios verificables estén cumplidos o un bloqueo requiera decisión humana; no consumir uso en bucles para ocupar toda la noche. Entregar URL local si el servidor sigue en marcha, comandos reproducibles, capturas reales, tests ejecutados, limitaciones y siguientes acciones del equipo. No declarar producción, calidad IA ni concurrencia de 100 usuarios sin pruebas específicas. Cerrar cada actualización con Siguiente paso y Qué tenéis que hacer.
```

## Criterios de terminado del prototipo

- [x] El recorrido es navegable localmente; no una colección de capturas o un plan.
- [x] El frontend permite editar/omitir datos, conserva estados desconocidos y tiene estados de carga/error/sin dato/chat no conectado.
- [x] El comparador y los escenarios funcionan sin depender de una respuesta LLM; tasas contractuales e hipótesis de mercado están diferenciadas.
- [x] El backend valida entradas, limita herramientas a lectura/cálculo puro y no acepta SQL libre ni URLs arbitrarias.
- [x] La proyección usa selección y consentimiento explícitos; se prueba que campos no seleccionados no salen. Borrado local no promete borrar datos del proveedor.
- [x] La simulación no pide identidad bancaria/pagos, no envía leads y no produce efectos reales.
- [x] Tests y smoke local ejecutados con resultados registrados; fallos abiertos visibles. Pruebas IA externas pendientes si falta acceso/autorización.
- [x] README con arranque/parada y alcance; informe de cierre con archivos/capturas/comandos reales y bloqueos, sin garantía de producción o carga.

## Límites operativos

No se ha fijado una hora de corte. La parada se define por los criterios o por bloqueo; no significa trabajo ilimitado ni garantía de ejecución continua. `/goal` no es por sí solo una tarea durable que sobreviva al cierre del proceso, suspensión del ordenador o agotamiento de cuota. Cualquier ejecución nocturna independiente requiere verificar el mecanismo y su alcance antes de afirmar que está corriendo.
