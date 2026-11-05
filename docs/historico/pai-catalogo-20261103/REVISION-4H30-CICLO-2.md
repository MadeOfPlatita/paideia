# B4 — Re-revisión independiente (segunda pasada)

Fecha: 2026-11-04 13:31 (Europe/Madrid). Árbol: `C:/Users/aleja/Downloads/App Financiera` (sin commitear).
No se ha modificado código, docs, `.env` ni Git; no ha habido llamadas reales ni red externa. Todo se ejecutó contra servidores loopback reales de la app, con `FakeChatProvider` sintético cerrado y datos ficticios/internos del repo. Los servidores y el navegador se cerraron al terminar.

## Veredicto

**`passed: false`.**

El defecto bloqueante original **B4-01** (la fuente resuelta por `source_refs` no llegaba a la lectura del catálogo de Pai) **está corregido en la proyección de herramientas**: `get_product_detail` y `search_products` devuelven para ACC-01 la URL del PDF, su título y la fecha `2026-10-27`, con `source_resolution="partial"`, `source_class="unknown"` y `attribution_state="partial"`. El panel de chat muestra el enlace «Fuente de la condición», «atribución parcial» y «clase de fuente: Desconocida».

Pero el estado FINAL de `pai_tools.py` (editado a las 13:23:55, hash `7aae51d4…`) no se refleja en el DTO de chat/panel: `pai_runtime._evidence_product` sigue exigiendo clase oficial/secundaria y resolución completa para conservar `documented`, así que **degrada ACC-01 a `conditions_unknown`**. El panel dice, en la misma ficha, «Condiciones desconocidas; atribución parcial» y dos líneas después «TAE: 2.61 % — documentada» con la fuente enlazada. Es una contradicción de estado en el producto central de B4 y no aparece en las pruebas del autor.

## Estado revisado

El árbol cambió durante la revisión: `pai_tools.py` pasó de `95dc071c…` (13:10:59) a `7aae51d4…` (13:23:55). Todos los resultados finales de este informe se tomaron después de reiniciar los servidores contra el hash final. No hubo más cambios hasta las 13:31.

```
7aae51d4092cb5681688aa62cfdbe886b9095412b930660ca1fa5d1617aa7272  app/pai_tools.py
13bb7abd6e7ecdf542201981e834376f4b6d4800939244ea5a1ebdf05d6f6243  app/pai_runtime.py
fd2ef09d9adc5a2816c4460c9a140e3d5bb925fef82e0e262240c28a88fbf32b  app/catalogue_adapter.py
3407ff17a3b8586fd24bb368f8acfbd95e5635e7d3948a83c97fce74c7e2a882  app/catalogue_conditions.py
c8a0fdc4c841b29fd760e56594e7a8687a7bf79cc74537174b9070b69c8d016d  app/static/app.js
b003e1e2c0c361e3dfaecf9ec8cdad0547932602e78659ac2398804789350a22  app/app.py
240cc27c4f86fba0fc389121be2bc0e558f7b4a52c258a50883084f68e253bb9  api/index.py
ef735d9bc2dd7b3e7a4030a8d07ae345fe86d0a3ed783d5ec62a23ca45212fbc  api/_core/catalogue_conditions.py
c8a0fdc4c841b29fd760e56594e7a8687a7bf79cc74537174b9070b69c8d016d  api/_static/app.js
```

## 1. ACC-01 y DEP-02: la fuente ya llega; estado de chat incoherente

### ACC-01 (Renault Bank)

`derive()` resuelve el id 1 a:

```
source_ids: ["https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf"]
source_refs: [{url: "…RenaultBank.pdf",
               title: "Renault Bank — Información precontractual global",
               accessed: "2026-10-27"}]
```

`ToolDispatcher._project_conditions` usa ahora `source_refs` y devuelve en **`get_product_detail` y `search_products`**:

```
conditions_state: "documented"
attribution_state: "partial"
annual_rate_percent: state "known", value "2.61", source_resolution "partial",
  source_class "unknown", class_state "consistent"
sources: [{url: "…RenaultBank.pdf", class: "unknown",
           title: "Renault Bank — Información precontractual global",
           retrieved_at: "2026-10-27", resolution: "resolved"}]
limitations: ["Fuente enlazada desde el registro de fuentes; el registro no declara
              si es oficial o secundaria."]
```

El enlace no se declara oficial en ningún sitio: la única aparición de «oficial» es la
limitación que dice que el registro **no** declara si es oficial o secundaria.

El **DTO de `/api/chat`** (mismo turno, mismo producto) conserva la condición, el valor,
la URL y `attribution_state="partial"`, pero cambia el estado del producto:

```
conditions_state: "conditions_unknown"
attribution_state: "partial"
annual_rate_percent: known 2.61 · partial · unknown · url …RenaultBank.pdf · 2026-10-27
```

El panel real de Chromium (sesión local, `http://127.0.0.1:51313/#chat`, mensaje
`B4-ACC01`, consentimiento marcado, `FakeChatProvider` cerrado) muestra:

```
Cuenta Contigo (ACC-01)
Familia: cuenta_remunerada · Emisor: Renault Bank · identidad verificada
Condiciones desconocidas; atribución parcial · fecha de referencia: 2026-11-04.
…
TAE: 2.61 % — documentada; clase de fuente: Desconocida.
Consulta de la fuente: 2026-10-26.
Vigencia: 2026-10-21 → 2026-11-18.
Atribución de la condición: atribución parcial.
Fuente enlazada desde el registro de fuentes; el registro no declara si es oficial o secundaria.
Fuente de la condición: https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf
```

El enlace es un `<a href="https://doc.renaultbank.es/…RenaultBank.pdf" target="_blank" rel="noopener noreferrer">`; el `<a>` y el href se verificaron en el DOM. Referencias locales: «Cuenta Contigo — condiciones — clase: Desconocida; consultada: 2026-10-27».

**Causa exacta del estado incoherente:** `pai_runtime.py:516-522`:

```python
if conditions_state == "documented" and not any(
        condition["state"] == "known"
        and condition["source_class"] in {"official", "secondary"}
        and condition["source_resolution"] == "resolved"
        and condition["class_state"] != "inconsistent"
        for condition in conditions):
    conditions_state = "conditions_unknown" if conditions else "identity_only"
```

ACC-01 es `known` + `partial` + `unknown`, así que no cumple esa puerta y se degrada a
`conditions_unknown`. No se añade ningún motivo que explique el cambio: el panel solo
hereda «Revisión pendiente…». El tool DTO dice `documented`; el chat DTO y el panel dicen
`conditions_unknown`. El estado FINAL que el autor describe («ACC-01 documented+partial»)
es cierto en la herramienta, pero **no** en la lectura de chat/panel.

### DEP-02 (Openbank, control curado)

`get_product_detail` y el panel devuelven:

```
conditions_state: "documented"
attribution_state: "resolved"
TAE: 2.75 % — documentada; clase de fuente: Oficial.
Consulta de la fuente: 2026-11-03.
Atribución de la condición: fuente resuelta.
Fuente de la condición: https://www.openbank.es/deposito-a-plazo-fijo
Plazo: 6 meses — documentada; clase de fuente: Oficial.
```

La fuente consta como `official` en `data/condiciones.json` (`source.kind="official"`);
no es una clase inventada por el ledger. Por eso DEP-02 sigue `resolved/official` y no
`partial/unknown`: la regla «nunca oficial» aplica a las fuentes resueltas desde el
registro sin clase (ACC-01), no a una fuente curada que declara su clase.

## 2. Fallo cerrado y fuente interna sin registro

- `ConditionsService(sources_path=<ledger inexistente>)`: ACC-01 queda
  `conditions_unknown`, `attribution_state="none"`, condición `unknown`, `value=None`,
  `source_resolution="none"`, `sources=[]`; la nota es «Fuente sin URL verificable
  (ids: 1); no se publica el dato.». El panel no muestra 2.61 y el único enlace es el de
  identidad (el PDF), etiquetado «clase: Identidad… Acredita identidad, no condiciones».
- `_resolve_condition_sources(["1"], [], {})` devuelve `([], "unresolved", "unknown",
  ["Identificador de fuente interno sin registro resoluble; la condición no se atribuye
  a una fuente."])`.
- Una condición `known` con `source_ids=["1"]`, `source_refs=[]` y sin registro se
  proyecta con `source_resolution="unresolved"`, `sources=[]`,
  `attribution_state="unresolved"`; **no se inventa ninguna URL**. El valor se conserva
  con la limitación de fuente no resoluble, que es el comportamiento documentado del
  bloque (una condición conocida sin fuente enlazada queda `documented_unattributed`).
- Matiz: en el caso real de ledger vacío, `derive()` marca la condición `unknown` y
  vacía `source_ids`; por eso el chat muestra `none`/«sin fuente citada» en vez del
  literal `unresolved`. El fallo es más cerrado (sin valor), pero la etiqueta no es
  exactamente `unresolved`; ver límites.

## 3. Vencidos y conflictos

