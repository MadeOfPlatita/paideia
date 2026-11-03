# Paideia — primera selección ampliable de productos

| Campo | Valor | Campo | Valor |
|---|---|---|---|
| Corte | 27-10-2026 | Estado | Revisión de candidatos; no publicar ni ingerir automáticamente. |


## Resultado cuantitativo

| Indicador | Resultado | Definición |
|---|---:|---|
| Productos candidatos | 20 | Cuatro por cada familia aprobada en [REQUISITOS.md](../../REQUISITOS.md). |
| Identidad verificada | 14 | Fuente primaria previa identifica producto e ISIN cuando aplica. |
| Identidad propuesta | 6 | Snippet de fuente oficial; no se abrió directamente en esta ronda. |
| Pendiente dentro de selección | 0 | Ninguna identidad se fabricó para completar la cuota. |
| Pendiente fuera de selección | 1 | Trade Republic, clasificación/condiciones insuficientes.[24] |
| ISIN comprobados | 12/12 | Formato y checksum MOD-10/Luhn válidos; cuentas y depósitos: ISIN no aplicable. |
| Listos para publicación | 0/20 | Automatización, cache, transformación, display, redistribución, PDF y retención siguen pendientes. |

| Lectura de estados | Definición |
|---|---|
| `verified` / `proposed` | Estado de identidad, no de integridad de condiciones, vigencia, elegibilidad o permiso de publicación. |
| `pending` | Asunto no resuelto; no implica prohibición universal. |
## Selección y campos decisivos pendientes por candidato

