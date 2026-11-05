# Evidencia B1.3–B1.6 · Historial de Pai

**Corte de la medición:** 2026-11-04 05:54:40 +01 (04:54:40 UTC)
**Árbol:** `C:/Users/aleja/Downloads/App Financiera`, rama `master`, HEAD `f3729d4` + cambios sin commit.
**Artefacto medido:** `api/_static` (copia pública; idéntica a `app/static` en el corte), congelado en una instantánea byte a byte para que la medición no se mezcle con ediciones concurrentes.
**Navegador:** Chromium headless real, controlado por CDP (WebSocket), perfil limpio, ventana 1280×1000.
**Backend del chat:** fixture HTTP loopback sintético en `127.0.0.1` (sin Groq, sin red externa, sin `.env`, sin credenciales). Respuestas `provider_mode: "test_only"` y textos ficticios.
**Prueba:** `tests/b1_history_consent.test.cjs` (nueva, solo lectura sobre el producto).
**Resultado:** **61 comprobaciones, 57 PASS, 2 fallos de producto, 2 observaciones y 0 fallos de arnés.** Salida `1` (RED) por los dos fallos de producto; el arnés está completo.

> Los dos fallos son de **claridad de la información**, no de privacidad: el historial nunca viaja sin consentimiento, se limita a dos turnos, se borra de forma inmediata y no persiste. El detalle está en los criterios 2 y 4.

---

## 1. Qué se ha medido y qué no

### Medido

- Estado inicial del control de historial y su separación de los consentimientos de pregunta y mapa.
- Texto visible de la etiqueta, avisos del formulario y página de privacidad.
- Cuerpos HTTP reales de `POST /api/chat` en 13 cuerpos registrados (de 14 envíos; uno se bloqueó a propósito para probar la caída de red), capturados por el fixture.
- Comportamiento con consentimiento, sin consentimiento, al desmarcar y al volver a marcar.
- Borrado en reposo y **con una petición en vuelo**, incluida la guarda de revisión.
- Efecto del borrado sobre la copia local del mapa y sobre el perfil en memoria.
- Errores 500, respuesta malformada y caída de red; reintentos; contenido mostrado.
- Persistencia en `localStorage`, `sessionStorage`, cookies, URL, `window.name`, IndexedDB y logs de consola.
- Defensa del servidor real del prototipo con proveedor ficticio: 1 turno, 2 turnos, 3 turnos, consentimiento desajustado, ausencia de consentimiento y rol `system` inyectado.

### No medido / fuera de alcance

- Proveedor real (Groq) o cualquier red externa: prohibido por el encargo.
- Respuestas de una IA real y su uso semántico del historial; todas las respuestas son sintéticas.
- Modo `provider_mode: "external"`: el cliente **no guarda** historial en ese modo (`app.js:854`), así que la función es inerte fuera de `test_only`.
- Viewports móviles y lectores de pantalla; solo se comprobó visibilidad y etiquetado básico a 1280×1000.
- Retención del historial en un proveedor real: no auditada. El servicio local no lo persiste; solo lo pasa al proveedor en la petición (el `FakeChatProvider` de la sonda guarda las peticiones en memoria porque es un fixture de prueba).

---

## 2. Veredicto por criterio

| # | Criterio | Veredicto | Evidencia principal |
|---|---|---|---|
| 1 | Desactivado por defecto y control separado del consentimiento de la pregunta | **CUMPLE** | B1.3a–B1.3k; `app.js:710,736,737,739`; capturas 01 y 08 |
| 2 | El texto explica qué se conserva, cuántos turnos, dónde y qué se reenvía | **CUMPLE** (reserva: B1.4d) | B1.4a–B1.4g; `app.js:739,2746`; no enumera «preguntas/respuestas» |
| 3 | Sin consentimiento no viaja `history`; con consentimiento viaja solo lo visible, con tope de dos turnos | **CUMPLE** | B1.5a–B1.5l; HTTP 1–5; sonda de servidor 1–3 |
| 4 | Desmarcar deja de reenviar **y lo explica** | **NO CUMPLE** (parcial) | B1.6m–B1.6q; B1.6p falla; captura 06 |
| 5 | Borrado visible, inmediato y verificable, también a mitad de conversación, sin borrar mapa ni perfil | **CUMPLE** | B1.6a–B1.6k; capturas 04 y 05 |
| 6 | Tras borrar no se reenvía nada y el siguiente turno parte limpio | **CUMPLE** | B1.6g, B1.6h, B1.6l; HTTP 6 y 8 |
| 7 | Los errores del chat no filtran contenido ni historial | **CUMPLE** (con límite) | B1.7a–B1.7e; OBS-7f; `app.js:78,869` |
| 8 | Sin persistencia del historial en localStorage/sessionStorage/URL ni logs | **CUMPLE** | B1.6r–B1.6u; `chat_context_model.js:5,13,15`; `app.py:652-653` |

