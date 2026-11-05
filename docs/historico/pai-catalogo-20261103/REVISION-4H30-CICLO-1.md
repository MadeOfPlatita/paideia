# B4_REVIEW — Revisión adversarial de B4 (Pai con catálogo trazable)

Fecha: 2026-11-04, 13:17 (Europe/Madrid). Árbol: `C:/Users/aleja/Downloads/App Financiera` (rama `master`, sin commitear).
Revisión independiente: no se ha modificado código de la app, docs, git, `.env` ni se ha llamado a Groq/red externa. Todo se ejecutó contra el servidor HTTP local real, un navegador real y la función WSGI `api/index.py`, con un proveedor sintético cerrado (`FakeChatProvider` con `outcomes`) y los datos internos/ficticios del repo.

## Veredicto

**`passed: true`, con límites.** El estado final cumple los cuatro criterios del bloque:

1. La interfaz muestra el resultado determinista (principal 1.000,00, 3,00 %, 2 años, compuesto → saldo 1.060,90, interés 60,90) con sus supuestos; los cuatro textos adversarios exigidos y la prosa maliciosa con cifra correcta/atribución falsa se retienen; la explicación conceptual sin cifras se muestra.
2. ACC-02 muestra el conflicto literal y los campos desconocidos en tarjeta y ficha, sin presentar una TAE documentada; el PDF de Renault de ACC-01 está enlazado en la tarjeta/ficha de la biblioteca (como «Fuente primaria», que coincide con la fuente de la condición) y en Pai aparece ya como «Fuente de la condición».
3. Pibank (valid_to 2026-10-31) se muestra vencido y sin cifra vigente; una fuente no resoluble produce `unknown/SOURCE_UNRESOLVED` y no publica la cifra; una métrica/unidad incoherente se rechaza en la frontera de proyección.
4. La paridad local/WSGI en condiciones, fichas y comparación con los mismos datos da `ALL SAME: True` (32 comprobaciones) en el estado final.

Quedan límites no bloqueantes: el gate de prosa no cubre numerales compuestos con palabras; la ficha/biblioteca no usa `source_refs.title/accessed` ni etiqueta la fuente como «de la condición» (Pai sí la enlaza); Pai dice «documentadas sin fuente atribuible» aunque enlaza la fuente (atribución parcial por clase desconocida); el listado/comparación usan un conflicto genérico; las fuentes curadas no validan URL; `derive` sin registro es fail-open; Pibank mantiene el plazo como «documentado» sin vencimiento.

**Nota de estabilidad (importante):** el árbol se editó durante la revisión. En la instantánea de ~12:29, la ficha de `DEP-SELF-12` devolvía `product:null` y Pai no enlazaba la fuente de ACC-01 (`sources:[]`, «sin fuente resoluble»). El autor corrigió la ficha (app.py 12:40 / api/index.py 12:36) y la proyección de `source_refs` en Pai (`pai_tools.py` 13:10). El veredicto se refiere al estado final congelado (última edición 13:10, sin cambios hasta 13:17); los hashes están abajo. La instantánea anterior se conserva solo como evidencia del cambio (`selfbank_ficha_error.png`).

## Método y artefactos

- Servidor local real: `python b4_server.py --port 0` (puerto 53051). Usa `app.create_server`, `SnapshotRepository`, `ConditionsService`, `CatalogueWithConditions`, `LocalChatService`, `ToolChatRunner` y `ToolDispatcher` reales; solo el upstream es `FakeChatProvider` test-only. El router crea un `LocalChatService` nuevo por turno y consume `outcomes=(tool_call, texto_adversario)`.
- Función WSGI real: `python wsgi_server.py` (puerto 51355), `wsgiref` sirviendo `api/index.py` con `api/_core` y `api/_static`.
- Fallo cerrado: `python b4_broken_sources.py`, `ConditionsService(sources_path=<ledger inexistente>)`.
- Navegador real: Chromium local vía `browser_exec` (sesión aislada `b4rev`), no solo DOM simulado.
- Pruebas del autor (dato, no fuente de verdad): `python -m pytest tests/test_b4_*.py tests/test_catalogue_conditions.py tests/test_catalogue_sources.py tests/test_b6_compare_parity.py tests/test_pai_tools.py -q` → **133 passed, 112 subtests**; `node --test tests/*.cjs` → **85 passed**.

Hashes del estado revisado:

```
c8a0fdc4c841b29fd760e56594e7a8687a7bf79cc74537174b9070b69c8d016d  app/static/app.js
b003e1e2c0c361e3dfaecf9ec8cdad0547932602e78659ac2398804789350a22  app/app.py
814e6e3e5aa57d3e0dc8ac2b2a038bc1e18dc5845082501ef7c2c0e5d394c881  app/backend_services.py
95dc071ce82001f0666b7a168737a77c10787915d9071605ae327b1ae8c398fc  app/pai_tools.py
13bb7abd6e7ecdf542201981e834376f4b6d4800939244ea5a1ebdf05d6f6243  app/pai_runtime.py
240cc27c4f86fba0fc389121be2bc0e558f7b4a52c258a50883084f68e253bb9  api/index.py
ef735d9bc2dd7b3e7a4030a8d07ae345fe86d0a3ed783d5ec62a23ca45212fbc  api/_core/catalogue_conditions.py
```

`api/_static/app.js` es byte-idéntico a `app/static/app.js`; `api/_core/catalogue_conditions.py` es idéntico salvo la cabecera generada (verificado con `difflib` normalizando CRLF).

## 1. Turno de calculadora (HTTP real + navegador real): PASA, con límites

Escenario: principal 1000,00, tipo 3,00 %, plazo 2 años, compuesto, aportación 0, inflación 0. El `calculate_scenario` real devuelve `final_balance 1060.90`, `interest 60.90` (también en `/api/calculate`: `contributions 1000.00`, `final_balance 1060.90`, `interest 60.90`, `inflation_adjusted 1060.90`).

Comando:

```
cd .../b4rev_4h30
python http_probe.py 53051
```

Salida (extracto real):

```
--- chat A status=200
  answer: ''
  text_state: withheld_unbacked_claim withheld: calculation
  calc: {"hypothetical": true, "not_prediction": true, "currency": "EUR", "assumptions": {"principal": "1000.00", ... "years": 2, "method": "compound"...
--- chat B ... withheld_unbacked_claim withheld: calculation
--- chat C ... withheld_unbacked_claim withheld: calculation
--- chat D ... withheld_unbacked_claim withheld: calculation
--- chat E ... withheld_unbacked_claim withheld: attribution
--- chat F ... answer: 'El interés compuesto reinvierte los intereses y por eso el saldo crece más que con interés simple.' shown_unverified
--- chat G ... withheld_unbacked_claim withheld: calculation
--- chat H ... answer: 'El resultado es correcto y coincide con el cálculo.' shown_unverified
```

Textos exactos probados (A-E son los exigidos; E es la cifra correcta con atribución falsa):

- A `El interés obtenido es 1.000,00 euros.` → retenido (`calculation`).
- B `El saldo final es 2 euros.` → retenido.
- C `El interés es 3.00 euros.` → retenido.
- D `El interés es -1.000,00 euros.` → retenido (no se pierde el signo: no se publica).
- E `El saldo final es 1.060,90 euros, según la fuente oficial del banco.` → retenido (`attribution`).
- F `El interés compuesto reinvierte los intereses y por eso el saldo crece más que con interés simple.` → mostrado (`shown_unverified`), junto al resultado.
- G `El interés es sesenta con noventa céntimos.` → retenido (cifra con palabras).
- H `El resultado es correcto y coincide con el cálculo.` → mostrado; no contiene cifra, pero es una afirmación de corrección no verificada.

El DTO `calculation` no contiene `series`; contiene `assumptions` (principal, aportación, años, método, tasa, inflación, convención, timing, impuestos/comisiones) y `summary`; `answer_provenance.text_validation = "not_performed"`. La UI renderiza el panel determinista y no la prosa. Captura: `chat_A_panel_current.png` (verificada por visión: «Saldo final: 1.060,90 EUR», «Interés: 60,90 EUR»; el 1.000,00 solo aparece como principal/aportaciones).

Límite real (B4-L1): el gate de superficie no cubre numerales compuestos con palabras. `_SPELLED_NUMBER` incluye `dos`, `tres`, ..., pero no `doscientos`, `trescientos`, `quinientos`, `ochocientos`, `veintidós`, `billón`:

```
El saldo final es doscientos.      -> shown_unverified (debería retenerse)
El interés es trescientos.        -> shown_unverified
El interés es veintidós.          -> shown_unverified
El saldo final es un billón.      -> shown_unverified
```