| ID / familia | Producto literal e identidad | Estado y fuente primaria | Fecha efectiva separada de consulta | Campos decisivos aún pendientes para ingesta |
|---|---|---|---|---|
| ACC-01 · cuenta | **Cuenta Contigo** · ISIN no aplicable | Verificada; ficha precontractual Renault Bank.[1] | Promoción 21-10-2026 a 18-11-2026; TIN 3,00 % hasta 31-03-2027. Consultada 26-10-2026.[1] | Divisa explícita, saldo máximo, frecuencia pactada, condiciones posteriores a la promoción y términos de reutilización. |
| ACC-02 · cuenta | **Cuenta corriente remunerada** · ISIN no aplicable | Verificada como producto; página MyInvestor.[2] | La página mezcla bloques incompatibles; consulta 26-10-2026. No se fija una vigencia única.[2] | Resolver 2,50 % TAE/6 meses frente al FAQ de 1,25 %/12 meses y 0,30 % desde el séptimo; revisar bases legales, TIN y tipo posterior. |
| ACC-03 · cuenta | **Cuenta Remunerada Openbank** · ISIN no aplicable | Propuesta; snippet de página oficial, sin GET directo.[3] | El snippet ofrece un año, pero no una fecha efectiva inequívoca; consultado 27-10-2026.[3] | Leer página y bases completas, comprobar requisito de Bizum/código, periodo exacto, después de promo, entidad jurídica y elegibilidad. |
| ACC-04 · cuenta | **Cuenta Remunerada Pibank** · ISIN no aplicable | Propuesta; snippet de producto oficial, sin GET directo.[4] | Fecha de la tarifa no visible; consultado 27-10-2026.[4] | Vigencia, requisitos y elegibilidad completos, divisa contractual explícita, topes y términos de uso. |
| DEP-01 · depósito | **Depósito Tú+** · ISIN no aplicable | Verificado como producto; ficha Renault Bank.[1] | No consta fecha efectiva de una tarifa por plazo; consultada 26-10-2026.[1] | Plazos, TIN/TAE por plazo, mínimo/máximo, liquidación, divisa y disponibilidad vigente. |
| DEP-02 · depósito | **Depósito Open 6 meses** · ISIN no aplicable | Verificado como identidad histórica; ficha oficial Openbank.[5] | La ficha indica «Vigente desde 08.10.2026»; recuperada en ronda 1 y citada en fuentes locales.[5] | Vigencia actual, tramos/requisitos asociados a TAE/TIN y condiciones actuales. **Conflicto abierto:** YieldMeister etiqueta la fila como «Depósito Plazo Fijo 12m»/12 meses, mientras la ficha oficial localizada identifica 6 meses. No se corrigió ni fusionó ninguno de los dos registros.[5][21] |
| DEP-03 · depósito | **Depósito Pibank a 12 meses** · ISIN no aplicable | Propuesta; URL oficial enlazada desde Pibank y snippets de ficha, sin abrir/descargar en esta ronda.[6][7][20] | El snippet no fecha el TAE/TIN; consultado 27-10-2026.[7][20] | Confirmar documento vigente, tasa/TAE por plazo, mínimos, cancelación, liquidación, elegibilidad y fecha efectiva. |
| DEP-04 · depósito | **Depósito Sinycon Plus** · ISIN no aplicable | Propuesta; snippet de página oficial EBN, sin GET directo.[22] | Sin fecha efectiva visible; consultado 27-10-2026.[22] | Vincular el «hasta 2,85 % TAE» a plazo/tramo concreto, obtener TIN, calendario, condiciones y términos vigentes. |
| DEBT-01 · deuda | **Letra del Tesoro, venc. 15-01-2027** · `ES0L02701156` | Verificada por fila del Tesoro.[9] | Saldo efectivo **16-10-2026**, consulta previa 26-10-2026. La nota es específica de la tabla de Letras; otras secciones de la misma página pueden tener otra fecha efectiva.[9] | Oferta de suscripción actual, subasta/precio/yield, liquidación original, precio secundario, comisiones, fiscalidad y permiso de redistribución. |
| DEBT-02 · deuda | **Letra del Tesoro, venc. 05-02-2027** · `ES0L02702055` | Verificada por fila del Tesoro.[9] | Saldo efectivo **16-10-2026**, consulta 26-10-2026.[9] | Los mismos campos de oferta, subasta, precio secundario, comisiones, fiscalidad y permiso pendientes. |
| DEBT-03 · deuda | **Letra del Tesoro, venc. 05-03-2027** · `ES0L02703053` | Verificada por fila del Tesoro.[9] | Saldo efectivo **16-10-2026**, consulta 26-10-2026.[9] | Los mismos campos de oferta, subasta, precio secundario, comisiones, fiscalidad y permiso pendientes. |
| DEBT-04 · deuda | **Letra del Tesoro, venc. 09-04-2027** · `ES0L02704093` | Verificada por fila del Tesoro.[9] | Saldo efectivo **16-10-2026**, consulta 26-10-2026.[9] | Los mismos campos de oferta, subasta, precio secundario, comisiones, fiscalidad y permiso pendientes. |
| FND-01 · fondo | **Bestinver Bolsa, F.I.** · `ES0147622031` | Verificada; página oficial Bestinver.[10] | NAV publicado a **23-10-2026**, consulta 26-10-2026.[10] | KID/DFI minorista actual, SRI, divisa de clase, condiciones de suscripción/reembolso, coste completo y permiso para NAV/histórico. |
| FND-02 · fondo | **OLEA NEUTRAL, FI** · `ES0118537002` | Verificada; ficha oficial CNMV.[11] | Fechas de folleto/reglamento 01-10-2026/08-06-2026; consulta 26-10-2026.[11] | NAV/fecha, costes, riesgo, divisa, clase y disponibilidad minorista. El registro CNMV identifica, pero no prueba oferta disponible. |
| FND-03 · fondo | **Azvalor Internacional FI** · `ES0112611001` | Propuesta; snippet de página oficial Azvalor, sin GET directo.[12] | Fecha de registro indicada 23-10-2015; consulta 27-10-2026. No es fecha efectiva de condiciones.[12] | Lectura directa, DFI/KID actual, NAV efectivo, riesgo/costes completos, divisa de clase, disponibilidad y términos. |
| FND-04 · fondo | **Bestinver Internacional, F.I.** · `ES0114638036` | Propuesta; snippet de página oficial Bestinver, sin GET directo.[19] | El snippet no fecha el NAV que muestra; consulta 27-10-2026.[19] | Lectura directa, fecha de NAV, KID/DFI, riesgo, costes completos, divisa de clase, domicilio/eligibilidad y permisos. |
| ETF-01 · UCITS | **iShares Core MSCI Europe UCITS ETF EUR (Acc)** · `IE00B4K48X80` | Verificada; KID PRIIPs oficial en español.[15] | KID fechado **03-09-2026**, consulta 26-10-2026.[15] | Domicilio, NAV efectivo, listings/tickers, disponibilidad por broker/cliente y permiso de display/cache/export. |
| ETF-02 · UCITS | **Xtrackers S&P 500 Equal Weight UCITS ETF 2D** · `IE000CXLGK86` | Verificada; página oficial DWS; XLSX de holdings probado en ronda previa, no copiado aquí.[16] | NAV a **23-10-2026**, consulta 26-10-2026.[16] | Domicilio/divisa de clase, KID español, SRI/costes KID, NAV histórico y derechos sobre holdings. |
| ETF-03 · UCITS | **State Street SPDR MSCI Europe Industrials UCITS ETF** · `IE00BKWQ0J47` | Verificada; página oficial State Street; holdings probados previamente, no copiados aquí.[17] | NAV oficial y holdings a **23-10-2026**, consulta 26-10-2026.[17] | KID español exacto, domicilio/divisa de clase, elegibilidad minorista, precio de mercado y permiso de uso. `STQ FP` es un alias de listing, no otro producto. |
| ETF-04 · UCITS | **VanEck Semiconductor UCITS ETF** · `IE00BMC38736` | Verificada; página oficial VanEck en localización UK.[18] | NAV a **23-10-2026**, consulta 26-10-2026.[18] | KID español minorista actual, domicilio/divisa de clase, listings, elegibilidad en España y permisos de datos. |

