# Auditoría de calidad del catálogo de Paideia

Fecha de referencia: **2026-11-25**. Datos: `app/data/condiciones.json` (22 productos).
Estados derivados con la fecha del día (`ConditionsService`, `reference_date=None`).

Este informe responde a tres preguntas: cada dato, ¿tiene fuente y fecha?, ¿hay algo
inventado?, y lo que no se publica, ¿queda declarado como desconocido o simplemente
desaparece?

---

## 1. Tabla por producto

`cond. con valor` = condiciones que llegan a la ficha con una cifra o una cláusula
transcrita (estado `known` o `stale`). `desconocidas` = huecos declarados con su motivo
(estado `unknown`). La columna `estado hoy` es el estado de la **tasa anual**; un guion
indica que la familia no tiene tasa (fondo, ETF, letra).

| # | id | nombre | familia | estado hoy | cond. con valor | desconocidas | fuente | fecha |
|---|---|---|---|---|---|---|---|---|
| 1 | ACC-01 | Cuenta Contigo | cuenta_remunerada | stale (2026-11-18) | 11 | 1 | sí (official) | 2026-11-05 |
| 2 | ACC-02 | Cuenta corriente remunerada | cuenta_remunerada | stale (TTL) | 11 | 0 | sí (official) | 2026-11-05 |
| 3 | ACC-03 | Cuenta Remunerada Openbank | cuenta_remunerada | stale (2026-11-16) | 11 | 2 | sí (official) | 2026-11-05 |
| 4 | ACC-04 | Cuenta Remunerada Pibank | cuenta_remunerada | stale (TTL) | 11 | 1 | sí (official) | 2026-11-05 |
| 5 | DEP-01 | Depósito Tú+ | deposito | stale (2026-11-18) | 14 | 0 | sí (official) | 2026-11-05 |
| 6 | DEP-02 | Depósito Open 6 meses | deposito | known | 14 | 0 | sí (official) | 2026-11-03 |
| 7 | DEP-03 | Depósito Pibank 12 meses | deposito | **stale (2026-10-31)** | 13 | 1 | sí (official) | 2026-11-03 |
| 8 | DEP-04 | Depósito Sinycon Plus | deposito | known | 14 | 0 | sí (official) | 2026-11-05 |
| 9 | DEBT-01 | Letra del Tesoro — 15-01-2027 | letra_deuda_publica | — | 10 | 0 | sí (official) | 2026-11-05 |
| 10 | DEBT-02 | Letra del Tesoro — 05-02-2027 | letra_deuda_publica | — | 10 | 0 | sí (official) | 2026-11-05 |
| 11 | DEBT-03 | Letra del Tesoro — 05-03-2027 | letra_deuda_publica | — | 10 | 0 | sí (official) | 2026-11-05 |
| 12 | DEBT-04 | Letra del Tesoro — 09-04-2027 | letra_deuda_publica | — | 10 | 0 | sí (official) | 2026-11-05 |
| 13 | FND-01 | Bestinver Bolsa, F.I. | fondo_tradicional | — | 18 | 0 | sí (official) | 2026-11-05 |
| 14 | FND-02 | OLEA NEUTRAL, FI | fondo_tradicional | — | 32 | 0 | sí (official) | 2026-11-05 |
| 15 | FND-03 | Azvalor Internacional FI | fondo_tradicional | — | 34 | 0 | sí (official) | 2026-11-05 |
| 16 | FND-04 | Bestinver Internacional, F.I. | fondo_tradicional | — | 18 | 0 | sí (official) | 2026-11-05 |
| 17 | ETF-01 | iShares Core MSCI Europe UCITS ETF EUR (Acc) | etf_ucits | — | 28 | 0 | sí (official) | 2026-11-05 |
| 18 | ETF-02 | Xtrackers S&P 500 Equal Weight UCITS ETF 2D | etf_ucits | — | 28 | 0 | sí (official) | 2026-11-05 |
| 19 | ETF-03 | State Street SPDR MSCI Europe Industrials UCITS ETF | etf_ucits | — | 30 | 0 | sí (official) | 2026-11-05 |
| 20 | ETF-04 | VanEck Semiconductor UCITS ETF | etf_ucits | — | 26 | 0 | sí (official) | 2026-11-05 |
| 21 | DEP-EBN-12 | Depósito Nuevo Ahorro 12 meses | deposito | known | 15 | 0 | sí (official) | 2026-11-03 |
| 22 | DEP-SELF-12 | Depósito a 12 meses Self Bank | deposito | known | 13 | 0 | sí (**secondary_press**) | 2026-11-03 |

