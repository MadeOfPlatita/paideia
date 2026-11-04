# B8 — privacidad y capacidad del chat: evidencia

Bloque B8 del encargo nocturno. Sin rediseño: solo textos, controles y comportamiento de privacidad del chat y del perfil. Sin publicación.

## Qué fallaba antes (diagnóstico y pruebas RED)

`DIAGNOSTICO.md` y `tests/b8_privacy_regression.test.cjs` reproducían cuatro defectos reales, no de arnés:

1. El consentimiento decía «No se enviará mi mapa de perfil» mientras el cuerpo del POST llevaba los campos marcados.
2. Con la IA pública apagada la interfaz afirmaba «no se envía nada» pero hacía un POST que recibía 405.
3. El diálogo de borrado solo hablaba de «todas las copias del mapa» y no distinguía historial del chat ni lo ya enviado al proveedor.
4. Tras borrar en una pestaña, otra pestaña con autoguardado reescribía la clave y el borrado se deshacía en silencio.

## Ciclo 1 (`deleg_cb4b27b3`)

Cambios en `prototipos/paideia-local/static/app.js` y su copia `api/_static/app.js` (idénticas, `cmp` y `node --check`):

- Consentimiento y resumen ajustados a lo que viaja: pregunta, campos marcados, historial opcional y mapa completo se describen por separado.
- `chatIsConfigured()` como puerta de envío: sin IA configurada no se hace `POST /api/chat`; calculadora, biblioteca y escenarios siguen funcionando.
- Sección «Qué sale de este navegador» en Privacidad y alcance explícito del borrado: copia local del mapa, historial de la pestaña y mensajes ya enviados al proveedor.
- Fallo de almacenamiento: mensaje de error visible, sin «Copia local borrada» falso.
- `storage` entre pestañas: la pestaña B desactiva opt-in y autoguardado al recibir el borrado de A, y hay guardia adicional antes de autoguardar si la clave desapareció. El historial de chat de B no se toca.

## Ciclo 2 — hallazgo del revisor y corrección

La revisión `deleg_f88b1fa6` aprobó los cuatro objetivos y falló el bloqueo por un caso: si `/api/status` llegaba sin bloque `ai`, `chatIsConfigured()` devolvía verdadero y la interfaz hacía un POST con el texto «Proveedor configurado».

Corregido: sin bloque `ai`, con `ai.status` ausente o no textual, o si falla la comprobación, no hay envío. Añadido `B8-2b` con un fixture que responde `{"mode":"local_prototype"}`; se comprobó en rojo revirtiendo la línea y en verde con el arreglo. También se actualiza el aviso del chat al fallar `/api/status` y el mensaje de borrado del historial recuerda que no borra lo ya enviado.

## Verificación de esta máquina

- `node tests/b8_privacy_regression.test.cjs`: **28/28 PASS**, 0 fallos de producto, 0 de arnés; incluye el WSGI real para el caso de IA apagada y dos pestañas reales por CDP.
- Todos los `tests/*.test.cjs`: **0 archivos con fallo**.
- `python -m pytest tests -q` en ejecución aislada: **544 pruebas OK**.
- Copias de la versión pública sincronizadas: `static/` y `static/assets` idénticas a `api/_static/`.

Nota de entorno: si se lanzan a la vez los tests de navegador y la suite Python, dos pruebas de `test_session_ui_feedback.py` fallan por contención de puerto y de Tcl; aisladas pasan. No es un defecto del producto.

## Aceptación

Revisión independiente final `deleg_604d244d`: **passed: true**, con 72 comprobaciones propias en navegador real, 28/28 del test del repositorio y el caso G1 reproducido en rojo sirviendo la función antigua solo en memoria. Reprodujo las seis variantes de estado incompleto (sin `ai`, sin `status`, no textual, nulo, HTTP 500 y JSON inválido) con 0 POST, comprobó que calculadora, biblioteca y comparador siguen funcionando, y confirmó B8-1 a B8-4, la regresión de teclado y la ausencia de fugas en DOM, storage, URL y errores. Límites declarados: chat configurado con fixture `test_only`, comparación semántica (no byte a byte), fallos de almacenamiento simulados y solo Chrome headless.

## Límites

- Navegador de escritorio headless; dos pestañas CDP del mismo perfil, no dos ventanas ni dispositivos.
- Sin Vercel, sin proveedor real, sin retención del proveedor, sin lector de pantalla.
- El fixture simula `/api/chat`; el servidor real se usa para verificar que no hay POST cuando la IA está apagada.
- La revisión independiente final (`deleg_604d244d`) decide la aceptación; hasta entonces B8 está implementado, no cerrado.