La tabla del Tesoro muestra **8.780,5 / 8.597,1 / 8.623,1 / 9.010,2 millones de euros** para esas cuatro letras a fecha 16-10-2026; son importes vivos, no precios ni importes mínimos de compra.[9]

## Conflictos, fechas y reglas de conteo

1. **Openbank / YieldMeister:** se conservan separados la ficha Openbank de seis meses, efectiva desde 08-10-2026, y el registro del agregador con producto «12m»/12 meses. El segundo no pasa a comparador hasta resolver la discordancia; `stale=false` no corrige identidad ni condiciones.[5][21]
2. **MyInvestor:** la página tiene bloques incompatibles para promoción y FAQ. No se elige una cifra «más favorable» ni se deduce el tipo postpromoción; revisión de bases legales antes de comparación.[2]
3. **Fecha efectiva ≠ fecha de consulta.** Cada fila de `candidatos.json` separa `dates.checked_at` y `dates.effective`. Para las Letras uso el pie de la tabla específica que dice 16-10-2026; no traslado a esa tabla otra fecha que pueda aparecer para bonos u otra sección.[9]
4. **Deuda no es oferta:** los cuatro ISIN identifican instrumentos vivos en la tabla del Tesoro; no confirman acceso a una subasta o precio secundario disponible. No se cuentan benchmarks del BCE/Banco de España ni yields agregados como productos.[9]
5. **Fondos/ETF:** cada fila con ISIN es un fondo/clase concreto. Los tickers/listings son atributos y no duplican el producto; el UCITS ETF no se clasifica como fondo tradicional.[15][16][17]

## Estado técnico y permisos

| Aspecto | Estado y evidencia |
|---|---|
| Páginas/datos previos de Tesoro, Bestinver y CNMV | Pruebas puntuales de página/registro; no son integración ni garantía de frescura.[9][10][11] |
| ETF y holdings | NAV/documentos por producto; archivos de holdings probados en rondas previas, no copiados aquí.[15][16][17] |
| Propuestas Openbank, Pibank y EBN | Snippets oficiales solamente; no lectura directa de página en esta ronda.[3][4][22] |
| Propuestas Azvalor y Bestinver Internacional | Snippets oficiales solamente; no lectura directa de página en esta ronda.[12][19] |
| Automatización, copia/cache, transformación, display, redistribución, PDF y retención | Pendiente por fuente/acción. Los términos no revisados siguen pendientes; no se etiquetan como prohibición universal. |
| Actividad de descarga en esta ronda | Ningún PDF, histórico masivo o nuevo XLSX/CSV de holdings descargado. |
## Expansión posterior, sin añadir familias

- **Cuentas:** Trade Republic queda fuera de la selección por clasificación y condiciones pendientes; Open Young es un producto infantil, no apto para comparación con la audiencia adulta de Paideia.[24][23]
- **Depósitos:** Depósito Más DB aparece como alternativa oficial para una futura lectura directa; no se cuenta entre los cuatro de este corte.[8]
- **Letras/deuda pública:** ampliar solo con nuevos ISIN únicos en la misma tabla oficial, checksum validado y fechas efectivas por fila; nunca añadir benchmarks como producto.[9]
- **Fondos tradicionales:** ampliar con nuevas clases/fondos del registro CNMV o de gestoras, pero validar cada ISIN/clase y documento minorista; el listado UCITS es una vía de descubrimiento, no prueba de oferta.[11][26]
- **ETF UCITS:** Vanguard FTSE All-World USD Acc (`IE00BK5BQT80`) queda como expansión después de conseguir/revisar KID español y la elegibilidad minorista; el factsheet revisado se dirige a inversores profesionales.[25]

## Auditoría del límite de consultas

