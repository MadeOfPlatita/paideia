# Acceso a IA real: prueba local con entrada protegida

El grupo autorizó proceder con IA real y eligió correo electrónico para Groq. browser_vault no reconoció el origen de login en dos intentos, incluso con navegación al login en la sesión por defecto; no se sabe la causa y no se reintentó indefinidamente. No se guardaron credenciales. El usuario eligió expresamente la alternativa de ventana local enmascarada.

## Funcionamiento

Ejecutar desde el prototipo: `python -B secure_groq_smoke.py`.

La ventana permite abrir Groq en el navegador del usuario, comprobar la organización/plan Free e introducir una clave API en un campo enmascarado. No se crea cuenta, clave ni facturación automáticamente. El usuario confirma el plan gratuito: la casilla no verifica técnicamente el plan ni garantiza coste si la clave corresponde a una organización de pago.

Clave solo en memoria del proceso; no se escribe en .env, repositorio, logs ni informes. No se lee el entorno del usuario para buscar secretos. Se borra el campo al enviar. No se promete borrado forense de RAM; cerrar finaliza la sesión y no deshace una petición ya enviada.

Una petición por apertura, sin reintentos, destino fijo Groq, modelo openai/gpt-oss-20b, salida máxima256, timeout de socket15segundos, límites del adaptador existentes. Pregunta fija ficticia sobre ahorrar/invertir. Sin perfil, historial ni datos del catálogo; no activa todavía el chat web ni sus herramientas.

El resultado seguro se guarda en `app/evidence/REAL-IA-SMOKE.json` solo tras ejecutar. Contiene estado, respuesta sin reasoning, indicadores de truncado/rechazo y conteo de llamadas, nunca la clave. Solo un resultado con test_only:false acredita uso externo; los tests usan transporte sintético identificado y no escriben en ese destino.

## Verificado antes de abrir la ventana real

Cuatro regresiones nuevas: bloqueo sin confirmar Free, intento único, campo enmascarado sin envío al abrir, recorrido de ventana con clave ficticia y reporte sin secreto. Se probaron con rojo→verde. También regresión global; salida en offline-tests.json. Que estos tests pasen NO acredita llamada a Groq.

## Pendiente

Que el usuario introduzca su clave por esta ventana y confirme Free. Después leer el resultado seguro y valorar conectividad/respuesta real; truncado, rechazo o HTTPfallido no se ocultan. El benchmark A/B/C, herramientas con modelo real, chat web y presupuesto durable siguen pendientes.
