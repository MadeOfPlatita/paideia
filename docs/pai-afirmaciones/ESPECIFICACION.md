# ESPECIFICACIÓN — Canal de afirmaciones estructuradas en el chat de Pai

Fecha: 4/11/2026 (UTC+01:00).
Estado: **propuesta técnica, no implementada**. Este documento no modifica código.
Ámbito: `app`. Sustituir, en el chat real, la retención léxica de
prosa por una **selección cerrada y verificable** de afirmaciones.

Método: cada afirmación sobre el comportamiento actual se apoya en código leído. Las
comprobaciones marcadas «verificado» se ejecutaron en modo lectura (importar y llamar
funciones puras o medir el catálogo, sin red, sin proveedor y sin escribir estado).

---

## 0. Resumen de la decisión

1. El modelo deja de redactar. Devuelve **solo identificadores**: `version`, `intent`,
   `claim_ids` y, opcionalmente, `evidence_refs` con ids de evidencia local.
2. Todo el texto que ve el usuario lo compone el servidor a partir de un **registro
   cerrado**: 39 afirmaciones editoriales de `docs/pai-afirmaciones/CATALOGO.md` §9 más
   5 plantillas de evidencia de `claims_channel.py`. El modelo no aporta ni una palabra,
   ni una cifra, ni una atribución.
3. Las **cifras nunca viajan por el canal de texto**. Viven exclusivamente en los
   bloques ya existentes `calculation` (motor determinista) y `catalogue` (fichas
   locales con clase y fechas). El texto solo explica qué significan.
4. Si la selección no es válida, el turno se rechaza **entero** (fail-closed), se
   conservan los paneles locales que sí existen y se declara el motivo exacto. Nunca
   se rellena el hueco con prosa.
5. El canal es **aditivo y opt-in** (`claims_mode=False` por defecto). La ruta actual
   —incluida `_text_surface_gate`— queda intacta para los turnos sin canal cerrado.

Consecuencia de producto que hay que aceptar explícitamente: en modo afirmaciones Pai
solo puede decir lo que esté en el registro cerrado. Abrir un tema nuevo exige añadir
una afirmación editorial revisada, no relajar el canal.

---

## 1. Mapa exacto del camino actual

### 1.1 Orden de decisión, de la petición a la pantalla

| # | Paso | Fichero:línea |
|---|------|----------------|
| 1 | Ruta HTTP `POST /api/chat` | `app.py:598-600` |
| 2 | `_handle_chat` delega en el servicio | `app.py:550-551` |
| 3 | `LocalChatService.chat` valida tamaño (16 KiB) y claves del payload | `backend_services.py:455-464` |
| 4 | Ticket, proveedor habilitado, proveedor de prueba cerrado | `backend_services.py:465-473` |
| 5 | Consentimiento exacto (`notice_version`, `purpose`, `approved_fields`) | `backend_services.py:474-480` |
| 6 | Consentimiento separado de contexto/historial | `backend_services.py:481-495` |
| 7 | Se construye `messages` (system + historial + usuario) | `backend_services.py:496-502` |
| 8 | Rama estructurada de prueba (`_structured_session_test_only`) | `backend_services.py:503-507` |
| 9 | Rama `structured_mode` (fixture): `select_education` → `render_selection` | `backend_services.py:508-521` |
| 10 | Rama de herramientas: `_tools_chat` | `backend_services.py:522-523` |
| 11 | `_tools_chat`: aprobación de catálogo y admisión | `backend_services.py:576-580` |
| 12 | Admisión: `submit`/`status`, cola 202, `claim` del ticket | `backend_services.py:595-613` |
| 13 | `ReservedProvider.chat` (cuenta llamadas y traduce errores) | `backend_services.py:616-650` |
| 14 | `ToolChatRunner(...).run(messages)` | `backend_services.py:674-675` |
| 15 | Runner: `provider.chat(..., tools=definitions)` | `pai_runtime.py:1001-1003` |
| 16 | Runner: validación del `ChatResult` | `pai_runtime.py:1007-1009` |
| 17 | Runner: refusal / longitud / sin `tool_calls` → DTO de respuesta | `pai_runtime.py:1012-1023` |
| 18 | Runner: una sola llamada, id/nombre/argumentos válidos, dispatch | `pai_runtime.py:1024-1078` |
| 19 | Runner: proyección del cálculo determinista | `pai_runtime.py:1081-1082` |
| 20 | Runner: `catalogue_used` y fichas proyectadas | `pai_runtime.py:1083-1096` |
| 21 | Runner: agregado de fuentes (máx. 20) | `pai_runtime.py:1097-1104` |
| 22 | Runner: `_answer_dto` → si hubo catálogo, `answer=""` y estado retenido | `pai_runtime.py:140-153` |
| 23 | Servicio: normaliza estado y **refuerza** la retención si `catalogue.used` | `backend_services.py:686-696` |
| 24 | Servicio: frontera léxica `_withhold_unbacked_claim` | `backend_services.py:702-703` |
| 25 | Servicio: `_financial_checked` (detector estrecho «sin riesgo») | `backend_services.py:335-338`, aplicado en `552` y `704` |
| 26 | Servicio: DTO final (`answer`, `catalogue`, `calculation`, `sources`, `answer_provenance`) | `backend_services.py:704-714` |
| 27 | UI: valida `provider_mode` y `answer` | `static/app.js:1054-1056` |
| 28 | UI: intenta el canal estructurado existente | `static/app.js:1058-1059` |
| 29 | UI: si está retenido, pinta aviso + fichas + cálculo; si no, pinta `answer` | `static/app.js:1085-1104` |
| 30 | UI: fuentes y trazabilidad | `static/app.js:1105-1106` |

### 1.2 Quién decide, exactamente, qué texto ve el usuario