**Pibank (DEP-03, `valid_to 2026-10-31`)** — panel real:

```
Condiciones documentadas pero no vigentes; fuente resuelta · fecha de referencia: 2026-11-04.
Hay condiciones vencidas o en conflicto; no se presentan como vigentes.
TAE: 3.03 % — vencida; clase de fuente: Oficial.
Vigencia: sin inicio declarado → 2026-10-31.
La vigencia declarada ya terminó.
```

La tasa no se presenta como vigente: va etiquetada «vencida» y la ficha declara que la
vigencia terminó. El plazo sigue `known` y se rotula «documentada» sin marca de
vencimiento (límite heredado B4-L2).

**ACC-02 (MyInvestor)** — panel real: «TAE: sin valor documentado — en conflicto; clase de
fuente: Desconocida», atribución parcial y el conflicto literal:

```
La misma página mezcla 2,50 % TAE/6 meses y un FAQ con 1,25 % TAE/12 meses,
2,50 %/6 meses y 0,30 % desde el séptimo mes; no elegir una tarifa ni corregir
bloques sin revisar bases legales.
```

También aparece bajo «Conflictos que siguen abiertos». No se publica una TAE elegida.

## 4. Calculadora, paridad y suite

- Turno `B4-CALC` (principal 1000,00; 3,00 %; 2 años; compuesto; aportación 0; inflación
  0): HTTP 200, `answer=""`, `answer_text_state="withheld_unbacked_claim"`,
  `withheld_reason="calculation"`, `summary.final_balance="1060.90"`,
  `summary.interest="60.90"`, `contributions="1000.00"`, sin `series`. Panel real:
  «Saldo final: 1.060,90 EUR», «Interés: 60,90 EUR», sin prosa del modelo (el texto
  sintético adversario «El interés obtenido es 1.000,00 euros.» se retuvo).
- Batería de prosa A–P: los cuatro textos exigidos, la atribución falsa y las cifras con
  palabras incluidas en `_SPELLED_NUMBER` siguen retenidos; F y H (sin cifra) se muestran
  como `shown_unverified`. Sin regresión.
- Paridad local (`app.py`, puerto 51313) vs `api/index.py`: **32/32 checks, ALL SAME:
  True** (conditions completo, 6 productos, 4 comparaciones y bundle empaquetado).
- Suite: `pytest` de B4 + catálogo + Pai → **151 passed, 124 subtests passed**; `node
  --test tests/*.cjs` → **86 passed**.
- El navegador solo cargó recursos de `http://127.0.0.1:51313` (sin orígenes externos).

## 5. `source_refs` malformados

Casos probados contra `_project_conditions` y contra el DTO de `get_product_detail`:
`source_refs` como string, como objeto, URL `http://`, URL `javascript:`, título de 201
caracteres, cinco referencias, fecha `27/10/2026` y referencia que no es objeto. En todos:

```
_ToolFailure("REPOSITORY_ERROR", "Condiciones no válidas en el catálogo.")
dispatcher: {"status":"error","data":{},"sources":[],
             "error":{"code":"REPOSITORY_ERROR","message":"Condiciones no válidas en el catálogo."}}
```

No se filtró la URL malformada, ni el valor 2.61, ni el id interno. El turno HTTP con el
caso de tipo erróneo devolvió **502** `{"error":{"code":"CHAT_TOOL_ERROR","message":"No se
pudo completar el turno de herramientas.","request_id":…,"retryable":false}}` y el panel
mostró «No se pudo completar el turno de herramientas.»; no hubo traza ni caída del
servidor. El turno se aborta de forma controlada (ver límites).

## Defecto bloqueante

### B4-R2-01 — El DTO de chat/panel degrada ACC-01 a `conditions_unknown` aunque la condición es `known` y tiene fuente enlazada

- **Dónde:** `app/pai_runtime.py::ToolChatRunner._evidence_product`
  (líneas 516-522), en interacción con el nuevo `attributable_known` de
  `app/pai_tools.py` (líneas 370-377).
- **Observado:** el tool DTO de ACC-01 devuelve `conditions_state="documented"` y
  `attribution_state="partial"`; el DTO de `/api/chat` devuelve el mismo producto con
  `conditions_state="conditions_unknown"`. El panel muestra «Condiciones desconocidas;
  atribución parcial» y, a la vez, «TAE: 2.61 % — documentada» y el enlace a la fuente.
  No hay ningún motivo que explique el paso a desconocidas.