No es uno de los cuatro casos exigidos y la UI declara `text_validation: not_performed`, pero es una vía real para que una cifra absurda aparezca como prosa del modelo en un turno de calculadora. No la considero bloqueante por sí sola; la anoto como límite.

## 2. Conflictos, campos desconocidos y fuente de la condición

### ACC-02 (MyInvestor): PASA en tarjeta y ficha

Tarjeta real (`#catalogue-results .product-card`, texto extraído):

```
Cuenta corriente remunerada · Cuenta remunerada · MyInvestor
Identidad verificada · Condiciones pendientes
Tasas en conflicto entre fuentes: no se comparan.
La misma página mezcla 2,50 % TAE/6 meses y un FAQ con 1,25 % TAE/12 meses,
2,50 %/6 meses y 0,30 % desde el séptimo mes; no elegir una tarifa ni corregir
bloques sin revisar bases legales.
Fuente primaria: https://myinvestor.es/cuentas-tarjetas/cuentas
Conflictos que siguen abiertos: Conflicto de fuentes pendiente de revisión; ver la ficha del producto.
Campos desconocidos: TIN y fecha efectiva inequívoca del bloque principal; tipo posterior a la promoción; ...
```

Ficha real:

```
Tasa anual (TAE): sin cifra utilizable · en conflicto; fuentes en conflicto ·
La misma página mezcla 2,50 % TAE/6 meses y un FAQ con 1,25 % TAE/12 meses, ...
Conflictos que siguen abiertos: [mismo texto literal]
Datos que siguen desconocidos: [6 campos]
```

No se presenta ninguna TAE como documentada: la condición está `conflict`, `value=None`, y la UI dice «sin cifra utilizable». El texto se inserta con `textContent`/`el(..., texto)` (no `innerHTML`; `grep -n innerHTML static/app.js` no devuelve usos), por lo que se muestra escapado. Capturas actuales: `acc02_search_current.png`, `acc02_ficha_current.png` (la ficha inferior se verificó por extracción de texto; la captura es del inicio de la ficha).

Matiz: la sección «Conflictos que siguen abiertos» de la tarjeta usa el marcador genérico; el texto literal se ve justo encima como `notes` de la condición. Para ACC-02 el requisito se cumple; para un producto cuyo conflicto no esté duplicado en `notes` (p. ej. DEP-02), la tarjeta solo muestra el marcador genérico. La ficha sí muestra el literal (ver abajo).

### ACC-01 (Renault Bank): PASA con límite de atribución

En la **biblioteca**, la tarjeta y la ficha muestran el PDF de Renault como «Fuente primaria» (la URL coincide con la fuente de la condición):

```
Fuente primaria: https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf
```

Comprobación en la ficha (`#product-detail`) y captura `acc01_search.png`:

```
"Fuente de la condición" in text  -> False
"Fuente de las condiciones" in text -> False
"Información precontractual global" in text -> False   # title del ledger
"2026-10-27" in text -> False                           # accessed del ledger
links -> ['https://doc.renaultbank.es/...RenaultBank.pdf']  # solo el primary
```

Es decir: el enlace al PDF está visible, pero la ficha/biblioteca no lo etiqueta como fuente de la condición ni usa `source_refs.title/accessed`; si la fuente de la condición no coincidiera con `primary_url`, la ficha no tendría enlace (hoy coinciden).

En **Pai** (el núcleo de B4), el estado final **sí enlaza la fuente de la condición**. Turno `B4-P` (`get_product_detail` ACC-01), texto real de `#chat-feedback`:

```
Cuenta Contigo (ACC-01)
Familia: cuenta_remunerada · Emisor: Renault Bank · identidad verificada
Condiciones documentadas sin fuente atribuible; atribución parcial · fecha de referencia: 2026-11-04.
...
TAE: 2.61 % — documentada; clase de fuente: Desconocida.
Consulta de la fuente: 2026-10-26.
Vigencia: 2026-10-21 → 2026-11-18.
Atribución de la condición: atribución parcial.
Fuente enlazada desde el registro de fuentes; el registro no declara si es oficial o secundaria.
Fuente de la condición: https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf
```

El DTO de `http_probe.json` `chat_P` confirma:

```
ACC-01 documented_unattributed partial
 annual_rate_percent known 2.61 partial unknown
 [{'url': 'https://doc.renaultbank.es/...RenaultBank.pdf', 'class': 'unknown',
   'retrieved_at': '2026-10-27', 'resolution': 'resolved'}]
```