| Decisión | Función | Regla |
|---|---|---|
| Texto vacío si hubo catálogo | `ToolChatRunner._answer_dto` (`pai_runtime.py:147-150`) | `catalogue_used=True` ⇒ `answer=""`, estado `withheld_catalogue_evidence` |
| Refuerzo independiente | `LocalChatService._tools_chat` (`backend_services.py:692-695`) | Si `catalogue.used is True`, fuerza retención aunque el runner devolviera prosa |
| Retención léxica | `_withhold_unbacked_claim` (`backend_services.py:154-172`) | Cifras, atribuciones e identificadores en la prosa ⇒ `answer=""` |
| Patrón léxico | `_text_surface_gate` (`backend_services.py:122-134`) | `identifier` → `attribution` → `figure`; nunca es verificación semántica |
| Rechazo por calidad | `_financial_checked` (`backend_services.py:335-338`) | `assess_financial_text` no vacío ⇒ HTTP 502, sin reintento |
| Render final | `static/app.js:1078-1116` | Si el estado empieza por `withheld` **o** hubo catálogo, no imprime `answer` en ningún caso |
| Texto del aviso | `static/chat_withheld_notice.js:20-26` | Elige por `catalogueUsed`, luego `hasCalculation`, luego `reason`; si no consta, aviso genérico |

El DTO declara siempre `text_validation: "not_performed"` (`backend_services.py:189`), y
`answer_provenance` degrada silenciosamente cualquier estado desconocido a
`shown_unverified` (`backend_services.py:181-182`). **Verificado**: llamar
`answer_provenance({"answer_text_state": "shown_closed_claims", ...}, [])` devuelve
`text_state: "shown_unverified"`. Cualquier estado nuevo debe añadirse a esa lista o la
procedencia mentirá.

### 1.3 Por qué la frontera léxica no puede convivir con datos del catálogo

**Verificado** ejecutando `_text_surface_gate` sobre una frase compuesta por el servidor:

```
_text_surface_gate("La ficha local de DEP-X registra una TAE de 3.10 % con estado conocido.")
→ (False, "identifier")
```

El identificador `DEP-X` dispara `_IDENTIFIER_SURFACE` (`backend_services.py:103`) y el
`%` dispararía `_FIGURE_MARKER` (`67-71`). Es decir: la frontera bloquea exactamente el
texto que sí está respaldado por una ficha local, porque no puede distinguirlo de una
invención.

Medición sobre el catálogo completo (**verificado** sobre `CATALOGO.md` §9): de los 39
textos editoriales, **7 quedarían retenidos** por la frontera si pasaran por ella —4 por
`figure` y 3 por `attribution`—, aunque **los 39 pasan** `assess_financial_text`. El
falso positivo es léxico: las palabras «porcentaje» y «punto» disparan `_FIGURE_MARKER`
(`backend_services.py:68`), y «confirma»/«confirmar» y el literal «fuente:» disparan
`_ATTRIBUTION_SURFACE` (`92-102`). Los cinco textos de la v1 actual sí pasan la frontera
(`(True, 'concept_only')` y `()`), pero la v2 no puede depender de ese filtro.

Conclusión: para mostrar datos locales con su valor y su fuente no se puede usar prosa
del modelo filtrada; hace falta texto **compuesto por el servidor** con procedencia
estructural. Eso es este canal.

### 1.4 Qué es y qué no es el canal estructurado existente

Lo que ya existe y se reutiliza:

- `structured_education.EDITORIAL` (`structured_education.py:6-12`): cinco textos
  cerrados, sin cifras.
- `structured_education.render_selection` (`:15-48`): validación estricta de
  `{version, intent, claim_ids}` y render de `answer` + `structured_education`.
- `structured_provider_adapter.parse_selection` (`:156-178`): JSON estricto, sin claves
  duplicadas, sin `NaN`, tamaño máximo 4096 bytes, `finish_reason == "stop"`.
- `groq_structured_adapter.build_structured_request` (`:8-36`): construye el
  `response_format` con `json_schema` y enumera los ids. Solo construye bytes; no envía.
- `FakeChatProvider` (`structured_provider_adapter.py:47-136`): proveedor falso con
  `outcomes` guionizados, sin transporte.

Lo que impide usarlo tal cual en el chat real:

| Límite | Dónde | Efecto |
|---|---|---|
| Exige proveedor falso | `StructuredProviderAdapter.__init__` (`:184-188`) | No admite un proveedor real |
| Prohíbe herramientas, admisión, contexto e historial | `backend_services.py:392-397` | No puede ejecutar el catálogo |
| Devuelve `provider_mode: "test_only"` y `external_sent: False` | `structured_education.py:46-47` | Mentiría sobre el origen en un turno externo |
| El cliente exige `provider_mode === "test_only"` y `external_sent === false` | `static/structured_education_ui.js:38` | No renderiza un turno real |
| El cliente compara el texto con una copia local del editorial | `static/structured_education_ui.js:42` | Solo sirve para textos fijos, no para plantillas con datos |
| El esquema del proveedor es `strict: false` | `groq_structured_adapter.py:19` | La garantía es la validación del servidor, no el proveedor |

Por eso el canal nuevo es **paralelo**, no una mutación del existente: `paideia-education-v2`
(39 ids, `CATALOGO.md` §9) frente a `paideia-education-v1` (5 ids).

---

## 2. Contrato del canal estructurado

### 2.1 Esquema JSON exacto de la respuesta del modelo

La respuesta del modelo es el **último mensaje sin `tool_calls`** del ciclo de
herramientas. No hay una llamada extra: el runner ya recibe ese mensaje
(`pai_runtime.py:1020-1023`); lo que cambia es cómo se interpreta.

```json
{
  "version": "paideia-education-v2",
  "intent": "explain",
  "claim_ids": ["ficha_tasa", "fuente_atribucion_con_prueba"],
  "evidence_refs": [
    {"claim_id": "ficha_tasa", "source_id": "identity:DEP-EJEMPLO"}
  ]
}
```

