# Revisión adversarial del canal de afirmaciones cerradas

**Fecha:** 4 de noviembre de 2026 · **Objeto:** commit `1cf5ab5` («Integra el canal de afirmaciones cerradas (paideia-education-v2)») · **Ámbito:** `app` y su copia desplegada en `api/` · **Modo:** offline, proveedor falso, sin Groq y sin red.

**Veredicto: APTO CON SALVEDADES.**

El canal cumple la propiedad central que se le pedía: el modelo no puede introducir ni una palabra, ni una cifra, ni una atribución en el texto que ve la persona. Las 54 variantes de ataque probadas contra `validate_selection`, las 12 variantes de JSON hostil contra `parse_selection` y los 10 payloads de marcado contra la UI fueron rechazados o renderizados como texto literal; ninguna produjo texto parcial, ningún nodo peligroso y ninguna cifra del escenario apareció en `answer`.

No cumple, en cambio, tres extremos del contrato que el propio commit y la especificación declaran: la UI `claims_view.js` no se ejecuta en el flujo v2 real, el rechazo se convierte en `502` en lugar de `200 + claims.state="rejected"`, y una selección vacía se acepta como `empty` aunque `CATALOGO.md` §8 y `ACEPTACION.md` G18 exigen rechazarla. Son defectos de integración y de contrato, no vías de inyección. El detalle está en §9.

---

## 1. Instantánea verificada

`git log --oneline -3` sitúa `1cf5ab5` en cabeza. `git show --stat 1cf5ab5` devuelve 15 ficheros y `+1419/-16`:

```
 api/_static/app.js                                 |   4 +
 api/_static/claims_view.js                         | 115 ++++++++
 api/_static/index.html                             |   1 +
 api/_static/structured_education_ui.js             |  14 +
 app/claims_catalog.py         | 233 +++++++++++++
 app/claims_channel.py         | 154 +++++++++
 app/static/app.js             |   4 +
 app/static/claims_view.js     | 115 +++++++
 app/static/index.html         |   1 +
 app/static/structured_education_ui.js | 14 +
 app/structured_education.py   |  50 ++-
 app/structured_provider_adapter.py | 9 +-
 app/tests/claims_view.test.cjs | 224 +++++++++++++
 app/tests/test_claims_channel.py | 373 +++++++++++++++++++++
 app/tests/test_claims_integration.py | 124 +++++++++++++
```

Los seis SHA-256 facilitados coinciden exactamente:

| Fichero | SHA-256 observado |
|---|---|
| `claims_catalog.py` | `feb009e1823e9ba4205bf7de7b6d23267d069df8c9f6c4bb012269f5c13a53fa` |
| `claims_channel.py` | `0a1c40b31359a47bec84e925080f37077c2c23a76eb06818b0880cb2e748780a` |
| `structured_education.py` | `1f39d45b2c987fd9b72f9320b11b71c773cfe7839e485e0dee781c0c606f48b9` |
| `structured_provider_adapter.py` | `754dce0534f9974d2ee0f845c750da1ccc598441726acf7f9dddfd9f822e154b` |
| `static/claims_view.js` | `4ac51dbf0318e2afc4119c8ef5dcf52226b7ddc5ab1e221ff0b3ae2bde06eab5` |
| `static/structured_education_ui.js` | `3a87673c009a56f27342d998eb64512492ab357555563764612ab1f72d3ad3ae` |

Las copias de `api/_static/` son idénticas byte a byte a las del prototipo (`diff` sin salida para `app.js`, `index.html`, `claims_view.js` y `structured_education_ui.js`; `build_core.py` copia `static/` en bloque). `git diff 1cf5ab5 -- <los cuatro ficheros Python/JS del canal>` no devuelve nada: el árbol de trabajo, en lo que respecta a este commit, está limpio (hay cambios ajenos en `mission_ledger.py` y pruebas de misión que no se tocan aquí).

El catálogo es copia literal del bloque JSON de `docs/pai-afirmaciones/CATALOGO.md` §9: 39 entradas, mismos ids, mismo orden, `text/when/never_claim` idénticos (`json.loads` del bloque comparado entrada a entrada: `contenido identico: True`).

---

## 2. Suites ejecutadas