**Lectura del veredicto:** 7 criterios cumplen (uno con reserva de redacción y otro con un límite de endurecimiento) y 1 no cumple en su mitad explicativa. No se ha encontrado ninguna fuga de historial ni envío sin consentimiento.

---

## 3. Artefacto y reproducibilidad

### 3.1. Instantánea medida

El árbol estaba siendo editado por otro agente durante la sesión. `api/_static/app.js` cambió al menos en estas versiones:

| Hora de la versión (mtime local) | SHA-256 (12) | Nota |
|---|---|---|
| 05:29 | `a8bb41bdd1f7` | medida y descartada por cambio posterior |
| 05:48 | `b0724c1464dc` | medida y descartada por cambio posterior |
| 05:51 | `f64389b206bb` | medida y descartada por cambio posterior |
| **05:52:37** | **`79e23de3176f`** | **instantánea congelada y medida; estable antes, durante y después** |

La instantánea está en:

`C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/cache/scratch/b1-static-79e23de3176f/`

Hash de la instantánea = hash del árbol vivo en el momento del corte:

- `app.js` = `79e23de3176f921529ee90e0da52414f738e9318250d62031a3e63d848f44991`
- `index.html` = `0f67ca8162decaf6c959a26ea5812913a621a44bcab6d83a97adb0fa3a66cc20`
- `chat_context_model.js` = `77d03d3d54c33a1119a676cd3593db2d6a9c3e6bea16f06e805bc022875b343d`
- `profile_model.js` = `0f24fb027b54b6e166f8bbe42a79d08e2f31ccfcd42994013050a88dded72b89`

`api/_static/app.js` y `app/static/app.js` tenían el mismo hash en el corte; la copia pública y la del prototipo estaban sincronizadas. Las líneas citadas en este documento corresponden a `79e23de3176f`.

Backend usado en la sonda de servidor (sin cambios desde las 03:04):

- `backend_services.py` = `dbb59a0dedf251e8b9f16b1480f0dfeaf54f24de5b33e6ca7eb77e2cfab1f0c0`
- `chat_context.py` = `39a6464f95d8116a5dec3f8a8b3d56b894ef2817a334d65a539826043dbe728c`
- `app.py` = `3dbe5d48503a5d580f2a7865439c8f1b8b4087aa756960e95d9a95317e367c3d`

Prueba:

- `tests/b1_history_consent.test.cjs` = `147c59b5f76408dfbff4743b549d8d214645ea9d247e5b3a5d546b43a9fb4400`

### 3.2. Cómo se ejecuta

```bash
# Medición normal contra api/_static
node tests/b1_history_consent.test.cjs

# Medición reproducible contra la instantánea congelada
B1_STATIC_ROOT=".../b1-static-79e23de3176f" \
B1_SHOTS=".../b1-historial-79e23d" \
node tests/b1_history_consent.test.cjs
```

La prueba abre Chrome headless, levanta dos fixtures loopback (uno con historial disponible y otro sin él), siembra un perfil ficticio en `localStorage`, ejecuta 14 envíos (13 cuerpos registrados; uno bloqueado a propósito) y guarda capturas y JSON de evidencia. **No modifica código de producción, no lee `.env`, no usa Groq y no hace peticiones fuera de `127.0.0.1`.** La comprobación B1.3k confirma que la página no carga recursos externos.

---

## 4. Criterio 1 · Desactivado por defecto y control separado

**Veredicto: CUMPLE.**

### Código

- `app.js:737` crea la casilla sin `checked` y la desactiva si el proveedor no anuncia la capacidad:
  `const historyConsent = el("input", {type:"checkbox", id:"chat-history-consent", disabled:chatCapabilities?.history !== true});`
