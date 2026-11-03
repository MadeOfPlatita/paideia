# Hito D — evidencia focalizada (2026-10-30)

Fixture aislada TEST ONLY: servidor propio `python -B tests/serve_d_fixture.py`, puerto aleatorio, `http://127.0.0.1:58148/`, PID informado 29512; sin proveedor, claves ni red remota. El nombre «SINTÉTICO TEST ONLY» y entidad ficticia no son productos reales. UI preexistente dice «candidato real» porque sirve catálogo normal; en esta prueba el servidor sustituye exclusivamente su respuesta por el fixture sintético. No se debe atribuir este caso a productos reales.

## Rojo → verde

`tests/d_simulation_ui.js`, ejecutado sobre DOM de navegador real en URL fixture, antes de tocar `app.js`: `RED: previous acknowledgement survives changed amount`. Pasos: elegir fixture, revisar tipo/costes desconocidos, introducir 100, marcar comprensión, volver, cambiar a 200, continuar. El check quedaba marcado y el botón de crear justificante habilitado: la aceptación antigua sobrevivía a una modificación del ejercicio. Corrección mínima: al volver desde comprensión se invalida la aceptación; no se altera el diseño. Recarga limpia y mismo test: `pass: true`. Comprobó botón bloqueado antes de aceptación y tras volver; comprobante con importe 200, etiqueta ENSAYO FICTICIO, sin contrato ni operación. Cero almacenamiento durante el flujo.

Impresión: sin abrir diálogo nativo, CDP emuló `print`: recibo `display:block`, navegación lateral, acompañamiento y botones `.no-print` `display:none`. En esa vista el main incluye además encabezado, aviso y progreso; no se afirma aislamiento exclusivo del comprobante ni ausencia de fugas para cualquier extensión/impresora. No se comprobó PDF o diálogo de impresión.

## Perfil y solicitudes

`tests/d_profile_ui.js` en navegador real, fixture limpio: `pass:true`. Resumen mostró «No lo sé», «Omitido», «0,00 €» y «Aún no preguntado»; `localStorage`/`sessionStorage` vacíos en pausa. Guardar sin consentimiento y marcar casilla sin guardar: 0 entradas; guardar explícito: 1; revocar confirmando (confirm stub solo en esta prueba): 0. La acción de chat sin consentimiento envió 0 peticiones; con consentimiento explícito se observó exactamente una `POST /api/chat`, cuerpo `{"message":"Pregunta ficticia","consent":{"notice_version":"paideia-chat-remote-v1","accepted_chat_processing":true,"purpose":"free_chat","approved_fields":[]}}`, sin perfil. Fixture devuelve 405 deliberadamente: no prueba IA. Durante el ensayo se observaron GET locales de `/api/status`, `/api/catalogue` y recursos; no operación comercial. Se observaron las rutas y el cuerpo de chat de este recorrido, no una garantía universal para otros recorridos.

Regresión: `node --test tests/*.test.cjs` → 32/32 OK; `node --check static/app.js` → exit 0. `profile_flow.test.cjs` y `profile_model.test.cjs` incluidos: distinción de estados y representación decimal-string. Las pruebas D en navegador son expresiones JS que deben ejecutarse en página recién cargada por controlador CDP/browser, no se ejecutan con `node --test`; arrancar fixture y sustituir el puerto impreso. El runner de navegador y evidencia son herramientas de sesión, no se ha añadido dependencia.

Servidor propio terminado (`process_manage kill`, sesión `proc_36f90d55a49a`); `connect_ex 10061`, sin LISTEN, quedan sockets TIME_WAIT PID 0. Sin otros procesos tocados.

## Límites

Prueba focalizada sintética, no aceptación de oferta, tasa, condición real, privacidad universal o impresión física. Falta revisión independiente de seguridad, ejecución final de suite Python/HTTP global por coordinador y verificación de impresión física o PDF si se autoriza. No se han realizado pagos ni envíos comerciales, ni se ha diseñado un flujo nuevo.
