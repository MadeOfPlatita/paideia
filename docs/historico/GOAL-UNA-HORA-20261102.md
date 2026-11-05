# Paideia — misión de una hora: estabilización e integración útil

## Activación y tiempo

Este documento prepara el encargo; no activa procesos ni el mecanismo /goal. Al recibir la orden de ejecución, consulta el reloj del sistema y crea un directorio nuevo bajo `docs/ia-groq-estructurada/ejecuciones/`. Guarda START.json con inicio y corte absoluto = inicio + 60 minutos. Ese corte se fija una sola vez; en continuaciones, notificaciones, reinicios y revisiones se conserva, no se recalcula. Reserva los últimos 10 minutos para regresión, cierre de procesos propios e informe. Comprueba el reloj antes de nuevas tareas y al volver de una interrupción. No iniciar tareas que excedan el tiempo restante. Detener antes si se cumplen los hitos viables, se agota el uso, hace falta autorización humana o persiste un bloqueo tras dos ciclos de corrección y revisión. No esperar ni consumir cuota para completar artificialmente la hora. No prometer ejecución ininterrumpida si se cierra Hermes, se suspende el PC o se alcanza el límite de turnos.

## Ámbito y estado comprobado al preparar

Raíz: `C:/Users/aleja/Downloads/App Financiera/`. Aplicación: `app/`. Perfil Hermes: trabajos, ningún otro. Lee el informe `docs/ia-groq-estructurada/ejecucion-40min-20261030/RESULTADOS.md` y comprueba el código actual antes de modificarlo.

El 2/11 se comprobó que backend_services.py importa secure_groq_session a nivel de módulo y este importa tkinter y ttk a nivel de módulo. También continúan respuestas exitosas con `external_sent` derivado del booleano del servicio. No asumir que la configuración del lanzador basta para garantizar procedencia.

Base histórica, no ejecución nueva: 327 unittest sin tres módulos GUI, 40 Node, 19 HTTP; varias pruebas son funciones pytest y no se descubren con unittest. No sumar subtests como tests distintos ni declarar suite completa omitiendo esas funciones. El modo estructurado real no está ensamblado; sí existe recorrido sintético HTTP→admisión→presupuesto→fixture→parser→render. Conectividad real histórica no demuestra esta integración ni calidad de modelo. Las misiones reales anteriores están caducadas.

## Prioridad 1 — dos defectos concretos, con aceptación verificable

### A. Backend sin dependencia obligatoria de GUI

Reproducir primero en subproceso aislado la importación/arranque del backend con tkinter y sus submódulos bloqueados. Refactorizar la dependencia entre identidad/fachada de sesión y presentación GUI: importar Tk solo donde sea necesario o separar responsabilidades con cambios mínimos. No falsear tkinter en producción ni quitar la validación de identidad del proveedor para evitar el ciclo. Verificar que app/backend se pueden importar y servir HTTP loopback sin Tk y que las funciones de GUI quedan aisladas; no abrir ninguna ventana Tk. Mantener la compatibilidad del código de entrada segura sin ejecutarlo. Nueva prueba automatizada debe fallar antes del cambio y pasar después.

### B. Metadatos veraces por construcción

Reproducir con conexión HTTPS ficticia y sockets externos bloqueados la configuración de proveedor real + test_only del servicio que produciría `external_sent:false` incorrecto. Rechazar esa combinación antes de cualquier intento o derivar los metadatos de una frontera confiable explícita. No confiar en la mera etiqueta test_only ni en campos que suministre el cliente/modelo. Mantener el proveedor falso cerrado sin red; no activar ningún modo real por payload. Conservar not_started/unknown/completed y no afirmar ausencia de envío si es incierto. `completed` significa retorno de la llamada local de envío, no recepción, procesamiento ni facturación del proveedor. Pruebas de respuestas exitosas y errores a través de servicio y HTTP; sin reintentos automáticos, sin pérdida de sanitización. No habilitar la vía real estructurada para conseguir esta prueba.

## Prioridad 2 — siguiente integración, no otra simulación aislada

Solo tras cerrar A y B con revisión favorable y tiempo suficiente: completar una rebanada útil que conecte componentes existentes de la educación estructurada con la fachada contada y su contrato de salida, dejándola desactivada por defecto. Antes de delegar, ejecutar un tracer mínimo de contratos para detectar interfaces incompatibles. Ejercitar el transporte HTTPS real con HTTPSConnection ficticia, sin red externa; no convertir resultados reales en FakeChatProvider para atribuir procedencia falsa. Parser cerrado, texto editorial local, supuestos explícitos del mismo turno y cálculo servidor; escenario no añadido al cuerpo remoto. Consentimiento/admisión/cuota/revocación/plazo/singleflight deben seguir intactos. Si solo se puede entregar diseño o un fake separado, marcar el hito bloqueado en lugar de llamarlo integración completa.