| Comando | Resultado |
|---|---|
| `python -m pytest tests/test_claims_channel.py tests/test_claims_integration.py -q` | **44 passed, 186 subtests passed** en 0,13 s |
| `node --test tests/claims_view.test.cjs` | **13 tests, 13 pass, 0 fail** |
| `python -m pytest tests -q` | **675 passed, 1 skipped, 7 warnings, 691 subtests passed** en 94,93 s |
| `node --test tests/*.test.cjs` | **108 tests, 108 pass, 0 fail** |

El `1 skipped` y los avisos de `tkinter` son preexistentes y ajenos al canal; no hay ningún fallo. Los números coinciden con los que declara el mensaje del commit (675 Python + 108 Node; 44 nuevas de canal/integración y 13 de UI).

---

## 3. Ataques al canal: `validate_selection` / `parse_selection`

Se ejecutaron 54 ataques directos a `claims_channel.validate_selection` y 12 respuestas JSON hostiles a `structured_provider_adapter.parse_selection`. **Todos fueron rechazados; 0 desviaciones.** En los 54, la excepción fue `ValueError` y `str(exc)` pertenece exactamente al conjunto de códigos de `REJECTION_REASONS` (`invalid_shape`, `invalid_version`, `invalid_intent`, `invalid_claim_id`, `duplicate_claim`, `too_many_claims`, `invalid_evidence_ref`). En los 12, `parse_selection` devolvió `ProviderError('invalid_response')`, sin mensaje del modelo.

Resumen por categoría:

| Categoría | Casos probados | Resultado |
|---|---|---|
| Raíz no dict | `None`, `[]`, `"paideia"`, `0`, `True`, `{}`, subclase de `dict` | `invalid_shape` (7/7) |
| Claves extra / texto del modelo | `answer`, `texto`, `__class__`, `answer` junto a `evidence_refs` | `invalid_shape` (4/4) |
| Versión | con prosa añadida, mayúsculas, `None` | `invalid_version` (3/3) |
| Intención | prosa («explica y recomienda contratar»), `None`, `True` | `invalid_intent` (3/3) |
| Ids | inventado, id válido + sufijo, id válido + espacio, homóglifo cirílico, 10.000 caracteres, NUL, `True`, `1`, `dict`, lista de listas, `None` | `invalid_claim_id` (11/11) |
| Contenedor de ids | string, `dict`, `tuple`, `set`, `None` | `invalid_shape` (5/5) |
| Duplicados y límite | repetido, 60 repetidos, 7 distintos | `duplicate_claim` (2/2) y `too_many_claims` (1/1) |
| `evidence_refs` | string, `dict`, `None`, 4 refs, vacía, sin prefijo, prefijo solo, espacio, guion final, doble guion, salto de línea, 65 caracteres, duplicada, unicode, `<b>`, `True`, `1`, lista anidada | `invalid_evidence_ref` (18/18) |

Casos representativos y salida exacta:

```
id homoglifo        -> ValueError: invalid_claim_id
id 10.000 chars     -> ValueError: invalid_claim_id
7 distintos         -> ValueError: too_many_claims
clave extra answer  -> ValueError: invalid_shape
version con prosa   -> ValueError: invalid_version
ref newline         -> ValueError: invalid_evidence_ref
rejected("texto libre del modelo") -> ValueError: invalid_reason
```

Ningún mensaje de error contiene el texto enviado: `rejected()` solo acepta los siete códigos; cualquier otra cadena, incluida prosa, se rechaza con `invalid_reason`.

Borde JSON en `parse_selection` (todas `ProviderError(invalid_response)`, sin traza hacia el cliente):

| Respuesta del modelo | Resultado |
|---|---|
| `answer` con prosa libre en lugar de `claim_ids` | rechazada |
| clave `claim_ids` duplicada en el objeto JSON | rechazada (`object_pairs_hook` detecta duplicados) |
| `NaN` / `Infinity` | rechazada (`parse_constant`) |
| contenido extra tras el objeto | rechazada |
| raíz array o número | rechazada |
| id inventado | rechazada |
| id válido + texto del modelo en el mismo array | rechazada |
| 7 ids | rechazada |
| id de 10.000 caracteres | rechazada |
| respuesta de más de 4.096 bytes | rechazada |