- `app.js:710` es el consentimiento de la pregunta (`#chat-consent`), con su propia etiqueta.
- `app.js:736` es el consentimiento del mapa (`#chat-context-consent`).
- `app.js:739` es el consentimiento del historial (`#chat-history-consent`), con etiqueta propia.
- `app.js:712` avisa: «Mapa e historial: opcionales y con consentimiento aparte. El historial sigue desactivado en el servidor normal…».

### Navegador

| Check | Resultado | Valor observado |
|---|---|---|
| B1.3a | PASS | `#chat-history-consent` con `checked === false` aunque el fixture anuncia `history: true` |
| B1.3b | PASS | `#chat-consent` también nace `checked === false` |
| B1.3c | PASS | el checkbox de historial no está anidado en la etiqueta de la pregunta ni en la del mapa; son tres controles distintos |
| B1.3d | PASS | el control es visible (`offsetParent !== null`) |
| B1.3e | PASS | el aviso dice «historial: habilitado» en el proveedor de prueba |
| B1.3f | PASS | el callout declara mapa e historial «opcionales y con consentimiento aparte» |
| B1.3i | PASS | cargar la página no hace ningún `POST /api/chat` |
| B1.3j | PASS | marcar solo la casilla de historial no envía nada; hace falta pulsar el botón |
| B1.3g | PASS | con un proveedor sin capacidad, la casilla queda `checked=false` y `disabled=true` |
| B1.3h | PASS | el aviso dice «historial: desactivado» |
| B1.3k | PASS | 0 recursos `http(s)` fuera del origen del fixture |

### Capturas

- `01-chat-consentimientos.png`: formulario con la casilla de historial desmarcada y el botón «Borrar historial de esta pestaña» visible.
- `08-historial-no-disponible.png`: casilla atenuada/desactivada y aviso «historial: desactivado».

### Lectura

El valor por defecto es seguro y el control es genuinamente independiente: activar el historial no marca ni el consentimiento de la pregunta ni el del mapa. La comprobación con capacidad ausente demuestra además que el control no se puede forzar cuando el proveedor no lo ofrece. El servidor público declara `history: false` (`api/index.py:163`), por lo que en la versión pública la función no está disponible.

---

## 5. Criterio 2 · Información clara

**Veredicto: CUMPLE (con reserva).** Los cuatro datos principales están, pero el texto no enumera el contenido y no hay una lista visible de lo almacenado.

### Texto exacto de la etiqueta

> «Autorizo conservar en esta pestaña y reenviar hasta dos turnos anteriores ficticios en esta prueba; sin guardado automático.»

(`app.js:739`)

### Texto exacto de la página de privacidad

> «Historial: es opcional y separado del mapa. Vive en la memoria de esta pestaña y solo se reenvía con su propia autorización; no se guarda en el almacenamiento local.»

(`app.js:2746`)

### Desglose del criterio

| Elemento exigido | ¿Está? | Texto / comprobación |
|---|---|---|
| Cuántos turnos (máximo dos) | Sí | «hasta dos turnos» — B1.4a PASS |
| Dónde (solo esta pestaña) | Sí | «en esta pestaña» — B1.4b PASS |
| Sin guardado automático | Sí | «sin guardado automático»; privacidad: «no se guarda en el almacenamiento local» — B1.4b/B1.4f PASS |
| Qué se reenvía | Sí, como categoría | «reenviar hasta dos turnos anteriores» — B1.4c PASS |
| Qué se conserva, nombrado explícitamente | **No** | la etiqueta dice «turnos anteriores ficticios», pero no «tus preguntas y las respuestas de Pai» ni «mensajes» — B1.4d **FAIL** |
| Es una prueba con contenido ficticio | Sí | «ficticios en esta prueba» — B1.4e PASS |

### Reserva

La etiqueta comunica bien el **cuántos**, el **dónde** y el **no guardado automático**. Para «qué se conserva» usa la palabra «turnos», que en el contexto de un chat es razonable pero no explícita: no dice que se guardan la pregunta de la persona y la respuesta de Pai, y **no hay ninguna lista o contador en la interfaz** que permita ver exactamente qué se va a reenviar antes de enviarlo. La página de privacidad tampoco enumera el contenido; solo dice «Historial».

Por eso: **CUMPLE (con reserva)**. Si la aceptación exige que el texto nombre el contenido de forma literal (preguntas/respuestas/mensajes) o que se pueda auditar antes del envío, entonces este criterio debe considerarse **NO CUMPLE** en ese punto concreto. El fallo B1.4d es el que sostiene esta reserva.