Cadena final: `derive()` resuelve el id 1 a la URL y rellena `source_refs`; `pai_tools._project_conditions` lee `source_refs`, valida URL/título/fecha y `_resolve_condition_sources(..., refs_by_url)` publica la fuente con `resolution: resolved`, `source_class: unknown`; `pai_runtime._evidence_condition` la conserva; `renderChatCatalogue` pinta «Fuente de la condición». La condición queda `source_resolution="partial"` (la clase no está declarada en el ledger) y el producto `conditions_state="documented_unattributed"`, por eso el encabezado dice «documentadas sin fuente atribuible»/«atribución parcial» aunque el enlace esté justo debajo. Es una contradicción de etiquetas, no una ausencia de enlace.

Límite (B4-L3): la ficha de la biblioteca no usa `conditionSourceRef`/`source_refs` para etiquetar la fuente; solo muestra el `primary_url`. Pai sí la enlaza. La fecha de consulta de la ficha (2026-10-26) es `checked_at` del snapshot, no `source_refs.accessed` (2026-10-27). No bloquea el enlace visible de ACC-01, pero la atribución específica de la condición queda incompleta en la biblioteca.

## 3. Vencidos y fallo cerrado: PASA

### Pibank (DEP-03, `valid_to 2026-10-31`)

`GET /api/products/DEP-03` (53051):

```
annual_rate_percent stale PROMOTION_EXPIRED 3.03 2026-10-31
term_months known CURATED_TERM 12
```

UI real (tarjeta y ficha):

```
Oferta vencida: no se muestra como tasa vigente.
La vigencia declarada ya terminó.
...
Vigencia de la condición: vencida · hasta 2026-10-31
Tasa anual (TAE): sin cifra utilizable · vencida; vigencia terminada · vigencia hasta 2026-10-31 · La vigencia declarada ya terminó.
```

No se muestra 3,03 % como tasa vigente; el número no aparece en la tarjeta/ficha de la biblioteca. Captura: `pibank_ficha.png`. En Pai, la condición `stale` conserva el valor pero se etiqueta «vencida» y `conditions_state=documented_not_current`; no se presenta como actual.

Límite (B4-L4): `_curated_conditions` aplica `valid_to` solo a la tasa; `term_months` sigue `known` y la ficha lo rotula «Plazo: 12 meses · documentada por la fuente; plazo documentado», sin marca de vencimiento. No es una tasa vigente, pero el plazo de una oferta vencida se muestra como documentado sin advertir que pertenece a la oferta vencida.

### Fuente no resoluble: PASA (fallo cerrado)

Servidor con `sources_path` inexistente (52891; el servicio cae a registro vacío, no a `None`):

```
GET /api/conditions -> 200, source_registry "applied", state_counts {"unknown": 8, "known": 7, "stale": 1}
ACC-01: annual_rate_percent unknown SOURCE_UNRESOLVED None
        notes ["Fuente sin URL verificable (ids: 1); no se publica el dato."]
```

UI real: tarjeta de ACC-01:

```
Sin tasa documentada para este producto.
Fuente sin URL verificable (ids: 1); no se publica el dato.
```

No aparece `2,61` en la tarjeta. `derive` con registro vacío/parcial también devuelve `unknown/SOURCE_UNRESOLVED/value=None` (`b4_unit_probe.py`), y con registro resuelto `known/5.00/URL`.

### Unidad/métrica incoherente: PASA en la frontera de proyección

`b4_unit_probe.py`:

```
tool projection metric/unit mismatch: rejected: REPOSITORY_ERROR
runtime evidence metric/unit mismatch: None
tool projection unknown+value: rejected: REPOSITORY_ERROR
```

`pai_tools._project_conditions` rechaza la condición incoherente (y el turno falla cerrado, sin cifra); `pai_runtime._evidence_condition` la descarta y `_evidence_product` marca `conditions_unknown` si hay condiciones inválidas. No existe una ruta de `derive` que emita un par métrica/unidad incoherente (las construye siempre emparejadas), por lo que la comprobación es de frontera y no de UI.

## 4. Paridad local / WSGI: PASA en el estado final

Comando:

```
python parity_probe.py 53051
```

Resultado final:

```
OK conditions/status
OK conditions/full
OK product ACC-01 status / identity / conditions
OK product ACC-02 status / identity / conditions
OK product DEP-02 status / identity / conditions
OK product DEP-03 status / identity / conditions
OK product DEP-EBN-12 status / identity / conditions
OK product DEP-SELF-12 status / identity / conditions
OK compare deposits status / facts
OK compare accounts status / facts
OK compare mixed status / facts
OK compare curated-only status / facts
OK bundle SOURCES resolves like ledger
OK bundle CURATED == condiciones.json
OK bundle CANDIDATES relevant fields == snapshot
OK bundle CANDIDATES conflicts == snapshot conflicts
ALL SAME: True
```

Se compararon: `/api/conditions` completo; `/api/products/{ACC-01,ACC-02,DEP-02,DEP-03,DEP-EBN-12,DEP-SELF-12}` (identidad, `conflicts`, `unknown_fields`, condiciones con valor/estado/motivo/unidad/source_ids/vigencia/permission_state, `source`, `rate_tiers`); `/api/compare` con `deposit_tae_12m_eur` para DEP-01/02/03, ACC-01/02, mixto y DEP-EBN-12/DEP-SELF-12 (items, `reasons`, `comparability` completo). También se comprobó que el bundle empaquetado resuelve las mismas fuentes que el ledger, que `CURATED` es idéntico y que los campos relevantes de `CANDIDATES` coinciden con el snapshot.

Paridad UI: la ficha local de `DEP-SELF-12` (antes `product:null`) ahora carga igual que la WSGI, y la ficha local de `DEP-02` muestra el conflicto literal como la WSGI. La comparación EBN/Self produce el mismo texto en ambas apps (3,10 % y 2,75 % con «fuente secundaria, pendiente de confirmar»). Capturas: `wsgi_selfbank_ficha.png`, `selfbank_ficha_error.png` (esta última es de la instantánea anterior; el estado final ya no falla; se conserva solo como evidencia del cambio).

**Nota de la carrera:** el árbol se editó mientras se revisaba. La instantánea de ~12:29 fallaba la ficha de `DEP-SELF-12` (`{"product": null}`) y la ficha de `DEP-02` solo tenía el conflicto genérico; el estado final (app.py 12:40, api/index.py 12:36) las corrige. No cuento esos fallos transitorios como bloqueantes del estado final, pero sí dejo constancia de que la verificación se hizo sobre los hashes indicados.

## 5. Límites y defectos no bloqueantes

- **B4-L1 (gate de prosa):** numerales compuestos con palabras (`doscientos`, `trescientos`, `quinientos`, `ochocientos`, `veintidós`, `billón`) pasan como `shown_unverified`. Ver `text_gate_probe.py`; los cuatro textos exigidos, la atribución falsa y las grafías incluidas en `_SPELLED_NUMBER` sí se retienen.
- **B4-L2 (conflictos en listado/comparación):** `/api/catalogue` y `/api/compare` usan un marcador genérico; el texto literal se reserva para la ficha. En ACC-02 el literal se recupera por `notes` de la condición; en DEP-02 la tarjeta de búsqueda no muestra el conflicto real (solo la ficha). Es una decisión de diseño declarada, pero el requisito «conflictos reales en resultados de búsqueda» no se cumple para DEP-02.
- **B4-L3 (atribución en biblioteca):** la ficha/tarjeta de ACC-01 muestra el PDF como «Fuente primaria», no como «fuente de la condición», y no usa `source_refs.title/accessed`; Pai sí enlaza la condición. La fecha de consulta de la ficha es `checked_at` (2026-10-26), no `accessed` del ledger (2026-10-27).
- **B4-L4 (Pibank/plazo):** `valid_to` solo marca `stale` la tasa; `term_months` sigue `known` y se rotula «documentado» sin vencimiento.
- **B4-L5 (fuente curada inválida):** `_curated_conditions` no valida la URL. Un registro curado con `source:{}` produce `state=known, value=4` con `source_ids=[]` (la UI diría «TAE documentada» sin fuente); una URL `javascript:...` se publica en `source_ids` (la UI no la enlaza por `isSafePrimaryUrl`, pero el JSON la expone). Los cuatro registros actuales tienen URL https válida, así que no se dispara hoy.
- **B4-L6 (`derive` sin registro):** `derive(snapshot, today)` con `sources=None` mantiene `known` y `source_ids=["1"]` (id numérico sin URL). Los dos llamadores de la app pasan `sources` (`ConditionsService._sources()` y `api/index.py` con `SOURCES`), pero el valor por defecto del módulo es fail-open para cualquier otro llamador.
- **B4-L7 (tasas absurdas del snapshot):** `_decimal` limita las curadas a 0..1000, pero `_rates`/`annual_rate` no acotan el snapshot: un literal `9999 % TAE` con id resoluble produce `known 9999 DOCUMENTED_PROMO_TAE`. No hay tal literal en los datos actuales; es una frontera numérica ausente.
- **B4-L8 (prosa meta):** «El resultado es correcto y coincide con el cálculo.» se muestra (`shown_unverified`); no contiene cifra, pero afirma corrección no verificada. El DTO declara `text_validation: not_performed` y la UI lo repite; no se presenta como cálculo verificado.
- **B4-L9 (etiquetas de estado):** ACC-01 muestra en Pai «Condiciones documentadas sin fuente atribuible; atribución parcial» aunque justo debajo enlaza «Fuente de la condición»; `conditions_state=documented_unattributed` porque el ledger no declara clase oficial/secundaria. En la biblioteca, el badge «Condiciones pendientes» convive con la sección «Condiciones documentadas». No declara documentado lo que no lo está, pero la señal es contradictoria. `CatalogueWithConditions._conditions_state` puede devolver `documented` para DEP-03 por el plazo `known` sin `effective_to` antes de mirar la tasa `stale`; la herramienta de Pai lo recalcula y no lo hereda, pero el adaptador queda frágil.