**Totales**: 22 productos, **386 condiciones servidas** → 375 `known`, 6 `stale`,
5 `unknown`. Por familia: 4 cuentas, 6 depósitos, 4 letras, 4 fondos, 4 ETF.

Todas las fichas declaran `source.url`, `source.kind` y `source.retrieved_at`. Las 22
tienen fuente; **DEP-SELF-12 es la única con fuente secundaria** (Rankia), no oficial:
sus condiciones se sirven con la nota «Fuente secundaria: confirmación en página
oficial pendiente» y su identidad queda como `proposed`.

---

## 2. Incoherencias encontradas

Cada una con archivo:línea, clasificación (DATOS o CÓDIGO) y arreglo.

### 2.1 El nominal adjudicado de las letras estaba ×100 (DATOS) — corregido

`condiciones.json:2044, 2169, 2293, 2417`

El literal dice «Nominal adjudicado 751,69» (millones de euros, como anota la propia
nota), y el valor almacenado era `75169000000` con unidad `millones EUR`: 75.169
millones de millones. Debía ser 751.690.000 €. Las otras tres letras tenían el mismo
error de escala, y en unidades incoherentes entre sí (`millones EUR` en DEBT-01,
`EUR` en las demás).

Es el fallo más peligroso del lote porque **es plausible**: 75.169 millones de euros es
una cifra del orden de magnitud de la deuda española, así que ningún test de presencia
lo detecta. Verificado con Python: `751,69 × 10⁶ = 751.690.000`, almacenado
`75.169.000.000` → factor ×100.

**Arreglo aplicado**: valor en euros y unidad `EUR` en las cuatro, nota que explicita la
conversión. No se inventó ningún dato: la cifra sale del literal que ya estaba.

### 2.2 ACC-01 servía un tramo con TAE < TIN (DATOS) — corregido

`condiciones.json:623-629`

El tramo base emparejaba `tae: "2.61"` con `tin: "3"`. Una TAE anual no puede ser menor
que el TIN anual del mismo tramo. El origen está a la vista en las dos filas
transcritas: el 2,61 % es la promoción (contratable hasta 18/11/2026) y el 3,00 % TIN es
«garantizado hasta el 31/03/2027» — **dos bloques distintos de la misma página**. El
tramo inventaba un producto que no existe.

**Arreglo aplicado**: el tramo conserva solo la TAE 2,61 % y su etiqueta de promoción.
El TIN 3,00 % sigue en su propia fila documentada con su vigencia real (31/03/2027). No
se descartó ningún dato publicado: se dejó de mezclar dos.

### 2.3 DEP-SELF-12 servía como incondicional una tasa que exige dinero nuevo (DATOS) — corregido

`condiciones.json:476-486`

El tramo «sin_requisito» declaraba `tae: 2.75, tin: 2.72`. Dos problemas:

- **El 2,72 % no existe en ningún literal del registro.** Buscado en todo el producto:
  no aparece. La ficha documenta «2,47 % TIN / 2,50 % TAE» y, aparte, «2,75 % TAE para
  nuevos clientes y nuevos saldos». El 2,72 es una cifra sin respaldo.
- **El 2,75 % es la promoción por dinero nuevo**, y `requirements` ya la declaraba
  («nuevos clientes o dinero nuevo»). Servirla como tasa base sin condición es
  presentar una oferta condicionada como si fuera general.

**Arreglo aplicado**: tramo base 2,50 % TAE / 2,47 % TIN (lo que la ficha dice sin
condición) y un segundo tramo con el 2,75 % y su condición. Es exactamente el caso de
«dos tramos son una oferta, no un conflicto»: se conservan los dos con su requisito.

### 2.4 DEP-03: dos fechas de vigencia contradictorias para la misma oferta (DATOS) — corregido

`condiciones.json:169` (`valid_to`) frente a `condiciones.json:283-292` (`promocion_ventana_alta`)