| Control | Resultado |
|---|---|
| Selección | 6 identidades propuestas con una búsqueda oficial cada una; 14 identidades verificadas reutilizan evidencia de las dos rondas. |
| Máximo por candidato seleccionado | 1 búsqueda dirigida; ninguna propuesta seleccionada recibió una segunda búsqueda. |
| Descargas esta ronda | 0 PDFs, 0 históricos masivos y 0 nuevos XLSX/CSV de holdings. |
| Excepciones excluidas | Cobas Selección se buscó dos veces y se excluyó; BFF/Facto tuvo dos intentos de dominio oficial y una búsqueda amplia que devolvió solo páginas secundarias. Ninguno aporta datos al conteo.[13][14] |
| Registro del lote | `evidencia/retrieval-batches.json`. |
## Evidencia y artefactos

| Artefacto | Contenido |
|---|---|
| [`candidatos.json`](candidatos.json) | 20 fichas con campos disponibles/desconocidos, identidad literal, checksum, fechas separadas, estados técnicos y permisos por acción. |
| [`evidencia/sources-ledger.json`](evidencia/sources-ledger.json) | Ledger de URLs y extractos literales. |
| [`evidencia/source-evidence-manifest.json`](evidencia/source-evidence-manifest.json) | Método/fecha de recuperación y relación URL-evidencia. |
| `evidencia/source-excerpts.txt`, `source-22.txt`–`source-26.txt` | Extractos mínimos; sin PDFs ni series históricas. |
| [`evidencia/retrieval-batches.json`](evidencia/retrieval-batches.json) | Consultas públicas adicionales y auditoría del límite. |
| Fuentes internas de las rondas | [requisitos](../../REQUISITOS.md), [síntesis](../../investigacion-apis-02/00-SINTESIS.md), [bancos](../../investigacion-apis-02/05-bancos-fichas-importables.md), [fondos](../../investigacion-apis-02/02-fondos-tradicionales.md), [ETF](../../investigacion-apis-02/03-etf-emisores.md), [registros](../../investigacion-apis-02/06-identificadores-registros.md), [deuda](../../investigacion-apis-02/07-deuda-instrumentos.md). |
## Sources

[1] https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf — Renault Bank — Información precontractual global
    > "Promoción aplicable exclusivamente a nuevos clientes que contraten la Cuenta Contigo entre el 21/10/2026 y el 18/11/2026, ambos inclusive."
    > "la TAE será del 2,61% TAE"
[2] https://myinvestor.es/cuentas-tarjetas/cuentas — MyInvestor — Cuenta corriente remunerada
    > "Hazte cliente y remunera tu dinero al 2,5 % TAE durante los 6 primeros meses."
    > "Para un saldo máximo de 70.000 €."
[3] https://www.openbank.es/cuenta-remunerada — Openbank — Cuenta Remunerada
    > "Cuenta Remunerada sin Nómina al 3,25% TAE"
    > "3,25% TAE 1 y 3,20% TIN"
[4] https://www.pibank.es/cuenta-remunerada — Pibank — Cuenta Remunerada
    > "Cuenta Remunerada Pibank"
    > "Remuneración al 2,02% TAE1"
[5] https://www.openbank.es/assets/static/pdf/Productos/302_923_31_Deposito_6/302_923_31_Deposito_6.pdf — Openbank — Depósito a 6 meses, ficha oficial
    > "Vigente desde 08.10.2026."
    > "3,25% TAE y 3,22% TIN anual."
[6] https://www.pibank.es/deposito-bancario-plazo-fijo — Pibank — Depósito a plazo fijo
    > "Saber más https://www.pibank.es/deposito-bancario-plazo-fijo/"
[7] https://img.pibank.es/pdfs/deposito/deposito_ip.pdf — Pibank — Ficha precontractual del Depósito Pibank
    > "Divisa : EURO."
    > "Duración de la Imposición: 12 meses."
[8] https://www.deutsche-bank.es/es/particulares/ahorro-inversion/productos/depositos/deposito-mas.html — Deutsche Bank — Depósito Más DB
    > "# Depósito Más DB"
    > "Plazo: 12 meses"
    > "TAE 2,75 %"
[9] https://www.tesoro.es/en/deuda-publica/valores-del-tesoro/valores-en-circulacion — Tesoro Público — Valores en circulación
    > "ES0L02701156 | 01/15/2027 | 8,780.5"
    > "ES0L02702055 | 02/05/2027 | 8,597.1"
    > "ES0L02703053 | 03/05/2027 | 8,623.1"
    > "ES0L02704093 | 04/09/2027 | 9,010.2"
    > "Data as at 10/16/2026."
[10] https://www.bestinver.es/fondos-de-inversion/bestinver-bolsa — Bestinver — Bestinver Bolsa, F.I.
    > "Bestinver Bolsa, F.I."
    > "Código ISIN: ES0147622031"