## 6. Evidencia reproducible (archivos)

En `C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/cache/scratch/b4rev_4h30/`:

- `b4_server.py` — fixture loopback con el servidor real y proveedor sintético cerrado; escenarios A–H, S (search_products MyInvestor), P (get_product_detail ACC-01).
- `http_probe.py`, `http_probe.json`, `http_stdout_current.txt` — turnos de calculadora A–H, S (`search_products` MyInvestor), P (`get_product_detail` ACC-01), fichas, condiciones, comparación y `/api/calculate`.
- `parity_probe.py`, `parity_probe.json`, `parity_stdout_current.txt` — paridad local/WSGI (32 checks, `ALL SAME: True`).
- `b4_unit_probe.py`, `unit_probe.json` — fuente no resoluble, parcial, resuelta, sin registro; métrica/unidad y `unknown` con valor.
- `text_gate_probe.py`, `text_gate_probe.json` — batería de prosa (A–P) y límite de numerales compuestos.
- `d1_probe.py`, `d1_source_projection.json` — cadena `source_refs` → `sources` de Pai (ACC-01 vs DEP-02).
- `b4_broken_sources.py` — servidor con ledger inexistente (fallo cerrado).
- `wsgi_server.py` — servidor de la función WSGI empaquetada.
- Capturas: `chat_A_panel_current.png`, `acc01_search.png`, `acc02_search_current.png`, `acc02_ficha_current.png`, `pibank_ficha.png`, `wsgi_selfbank_ficha.png`, `selfbank_ficha_error.png` (esta última es de la instantánea anterior, antes del arreglo de ficha de los productos curados).

Comandos usados (desde la carpeta scratch). Los puertos son los de esta ejecución; al repetir, usar el que imprima cada fixture:

```
python b4_server.py --port 0                 # -> 53051
python http_probe.py 53051
python parity_probe.py 53051
python b4_unit_probe.py
python text_gate_probe.py
python d1_probe.py
python b4_broken_sources.py                  # -> 52891
python wsgi_server.py                        # -> 51355
```

Navegador: `browser_exec` local, sesión `b4rev`; `new_tab('http://127.0.0.1:53051/#chat')`, rellenar `#chat-message`, marcar `#chat-consent`, pulsar `#chat-submit`, leer `#chat-feedback`; para biblioteca, `#biblioteca`, `#catalogue-search`, `Ver detalle` y `#product-detail`. Las capturas se tomaron con `capture_screenshot()`/CDP y se inspeccionaron con visión.

## 7. Dictamen JSON

