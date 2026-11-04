# B1 — avisos de timeout, ciclo 2 (evidencia)

**Fecha del corte:** 2026-11-04 08:40 +01 (Europe/Madrid)
**Árbol:** `C:/Users/aleja/Downloads/App Financiera`, sin commit ni restauración.
**Estado:** listo para **revisión independiente**. Este documento no declara aprobación.

## 1. Qué se corrigió

Solo `app.js` y sus pruebas. No se tocó backend, filtros, `.env`, proveedor real ni app.py.

- **Mensaje exacto enviado:** `state.chatTicketQuery` y `state.chatUncertainQuery` ligan ticket e incertidumbre al texto que se envió. Una pregunta editada ya no recibe el botón «Reenviar pregunta» ni el aviso de que «la pregunta se conserva».
- **Edición durante el vuelo:** al fallar el envío A, si el cuadro contiene B, el aviso habla del envío anterior y dice que la pregunta actual todavía no se ha enviado. No afirma que A siga en el cuadro.
- **Ticket posiblemente consumido:** tras cualquier timeout de un intento que usó ticket, el ticket se descarta. El aviso dice que pudo quedar reclamado o cerrado y que un reenvío manual puede duplicar el turno o ser rechazado. El siguiente POST no adjunta el ticket.
- **`send_state` conservador:** `not_started` y `completed` se presentan como estado del último intento de transporte, sin convertirlos en prueba de que el turno completo no se envió o de que el proveedor lo procesó. `LOCAL_TIMEOUT`, `CHAT_TIMEOUT`/504 y 429 no prometen reenvío ni resultado.
- **Foco:** si el botón de envío tenía el foco, se traslada al cuadro de texto antes de deshabilitarlo; al terminar, si el foco quedó perdido en `BODY`, se devuelve al cuadro. No se roba el foco si el usuario lo movió a otro control.
- **Sin cambios en garantías B8:** consentimiento de pregunta, mapa e historial independientes; sin persistencia de mensajes; sin POST automático; edición permitida durante el vuelo.

## 2. Regresiones añadidas (primero en rojo)

En `prototipos/paideia-local/tests/chat_frontend_contract.test.cjs` (VM Node):

- editar tras timeout no etiqueta la pregunta nueva como reenvío;
- editar durante el vuelo no afirma que la pregunta anterior se conserva;
- ticket de un intento sin confirmar se descarta y no se adjunta al siguiente envío;
- `not_started`/`completed` no prueban el resultado del turno completo.

En `tests/b1_history_consent.test.cjs` (Chromium headless + fixture loopback):

- B1.9a/B1.9b: edición tras timeout y rerender de la página;
- B1.9c: edición durante el vuelo;
- B1.9d/B1.9e: ticket usado y descartado, sin reutilización posterior;
- B1.9f/B1.9g: mensajes conservadores para `send_state`;
- B1.9h: el foco no cae en `BODY` al deshabilitar el botón.

## 3. Resultados verificados

Ejecución serial, sin red externa, sin `.env`, sin proveedor real. Fixture HTTP en `127.0.0.1`.

| Prueba | Resultado |
|---|---|
| `node --test tests/chat_frontend_contract.test.cjs` (cwd `prototipos/paideia-local`) | **15/15 PASS** |
| `node tests/b1_history_consent.test.cjs` (cwd raíz) | **74 comprobaciones, 72 PASS, 0 fallos de producto, 0 fallos de arnés** |
| `node tests/b8_privacy_regression.test.cjs` | **28/28 PASS** |
| `node tests/b9_accessibility.test.cjs` | **32/32 PASS** |

Artefactos medidos:

- `api/_static/app.js` y `prototipos/paideia-local/static/app.js`: `5dce64dfe34f19352a01093025a24a347c5e0d57de196880adf47469b554b0b8` (idénticos).
- `tests/b1_history_consent.test.cjs`: `0c2a7a18eb241c4c4516e486be19e1709bf45bcd8a5ca3e0475f9c21dce4b938`.
- `prototipos/paideia-local/tests/chat_frontend_contract.test.cjs`: `1418ea160f8fe4d23c0e968954d4b855e5d3b87f6042aa307d47b1fbf321fa4b`.

Evidencia B1: `C:/Users/aleja/AppData/Local/Temp/b1-history-shots/b1_evidence.json` y capturas en la misma carpeta.

## 4. Límites y dudas que debe revisar una persona independiente

- No se probó Groq ni ningún proveedor real. `send_state` se interpreta desde el contrato del backend; no se observó una respuesta real con varias rondas de herramientas.
- La afirmación de que el ticket puede quedar reclamado/cerrado se deriva de `backend_services.py` (`finally: admission.complete(ticket)`), no de una prueba contra el almacén de admisión real.
- El cliente descarta el ticket ante cualquier timeout de un intento con ticket, aunque el backend quizá no lo hubiera reclamado. Es una decisión conservadora deliberada: prioriza no presentar una cola válida falsa sobre permitir un reintento con ticket.
- El foco se mueve al cuadro de texto cuando el envío partió del botón. Es intencionado para no dejarlo en `BODY`, pero cambia el punto de foco durante la espera; debe revisarse con lector de pantalla.
- B1.9h comprueba el foco en Chromium headless; no sustituye una prueba con lector de pantalla.
- No hay commit, restauración ni publicación. El estado queda en el árbol de trabajo para la revisión independiente.