### Capturas

- `01-chat-consentimientos.png`: etiqueta completa junto al control.
- `02-privacidad-historial.png`: sección «Qué sale de este navegador» con la línea de historial.

---

## 6. Criterio 3 · Sin consentimiento no viaja; con consentimiento, solo lo visible y dos turnos

**Veredicto: CUMPLE** (en el escenario `test_only`; ver límite al final).

### Evidencia HTTP real del navegador

Cuerpos capturados por el fixture; `null` significa que la clave no existe en el JSON.

| Seq | Situación | Claves del cuerpo | `history` | `context_consent` |
|---|---|---|---|---|
| 1 | Pregunta con consentimiento de chat, sin historial | `consent, message` | ausente | ausente |
| 2 | Primer turno con consentimiento de historial | `consent, context_consent, history, message` | `[]` (0) | `{context:false, history:true}` |
| 3 | Segundo turno consentido | ídem | 2 mensajes (T2) | `{context:false, history:true}` |
| 4 | Tercer turno consentido | ídem | 4 mensajes (T2+T3) | `{context:false, history:true}` |
| 5 | Cuarto turno consentido | ídem | 4 mensajes (T3+T4); T2 ya no viaja | `{context:false, history:true}` |
| 9 | Tras desmarcar el historial | `consent, message` | ausente | ausente |
| 10 | Al volver a marcar | ídem | 2 mensajes (T8); T9 no aparece | `{context:false, history:true}` |
| 11 | Error 500 con historial consentido | ídem | 4 mensajes | `{context:false, history:true}` |
| 12 | Respuesta malformada con historial consentido | ídem | 4 mensajes | `{context:false, history:true}` |

Cuerpos completos en `b1_http_evidence.json`.

### Comprobaciones

| Check | Resultado | Qué demuestra |
|---|---|---|
| B1.5a | PASS | sin consentimiento de historial no existe la clave `history` |
| B1.5b | PASS | tampoco se envía `context_consent`; no se activa el mapa por arrastre |
| B1.5c | PASS | tras un turno sin consentimiento la memoria sigue vacía |
| B1.5d | PASS | con consentimiento, `context_consent` lleva `context:false` y `history:true` |
| B1.5e | PASS | activar historial no envía `context` ni ramas del perfil |
| B1.5f | PASS | el primer turno consentido envía `history: []` (aún no hay anteriores) |
| B1.5g | PASS | la memoria guarda exactamente la pregunta y la respuesta mostradas |
| B1.5h | PASS | la respuesta guardada es la que aparece en `#chat-feedback` |
| B1.5i | PASS | el segundo turno reenvía el turno anterior completo y en orden |
| B1.5j | PASS | el tercer turno reenvía exactamente 4 mensajes (dos turnos) |
| B1.5k | PASS | el tope se mantiene: el turno más antiguo se descarta y no se reenvía |
| B1.5l | PASS | cada entrada tiene solo `role` y `content`; no hay campos ocultos ni perfil |

**Precisión sobre «solo lo visible»:** la comprobación compara cada mensaje reenviado con el texto que se mostró en `#chat-feedback` al recibir ese turno. No existe una lista de historial en la interfaz, así que no se puede contrastar contra un transcript visible; lo que sí se descarta es cualquier campo oculto, rama del perfil o mensaje que no se haya mostrado. El turno anterior deja de estar en pantalla cuando llega el siguiente, pero su texto es exactamente el que la persona vio.

### Código

- `app.js:786`: `payload.history = PaideiaChatContext.history().slice(-4);` — 4 mensajes = 2 turnos.
- `chat_context_model.js:13`: `turns = turns.concat([...]).slice(-4);` — el propio modelo también recorta a 4.
- `chat_context_model.js:12`: rechaza mensajes de más de 1.000 caracteres.
- `app.js:777`: `includeHistory` se lee del checkbox en el momento del envío, no de un valor por defecto.

### Defensa en el servidor (sonda loopback real)

Servidor del producto (`app/app.py`) con `FakeChatProvider` y `history_enabled=True`, peticiones sintéticas a `127.0.0.1`:

| Caso | HTTP | Código | Resultado |
|---|---|---|---|
| 1 turno (2 mensajes) con consentimiento de historial | 200 | — | `provider_mode: test_only` |
| 2 turnos (4 mensajes) | 200 | — | `provider_mode: test_only` |
| 3 turnos (6 mensajes) | 400 | `INVALID_CHAT_CONTEXT` | rechazado |
| `history` presente pero `context_consent.history=false` | 403 | `CHAT_CONTEXT_NOT_ALLOWED` | rechazado |
| `history` sin `context_consent` | 403 | `CHAT_CONTEXT_NOT_ALLOWED` | rechazado |
| rol `system` inyectado en `history` | 400 | `INVALID_CHAT_CONTEXT` | rechazado |
| sin consentimiento de la pregunta | 403 | `CHAT_CONSENT_REQUIRED` | rechazado |

Código del servidor:

- `chat_context.py:40-47`: exige lista, máximo 4 mensajes, longitud par, roles `user`/`assistant` y máximo 6.000 caracteres totales.
- `backend_services.py:371-380`: exige que `context_consent.history` coincida con la presencia de `history` y que el historial esté habilitado.
- `backend_services.py:389-391`: añade el historial como mensajes no confiables después del sistema y antes de la pregunta actual.

### Límite de alcance

`app.js:854` solo añade el turno a la memoria si `result.provider_mode === "test_only"`. Con un proveedor externo (`"external"`) el historial **nunca crece**, aunque el consentimiento esté marcado; además la versión pública declara `history: false` (`api/index.py:163`). Es una decisión de seguridad coherente con B8 («el historial sigue desactivado en el servidor normal»), pero significa que la función de dos turnos es, hoy, una función de prueba sintética. La verificación de este criterio es válida para ese ámbito.

---

## 7. Criterio 4 · Desmarcar deja de reenviar y lo explica

**Veredicto: NO CUMPLE (parcial).** La conducta es correcta; falta la explicación en el momento de desmarcar.

### Lo que sí cumple

| Check | Resultado | Qué demuestra |
|---|---|---|
| B1.6m | PASS | desmarcar no altera el consentimiento de la pregunta (`chat=true`) ni el del mapa (`context=false`) |
| B1.6n | PASS | el siguiente envío no lleva `history` ni `context_consent` |
| B1.6o | PASS | el turno enviado sin consentimiento no se añade a la memoria |
| B1.6q | PASS | al volver a marcar, reenvía solo el turno que sigue en memoria (T8); el turno T9 enviado sin consentimiento no aparece |

Evidencia HTTP: seq 9 (`keys=consent,message`, sin `history`) y seq 10 (`history` = solo T8). La comprobación B1.6q compara el contenido exacto y verifica que `MARCA-B1-T9` no está en el cuerpo.

### Lo que no cumple

| Check | Resultado | Observación |
|---|---|---|
| B1.6p | **FAIL** | al desmarcar, `#chat-feedback` no cambia y no aparece ningún texto que diga que el historial deja de reenviarse |

Evidencia:

- `app.js:737` crea el checkbox, pero **no hay ningún `change`/`input` listener** sobre `#chat-history-consent`.
- Antes y después de desmarcar, el feedback es idéntico (capturado en B1.6p):
  `PRUEBA SINTÉTICA — NO ES UNA IA REAL. Respuesta sintética 8… Trazabilidad…`
- La captura `06-historial-desmarcado.png` muestra la casilla vacía, pero ningún aviso nuevo junto a ella.

La etiqueta permanente («Autorizo conservar… y reenviar…») y la página de privacidad («solo se reenvía con su propia autorización») explican la regla general, pero el criterio pide que **al desmarcar** se explique. Hoy la persona tiene que inferirlo. Es un fallo de claridad, no de privacidad: el comportamiento seguro sí ocurre.

---

## 8. Criterio 5 · Borrado visible, inmediato, verificable, en mitad del flujo, sin tocar mapa ni perfil

**Veredicto: CUMPLE.**

### Código

`app.js:741`:

```js
const historyClear = button("Borrar historial de esta pestaña", () => {
  historyRevision += 1;
  PaideiaChatContext.clear();
  feedback.textContent = "Historial borrado de esta pestaña. Los mensajes ya enviados al proveedor no se borran.";
}, "button button-quiet", {id:"chat-history-clear", type:"button"});
```

`app.js:854` protege la respuesta en vuelo:

```js
if (!withheld && includeHistory && historyConsent.checked && historyAtSend === historyRevision && result.provider_mode === "test_only" && result.answer) {
```

### Comprobaciones

