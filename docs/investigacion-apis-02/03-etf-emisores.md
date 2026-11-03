# Fuentes máquina de emisores ETF UCITS — ronda 03

**Corte: 26-10-2026.** Se probaron tres descargas públicas de solo lectura (iShares, Xtrackers/DWS y SPDR/State Street), sin cuenta ni claves. No se validó una API agregada ni los derechos de redistribución. Una URL pública y una respuesta 200 no otorgan permiso para republicar datos.[2][4][5]

## Decisión ejecutiva

- **Mejor base de holdings para importar por ISIN:** Xtrackers/DWS y SPDR publican XLSX con ISIN de cada valor; ambos archivos se descargaron y analizaron. Son exportaciones web por producto, no APIs oficiales documentadas.[3][4][5]
- **iShares/BlackRock:** también se probó un CSV de holdings, pero el archivo no trae ISIN de cada posición y su ruta usa un ID interno de producto; hay que resolver ISIN/clase por separado.[1][2]
- **Amundi y Vanguard:** sus documentos oficiales aportan atributos útiles, pero en esta pasada solo se verificaron fichas PDF; no se probó una fuente de holdings/NAV estructurada diaria. Las fichas consultadas se destinan a inversores profesionales, por lo que no deben sustituir el KID/DFI minorista español.[6][7]
- **KID español:** sí se verificó un KID PRIIPs español de iShares para una clase concreta. Los sitios de los demás emisores requieren comprobar idioma, clase e idoneidad documento por documento; no inferir que una ficha profesional es un KID.[8]

**Recomendación Paideia:** carga inicial pequeña con ISIN exactos, documentos y campos manualmente revisados; programar una tarea diaria compartida que guarde el archivo bruto, hora de recuperación y fecha efectiva del emisor. Cachear el catálogo para los usuarios.[2][4]

Los tres archivos de holdings probados son composiciones, no cotizaciones de bolsa.[2][4][5]

La página de SPDR diferencia NAV oficial y fecha; mantenga esa serie separada del precio de mercado.[10]

## Candidatos priorizados

| Prioridad | Emisor y recurso | Lo que cubre | Estado / límites |
|---|---|---|---|
| 1 | **Xtrackers (DWS)** — enlace de producto a `/etfdata/export/LUX/ENG/excel/product/constituent/{ISIN}/` | Ficha con ISIN, NAV y fecha, all-in-fee/TER; XLSX de holdings con ISIN y peso, nombre, país, divisa, mercado, clase de activo/sector y otros metadatos.[3][4] | **Descarga probada** por GET público. Excel ZIP válido (40.541 bytes); Content-Type devuelto no es el MIME XLSX habitual. El archivo lleva descargo de responsabilidad: DWS no garantiza exactitud, integridad o puntualidad. No es un feed garantizado.[4] |
| 2 | **SPDR / State Street** — archivo diario `holdings-daily-emea-en-{ticker}.xlsx` y página de producto | XLSX con ISIN/ticker de la clase y fecha de holdings; ISIN, SEDOL, nombre, divisa, cantidad, peso, país, precio local, sector/industria y valor de mercado base. La página STQ publica NAV oficial fechado, TER y documentos KID.[5][10] | **Descarga probada** (17.661 bytes). En la página localizada para Suecia se encontraron KID inglés y sueco, no un enlace español; eso no prueba que no exista para la localización española.[10] |
| 3 | **iShares / BlackRock** — enlace de producto a `.../products/{productId}/.../latest-holdings.csv` | CSV de posiciones: ticker, nombre, sector, clase de activo, valor de mercado, peso, nominal, participaciones, precio, país/ubicación, bolsa y divisa de mercado.[1][2] | **Descarga probada** (80.271 bytes). El fichero no incluía ISIN de las posiciones en la cabecera observada; la ruta usa el ID interno `328657`, no el ISIN de clase. Hace falta un maestro ISIN↔productId/clase y un security master para las posiciones.[2] |
| 4 | **Amundi** — PDFs `pdfDocuments/monthly-factsheet/{ISIN}/.../{fecha}` | Ficha mensual consultada: ISIN, clase Acc, UCITS, replicación, moneda de clase, SRI, NAV/AUM con fecha, coste con etiqueta propia y frecuencia declarada de cálculo del NAV.[6] | **Documentado, no feed probado.** La ficha de ejemplo dice NAV/AUM a 31-08-2026 y cálculo diario, pero la cifra extraída es mensual; no equivale a una serie diaria. La ficha indica “solely” para profesionales y remite al KID para el conjunto completo de costes.[6] |
| 5 | **Vanguard** — factsheets PDF en `fund-docs.vanguard.com` | La ficha de IE00BK5BQT80 contiene clase USD acumulativa, OCF 0,14%, UCITS/domicilio y tickers/bolsas; es útil para dar de alta la clase y sus listings.[7] | **Documentado, no feed probado.** La ficha se declara dirigida a profesionales y muestra holdings resumidos; no se verificó un CSV/API de cartera completa ni KID español en esta ronda.[7] |
| 6 | **VanEck** — página de producto y documentos | La página consultada expone ISIN, NAV/fecha, TER, SFDR y enlace a KIID; aporta un candidato adicional para catálogo, no una fuente de datos estructurados de cartera.[9] | **Página documentada, descarga no probada.** El enlace de KIID observado era genérico/inglés; holdings completos, KID español y derechos quedan sin verificar.[9] |