El campo de cabecera dice `valid_to: 2026-10-31`, y la fila transcrita de la **misma URL**
dice «Oferta válida hasta el 30/11/2026». Una de las dos está mal. El estado se deriva
del `valid_to` (vencida), que es la lectura conservadora, pero la ficha además afirmaba
`promotion_window = "Oferta válida hasta el 30/11/2026"` como dato conocido: el usuario
leía «vencida» y «válida hasta el 30/11» en la misma pantalla.

**Arreglo aplicado**: la fila queda con `value: null` y una nota que declara la
discrepancia. No se elige una fecha — eso sería inventar. El estado sigue derivándose
del `valid_to` documentado y la ventana pasa a `unknown` con su motivo. **Queda pendiente
una comprobación contra la fuente viva** para decidir cuál de las dos fechas es la buena.

### 2.5 Las condiciones declaradas desconocidas no llegaban nunca a la ficha (CÓDIGO) — corregido

`app/catalogue_conditions.py:607-609` (`if raw is None or raw == "": continue`)

El JSON usa `{"value": null, "note": "La página no publica cifra…"}` como forma de
**declarar** un hueco. `_documented_conditions` descartaba esas filas en silencio. Efecto
medido: cuatro declaraciones explícitas (ACC-01 `saldo_maximo_remunerado`, ACC-03
`importe_maximo` y `tae_posterior`, ACC-04 `importe_maximo`) no aparecían en ninguna
ficha. El usuario veía una ausencia sin motivo, **indistinguible de un campo que nadie
transcribió** — que es justo lo que la app promete no hacer.

**Arreglo aplicado**: una fila con `value` nulo se emite como `unknown` con motivo
`CURATED_NOT_PUBLISHED` y su nota. No se rellena ninguna cifra; se declara el hueco,
que es el contrato del proyecto. Estado servido: 4 huecos declarados nuevos (5 contando
la ventana de DEP-03).

### 2.6 La lista del catálogo decía «vigente» lo que el chat decía «vencido» (CÓDIGO) — corregido

`app/catalogue_adapter.py:91-106`

`_conditions_state` solo sabía devolver `documented` o `pending`, y devolvía
`documented` en cuanto **una** condición estuviera vigente. En una ficha con diez
condiciones permanentes y la tasa promocional caducada, eso daba `documented`.

Medido antes del arreglo, con `/api/catalogue` frente a las herramientas del chat:

| producto | `/api/catalogue` | chat / herramientas |
|---|---|---|
| ACC-01, ACC-02, ACC-03, ACC-04, DEP-01, DEP-03 | `documented` | `documented_not_current` |

Seis productos vencidos se servían como vigentes en la biblioteca. **Dos superficies del
mismo dato en desacuerdo.**

**Arreglo aplicado**: la lista aplica la misma regla que el proyector de herramientas —
si hay algo `stale` o `conflict`, la ficha es `documented_not_current`. Hubo que ampliar
dos validadores que rechazaban el estado nuevo (`pai_tools.py:463`, `app.py:468`) y la
etiqueta de la tarjeta (`static/app.js:246`), que lo colapsaba a «no validadas».

### 2.7 DEP-04: los ocho tramos publicados se descartaban enteros (CÓDIGO) — corregido

`app/pai_tools.py:905` (`len(raw_tiers) > 6` → `invalid`)

El Depósito Sinycon Plus publica ocho plazos (1, 3, 6, 12, 18, 24, 36 y 48 meses). El
tope estructural de 6 marcaba el producto entero como `invalid` y la ficha se quedaba
**sin ningún tramo** — ocho datos transcritos con su URL, tirados por un límite.

**Arreglo aplicado**: tope elevado a 12 (constante `MAX_RATE_TIERS`, con el porqué
escrito). Se conserva un límite para que un informe corrupto no infle la respuesta.
Estado: `DEP-04` pasa de 0 a 8 tramos servidos.

### 2.8 ACC-04: la nota desmentía su propio valor (DATOS) — corregido

`condiciones.json:1220`

`importe_minimo: "0"` con nota «La página **no publica cifra** (…) Se codifica 0 = sin
mínimo exigido, **no un importe de 0 €**». La nota admitía que el valor era una
codificación interna, no un dato de la fuente. Pero la fuente sí publica la frase
(«desde el primer euro»), así que el 0 **es** el mínimo documentado y lo que estaba mal
era la nota.