| Check | Resultado | Qué demuestra |
|---|---|---|
| B1.6a | PASS | botón visible con el texto exacto «Borrar historial de esta pestaña» y tamaño > 0 |
| B1.6b | PASS | el clic vacía la memoria en el mismo tick: `history.length 4 → 0` |
| B1.6c | PASS | mensaje visible: «Historial borrado de esta pestaña. Los mensajes ya enviados al proveedor no se borran.» |
| B1.6d | PASS | `localStorage["paideia.profile.v2"]` queda **byte a byte idéntica** |
| B1.6e | PASS | el resumen del perfil sigue mostrando «Aprender conceptos básicos», «Entre 1 y 3 años», «1.234,56 €» y «500,00 €» |
| B1.6f | PASS | el historial sigue a 0 tras cambiar de sección y volver al chat |
| B1.6i | PASS | se puede borrar con una petición en vuelo; la memoria pasa a 0 antes de que llegue la respuesta |
| B1.6j | PASS | la respuesta que llega después del borrado **no** se vuelve a guardar (guarda `historyAtSend === historyRevision`) |
| B1.6k | PASS | esa respuesta se sigue mostrando, pero no queda en memoria |

### Capturas

- `04-historial-borrado.png`: botón visible y mensaje de borrado en el feedback.
- `05-mapa-intacto.png`: resumen del perfil intacto después del borrado.

### Lectura

El borrado es visible (botón y mensaje), inmediato (mismo tick), verificable (la memoria queda a 0 y el siguiente POST lo confirma) y funciona en mitad de una conversación, incluso con una respuesta en vuelo. No toca la copia local del mapa ni el perfil en memoria. La guarda de revisión es la pieza clave que evita que la respuesta tardía resucite el historial.

**Matiz menor, no bloqueante:** el botón está siempre activo aunque el historial esté vacío; en ese caso el mensaje «Historial borrado» se muestra igualmente. No afecta a la privacidad, pero un estado «No hay historial que borrar» sería más preciso.

---

## 9. Criterio 6 · Tras borrar no se reenvía nada y el siguiente turno parte limpio

**Veredicto: CUMPLE.**

| Check | Resultado | Qué demuestra |
|---|---|---|
| B1.6g | PASS | tras borrar, el siguiente POST lleva `history: []` y **ningún** marcador de T2–T5 en el cuerpo |
| B1.6h | PASS | la memoria solo contiene el turno nuevo (T6), sin turnos previos |
| B1.6l | PASS | tras el borrado en vuelo, el turno siguiente también lleva `history: []` |

Evidencia HTTP: seq 6 (`history_len=0` tras el borrado) y seq 8 (`history_len=0` tras el borrado en vuelo). La comprobación B1.6g busca además los marcadores T2, T3, T4 y T5 en el cuerpo crudo y no los encuentra.

**Precisión honesta:** el cuerpo sigue llevando la clave `history` con un array vacío (`[]`) y `context_consent.history=true`. No se reenvía **ningún mensaje** anterior, pero la clave vacía sí viaja. Si el criterio exige que ni siquiera aparezca la clave, eso no se cumple; si exige que no se reenvíe contenido, se cumple. La interpretación razonable es la segunda y así se registra.

---

## 10. Criterio 7 · Los errores del chat no filtran contenido ni historial

**Veredicto: CUMPLE (con límite de endurecimiento).**

### Comprobaciones

| Check | Resultado | Qué demuestra |
|---|---|---|
| B1.7a | PASS | un 500 muestra «Fallo sintético del proveedor; no hay reintento automático.»; el DOM no contiene T11 ni T10 |
| B1.7b | PASS | el error no añade el turno fallido a la memoria |
| B1.7c | PASS | una respuesta JSON malformada muestra el mensaje genérico «La respuesta del servicio local no tenía el formato esperado.»; no aparece el marcador `FUGA_MARCADOR_JSON` |
| B1.7d | PASS | una caída de red (URL bloqueada por CDP) muestra «No se pudo conectar con el servicio local…»; sin T13 ni T12 en el DOM |
| B1.7e | PASS | 2 errores HTTP → 2 POST; caída → 1 intento de red y 0 peticiones al servidor; sin reintentos automáticos |

Los cuerpos 11 y 12 llevaban 4 mensajes de historial y el DOM de error no mostró ninguno. La captura `07-error-chat.png` muestra solo el mensaje de error.

### Límite