No es necesario finalizar toda la conexión real durante esta hora. No abrir una ventana de clave ni hacer una llamada real para completar el objetivo. No ampliar alcance a rediseño visual, nuevos proveedores, migraciones masivas o investigación indefinida de datos.

## Prioridad 3 — verificación conjunta y entrega reproducible

- TDD secuencial: un comportamiento RED→GREEN cada vez, conservar evidencia de ambos. Fallos de importación por typo no demuestran una prueba de comportamiento; distinguirlos.
- Delegación con archivos exclusivos; cambios compartidos coordinados por el principal. Revisores independientes, solo lectura, con pruebas adversariales sintéticas. Máximo dos ciclos de corrección por bloqueo; si persiste, mantener el modo afectado desactivado, documentar y no continuar corrigiendo ese bloqueo sin nueva autorización. No convertir ataques con control arbitrario de Python en requisito imposible de sandbox: cubrir fronteras soportadas, describir límites y no prometer invulnerabilidad.
- Regresión: inspeccionar el recolector antes de usarlo. Ejecutar tests unittest y funciones pytest relevantes sin abrir GUI; bloquear tkinter.Tk defensivamente, excluir solo los casos que de verdad necesiten ventanas y registrar cuáles. No excluir todo test de sesión por nombre. Si existe incompatibilidad en un módulo excluido, declararla. No instalar paquetes para conseguir un recuento. Recuperar las suites disponibles, sin depender de que sobrevivan runners temporales de scratch.
- Ejecutar `node --test tests/*.test.cjs` y sintaxis JS; ejecutar HTTP local con servidor propio recién iniciado en loopback y cierre en finally. El servidor normal y el modo estructurado requieren pruebas diferenciadas. Probar en navegador las interfaces afectadas si hay cambios de UI; datos sintéticos y origen aislado.
- Retener resultados fallidos antes del fix o de corregir prerrequisitos; no eliminar aserciones ni sustituir una prueba de excepción por un HTTP500 sin restaurar la cobertura anterior.
- Guardar un runner de regresión no-GUI reutilizable en el proyecto si falta uno; no depender exclusivamente de rutas cache/scratch. Documentar inicio local y diferencias entre IA desactivada, fixture y conexión real futura.
- Informe final con cambios, hora real de inicio/cierre, comandos, resultados reales, módulos excluidos, revisiones, estado de cada hito (completo/parcial/bloqueado), procesos y puertos propios comprobados, y próximos pasos. Actualizar un índice/estado breve actual sin alterar informes históricos para fingir éxitos.

## Restricciones y permisos

Permite leer/editar código y documentos del proyecto, ejecutar código propio/tests, crear fixtures y ledgers sintéticos efímeros, usar conexiones instrumentadas y servidores/navegador loopback aislados y cerrarlos. Ninguna llamada de la aplicación a Groq u otros proveedores externos, ninguna clave real, datos personales, lectura de secretos de entorno/portapapeles/memoria ajena, ni ventana de entrada segura. Sin cuentas, pagos, instalaciones, bases de datos nuevas, despliegues ni ejecución de código descargado. No tocar ledgers/manifiestos reales caducados, ampliar sus fechas o reducir sus guardias. No saltar auth/WAF. No hacer commits ni inicializar Git para poder revisar; si no hay repositorio, revisar archivos explícitos y reconocerlo.

La autorización histórica general no elimina estas fronteras. Una futura prueba real necesita su misión y autorización específicas, confirmación humana Free y entrada voluntaria por la ventana segura; el plan no queda técnicamente verificado por un checkbox. El modelo no genera condiciones de productos, supuestos ni resultados financieros a presentar como hechos.

## Definición de terminado

Para declarar completo el objetivo principal: A y B implementados, regresión pertinente ejecutada sin nuevos fallos, revisión independiente favorable y evidencia guardada. La prioridad 2 solo se declara completa si el recorrido integrado se ha probado, no por crear módulos o planes. Si no se logra, entregar estado parcial/bloqueado y detener la misión honestamente; un informe por sí solo no satisface el objetivo. No declarar Paideia terminada ni IA real conectada. Terminar con Siguiente paso y Qué tenéis que hacer; si no hay intervención necesaria, decirlo.