`validate_selection` normaliza siempre a `{version, intent, claim_ids, evidence_refs}` con listas propias. Una selección de 6 ids válidos se acepta; 7 no. Una lista vacía se acepta como `empty` (ver §9, D3). `evidence_refs` válidas se validan pero **no salen en el DTO**: `compose` no las usa y el resultado tiene `sources: []`; el modelo no puede convertir una referencia en una atribución visible.

---

## 4. Composición: textos y cifras

### 4.1 Sin cifras

Los 39 textos del catálogo no contienen ningún dígito, `%` ni `€` (comprobado carácter a carácter; el mínimo es 196 caracteres y el máximo 471). Cuatro combinaciones de 6 afirmaciones, incluida una en orden inverso, produjeron `answer` sin un solo dígito. La comprobación es fuerte: cualquier cifra en `answer` sería necesariamente una fuga.

### 4.2 El escenario no entra en `answer`

Con un escenario de ataque `principal=987654.32`, `annual_rate_percent=7.77`, `years=7`, `monthly_contribution=123.45`, `inflation_percent=3.33`, la respuesta renderizada por el canal fue:

```
saldo final del motor: 1681179.95
answer == union de textos: True
cifras en answer: []
calculation.summary: {'contributions': '998024.12', 'final_balance': '1681179.95',
                      'interest': '683155.83', 'inflation_adjusted': '1336685.38'}
```

`answer` es exactamente `"\n\n".join(textos)`; `calculation` viaja en su propio panel y no se copia dentro de `claims.items[].text` ni de `answer`. Las claves del DTO v2 son `answer`, `provider_mode`, `external_sent`, `claims`, `structured_education`; `claims.items[]` solo tiene `id` y `text`, nunca `when` ni `never_claim`.

### 4.3 El orden no es el del catálogo

`compose` respeta el orden de `claim_ids`, no el orden de `claims_catalog.CLAIM_IDS`. Prueba con dos ids invertidos:

```
pedido: ['ahorro_riesgos_de_invertir', 'alcance_educativo_sin_asesoramiento']
items : ['ahorro_riesgos_de_invertir', 'alcance_educativo_sin_asesoramiento']
sigue el orden pedido: True
coincide con el orden del catalogo: False
```

Esto es coherente con `claims_channel.compose` («en el orden elegido») y con `ESPECIFICACION.md:350-351` («el orden es suyo, y no cambia el contenido»), pero contradice el comentario de `static/claims_view.js:22-25` («claims_channel compone en el orden del catálogo») y el de `tests/claims_view.test.cjs:86` («El servidor compone en orden de catálogo»). El modelo conserva así la única autoría que le queda: qué afirmaciones y en qué orden. No puede cambiar las palabras, pero sí la secuencia; es el riesgo residual de «selección sesgada» que la especificación reconocía y que el código no mitiga con invariantes de cobertura.

### 4.4 Fin a fin por el servicio

Con `LocalChatService` y un `FakeChatProvider` que devuelve la selección:

| Turno | Resultado real |
|---|---|
| v2 válida de 2 ids | aceptada, `claims=shown/2`, `answer` compuesto |
| v2 con id inventado tras uno válido | `502 CHAT_STRUCTURED_INVALID_RESPONSE`, sin texto |
| v2 con prosa en `answer` | `502`, sin texto |
| v2 con 7 ids | `502`, sin texto |
| v2 vacía (`claim_ids: []`) | aceptada, `answer=""`, `claims=empty/0` |
| v2 `calculate` con escenario | aceptada, cálculo del motor, `answer` sin cifras |
| v2 `calculate` sin escenario | `502`, sin texto |
| v1 válida | aceptada, sin clave `claims`, mismos textos de siempre |

No hay texto parcial en ningún rechazo: la validación ocurre antes de construir `items`, y el servicio traduce cualquier excepción a un mensaje fijo en español, sin interpolar la respuesta del modelo.

---

## 5. Ataques a la UI

### 5.1 `claims_view.js` con DOM mínimo