El cliente muestra **literalmente** el `error.message` que devuelve el servidor:

- `app.js:78`: `throw new ApiFailure(typeof error.message === "string" ? error.message : …)`
- `app.js:225`: `apiErrorText` devuelve `error.message` para `ApiFailure`
- `app.js:869`: `feedback.textContent = apiErrorText(error)`

El servidor incluido usa mensajes estáticos y no echa contenido en ellos (`backend_services.py:344-385,426`), por lo que el stack real no filtra. Pero la sonda OBS-7f demuestra que, si un servidor futuro devolviera un `error.message` con historial, la interfaz lo pintaría tal cual: **no hay redacción en el cliente**. No es un fallo del stack actual; es una recomendación de endurecimiento (mapear códigos a textos fijos o no mostrar mensajes arbitrarios).

---

## 11. Criterio 8 · Sin persistencia en localStorage/sessionStorage/URL ni logs

**Veredicto: CUMPLE.**

| Check | Resultado | Qué demuestra |
|---|---|---|
| B1.6r | PASS | ningún marcador de pregunta o respuesta en `localStorage`, `sessionStorage`, cookies, URL, `window.name` ni IndexedDB |
| B1.6s | PASS | la única clave local es `paideia.profile.v2` (el mapa), no el historial |
| B1.6t | PASS | tras recargar, `history.length === 0` y ningún marcador visible; el historial no se restaura |
| B1.6u | PASS | 0 entradas de consola/log con marcadores; las 2 entradas capturadas son solo «Failed to load resource» de los 500/400 provocados |

### Código

- `chat_context_model.js:5`: `let turns=[];` — memoria de módulo, no almacenamiento.
- `chat_context_model.js:13`: `turns = … .slice(-4);` — tope en memoria.
- `chat_context_model.js:15`: `function clear(){turns=[];}` — borrado real.
- `app.js`: **0 ocurrencias de `console.`**; el módulo del historial **0 ocurrencias de `localStorage`/`sessionStorage`**.
- `app.py:652-653`: `def log_message(self, fmt, *args): return` — el servidor no escribe logs de peticiones.

### Matiz

El mapa sí se guarda en `localStorage` cuando la persona lo autoriza en Privacidad; eso es un dato distinto y esperado. La comprobación B1.6s exige que la única clave sea `paideia.profile.v2` y que no contenga marcadores de historial. El historial no toca ese almacén.

---

## 12. Hallazgos y recomendaciones (sin tocar código en este trabajo)

1. **B1.4d — nombrar el contenido.** La etiqueta dice «dos turnos anteriores ficticios», pero no «tus preguntas y las respuestas de Pai». Añadir esas palabras (o un desplegable «Ver qué se guardará») cerraría la reserva del criterio 2. Hoy no hay forma de auditar visualmente la lista antes de enviar.
2. **B1.6p — aviso al desmarcar.** Añadir un `change` sobre `#chat-history-consent` que muestre, por ejemplo: «Historial desmarcado: no se reenviará ni se conservará en esta pestaña. Lo ya enviado al proveedor no se puede borrar desde aquí.» Es la pieza que falta para el criterio 4.
3. **Errores del servidor.** Mapear códigos conocidos a textos fijos en el cliente, en lugar de renderizar `error.message` arbitrario. El servidor actual ya usa mensajes estáticos; esto es defensa en profundidad.
4. **Alcance real del historial.** `app.js:854` solo guarda en `test_only`. Si el producto quiere historial con proveedor real, hay que revisar esa guarda con revisión de privacidad; hoy la función es una demostración sintética.
5. **Botón de borrado siempre activo.** Con 0 entradas sigue diciendo «Historial borrado». Un estado «No hay historial que borrar» sería más preciso; no afecta a la privacidad.
6. **Contradicción visual en modo prueba.** En `test_only`, el panel lateral dice «Chat IA no conectado» mientras el formulario permite enviar y responde con «PRUEBA SINTÉTICA». No es un fallo de B1.3–B1.6, pero conviene alinear el texto para que la persona no reciba mensajes contradictorios sobre si el chat está conectado.

---

## 13. Limitaciones de la verificación