[11] https://www.cnmv.es/portal/consultas/iic/fondo?lang=es&nif=V85962447 — CNMV — Ficha OLEA NEUTRAL, FI
    > "OLEA NEUTRAL, FI"
    > "4231 14/05/2010 ES0118537002 01/10/2026 08/06/2026"
[12] https://www.azvalor.com/fondos-de-inversion/azvalor-internacional — Azvalor — Azvalor Internacional FI
    > "# Azvalor Internacional FI"
    > "Fecha de Registro en la CNMV 23/10/2015"
[13] https://www.cobasam.com/productos/inversion-libre/cobas_seleccion — Cobas AM — Cobas Selección FI
    > "Cobas Selección FI Clase B"
    > "Domicilio Paseo de la Castellana 53. Segunda planta. 28046 Madrid. España."
[14] https://www.cobasam.com/wp-content/uploads/2026/01/Comentario-Segundo-Semestre-2025.pdf — Cobas AM — Informe de clases de Cobas Selección FI
    > "Clase A - ES0124037039 Clase B - ES0124037021 Clase C - ES0124037005 Clase D - ES0124037013"
[15] https://www.blackrock.com/es/profesionales/literature/kiid/eu-priips-ishares-core-msci-europe-ucits-etf-eur-acc-ie00b4k48x80-es.pdf — BlackRock/iShares — KID español IE00B4K48X80
    > "iShares Core MSCI Europe UCITS ETF EUR (Acc), EUR Accu, ISIN: IE00B4K48X80"
    > "La fecha de este documento es 03 septiembre 2026."
[16] https://etf.dws.com/en-lu/IE000CXLGK86-s-p-500-equal-weight-ucits-etf-2d — DWS — Xtrackers S&P 500 Equal Weight UCITS ETF 2D
    > "Xtrackers S&P 500 Equal Weight UCITS ETF 2D"
    > "NAV (23.10.2026): 104.46 USD All-in-fee (TER): 0.15%"
[17] https://www.ssga.com/se/en_gb/intermediary/etfs/state-street-spdr-msci-europe-industrials-ucits-etf-stq-fp — State Street — SPDR MSCI Europe Industrials UCITS ETF
    > "State Street® SPDR® MSCI Europe Industrials UCITS ETF"
    > "NAV EUR (Official NAV) €411,94 as of 23 Oct 2026"
[18] https://www.vaneck.com/uk/en/investments/semiconductor-etf/overview?al=en&audience=retail&disclaimer=true — VanEck — Semiconductor UCITS ETF
    > "VanEck Semiconductor UCITS ETF"
    > "NAV $97.02 as of 23 Oct 2026"
[19] https://www.bestinver.es/fondos-de-inversion/bestinver-internacional — Bestinver — Bestinver Internacional, F.I.
    > "Bestinver Internacional, Fondo de Inversión"
    > "Código ISIN: ES0114638036"
[20] https://www.pibank.es — Pibank — página de inicio y productos
    > "Depósito Pibank a 12 meses"
    > "Cuenta Remunerada Pibank"
[21] https://yieldmeister.com/api/v1/rates — YieldMeister — respuesta pública de rates, fila Openbank
    > "Depósito Plazo Fijo 12m"
[22] https://www.ebnbanco.com/ahorro/deposito-sinycon-plus — EBN Banco — Depósito Sinycon Plus
    > "Depósito Sinycon Plus"
    > "rentabilidad de hasta el 2,85% TAE."
    > "A partir de 5.000€ y hasta 400.000€"
    > "No, la cancelación anticipada en este producto no está permitida."
[23] https://www.openbank.es/cuentas-de-ahorro — Openbank — Cuentas de ahorro, incluida Open Young
    > "Cuenta de Ahorro Open Young"
    > "Una cuenta de ahorro infantil pensada para que su dinero crezca con ellos."
    > "0,15 % TAE1 y TIN anual."
[24] https://traderepublic.com/es-es/interes — Trade Republic — Interés sobre efectivo
    > "Trade Republic: 3,04 % TAE sobre tu efectivo"
[25] https://fund-docs.vanguard.com/FTSE_All-World_UCITS_ETF_USD_Accumulating_9679_EU_INT_UK_EN.pdf — Vanguard — FTSE All-World UCITS ETF USD Acc factsheet
    > "ISIN IE00BK5BQT80 USD Accumulating"
    > "This document is directed at professional investors and should not be distributed to, or relied upon by retail investors."
[26] https://www.cnmv.es/portal/consultas/mostrarlistados?id=26&lang=es&page=1 — CNMV — Listado completo de UCITS
    > "CNMV - Listado completo de UCITS"