Se probaron 10 textos hostiles: `<img src=x onerror=alert(document.domain)>`, `<script>alert(document.domain)</script>`, `</li></ul><svg onload=...>`, `"><img ...>`, entidades `&lt;script&gt;`, cierre de comilla y `alert`, plantilla `{{constructor.constructor(...)}}`, NUL + RLO, 100.000 caracteres y saltos de línea/tabulador. En los 10:

- los únicos tags creados fueron `DIV`, `SECTION`, `UL`, `LI` (nunca `IMG`, `SCRIPT`, `SVG`, `IFRAME` ni `OBJECT`);
- ningún nodo tuvo atributos `on*`;
- el `textContent` del `li` fue exactamente el texto de entrada, incluido el marcado;
- no se lanzó ninguna excepción;
- `PROBLEMAS: 0`.

Formas raras de `claims`: `null`, string, array, número, `items` null/string/objeto, items con `null`/número/string/objetos incompletos, duplicados, `state` en mayúsculas, `version` con intento de inyección de atributo (`v2" onmouseover="...`), `version` de 100 caracteres, id de 10.000 caracteres, id con comillas y un item con prototipo heredado. Todas degradaron sin lanzar (salvo un `state` definido como getter que lanza, imposible en JSON) y sin crear nodos peligrosos. El atributo `data-claims-version` solo se escribe si la versión cumple `^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$`; el `data-claim-id` se escribe con `setAttribute`, que no interpreta HTML.

La fuente no contiene `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval(` ni `new Function(` (grep vacío en las dos copias, prototipo y `api/_static`). `app.js` pinta los items v2 con `textElement`, que construye un nodo de texto (`document.createTextNode`), no HTML.

### 5.2 El cliente acepta texto arbitrario del servidor (defensa en profundidad)

`structured_education_ui.js:40-52` valida la forma v2 (id `^[a-z0-9_]{3,64}$`, texto de 20 a 600 caracteres, sin dígitos/`%`/`€`, sin duplicados, máximo 6) pero **no compara el texto con el catálogo**: el cliente no tiene el catálogo ni un `catalog_digest`. Por eso acepta:

```
ACEPTA  v2 html sin cifras   items=1 texto0="<img src=x onerror=alert(document.domain)>"
ACEPTA  v2 script sin cifras items=1 texto0="<script>alert(document.domain)</script>"
RECHAZA v2 texto con digito  Texto de afirmación no válido
```

La reproducción es segura (`textContent`), pero la etiqueta que acompaña al bloque —«Contenido educativo de Paideia; no es redacción libre del modelo»— no está verificada en el cliente: si el servidor o el transporte se comprometieran, cualquier frase de 20 a 600 caracteres sin dígitos se presentaría como afirmación de Paideia. El modelo no puede llegar aquí (el servidor compone el DTO), así que no es una vía del modelo; es la ausencia del `catalog_digest` que `ESPECIFICACION.md:383-386` exigía como defensa en profundidad.

### 5.3 La UI nueva no se ejecuta en el flujo v2

`app.js:1058` llama a `PaideiaStructuredEducation.select`; para cualquier respuesta v2, `structured` es un objeto (aunque `items` esté vacío), de modo que se entra en `if (structured)` (`app.js:1068`) y se pintan los items como párrafos (`app.js:1070`). La llamada a `PaideiaClaims.render` está en el `else` (`app.js:1077-1107`): solo se ejecutaría si la respuesta **no** tuviera `structured_education`, cosa que el backend v2 nunca hace. Comprobación directa:

```
select() devuelve: {"items":[],"calculation":null}
¿entra en la rama if(structured) de app.js? true
¿se ejecuta PaideiaClaims.render (else de app.js:1105)? false
```

Consecuencias: los estados `shown/empty/rejected`, los `aria-label`, el marcador `data-paideia-claims` y el aviso neutro de `claims_view.js` no se usan en el producto; una selección vacía pinta solo el encabezado «Contenido educativo de Paideia…» sin cuerpo, y un rechazo no llega a la UI como bloque. El contenido sigue siendo seguro porque `app.js` usa `textElement`, pero el contrato de UI que el commit dice haber integrado no está activo (ver D1).

---

## 6. Regresión v1