- **Proveedor sintético.** No se ha usado Groq ni red externa. Las respuestas son ficticias y el historial se limita a `provider_mode: "test_only"`. No se puede concluir cómo usaría un modelo real dos turnos de contexto.
- **Instantánea, no árbol vivo.** El archivo `app.js` cambió cuatro veces durante la sesión (05:29, 05:48, 05:51, 05:52). La medición válida es la de `79e23de3176f`, congelada y verificada byte a byte; si el árbol sigue cambiando, hay que repetir la medición sobre el nuevo hash. La instantánea coincide con el árbol vivo en el corte de las 05:54.
- **Un solo viewport.** 1280×1000; no se ha probado en móvil ni con zoom alto. La visibilidad del control se comprobó con `offsetParent` y rectángulo, no con un lector de pantalla.
- **El fixture no es el servidor del producto.** Los cuerpos HTTP del navegador vienen del fixture; la defensa del servidor se comprobó aparte con la sonda loopback del servidor real y proveedor ficticio.
- **Los dos FAIL son de claridad.** No hay evidencia de envío sin consentimiento, de reenvío tras borrar ni de persistencia. Si el criterio de aceptación exige la explicación literal al desmarcar o el nombre explícito del contenido, el veredicto correspondiente es «no cumple»; si basta la descripción por «turnos» y la etiqueta permanente, el criterio 2 puede aceptarse con la reserva indicada.

---

## 14. Índice de evidencia

### Prueba

- `tests/b1_history_consent.test.cjs` — 61 comprobaciones, sin modificar código de producción.
- `b1_evidence.json` — resultado completo, hashes, checks, peticiones y capturas.
- `b1_http_evidence.json` — 13 cuerpos POST completos.
- `b1_server_probe.py` — script de la sonda loopback del servidor real (sin red externa).
- `b1_server_probe.json` — 7 casos de la sonda del servidor real.

Ruta base de los artefactos:

`C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/cache/scratch/b1-historial-79e23d/`

### Capturas (revisadas visualmente)

| Archivo | Qué muestra |
|---|---|
| `01-chat-consentimientos.png` | Formulario con la casilla de historial desmarcada, etiqueta completa y botón de borrado |
| `02-privacidad-historial.png` | Sección «Qué sale de este navegador» y la línea «Historial: …» |
| `03-historial-consentido.png` | Turno respondido con historial consentido y feedback sintético |
| `04-historial-borrado.png` | Botón de borrado y mensaje «Historial borrado de esta pestaña…» |
| `05-mapa-intacto.png` | Resumen del perfil con objetivo, horizonte e importes tras borrar el historial |
| `06-historial-desmarcado.png` | Casilla de historial vacía; **sin** aviso nuevo al desmarcar (fallo B1.6p) |
| `07-error-chat.png` | Error 500 mostrado sin pregunta ni historial |
| `08-historial-no-disponible.png` | Casilla atenuada/desactivada y aviso «historial: desactivado» |

### Confirmación de no modificación

- No se ha editado `app.js`, `styles.css`, `index.html`, `api/_static/*` ni ningún archivo de producción.
- No se ha editado la prueba existente `tests/b8_privacy_regression.test.cjs`.
- No se ha hecho commit, push ni deploy.
- Solo se han creado: esta evidencia, la prueba nueva y los artefactos de scratch.

## Actualización: los dos fallos de claridad corregidos

Medida sobre la instantánea `79e23de3176f`, esta verificación dejó dos fallos de producto, ambos de claridad y ninguno de privacidad. Se corrigieron después del cierre de B9, porque comparten archivo con ese bloque:

- **B1.4d** — la etiqueta del historial ahora dice: «Autorizo conservar en esta pestaña, solo durante esta prueba con contenido ficticio, mis preguntas y las respuestas de Pai de hasta dos turnos anteriores (cuatro mensajes como máximo) y reenviarlos con la pregunta siguiente; sin guardado automático.»
- **B1.6p** — al marcar o desmarcar la casilla, `#chat-feedback` explica el efecto inmediato: qué se reenviará y que lo ya conservado sigue en esta pestaña hasta pulsar «Borrar historial de esta pestaña».

`node tests/b1_history_consent.test.cjs` pasa de 58 a **59 comprobaciones verdes, 0 fallos de producto**, en la misma ejecución que B8 (28/28) y B9 (24/24). Los límites de la medición original siguen vigentes: sin lector de pantalla, sin proveedor real y con navegador de escritorio.

Copia sin aviso al desmarcar: `06-historial-desmarcado.png` refleja el estado anterior; la captura nueva del aviso está en el scratch de la corrección.