**Arreglo aplicado**: nota reescrita para decir lo que la fuente publica. El valor no
cambia.

### 2.9 Las condiciones no tenían `retrieved_at` en el patrón del snapshot (sin defecto real)

Revisado y descartado: las 22 fichas traen `source.retrieved_at` y las 386 condiciones
servidas llevan fecha. Las filas del snapshot puntuales que anotaban `accessed` posterior
a `source.retrieved_at` (p. ej. 2026-11-06 frente a 2026-11-03) no son un error: la nota
de cabecera del fichero ya lo declara — «cada fila lleva su propia fecha de consulta en
`accessed`, que prevalece sobre la de este campo».

### 2.10 Verificado y correcto (sin acción)

- **Duplicados**: ningún `candidate_id` ni nombre repetido. Las cuatro letras comparten
  URL de ficha, lo cual es correcto (es la misma página del Tesoro, cuatro ISIN
  distintos).
- **Mínimo > máximo**: ninguno, ni en cabecera ni en las métricas transcritas.
- **Productos con 0 condiciones**: ninguno de los 22.
- **Métricas no interpretables**: las 80 métricas presentes están en el mapa
  `DOCUMENTED_METRICS` (82 entradas). Ninguna se descarta en silencio.
- **Rangos de tasa**: todas dentro de [0, 20] salvo los precios de letra
  (`precio_medio` 98,6-99,3), que son porcentaje del nominal y su rango natural es ~100.
- **Familias sin tasa**: fondos, ETF y letras no llevan fila `annual_rate_percent`
  inventada.
- **Fecha de vencimiento futura**: `vencimiento` de las cuatro letras es 2027, futuro
  por naturaleza, no un dato caducado.

---

## 3. Estados con la fecha de HOY (2026-11-25)

El sistema deriva el estado de la fecha del día, así que las promociones caducan solas.
**Seis productos están vencidos hoy** y la app lo declara en las tres superficies
(lista, ficha y chat) tras el arreglo 2.6:

| producto | motivo del vencimiento | fecha |
|---|---|---|
| **DEP-03** Depósito Pibank 12 meses | `valid_to` documentado | 2026-10-31 |
| **ACC-03** Cuenta Remunerada Openbank | ventana de alta | 2026-11-16 |
| **ACC-01** Cuenta Contigo | ventana de alta | 2026-11-18 |
| **DEP-01** Depósito Tú+ | «Condiciones válidas hasta» | 2026-11-18 |
| **ACC-02** Cuenta corriente remunerada | TTL de 7 días desde la consulta (2026-11-05) | — |
| **ACC-04** Cuenta Remunerada Pibank | TTL de 7 días desde la consulta (2026-11-05) | — |

Los dos últimos caducan por **antigüedad**, no por fecha declarada: la fuente no fija
término y la consulta tiene más de los 7 días que la familia admite. Es el
comportamiento correcto —una cuenta remunerada se mueve cada semana— y no un defecto de
los datos.

DEP-03 se sirve como vencida, tal y como exige el encargo. La tasa sigue visible
(`3.03`) pero con estado `stale` y motivo `PROMOTION_EXPIRED`, nunca como oferta actual.

---

## 4. Arreglos propuestos y aplicados

| # | incoherencia | clase | arreglo | estado |
|---|---|---|---|---|
| 2.1 | nominal adjudicado ×100 | DATOS | valor en euros, unidad `EUR`, nota de conversión | aplicado |
| 2.2 | ACC-01 TAE 2,61 < TIN 3,00 | DATOS | tramo sin el TIN de otro bloque | aplicado |
| 2.3 | DEP-SELF-12 TIN 2,72 inexistente y promo servida como base | DATOS | base 2,50/2,47 + tramo condicionado 2,75 | aplicado |
| 2.4 | DEP-03 dos fechas de vigencia | DATOS | ventana a `unknown` con la discrepancia declarada | aplicado (falta cotejo con la fuente) |
| 2.5 | huecos declarados descartados en silencio | CÓDIGO | se emiten como `unknown` + motivo | aplicado |
| 2.6 | lista `documented` vs chat `documented_not_current` | CÓDIGO | misma regla en las tres capas | aplicado |
| 2.7 | DEP-04 ocho tramos descartados | CÓDIGO | tope 6 → 12 | aplicado |
| 2.8 | ACC-04 nota que desmentía el valor | DATOS | nota reescrita | aplicado |
| — | DEP-03: ¿31/10 o 30/11? | DATOS | **pendiente de cotejo con la fuente viva** | abierto |
| — | DEP-SELF-12 solo tiene fuente secundaria | DATOS | **pendiente**: falta la ficha oficial de Self Bank | abierto |
| — | ACC-02 conflicto de fuente abierto (2,50 %/6 m frente a 1,25 %/12 m) | DATOS | declarado en el snapshot; requiere revisar bases legales | abierto |