Se comparó el `structured_education.py` del commit padre (`1cf5ab5^`) con el actual, cargando el módulo antiguo en un directorio aislado y el nuevo en un subproceso limpio. Para tres selecciones v1 (una afirmación, tres afirmaciones y `calculate` con escenario) el objeto devuelto fue **estructuralmente idéntico** (`IGUAL` en los tres casos, comparando el JSON completo con claves ordenadas: mismos textos, mismas claves y mismos valores). También coinciden los cinco casos de error probados:

```
id inventado             old=('ValueError', 'invalid claims') new=('ValueError', 'invalid claims') IGUAL
clave extra              old=('ValueError', 'invalid selection') new=('ValueError', 'invalid selection') IGUAL
calculate sin escenario  old=('ValueError', 'invalid scenario') new=('ValueError', 'invalid scenario') IGUAL
explain con escenario    old=('ValueError', 'unexpected scenario') new=('ValueError', 'unexpected scenario') IGUAL
lista vacia              old=('ValueError', 'invalid claims') new=('ValueError', 'invalid claims') IGUAL
```

La refactorización de `_calculation` conserva la semántica: `intent != 'calculate'` con escenario sigue lanzando `unexpected scenario`, y `calculate` sin escenario sigue lanzando `invalid scenario`. Las pruebas v1 existentes siguen verdes en la suite completa. `render_selection` con una selección v1 y un id v2 sigue rechazando (`ValueError: invalid claims`), y una selección v2 no se acepta por la rama v1.

---

## 7. Superficie pública (`api/`)

- `api/index.py` solo importa `_core.catalogue_conditions`, `_core.catalogue_data` y `_core.domain`. **No importa** `claims_catalog`, `claims_channel`, `structured_education` ni el adaptador. `grep -rn "claims" api --include=*.py` solo encuentra un comentario en `_core/domain.py`.
- Llamada WSGI real a la función desplegada:

```
GET  /api/status      -> 200 OK   ai.connected=false, ai.status="not_configured",
                                  ai.capabilities.structured_education=false
POST /api/chat        -> 405 Method Not Allowed
GET  /api/chat-status -> 404 Not Found
```

- `api/_static/claims_view.js` y `structured_education_ui.js` se sirven como estáticos, pero sin `/api/chat` no hay ningún DTO con `claims` que los alimente; el canal no está expuesto en la función pública. El chat público sigue apagado, como declara el commit.

---

## 8. Honestidad de las 39 afirmaciones

Leídos los 39 `text` completos (no los `when` ni los `never_claim`, que no se renderizan), **ninguno promete rentabilidad, garantiza un resultado, recomienda contratar un producto o una entidad, ni atribuye una condición a una entidad concreta**. No hay nombres de entidades, productos, países ni fechas; no hay dígitos, `%`, `€`, «oficial», «vigente» ni «vigencia». Las apariciones de «garantía» son el sustantivo técnico («garantía de depósitos») y las de «garantiza» son negaciones («no garantiza conservar el capital», «no garantiza el resultado»). `comparar_sin_recomendar` y `alcance_educativo_sin_asesoramiento` explicitan la prohibición de recomendar.

Ahora bien, hay cuatro frases que un revisor editorial debería matizar, aunque no son promesas ni recomendaciones:

| Entrada | Frase exacta | Problema |
|---|---|---|
| `fuente_dato_vencido_no_sirve` | «Aunque el dato sea correcto como registro histórico, no sirve como oferta ni como base de una comparación.» | Demasiado absoluta: un dato pasado sí puede ser base de una comparación histórica; lo que no es es una oferta actual. |
| `ahorro_riesgo_inflacion` | «El ahorro conserva el importe nominal» | No se cumple si hay comisiones, tipos negativos o pérdida del efectivo; es una simplificación presentada como regla. |
| `interes_ejemplo_tin_tae` | «…el rendimiento efectivo del año supera al tipo nominal pactado» | Solo es cierto con tipos positivos; con un tipo nominal negativo la capitalización lo hace más negativo, no mayor. |
| `garantia_limite_por_persona` | «La cobertura tiene un límite máximo por persona y entidad…» | Describe un régimen legal concreto (España/UE) sin nombrarlo; en otras jurisdicciones el perímetro y el titular pueden diferir. La primera frase de `garantia_de_depositos_que_es` sí dice «legislación aplicable», pero esta entrada no. |