- **Esperado:** que el DTO de chat conserve `documented` (o, como mínimo,
  `documented_unattributed`) con `attribution_state="partial"` y `source_class="unknown"`,
  coherente con el tool DTO, el valor conocido y la fuente enlazada; y una prueba de
  regresión del DTO de chat para ACC-01.
- **Evidencia:** `http_probe2.json` (`chat_ACC01`), `acc01_panel_final.txt`,
  `panel_acc01_final.png`, `pipeline_probe.json` (`detail_ACC-01`, `search_renault`) y las
  líneas de código citadas.

## Límites (no bloqueantes)

- **B4-R2-L1 — título descartado en chat:** `_project_conditions` conserva
  `title` en el tool DTO, pero `pai_runtime._evidence_condition` solo copia
  `url/class/retrieved_at/resolution`; el panel muestra la URL, no el título. La
  aceptación pedía URL y fecha, que sí están; si se exige la referencia con título en el
  chat, falta propagarlo.
- **B4-R2-L2 — `unresolved` literal en ledger vacío:** el caso de registro vacío queda
  `unknown`/`none` con nota «Fuente sin URL verificable»; no muestra el literal
  `unresolved` porque `derive()` vacía `source_ids`. El caso de id interno sin registro
  sí proyecta `unresolved`. En ambos no se atribuye ni se inventa URL.
- **B4-R2-L3 — `source_refs` malformados abortan el turno:** el DTO de herramienta es
  correcto y no filtra, pero `/api/chat` responde 502 `CHAT_TOOL_ERROR` en vez de degradar
  la condición a `unresolved` y mantener un turno 200. Es fallo cerrado, no caída.
- **B4-R2-L4 — Pibank/plazo:** la tasa vencida se marca; `term_months` sigue `known` y
  «documentada» sin marca de vencimiento (heredado B4-L2).
- **B4-R2-L5 — ficha de biblioteca de ACC-01:** sigue mostrando el PDF solo como «Fuente
  primaria» (coincide con `primary_url`), no como «Fuente de las condiciones»; DEP-02 sí
  muestra «Fuente de las condiciones» porque `entry.source` existe. Para ACC-01 el enlace
  no se pierde porque ambas URLs coinciden, pero la etiqueta no usa `source_refs`.
- **B4-R2-L6 — DEP-02 oficial:** `resolved/official` es correcto porque
  `data/condiciones.json` declara `kind:"official"`. Si la aceptación exigiera
  `partial/unknown` también para DEP-02, sería una contradicción con el dato curado, no
  un defecto de proyección.
- **B4-R2-L7 — gate de prosa:** siguen pasando numerales compuestos con palabras
  (`doscientos`, `trescientos`, `veintidós`, `billón`) como `shown_unverified`; es el
  límite B4-L1 ya conocido, no una regresión.

## Evidencia reproducible

Carpeta: `C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/cache/scratch/b4rev2_4h30/`.

Comandos (servidores loopback efímeros; cerrados al terminar):

```
python b4_server2.py --port 0                         # normal -> 51313
python b4_server2.py --port 0 --mode malformed        # -> 51315
python b4_server2.py --port 0 --mode broken_sources   # -> 51316
python pipeline_probe.py
python http_probe2.py 51313 51315 51316
python malformed_probe.py
python parity_probe.py 51313
python text_gate_probe.py
python -m pytest app/tests/test_b4_*.py \
  app/tests/test_catalogue_adapter.py \
  app/tests/test_catalogue_conditions.py \
  app/tests/test_catalogue_sources.py \
  app/tests/test_pai_tools.py \
  app/tests/test_pai_runtime.py -q
node --test tests/*.cjs
```

Archivos principales: `pipeline_probe.json`, `http_probe2.json`, `malformed_probe.json`,
`parity_probe.json`, `text_gate_probe.json`, `pipeline_stdout2.txt`,
`http_stdout2_new.txt`, `malformed_stdout2.txt`, `parity_stdout2_final.txt`.

Capturas: `panel_acc01_final.png`, `panel_dep02_final.png`, `acc02_panel_final.png`,
`pibank_panel_final.png`, `calc_panel_final.png`, `broken_sources_panel_final.png`,
`malformed_panel_final.png`.

Navegador: Chromium local, sesión `b4rev2`; `#chat-message`, `#chat-consent`,
`#chat-submit`, `#chat-feedback`; el panel se leyó por `innerText` y los enlaces por
`querySelectorAll("#chat-feedback a")`. `performance.getEntriesByType("resource")` solo
devolvió el origen `http://127.0.0.1:51313`.

## JSON

El dictamen legible por máquina está en `FINDINGS.json` (mismas claves `passed`,
`blocking_defects`, `limits` y `evidence`).