JSON Schema que se enviará como ayuda (`response_format`), sin depender de que el
proveedor lo respete. El bloque está **abreviado**: el `enum` real lo materializa
`build_claims_request` desde `CLAIM_IDS` (39 ids editoriales del catálogo + 5 de
evidencia); no se escribe a mano.

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["version", "intent", "claim_ids"],
  "properties": {
    "version": {"const": "paideia-education-v2"},
    "intent": {"enum": ["explain", "calculate"]},
    "claim_ids": {
      "type": "array",
      "minItems": 1,
      "maxItems": 6,
      "uniqueItems": true,
      "items": {"enum": ["… 39 ids de CATALOGO.md §9 …, ficha_tasa, ficha_plazo, ficha_conflicto, ficha_sin_tasa, ficha_sin_resultados"]}
    },
    "evidence_refs": {
      "type": "array",
      "maxItems": 6,
      "uniqueItems": true,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["claim_id", "source_id"],
        "properties": {
          "claim_id": {"enum": ["ficha_tasa", "ficha_plazo", "ficha_conflicto", "ficha_sin_tasa", "ficha_sin_resultados"]},
          "source_id": {
            "type": "string",
            "maxLength": 64,
            "pattern": "^identity:[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){0,2}$"
          }
        }
      }
    }
  }
}
```

Decisiones del esquema:

- **`version` obligatoria y constante**, `paideia-education-v2`, la misma que propone
  `CATALOGO.md` §8. La v1 de cinco ids (`paideia-education-v1`) se rechaza antes de
  resolver ids: el diccionario no es compatible hacia atrás.
- **`evidence_refs` opcional**: un turno conceptual no la necesita. Si aparece, su forma
  es cerrada.
- **Solo se admite el espacio de nombres `identity:`**. Los ids `condition:<producto>:<n>`
  existen (`pai_tools.py:845`) pero quedan **reservados**: el agregado de fuentes se
  trunca a 20 (`pai_runtime.py:1099-1100`), así que un id visto por el modelo puede no
  estar en el DTO y el rechazo sería inevitable. La ficha se identifica por producto; la
  fuente concreta la elige el servidor.
- **Una referencia por afirmación con evidencia**, exactamente una.
- **Máximo 6 afirmaciones**: `CATALOGO.md` §8 deja abierto mantener cinco o subir el
  límite; se elige seis porque P4 y P7 tienen seis afirmaciones pertinentes, con una
  prueba nueva que lo fija (`MAX_CLAIMS = 6`, separado de `len(CLOSED_IDS)`).

### 2.2 Registro cerrado de afirmaciones

Hay dos mitades y una sola fuente para cada una:

1. **Editorial (39 ids, 9 grupos).** Es el diccionario de `docs/pai-afirmaciones/CATALOGO.md`
   §9, con campos `text`, `when` y `never_claim`. `claims_channel.py` lo carga desde un
   módulo generado `claims_catalog.py`; no se copia a mano ni se reescribe.
   - `text` es lo único que se renderiza.
   - `when` solo alimenta la guía del selector en el prompt de sistema; nunca se muestra.
   - `never_claim` es una lista de revisión editorial; nunca se renderiza ni se envía.
2. **Evidencia (5 ids).** Plantillas fijas de `claims_channel.py` para los datos de la
   capa de condiciones (`CATALOGO.md` §8, «Datos de producto»).

| Grupo editorial | Prefijo | Ids |
|---|---|---|
| Alcance y límites | `alcance_` | 3 |
| Ahorro, inversión y riesgo | `ahorro_` | 3 |
| TIN, TAE e interés | `interes_` | 5 |
| Inflación y poder adquisitivo | `inflacion_` | 4 |
| Liquidez, plazo y cancelación | `liquidez_` | 4 |
| Comparar sin recomendar | `comparar_` | 5 |
| Garantía de depósitos | `garantia_` | 6 |
| Datos vencidos, fuentes y atribución | `fuente_` | 5 |
| Simulación y cálculo | `simulacion_` | 4 |

| id de evidencia | requiere | texto (plantilla fija) |
|---|---|---|
| `ficha_tasa` | 1 ref a producto con ≥1 condición `annual_rate_percent` | «La ficha local seleccionada incluye una condición de tasa; el panel de datos locales muestra el producto, su estado, su valor cuando consta y su fuente.» |
| `ficha_plazo` | 1 ref con ≥1 condición `term_months` | «La ficha local seleccionada incluye una condición de plazo; el panel de datos locales muestra el producto, su estado, su valor cuando consta y su fuente.» |
| `ficha_conflicto` | 1 ref con una condición en estado `conflict`, o con ≥2 valores conocidos distintos para la misma métrica | «Una de las fichas locales seleccionadas contiene valores incompatibles en una condición de tasa o plazo; no se muestra una cifra única y el conflicto figura en el panel.» |
| `ficha_sin_tasa` | 1 ref sin ninguna condición `annual_rate_percent` | «La ficha local seleccionada no acredita una condición de tasa; no se presenta ninguna cifra como si existiera.» |
| `ficha_sin_resultados` | 0 refs; `catalogue_state == "empty"` | «La búsqueda local no devolvió fichas para esta consulta; no se sustituye por texto del modelo.» |

Propiedades que hacen el registro verificable:

- **Ninguna plantilla interpola nada**: ni nombres de producto, ni cifras, ni fechas, ni
  datos del usuario. Es la regla de `CATALOGO.md` §8 («sin interpolar nombres, cifras ni
  datos del usuario») aplicada también a la evidencia.
- La relación con el producto vive en `evidence_refs`, no en el texto. La UI pinta junto
  al ítem una línea «Ficha local: …» tomada de `catalogue.products` con `textContent`.
- Ninguna plantilla contiene dígitos. En las cinco de evidencia tampoco hay coincidencias
  de `_SPELLED_NUMBER` (`backend_services.py:74-79`).
- Un `text` editorial nunca se reescribe en el servidor: se renderiza tal cual del
  diccionario, de modo que la revisión editorial de `CATALOGO.md` sigue siendo válida.

### 2.3 Validación campo a campo

Se ejecuta en `claims_channel.parse_selection` (forma) y `claims_channel.compose`
(disponibilidad). Es la misma disciplina que `parse_selection`
(`structured_provider_adapter.py:156-178`): JSON estricto, sin duplicados, sin `NaN`,
`finish_reason == "stop"`, `refusal is None`, `tool_calls == ()`, `answer` de tipo `str`
y ≤ 4096 bytes UTF-8.

| Campo | Regla | Rechazo |
|---|---|---|
| `answer` (crudo) | `str`; JSON válido; sin claves duplicadas; sin `NaN`/`Infinity`; ≤ 4096 B | `invalid_json` |
| raíz | `dict` exacto | `invalid_shape` |
| claves | `{version, intent, claim_ids}` o las mismas + `evidence_refs`; nada más | `invalid_shape` |
| `version` | `str` exactamente `"paideia-education-v2"` | `invalid_shape` |
| `intent` | `str` en `{explain, calculate}` | `invalid_shape` |
| `intent` vs escenario | `calculate` ⇔ hay `scenario` validado en el payload | `scenario_mismatch` |
| `claim_ids` | `list`, 1..6, `str`, todos en `CLOSED_IDS` (39 editoriales + 5 de evidencia), sin duplicados | `empty_selection` si `[]`; `unknown_claim` si algún id no existe; `invalid_shape` en el resto |
| `evidence_refs` | si existe: `list` 0..6; cada elemento `dict` exacto `{claim_id, source_id}` | `invalid_shape` |
| `evidence_refs[].claim_id` | debe estar en `claim_ids` y ser de tipo evidencia | `unbound_evidence` |
| `evidence_refs[].source_id` | `str` que cumple el patrón y cuyo producto está en `catalogue.products` | `unbound_evidence` |
| cobertura | toda afirmación de evidencia tiene exactamente 1 ref, salvo `ficha_sin_resultados` (0); las editoriales, ninguna | `unbound_evidence` |
| duplicados de ref | un `claim_id` no puede repetirse en `evidence_refs` | `invalid_shape` |
| disponibilidad | la afirmación debe satisfacer su `requiere` con el índice del turno | `unbound_evidence` |
| cobertura de catálogo | si `catalogue_state == "items"`, ≥1 afirmación de evidencia | `missing_required_evidence` |
| `ficha_sin_resultados` | exige `catalogue_state == "empty"` y 0 refs | `unbound_evidence` |
| tamaño compuesto | cada ítem ≤ 520 caracteres y `answer` ≤ 3000 (el `text` más largo del catálogo mide 471 — verificado sobre `CATALOGO.md` §9) | No es rechazo del modelo: es bug del servidor ⇒ 502 `CHAT_CLAIMS_COMPOSITION_ERROR`, sin texto |

`refusal`: si el `ChatResult` trae `refusal` no nulo, no hay selección; el turno se
marca `rejected/refusal` y no se muestra el texto de rechazo del modelo.

### 2.4 Índice de evidencia del turno

No es una estructura nueva de confianza: se deriva de lo que el runner **ya** proyectó.

```python
index = {
    "products": {product_id: projected_product},   # == catalogue["products"]
    "sources":  {source_ref_id: product_id},       # == sources[].source.source_ref.id
    "calculation": projected_calculation | None,
    "catalogue_state": "items" | "empty" | "unprojectable" | "none",
}
```

- `products` y `sources` son exactamente `catalogue["products"]` y `result["sources"]`
  (`pai_runtime.py:1083-1104`), ya validados por `_evidence_product`
  (`pai_runtime.py:487-622`) y `_model_sources` (`:667-686`).
- `catalogue_state` hay que exponerlo desde `run()`: hoy `_empty_catalogue_result`
  (`pai_runtime.py:637-653`) distingue «lista vacía explícita» de «forma no proyectable»,
  pero ese matiz no llega al DTO. Se calcula en el mismo bloque `1083-1096` y se guarda
  solo en el índice.
- El modelo ya ve `source_id` en cada mensaje de herramienta (`_model_sources`, `:675-676`),
  así que puede citar un id que ha visto; la validación comprueba además que resuelve.

Regla de visibilidad: un `source_id` es válido si (a) cumple el patrón, (b) su producto
está en `products` y (c) el id aparece en `sources`. Para `identity:<pid>` la condición
(c) se cumple siempre que (b), porque `_source_for` emite una cita de identidad por
producto (`pai_tools.py:601-614`).

---

## 3. Reglas de composición

### 3.1 Reparto de autoridad

| Elemento | Lo aporta | Nunca lo aporta |
|---|---|---|
| Qué afirmaciones se dicen | modelo (`claim_ids`) | — |
| A qué ficha se refiere una afirmación | modelo (`source_id`, espacio `identity:`) | — |
| Palabras del texto | registro cerrado del servidor | modelo |
| Cifras | `calculation.summary` / `catalogue.products[].conditions[].value` | texto compuesto |
| Atribución («según la ficha local», «documentada») | plantilla del servidor, solo si la evidencia existe | modelo |
| Orden de las afirmaciones | servidor: evidencia por `(claim_id, source_id)`; editorial en el orden del modelo | modelo (solo puede reordenar lo editorial) |
| Selección de qué condición se muestra | servidor (orden determinista) | modelo |

### 3.2 Orden y composición

1. **Bloque de evidencia** primero, ordenado por `(claim_id, source_id)`.
2. **Bloque editorial** después, en el orden elegido por el modelo (es lo único donde
   el orden es suyo, y no cambia el contenido).
3. **Sin texto de cálculo.** El resultado del motor se muestra en su panel
   (`static/app.js:755-767`), no se parafrasea. Así no hay dos sitios donde leer la
   misma cifra ni forma de atribuirla al concepto equivocado.
4. `answer` = unión de los textos con `"\n\n"`, en ese orden.
5. `claims.items[]` conserva `id`, `kind`, `text`, `evidence_refs`; el consumidor puede
   reconstruir la procedencia ítem a ítem.

Desviación consciente de `CATALOGO.md` §8 («unir en el orden devuelto»): la evidencia va
primero y el editorial después. El orden relativo de los editoriales sí es el del modelo.
Se hace así para que el dato local no quede enterrado bajo una introducción conceptual;
no cambia ninguna palabra del texto.

### 3.3 Invariantes verificables

- **I1 — Cero cifras.** El texto compuesto no contiene **ningún dígito** y, en las cinco
  plantillas de evidencia, ninguna coincidencia de `_SPELLED_NUMBER`
  (`backend_services.py:74-79`). No hay interpolación que pueda introducirlos.
  Comprobable con un test parametrizado sobre el registro completo.
- **I2 — Cero atribuciones del modelo.** Las expresiones de atribución solo existen en
  plantillas fijas ligadas a una ficha real; el modelo no puede emitir cadenas.
- **I3 — Cobertura.** `catalogue_state == "items"` ⇒ al menos una afirmación de evidencia
  que resuelve a un producto del índice. Un turno de catálogo no puede degradar a
  conceptos genéricos.
- **I4 — Sin cherry-picking.** El modelo elige el producto, no el valor. Si una métrica
  está en estado `conflict` o tiene ≥2 valores conocidos distintos, se usa
  `ficha_conflicto` y no se muestra ninguna cifra; nunca se elige «el mejor».
- **I5 — Cierre.** Todo `claim_id` está en el registro; toda `source_id` resuelve; en
  caso contrario se rechaza la selección **completa**.
- **I6 — Determinismo.** Misma `(selection, index, scenario)` ⇒ `answer` y
  `claims.items` byte a byte iguales. Sin reloj, sin azar, sin orden de diccionario
  dependiente de la plataforma.
- **I7 — Sin texto del modelo en el DTO.** `claims.model_text_used == false` y
  `answer ⊆ concat(plantillas)`; el test puede comprobarlo con el registro. El DTO
  incluye `claims.catalog_digest` (SHA-256 del registro canónico) y el cliente lo compara
  con la constante compilada: si alguien sustituye un `text`, el digest no cuadra y el
  turno se rechaza en la UI.

### 3.4 Cálculo determinista

Hoy el cálculo depende de que el modelo llame `calculate_scenario`
(`pai_runtime.py:1081-1082`). En el canal cerrado eso es un vector de cifras del modelo:
los argumentos los elige él. Regla nueva:

1. Si el payload trae `scenario`, el **servidor** lo valida (mismas reglas que
   `render_selection`, `structured_education.py:31-40`) y ejecuta
   `domain.calculate_scenario`.
2. Se proyecta con `ToolChatRunner._project_calculation` para obtener la misma forma que
   el resto del DTO. **Verificado**: con el escenario
   `{principal:"1000", annual_rate_percent:"3", years:1, monthly_contribution:"0",
   method:"simple", inflation_percent:"0"}` la proyección devuelve
   `summary.final_balance = "1030.00"` y descarta `series`.
3. En modo afirmaciones el despachador **no anuncia** `calculate_scenario`
   (`_ClaimsReadDispatcher`, solo `search_products` y `get_product_detail`). Si el modelo
   lo pidiera, el runner rechaza la llamada por «herramienta no anunciada»
   (`pai_runtime.py:1039-1042`) y el turno termina en **502 `CHAT_TOOL_ERROR`**
   (`backend_services.py:684-685`), sin texto. Es una violación de protocolo, no una
   selección degradada: se prefiere fail-closed a ignorar la llamada y seguir.
4. El resultado se expone en `calculation` y en el panel; el texto no lo repite.

### 3.5 Fuentes y atribución

- `sources` no cambia: se sigue agregando desde `dispatched["sources"]`
  (`pai_runtime.py:1097-1104`) con `tool`, `tool_call_id` y `source_ref`.
- La afirmación de evidencia no duplica la URL: enlaza por `source_id` y el panel de
  fuentes (`static/app.js:864-889`) muestra clase, fecha y ámbito.
- Si una condición tiene `class_state == "inconsistent"` o `source_resolution !=
  "resolved"`, la ficha ya no publica esa cita (`pai_tools.py:827-840`); la plantilla
  sigue siendo cierta porque no afirma una clase concreta.

---

## 4. Modo degradado

### 4.1 Principio

Un rechazo **no** es un error de transporte: es un turno sin texto, con los datos locales
que sí existen. Por eso devuelve **HTTP 200** con `claims.state = "rejected"`, no 502.
El 502 se reserva para fallo de proveedor o de herramienta (`finish_reason` en
`{"error","tool_error"}`, `backend_services.py:684-685`). Hoy `_failure`
(`pai_runtime.py:162-169`) no recibe `calculation`, así que un error de herramienta
posterior a un cálculo correcto también pierde el panel; es una limitación existente que
esta propuesta no cambia y que conviene declarar en el aviso.

### 4.2 Tabla de estados

| `rejected.reason` | Cuándo | `answer_text_state` | `withheld_reason` | Qué ve el usuario |
|---|---|---|---|---|
| — (`rendered`) | selección válida | `shown_closed_claims` | `null` | Ítems + paneles + fuentes + trazabilidad |
| `invalid_json` | prosa libre, JSON roto, duplicados, `NaN` | `withheld_unbacked_claim` | `invalid` | «No se pudo validar la selección de afirmaciones del modelo; no se muestra texto libre.» + paneles |
| `invalid_shape` | claves, tipos, enum o refs duplicadas | `withheld_unbacked_claim` | `invalid` | igual |
| `unknown_claim` | `claim_id` fuera del registro | `withheld_unbacked_claim` | `unknown_claim` | «El modelo eligió una afirmación que no existe en el catálogo cerrado; no se muestra texto libre.» |
| `unbound_evidence` | ref ausente, duplicada, de otro producto o no disponible | `withheld_unbacked_claim` | `unbound_evidence` | «El modelo citó una ficha local que este turno no aportó o no permite esa afirmación; no se atribuye el dato.» |
| `empty_selection` | `claim_ids: []` | `withheld_unbacked_claim` | `empty_selection` | «El modelo no eligió ninguna afirmación del catálogo cerrado; no hay respuesta que mostrar.» |
| `scenario_mismatch` | `calculate` sin escenario, o escenario con `explain` | `withheld_unbacked_claim` | `scenario_mismatch` | «La selección no coincide con el escenario enviado; no se muestra texto libre. El cálculo local se muestra con sus supuestos.» |
| `missing_required_evidence` | hubo fichas y ninguna afirmación las usa | `withheld_unbacked_claim` | `missing_required_evidence` | «El modelo no usó los datos locales que este turno sí aportó; no se muestra texto libre.» |
| `refusal` | `ChatResult.refusal` no nulo | `withheld_unbacked_claim` | `refusal` | «El proveedor ha rechazado esta consulta.»; se omite la línea duplicada de `app.js:1112` cuando hay bloque `claims` |

En todos los rechazos: `answer = ""`, `claims.items = []`,
`claims.model_text_used = false`, y **se conservan** `catalogue`, `calculation`,
`sources` y `tool_events` si existen. El aviso de motivo vive en un solo sitio,
`static/chat_withheld_notice.js:13-18`; hay que añadir las **seis** claves nuevas
(`unknown_claim`, `unbound_evidence`, `empty_selection`, `scenario_mismatch`,
`missing_required_evidence`, `refusal`) o el usuario verá el genérico «no se pudo
verificar localmente».

### 4.3 Lo que el modo degradado nunca hace

- No muestra el texto del modelo «solo esta vez».
- No reintenta la llamada (coherente con `backend_services.py:521` y `673`: «no hay
  reintento automático»).
- No inventa un catálogo vacío: si `catalogue_state == "unprojectable"`, el aviso dice
  que no se pudo verificar la ficha, no que no exista.
- No promete una cifra que no esté en `calculation` o en una condición publicada.
- No convierte un rechazo en 502 ni un 502 en respuesta vacía.

---

## 5. Cambios mínimos por fichero

### 5.1 Ficheros nuevos

| Ruta | Contenido | Por qué |
|---|---|---|
| `app/claims_catalog.py` | Copia generada del bloque JSON de `CATALOGO.md` §9: `EDITORIAL_V2 = {id: {text, when, never_claim}}`; sin lógica | Una sola fuente editorial, versionable y diffeable |
| `app/claims_channel.py` | `VERSION = "paideia-education-v2"`, carga de `claims_catalog.EDITORIAL_V2`, `EVIDENCE_CLAIMS`, `CLOSED_IDS`, `MAX_CLAIMS = 6`, `catalog_digest`, `build_index`, `validate_scenario`, `parse_selection`, `compose`, `system_contract`, helpers de invariantes | Una sola fuente del contrato y del texto; puro, sin I/O |
| `app/static/claims_ui.js` | `PaideiaClaims.project/select`: valida forma e ids, compara `catalog_digest` con la constante compilada, exige que cada texto de evidencia sea exactamente una de las cinco plantillas y que no haya dígitos | El cliente no confía en texto arbitrario del servidor |
| `tests/test_claims_channel.py` | Parseo, rechazos, plantillas, I1–I7, determinismo | Verificación sin red |
| `tests/test_claims_service.py` | Servicio completo con `FakeChatProvider` guionizado | Integración sin Groq |
| `tests/claims_ui.test.cjs` | Forma, ids desconocidos, dígitos fuera de lugar, doble render | Contrato de UI |

### 5.2 Ficheros modificados

| Fichero | Función | Cambio | Nuevo/Mod. |
|---|---|---|---|
| `pai_runtime.py` | `ToolChatRunner.__init__` (`:72-81`) | `claims_mode: bool = False`, validado con `type is bool` | Mod. |
| `pai_runtime.py` | `_dto` (`:111-138`) | Acepta `claims=None`; admite `ANSWER_TEXT_SHOWN_CLOSED`; añade la clave solo si no es `None` | Mod. |
| `pai_runtime.py` | `_answer_dto` (`:140-153`) | Nuevo parámetro `claims`; con claims válidos **no** fuerza `answer=""` por `catalogue_used` | Mod. |
| `pai_runtime.py` | `_answer_limitations` (`:84-108`) | Nota específica del canal cerrado | Mod. |
| `pai_runtime.py` | `run` (`:980-1127`) | Estado `catalogue_state`; en el mensaje final sin `tool_calls`, `parse_selection` + `compose`; rechazo con `_claims_rejection` | Mod. |
| `pai_runtime.py` | `_claims_rejection` | Construye DTO `answer=""`, `claims.state="rejected"`, paneles intactos | Nuevo |
| `backend_services.py` | constantes (`:58`) | `ANSWER_TEXT_SHOWN_CLOSED`, lista de motivos nuevos | Mod. |
| `backend_services.py` | `answer_provenance` (`:175-195`) | Whitelist del estado y de los motivos; `text_validation`/`text_origin` según canal | Mod. |
| `backend_services.py` | `LocalChatService.__init__` (`:376-422`) | `claims_mode=False`; exige `enabled`, `provider`, `admission`, `dispatcher`, `tools_enabled`; **no** exige `structured_mode` | Mod. |
| `backend_services.py` | `status` (`:443-452`) | `capabilities["claims_channel"]` | Mod. |
| `backend_services.py` | `chat` (`:454-523`) | `scenario` permitido con claims; prompt de sistema cerrado; rama a `_tools_chat(claims_payload=...)` | Mod. |
| `backend_services.py` | `_tools_chat` (`:576-714`) | Pasa `claims_mode` al runner; si hay `result["claims"]`, no aplica `692-695` ni `_withhold_unbacked_claim`; añade `claims` y ajusta procedencia | Mod. |
| `backend_services.py` | `_ClaimsReadDispatcher` | Solo `search_products` y `get_product_detail` | Nuevo |
| `pai_setup.py` | `build_chat_service` (`:300-332`) | Parámetro `claims_mode` (defecto `False`), trasladado a `_historical_chat_service` | Mod. |
| `static/app.js` | rama de respuesta (`:1054-1077`) | Si `result.claims` existe, `PaideiaClaims.select` y `renderChatClaims`; nunca imprime `answer` ni la frase de rechazo de `:1112` en ese caso | Mod. |
| `static/app.js` | `renderChatClaims` | `<ul>` de ítems + paneles + fuentes; `textContent` | Nuevo |
| `static/app.js` | `renderChatProvenance` (`:890-896`) | Si `text_validation === "closed_selection"`, otra frase de trazabilidad | Mod. |
| `static/app.js` | aviso (`:1090-1097`) | Pasa `reason` también cuando hubo catálogo, para no perder el motivo específico | Mod. |
| `static/chat_withheld_notice.js` | `REASONS` (`:13-18`) | Seis motivos nuevos, `refusal` incluido | Mod. |
| `static/index.html` | scripts (`:18-19`) | `<script src="./claims_ui.js" defer>` antes de `app.js` | Mod. |
| `tests/test_chat_context.py` | `:21` | Diccionario exacto de capacidades | Mod. |

`structured_education.py`, `structured_provider_adapter.py` y
`groq_structured_adapter.py` **no se tocan**: el canal v1 sigue siendo el de las pruebas
cerradas. `build_claims_request` (nuevo) puede vivir en `groq_structured_adapter.py`
reutilizando `build_chat_request`, sin modificar `build_structured_request`.

### 5.3 Pruebas existentes que podrían romperse

| Prueba | Por qué | Mitigación |
|---|---|---|
| `tests/test_chat_context.py:21` | Afirma el diccionario exacto de `capabilities` | Actualizar la línea (una clave nueva) |
| `tests/test_pai_setup_integration.py:135-136` | Espera prosa `"Respuesta sintética."` en la ruta ordinaria | `claims_mode=False` por defecto: sigue verde |
| `tests/chat_frontend_contract.test.cjs` (contexto vm sin `PaideiaClaims`) | Un acceso directo lanzaría `ReferenceError` y rompería toda la sección | Guardar con `typeof PaideiaClaims !== "undefined"`, igual que `PaideiaWithheldNotice` en `app.js:1090` |
| `tests/b4_chat_provenance.test.cjs` | Espera el render retenido actual | La rama nueva solo actúa si `result.claims` existe; el resto no cambia |
| `tests/test_structured_education.py`, `test_structured_provider_adapter.py` | Fijan `render_selection` y `parse_selection` | No modificar esos módulos |
| `tests/test_b4_cycle2_provenance.py`, `test_b4_cycle3_boundary.py`, `test_b4_cycle4_outcomes.py` | Asumen `_text_surface_gate` en la ruta de herramientas | La ruta sin claims conserva la frontera; el canal nuevo la evita **solo** con texto compuesto |

No hay ninguna prueba que afirme el conjunto exacto de claves del DTO de chat
(comprobado con búsqueda de `set(body)`/`set(result)`): añadir `claims` es aditivo.

### 5.4 Cómo probarlo sin Groq ni red

`FakeChatProvider` ya está importado en `backend_services.py:15` y aceptado por
`_closed_test_provider` (`:30-31`). Basta guionizar dos resultados:

```python
from providers import ChatResult, ToolCall
from structured_provider_adapter import FakeChatProvider
from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission
from pai_tools import ToolDispatcher
from backend_services import LocalChatService