Ninguna de las cuatro contiene cifras ni atribuciones, y ninguna convierte el canal en no apto; son correcciones de precisión editorial. La revisión es de lectura, no un dictamen jurídico; el propio `CATALOGO.md` advierte que no acredita revisión de profesores ni reguladores.

---

## 9. Defectos y salvedades

| # | Severidad | Defecto | Evidencia |
|---|---|---|---|
| D1 | **Alta (funcional)** | `claims_view.js` no se ejecuta en el flujo v2: el bloque de afirmaciones, sus estados y su aviso neutro son código muerto en el producto. Una selección vacía pinta un encabezado sin cuerpo. | `app.js:1058` selecciona; `app.js:1068` entra en `if (structured)`; `app.js:1105` (llamada a `PaideiaClaims.render`) está en el `else` de `app.js:1077`. Para v2, `select()` siempre devuelve objeto. |
| D2 | **Alta (contrato)** | El rechazo se convierte en `502 CHAT_STRUCTURED_INVALID_RESPONSE`, no en `200` con `claims.state="rejected"`. `claims_channel.rejected()` no tiene ningún llamador de producción. | `backend_services.py:517-521` y `:666-673` capturan `Exception` y lanzan `ServiceProblem(502, ...)`; `grep rejected(` solo encuentra la definición en `claims_channel.py:135` y las pruebas. `ESPECIFICACION.md:427-428` exige `200 + rejected`. |
| D3 | **Media** | Una selección con `claim_ids: []` se acepta como `state="empty"` y `answer=""`. `CATALOGO.md:244` y `ACEPTACION.md:113` (G18) exigen rechazarla; `ESPECIFICACION.md:289,444` la llama `empty_selection`. El modelo puede así devolver un turno vacío que la UI presenta como respuesta. | `claims_channel.py:81` solo comprueba `> MAX_CLAIMS`; `tests/test_claims_channel.py:186` codifica la aceptación; `app.js:1069` pinta el encabezado aunque `items` esté vacío. |
| D4 | Baja | `render_selection` con versión v2 y sin `intent` lanza `KeyError: 'intent'`, no `ValueError`. Hoy el servicio captura `Exception` y devuelve 502, pero el contrato del módulo (y `secure_structured_bridge`) espera `ValueError`. | `structured_education.py:49-50` despacha por `selection.get('version')`; `_render_claims` hace `selection['intent']` en la línea 38 antes de que `compose` valide. |
| D5 | Baja | El orden es el de la selección, no el del catálogo, al contrario de lo que dicen el comentario de la UI y el de su prueba. El modelo conserva la secuencia como forma de autoría. | `claims_channel.py:110-113`; `claims_view.js:22-25`; `tests/claims_view.test.cjs:86`; la especificación sí admite el orden del modelo (`ESPECIFICACION.md:350-351`). |
| D6 | Baja (defensa en profundidad) | No hay `claims.catalog_digest` ni comparación del texto con el catálogo en el cliente. `structured_education_ui.project` acepta cualquier texto de 20-600 caracteres sin dígitos, con un id que cumpla el patrón y sin duplicados, como afirmación de Paideia. | `structured_education_ui.js:40-52`; `ESPECIFICACION.md:383-386` pedía el digest y la comparación. La reproducción es segura; la atribución no está pinneada. |
| D7 | Baja | `evidence_refs` se valida pero se descarta: no viaja en el DTO, no se liga a `claim_ids` ni al catálogo, y su forma (`identity:<id>` como string) no es la de la especificación (`{claim_id, source_id}`). Si en el futuro se surface, sería un canal de atribución. | `claims_channel.py:84-97` valida; `compose` no las usa (`:110-132`); el DTO v2 no tiene `sources`. `ESPECIFICACION.md:290-292`. |
| D8 | Informativa | `compose(sources=...)` copia cualquier lista tal cual al DTO. No hay llamador de producción que le pase datos del modelo, pero la superficie pública invita a hacerlo. | `claims_channel.py:115-120`. |
| D9 | Informativa | `claims_view.render` puede lanzar si `claims.state` es un getter que lanza. Es imposible con JSON, así que el «nunca lanza» se cumple para datos, no para objetos hostiles en memoria. | `claims_view.js:96`; prueba con `get state(){throw}` devuelve `threw=boom`. |