### API oficial frente a descarga pública

No encontré una especificación pública de API oficial con autenticación, cuotas, SLA y licencia de redistribución en las fuentes examinadas.[1][4]

Las tres rutas probadas son **descargas públicas de archivos servidas desde sitios de emisores**, no APIs con contrato de campos.[2][4][5]

En el barrido acotado no localicé un catálogo/holdings JSON o XML documentado; los formatos máquina que sí superaron prueba fueron CSV/XLSX.[2][4][5]

En iShares aparece un patrón `.ajax?...dataType=fund...`; no se usó como integración ni se considera una API documentada.[1]

Las llamadas probadas no pidieron credenciales y funcionaron sin pagar en este ensayo; **límites, rate limits y permiso de almacenamiento/redistribución no confirmados**. No escalar llamadas por usuario: importar los productos de interés en un cron central y servir el catálogo propio. Las páginas/fichas de Amundi y Vanguard tienen restricciones de audiencia profesional expresas.[6][7]

## Pruebas de descarga (archivos brutos conservados)

| Fuente | Resultado real | Campos observados | Evidencia local |
|---|---|---|---|
| iShares CSV `latest-holdings.csv` | GET HTTPS, sin auth: **200**, `text/plain; charset=utf-8`, 80.271 bytes. As-of del archivo: **23/Oct/2026**. | El CSV empieza con una fila de fecha, una fila vacía y después cabecera; no asumir que la primera fila es el header. Cabecera con 12 campos, sin ISIN de cada posición.[2] | `docs/investigacion-apis-02/evidence/downloads/ishares-s-p-500-equal-weight-holdings.csv` |
| Xtrackers XLSX `constituent/IE000CXLGK86/` | GET HTTPS, sin auth: **200**, 40.541 bytes, ZIP/XLSX analizable; Content-Type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml`. | Hoja incluye descargo inicial, cabecera y filas de holdings. Cabecera: Name, ISIN, Country, Currency, Exchange, Type of Security, Rating, Primary Listing, Industry Classification, Weighting.[4] | `docs/investigacion-apis-02/evidence/downloads/xtrackers-ie000cxlgk86-constituents.xlsx` |
| SPDR STQ holdings XLSX | GET HTTPS, sin auth: **200**, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, 17.661 bytes. | Metadatos de fondo/clase y fecha 23-Oct-2026; filas con ISIN, SEDOL, Security Name, Currency, Number of Shares, Percent of Fund, país, Local Price, sector, industria y Base Market Value.[5] | `docs/investigacion-apis-02/evidence/downloads/spdr-stq-daily-holdings.xlsx` |

Los tres ensayos son comprobaciones puntuales: no prueban continuidad, cobertura de catálogo, frescura en cada ejecución, cuotas, uso comercial ni capacidad para 100 usuarios.[2][4][5]

## KID, campos manuales y modelo PostgreSQL

**KID/DFI:** el PDF español de iShares identifica IE00B4K48X80, lleva fecha 03-09-2026 y separa el indicador de riesgo 4/7, costes recurrentes (0,12%) y costes de operación (0,01%). Guardar el texto y las etiquetas originales del KID; no fusionar esos componentes ni llamar TER al total sin justificar la definición.[8]

Para el resto de clases se debe registrar manualmente URL, idioma, fecha, ISIN/clase exacta, SRI, horizonte y partidas de costes hasta validar una descarga española actual. La lista de documentos puede variar por clase, país y tipo de inversor.[6][7][10]

**Campos que quedan manuales o pendientes de una fuente licenciada:**

1. Maestro de share classes: ISIN, nombre legal, Acc/Dist, divisa de clase, cobertura FX, domicilio, condición UCITS, benchmark y método de réplica. No usar ticker de bolsa como identidad de clase; una clase puede tener varios listings.
2. Mapeo iShares ISIN↔productId y el ISIN del valor subyacente en sus holdings CSV; el archivo probado no lo expone.[2]
3. KID/DFI minorista español y extracción/revisión de costes/riesgo por ISIN; no reutilizar factsheets profesionales como documento minorista.[6][7][8]
4. Precio negociado (bolsa, ticker, divisa, hora, OHLCV) y serie histórica: se requiere otro proveedor autorizado; el NAV publicado y el precio de bolsa deben almacenarse en tablas distintas. La página SPDR identifica expresamente NAV oficial y fecha, mientras la hoja de holdings sólo es una composición.[5][10]
5. Derecho a cachear, transformar y redistribuir archivos/valores. No quedó confirmado en los documentos consultados; consultar términos/licencia del emisor e index providers antes de publicar al alumnado. El aviso de DWS limita la garantía sobre exactitud/completitud/puntualidad, pero no resuelve por sí solo la licencia de uso.[4]

**Esquema mínimo:** `fund_share_class(isin PK, issuer, legal_name, currency, acc_dist, hedged, ucits, domicile, benchmark, replication)`; `fund_metric(isin, metric_name_original, value, currency, effective_date, document_url)`; `holding(isin, effective_date, security_isin NULL, ticker NULL, name, currency, weight, market_value, source_file)`; `nav(isin, nav_date, currency, value, source_url)`; `exchange_quote(isin, exchange, ticker, quote_currency, timestamp, price, OHLCV, provider)`. Persistir también `retrieved_at`, fecha efectiva, tipo de dato y documento bruto.[2][4][5]

Mantener la etiqueta OCF/TER/coste KID tal como la publica cada fuente y mostrar “sin dato” cuando no esté verificado.[6][7][8]

## Sources

[1] https://ishares.com/uk/individual/en/products/328657/fund/1506575576011.ajax?dataType=fund&fileName=ISPE_holdings&fileType=csv — iShares S&P 500 Equal Weight UCITS ETF — product/holdings download reference
[2] https://www.ishares.com/uk/individual/en/products/328657/ishares-s-p-500-equal-weight-ucits-etf/latest-holdings.csv — iShares S&P 500 Equal Weight UCITS ETF — public holdings CSV
[3] https://etf.dws.com/en-lu/IE000CXLGK86-s-p-500-equal-weight-ucits-etf-2d — Xtrackers S&P 500 Equal Weight UCITS ETF 2D — official product page
[4] https://etf.dws.com/etfdata/export/LUX/ENG/excel/product/constituent/IE000CXLGK86 — DWS Xtrackers full securities list — XLSX export
[5] https://www.ssga.com/library-content/products/fund-data/etfs/emea/holdings-daily-emea-en-stq-fp.xlsx — SPDR MSCI Europe Industrials UCITS ETF — daily holdings XLSX
[6] https://www.amundietf.com/pdfDocuments/monthly-factsheet/IE0009DRDY20/ENG/LUX/INSTITUTIONNEL/ETF/20260831 — Amundi Prime Global UCITS ETF Acc — factsheet 31 August 2026
[7] https://fund-docs.vanguard.com/FTSE_All-World_UCITS_ETF_USD_Accumulating_9679_EU_INT_UK_EN.pdf — Vanguard FTSE All-World UCITS ETF USD Acc — factsheet 31 August 2026
[8] https://www.blackrock.com/es/profesionales/literature/kiid/eu-priips-ishares-core-msci-europe-ucits-etf-eur-acc-ie00b4k48x80-es.pdf — iShares Core MSCI Europe EUR Acc — Spanish PRIIPs KID
[9] https://www.vaneck.com/uk/en/investments/semiconductor-etf/overview?al=en&audience=retail&disclaimer=true — VanEck Semiconductor UCITS ETF — official product page
[10] https://www.ssga.com/se/en_gb/intermediary/etfs/state-street-spdr-msci-europe-industrials-ucits-etf-stq-fp — SPDR MSCI Europe Industrials UCITS ETF — product page (Sweden locale)