fake = FakeChatProvider(None, test_only=True, outcomes=(
    ChatResult("", None, (ToolCall("c1", "search_products", {"query": "deposito"}),), "tool_calls"),
    ChatResult('{"version":"paideia-education-v2","intent":"explain",'
               '"claim_ids":["ficha_tasa","fuente_atribucion_con_prueba"],'
               '"evidence_refs":[{"claim_id":"ficha_tasa",'
               '"source_id":"identity:DEP-EJEMPLO"}]}', None, (), "stop"),
))
service = LocalChatService(
    provider=fake, enabled=True, test_only=True, claims_mode=True,
    dispatcher=ToolDispatcher(repository, None), tools_enabled=True,
    admission=InterfazChatAdmission(policy, clock=clock, budget_state=budget_state),
)
# `policy`, `clock` y `budget_state` se construyen igual que en la ruta real:
# AdmissionPolicy + InMemoryBudgetState (pai_setup.py:172-185).
```

`FakeChatProvider` valida cada `outcome` con `_fixture_outcome`
(`structured_provider_adapter.py:23-35, 112-123`) y no abre transporte. Para la ruta de
sesión contada, `StructuredSessionFixture` + parcheo de `GroqHTTPSJSONTransport`, como en
`tests/test_pai_setup_integration.py:117-137`.

Casos mínimos a cubrir:

1. Turno conceptual: solo editoriales, `state=rendered`, sin `catalogue.used`.
2. Turno de catálogo con ficha: `ficha_tasa` + `fuente_atribucion_con_prueba`, `source_id` válido.
3. `source_id` de otro producto → `unbound_evidence`, paneles visibles.
4. `claim_id` inexistente → `unknown_claim`.
5. Prosa libre → `invalid_json`.
6. `claim_ids: []` → `empty_selection`.
7. Fichas presentes y selección solo editorial → `missing_required_evidence`.
8. Escenario sin `intent=calculate` → `scenario_mismatch`; con él, panel de cálculo.
9. Dos valores distintos de TAE → `ficha_conflicto`, ninguna cifra en el texto.
10. Repetición byte a byte de (2) para I6.

---

## 6. Riesgos y mitigación

| Riesgo | Por qué es real aquí | Mitigación |
|---|---|---|
| **Doble render** | `answer` y `claims.items` contienen el mismo texto; el panel de cálculo repite cifras si el texto las parafrasea | La UI pinta ítems y **nunca** `answer` cuando hay `claims`; el texto no contiene cifras (I1); test DOM que cuenta nodos y compara `textContent` |
| **Inyección de texto** | Nombres y condiciones del catálogo son datos no confiables (`pai_runtime.py:599-620`) | Ni una plantilla interpola datos: el texto es 100 % fijo. Los nombres solo aparecen en los paneles, con `textElement`/`textContent` (nunca `innerHTML`); CSP intacta (`app.py:653-657`); `catalog_digest` fijado en el cliente |
| **Compatibilidad del DTO** | Estado nuevo (`shown_closed_claims`) y motivos nuevos; `answer_provenance` degrada lo desconocido a `shown_unverified` (`:181-182`) | Actualizar whitelists; claves aditivas y solo en modo claims; cliente antiguo sigue leyendo `answer`, que es texto compuesto seguro |
| **Impresión / informe** | `window.print()` existe para el justificante (`app.js:3054`) y `@media print` en `styles.css:425`; el informe de comparación no consume el DTO de chat (`comparison_report.js`) | Verificar que `.chat-claims` no se oculta al imprimir y que no se imprime dos veces; no tocar el informe |
| **Accesibilidad** | El contenedor de respuesta es `role="status"` (`app.js:956`) y pasa a `aria-live="assertive"` en errores (`1131`, `1143`); seis párrafos nuevos pueden anunciarse de golpe y duplicarse | Una línea-resumen breve en la región viva y la lista `<ul>/<li>` con encabezado fuera de ella; máximo 6 ítems; probar con el lector del sistema |
| **Selección sesgada** | El modelo puede elegir solo la afirmación favorable u omitir la ficha | I3 (cobertura obligatoria), I4 (sin elección de valor), orden fijo, y el panel de datos locales siempre visible con todas las condiciones |
| **Rechazo total por un id malo** | Fail-closed pierde el turno entero | Motivo estable y visible, paneles conservados, sin reintento automático; el coste se acepta frente a mostrar algo no verificable |
| **Cobertura limitada** | Pai solo dirá lo que esté en el registro | Es la garantía, no un defecto: ampliar el registro con texto revisado, no relajar el canal |
| **Tripwire de calidad** | `_financial_checked` puede convertir un texto compuesto en 502 | Test que pasa las 39 afirmaciones y las 5 plantillas por `assess_financial_text` (las 44 devuelven `()` — verificado) |

---

## 7. Anexo — turno completo de ejemplo

Petición:

```json
{"message": "¿Qué TAE tiene el depósito de ejemplo?",
 "consent": {"notice_version": "paideia-chat-remote-v1",
             "accepted_chat_processing": true,
             "purpose": "free_chat", "approved_fields": []}}