**Lo que sí está bien y conviene no romper:** validación de forma exacta con `type()`, no `isinstance()`; ids como pertenencia a un diccionario cerrado; rechazo antes de componer; textos inmutables con `MappingProxyType`; `answer` como unión mecánica; `calculation` separado; DTO sin `when`/`never_claim`; `createElement`/`textContent` en la UI; `setAttribute` para ids; `parse_selection` con `object_pairs_hook` y `parse_constant`; límite de 4.096 bytes; y la rama v1 intacta.

---

## 10. Límites de esta revisión

- **Sin modelo real.** Todo se ejecutó con `FakeChatProvider`/`StructuredProviderAdapter`; no se usó Groq ni red. La propiedad es estructural (el DTO del modelo solo puede ser `{version, intent, claim_ids, evidence_refs?}`), pero el contrato de prompting para un modelo real no se probó: la prueba de Groq sigue bloqueada por el contador y el chat público está apagado.
- **UI con DOM mínimo, no navegador real.** Los ataques de §5 usan el stub de `tests/claims_view.test.cjs` (sin jsdom). Verifican creación de nodos, atributos y `textContent`; no ejecutan un motor HTML real ni CSP. No se detectó ninguna ruta a `innerHTML`/`eval`.
- **Sin HTTP de UI.** El fin a fin de §4.4 es a nivel de `LocalChatService`; no se levantó el servidor local ni se envió un formulario real. La superficie pública se probó invocando `api/index.py` como WSGI en proceso.
- **Matriz de aceptación no ejecutada.** `ACEPTACION.md` sigue diciendo 0/10 contra el código; esta revisión no ejecuta sus diez fixtures, solo comprueba el canal y los contratos que la matriz cita.
- **Catálogo editorial local.** La revisión de honestidad es lectura de los 39 textos, no una validación legal ni una revisión de profesor/regulador; el propio `CATALOGO.md` lo declara.
- **Árbol de trabajo ajeno.** Hay modificaciones no relacionadas (`mission_ledger.py`, `scripts/provision_mission.py`, pruebas de misión) y documentos sin seguimiento (`docs/seguridad/`); no se tocaron. El único fichero creado por esta revisión es este documento.

---

## 11. Qué corregir antes de llamarlo cerrado

1. **D1:** llevar la llamada a `PaideiaClaims.render` a la rama estructurada (o hacer que `structured_education_ui` devuelva el bloque `claims` y que `app.js` lo pinte), y añadir una prueba de integración de `app.js` que compruebe el marcador `data-paideia-claims` en una respuesta v2. Hoy las 13 pruebas de UI prueban el módulo, no su uso.
2. **D2:** decidir el contrato de degradación. Si se mantiene la especificación, devolver `200` con `claims.state="rejected"` y el motivo estable, conservando `calculation` y paneles; si se mantiene el 502, borrar `rejected()` y actualizar `ESPECIFICACION.md`/`ACEPTACION.md` para no declarar un estado que no existe.
3. **D3:** rechazar `claim_ids: []` como `empty_selection` (o cambiar explícitamente `CATALOGO.md` §8 y G18 y documentar por qué el vacío es un estado válido). Mientras se acepte, la UI debe mostrar el aviso neutro, no un encabezado sin cuerpo.
4. **D6:** añadir `claims.catalog_digest` (SHA-256 del registro canónico) y compararlo en `structured_education_ui.project`/`claims_view`; es la única forma de que el cliente pueda afirmar que el texto es del catálogo y no de un servidor sustituido.
5. **D4/D5:** normalizar el `KeyError` a `ValueError("invalid_shape")` y corregir los comentarios de orden (o ordenar por catálogo si se prefiere, pero entonces cambiar la especificación y las pruebas).
6. **Editorial:** matizar las cuatro frases de §8, sobre todo `fuente_dato_vencido_no_sirve` y `interes_ejemplo_tin_tae`.

Con D1-D3 corregidos, el veredicto podría subir a **apto** sin salvedades funcionales; la propiedad de seguridad que se pedía ya se cumple.