En ninguna corrección de datos se ha rellenado un valor que faltara: los dos huecos que
no se pueden resolver (2.4 y el cotejo de DEP-SELF-12) quedan como desconocidos con
motivo, que es la corrección correcta.

---

## 5. Tests nuevos

`app/tests/test_catalogo_invariantes_calidad.py` — **34 pruebas**, agrupadas por la
invariante que protegen. Corren contra el fichero real, no contra fixtures, porque el
defecto buscado (un dato mal transcrito) no aparece en una fixture.

| clase | invariante | pruebas |
|---|---|---|
| `ProcedenciaTests` | valor ⇒ URL + fecha, en el JSON y en lo servido | 4 |
| `DesconocidoTests` | `unknown` sin valor, `known` con valor, el hueco declarado llega con su motivo | 4 |
| `CoherenciaNumericaTests` | mínimo ≤ máximo, rangos, TAE ≥ TIN, escala del nominal, cifra dentro de su literal | 9 |
| `VigenciaTests` | nada vencido como vigente; lista = herramientas = chat; límite por días completos con fecha inyectada | 7 |
| `IntegridadTests` | sin duplicados, sin producto vacío, sin métrica no interpretable | 6 |
| `ServidoTests` | lo mismo por HTTP: lista sin fichas, detalle completo, vencido no vigente, hueco declarado, escala del nominal | 5 |

**Comprobado que muerden**: se reintrodujo cada defecto y la prueba se puso roja.

| defecto reintroducido | pruebas que se pusieron rojas |
|---|---|
| nominal ×100 en DEBT-01 | 2 (`test_un_importe_en_millones…`, `test_las_condiciones_de_una_letra…`) |
| ACC-01 TAE 2,61 con TIN 3,00 | 2 (`test_la_tae_de_un_tramo_no_es_menor…`, `test_un_tramo_servido_nunca_mezcla…`) |
| lista sin la regla de vencido | 3 (`test_ningun_producto_vencido…`, `test_una_promocion_vencida…`, `test_un_producto_vencido_no_se_sirve…`) |
| descarte silencioso de huecos | 2 (`test_lo_declarado_desconocido…`, `test_lo_que_la_fuente_no_publica…`) |

Además se ajustaron 6 pruebas existentes que **codificaban el comportamiento
defectuoso** (exigían `documented` para productos vencidos, o exigían que un hueco
declarado no tuviera fila). No se borró ninguna: se reescribió su contrato con el
porqué.

---

## 6. Salida de pytest

```
cd app && env -u PAIDEIA_GROQ_ENABLED -u GROQ_API_KEY -u PAIDEIA_LLM_PROVIDER PYTHONPATH=. \
  python -m pytest tests -q
```

```
1072 passed, 6 skipped, 11 warnings, 1115 subtests passed in 108.96s (0:01:48)
```

Antes de los cambios: 988 passed, 6 skipped, 1077 subtests. La diferencia son las 34
invariantes nuevas más las pruebas que ya existían y ahora pasan con el contrato
corregido.

---

## 7. Resumen

- **22 productos**, todos con fuente con URL y fecha de consulta. 386 condiciones
  servidas: 375 conocidas, 6 vencidas, 5 declaradas desconocidas con su motivo.
- **8 incoherencias reales**, 6 corregidas y verificadas con pruebas que se ponen rojas
  al reintroducir el defecto; 2 quedan abiertas por falta de fuente (no se inventan).
- La más grave era de escala: el nominal de las cuatro letras estaba ×100, y ninguna
  prueba de presencia lo veía porque la cifra resultante seguía siendo plausible.
- La más visible para el usuario: seis productos vencidos se servían como vigentes en la
  biblioteca mientras el chat decía lo contrario.
- 34 pruebas nuevas de invariante; suite completa en verde.