```json
{
  "block": "B4 — Pai con lectura del catálogo",
  "reviewed_at": "2026-11-04T13:17:00+01:00",
  "passed": true,
  "blocking_defects": [],
  "limits": [
    "B4-L1: el gate de prosa de calculadora no cubre numerales compuestos con palabras (doscientos, trescientos, quinientos, ochocientos, veintidós, billón); se muestran como shown_unverified. Los cuatro textos exigidos, la atribución falsa y las grafías incluidas en _SPELLED_NUMBER sí se retienen.",
    "B4-L2: /api/catalogue y /api/compare usan un marcador genérico de conflicto; el literal solo está en la ficha (y en notes de la condición cuando existe). Para DEP-02 la tarjeta de búsqueda no muestra el conflicto real.",
    "B4-L3: la ficha/tarjeta de ACC-01 muestra el PDF como «Fuente primaria», no como «fuente de la condición», y no usa source_refs.title/accessed; Pai sí enlaza la condición. La fecha de consulta de la ficha es checked_at (2026-10-26), no accessed (2026-10-27).",
    "B4-L4: valid_to de Pibank solo marca stale la tasa; term_months sigue known y se rotula «documentado» sin vencimiento.",
    "B4-L5: _curated_conditions no valida la URL de la fuente; un registro curado sin URL produce state=known con source_ids=[] y una URL javascript: se publica en source_ids. Los cuatro registros actuales son https válidos.",
    "B4-L6: derive(snapshot, today) con sources=None mantiene known y source_ids numéricos; los llamadores de la app pasan sources, pero el valor por defecto es fail-open.",
    "B4-L7: annual_rate no acota las tasas del snapshot; un literal 9999 % TAE con fuente resoluble produce known 9999.",
    "B4-L8: la prosa meta sin cifra («El resultado es correcto y coincide con el cálculo.») se muestra como shown_unverified; no se marca como cálculo verificado, pero afirma corrección no comprobada.",
    "B4-L9: ACC-01 muestra en Pai «documentadas sin fuente atribuible; atribución parcial» aunque enlaza «Fuente de la condición»; en la biblioteca el badge «Condiciones pendientes» convive con «Condiciones documentadas». CatalogueWithConditions._conditions_state puede devolver documented para DEP-03 por el plazo known antes de mirar la tasa stale.",
    "Nota de estabilidad: el árbol cambió durante la revisión; los fallos de ficha de DEP-SELF-12 y del enlace de fuente de ACC-01 de la instantánea ~12:29 están corregidos en el estado final (app.py 12:40, api/index.py 12:36, pai_tools.py 13:10). La paridad final pasa."
  ],
  "evidence": {
    "scratch_dir": "C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/cache/scratch/b4rev_4h30",
    "commands": [
      "python b4_server.py --port 0",
      "python http_probe.py 53051",
      "python parity_probe.py 53051",
      "python b4_unit_probe.py",
      "python text_gate_probe.py",
      "python d1_probe.py",
      "python b4_broken_sources.py",
      "python wsgi_server.py"
    ],
    "files": [
      "http_probe.json",
      "http_stdout_current.txt",
      "parity_probe.json",
      "parity_stdout_current.txt",
      "unit_probe.json",
      "text_gate_probe.json",
      "d1_source_projection.json",
      "b4_server.py",
      "wsgi_server.py",
      "b4_broken_sources.py"
    ],
    "screenshots": [
      "chat_A_panel_current.png",
      "acc01_search.png",
      "acc02_search_current.png",
      "acc02_ficha_current.png",
      "pibank_ficha.png",
      "wsgi_selfbank_ficha.png",
      "selfbank_ficha_error.png"
    ],
    "hashes": {
      "app/static/app.js": "c8a0fdc4c841b29fd760e56594e7a8687a7bf79cc74537174b9070b69c8d016d",
      "app/app.py": "b003e1e2c0c361e3dfaecf9ec8cdad0547932602e78659ac2398804789350a22",
      "app/backend_services.py": "814e6e3e5aa57d3e0dc8ac2b2a038bc1e18dc5845082501ef7c2c0e5d394c881",
      "app/pai_tools.py": "95dc071ce82001f0666b7a168737a77c10787915d9071605ae327b1ae8c398fc",
      "app/pai_runtime.py": "13bb7abd6e7ecdf542201981e834376f4b6d4800939244ea5a1ebdf05d6f6243",
      "api/index.py": "240cc27c4f86fba0fc389121be2bc0e558f7b4a52c258a50883084f68e253bb9",
      "api/_core/catalogue_conditions.py": "ef735d9bc2dd7b3e7a4030a8d07ae345fe86d0a3ed783d5ec62a23ca45212fbc"
    }
  }
}
```