```

Ronda 1: el modelo pide `search_products`; el runner proyecta la ficha
(`_evidence_product`), marca `catalogue_state="items"` y agrega la cita de identidad
`identity:DEP-EJEMPLO`.

Ronda 2 (mensaje final, sin herramientas):

```json
{"version": "paideia-education-v2", "intent": "explain",
 "claim_ids": ["ficha_tasa", "fuente_atribucion_con_prueba"],
 "evidence_refs": [{"claim_id": "ficha_tasa", "source_id": "identity:DEP-EJEMPLO"}]}
```

DTO resultante (recortado; el texto editorial es literalmente el de `CATALOGO.md` §9):

```json
{
  "answer": "La ficha local seleccionada incluye una condición de tasa; el panel de datos locales muestra el producto, su estado, su valor cuando consta y su fuente.\n\nAtribuir un dato a una entidad exige poder señalar el documento, la fecha y el punto concreto donde aparece; sin esa cadena, la atribución es una afirmación sin respaldo. Repetir un dato citando a un tercero no crea esa cadena.",
  "answer_text_state": "shown_closed_claims",
  "catalogue": {"used": true, "products": [{"id": "DEP-EJEMPLO", "...": "..."}]},
  "calculation": null,
  "sources": [{"tool": "search_products",
               "source": {"source_ref": {"namespace": "local-tools.v1",
                                         "id": "identity:DEP-EJEMPLO"}, "...": "..."}}],
  "claims": {
    "version": "paideia-education-v2",
    "state": "rendered",
    "model_text_used": false,
    "catalog_digest": "sha256:…",
    "selection": {"version": "paideia-education-v2", "intent": "explain",
                  "claim_ids": ["ficha_tasa", "fuente_atribucion_con_prueba"],
                  "evidence_refs": [{"claim_id": "ficha_tasa",
                                     "source_id": "identity:DEP-EJEMPLO"}]},
    "items": [
      {"id": "ficha_tasa", "kind": "evidence_bound",
       "text": "La ficha local seleccionada incluye una condición de tasa; el panel de datos locales muestra el producto, su estado, su valor cuando consta y su fuente.",
       "evidence_refs": ["identity:DEP-EJEMPLO"]},
      {"id": "fuente_atribucion_con_prueba", "kind": "editorial",
       "text": "Atribuir un dato a una entidad exige poder señalar el documento, la fecha y el punto concreto donde aparece; sin esa cadena, la atribución es una afirmación sin respaldo. Repetir un dato citando a un tercero no crea esa cadena.",
       "evidence_refs": []}
    ],
    "rejected": null
  },
  "answer_provenance": {
    "text_validation": "closed_selection",
    "text_origin": "server",
    "text_state": "shown_closed_claims",
    "withheld_reason": null,
    "tool_sources_present": true,
    "catalogue_evidence_present": true,
    "limitations": ["Cada frase procede de un catálogo cerrado del servidor; el modelo solo eligió identificadores. Las cifras se muestran únicamente en los paneles de datos locales y del motor determinista."]
  }
}
```

La cifra de la TAE no aparece en `answer`: está en `catalogue.products[].conditions[]`,
con su estado, clase y fechas, y el panel la pinta con `renderChatCatalogue`
(`app.js:768-863`). El modelo no ha escrito ninguna palabra del resultado.
