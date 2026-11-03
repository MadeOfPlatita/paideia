# APIs comerciales para catálogo financiero europeo / Paideia

## Decisión ejecutiva

Para una web UMA con hasta 100 visitantes, la elección no la decide el máximo de llamadas: la decide quién autoriza **display público y caché PostgreSQL**. Los tiers personales/internos no autorizan por defecto mostrar feeds a terceros; Twelve Data exige acuerdo para redistribuir, Finnhub prohíbe compartir sin aprobación y EODHD separa planes personales de comerciales.[5][19][38]

Las pruebas demo y límites gratuitos sirven para discovery, no para producción sin términos claros.[13][30]

**Prioridad para pedir términos y hacer una prueba real:**
1. **Twelve Data** — mejor señal concreta de listings ETF/UCITS europeos: su directorio demo identificó listings CSPX/Euronext y EUNL/Xetra; no entregó ISIN (valor `request_access_via_add_ons`). No se validaron precios para esos listings.[50][44]
2. **EODHD** — mejor documentación de OHLC EOD global + ETFs/fundamentales y ajustes; contrato comercial interno empieza en $399/mes y no permite mostrar a terceros. Enterprise se anuncia a $2.499/mes, pero el acuerdo debe nombrar expresamente el display externo.[10][38][39]
3. **FMP** — fuerte en búsqueda ISIN, perfil ETF y fundamentales, y el tier Ultimate anuncia cobertura global; no se probó un listing europeo y publicar requiere un acuerdo de display/redistribución aparte.[21][24]
4. **Alpha Vantage** — buen instrumento de prototipo educativo y dispone de precio ajustado, pero la API free/premium personal no autoriza mostrar a usuarios; el uso comercial se cotiza aparte. El demo sólo probó IBM/EEUU.[29][30][53]

**Low-cost a preguntar, no a lanzar:** marketstack Basic cuesta $9,99/mes (o $8,99/mes anual) y etiqueta el uso como comercial, pero la documentación pública consultada no aclara si eso autoriza display externo, redistribución ni caché duradera. **No interpretar “Commercial Use” como licencia de publicación.**[31]

**Depriorizar para este caso:** Finnhub ofrece precios de acciones internacionales, pero su paquete estándar de ETFs declara cobertura US; cobertura ETF mundial queda para advanced/enterprise. Tiingo no documenta precios europeos de acciones/ETF en su API actual.[16][36]

## Matriz de campos que realmente cubre la documentación

| Proveedor | Identidad y cobertura documentada | Precio/historial y ajustes documentados | ETF/fundamentales documentados | Estado y alcance de prueba |
|---|---|---|---|---|
| **Twelve Data** | Directorio de ETF incluye símbolo, nombre, moneda, exchange, MIC, país, FIGI/CFI e ISIN; ISIN se habilita con add-on. El mismo símbolo puede repetirse por venue. El test encontró un CSPX UCITS en Euronext/XAMS (EUR) con ISIN bloqueado.[44][50] | Time series: `datetime` local del exchange, `open/high/low/close` y `volume` si corresponde; metadatos con `symbol/currency/exchange/mic_code/type`. Hay parámetro de ajuste en la documentación; fijar su semántica y versión antes de calcular retornos.[42] | Catálogo ETF y endpoints de métricas/desglose; no confundir catálogo con holdings/NAV o con precio probado. La cobertura extensa ETF y soporte completo requieren tiers superiores.[44] | `endpoint-tested` para catálogo de 68.599 filas; sólo `documented` para precios EU. La respuesta real devuelve `isin=request_access_via_add_ons` incluso en fichas UCITS.[50] |
| **EODHD** | Símbolo `CODE.EXCHANGE`, sufijo propio; `EUFUND` existe para fondos europeos. La lista de exchanges/tickers es por mercado; el crosswalk ISIN→listing y el instrumento objetivo siguen sin probar.[11] | EOD: fecha, OHLC sin ajustar, `adjusted_close` ajustado por splits y dividendos, volumen ajustado por splits; EOD suele actualizar 2–3 h tras cierre.[10] | Fundamentals documenta stocks/ETFs globales (mutual funds US); endpoints permiten filtrar secciones/campos. El demo filtrado sólo probó `General::*` de AAPL, no datos ETF ni europeos.[40][52] | `endpoint-tested` en AAPL.US, sólo para forma y campos. Vendor advierte que ciertos CFD/ETF/Forex pueden ser precios indicativos, no adecuados para trading.[9] |
| **FMP** | `search-isin` documenta nombre, ticker, ISIN y market cap. Cobertura publicada: Starter US; Premium UK/Canadá; Ultimate Global. Un símbolo global no es prueba de que exista cada clase/listing UCITS.[21][24] | Histórico diario: OHLCV, cambios y VWAP. FAQ dice `close` ajustado por splits y `adjClose` por splits+dividendos.[23] | Perfil ETF: ticker/nombre, expense ratio y AUM; holdings se incluye en Ultimate. No se validó cadencia/histórico de holdings de ETF UCITS.[21] | `documented`; ninguna request al endpoint, sin clave disponible. |
| **Alpha Vantage** | Documenta equities globales y ETFs; la solicitud se hace por símbolo/mercado. No se identificó endpoint ISIN→listing en la documentación consultada. Cobertura de un UCITS europeo concreto no probada.[28] | Daily raw devuelve OHLCV; demo mostró fecha de refresco y zona horaria. `TIME_SERIES_DAILY_ADJUSTED` es premium y entrega OHLCV, adjusted close y eventos dividend/split; `full` history también es premium.[28][53] | ETF Profile/Holdings documentado, pero la amplitud para ETFs europeos no se probó.[28] | `endpoint-tested` en demo IBM/EEUU; no evidencia de precio UCITS europeo. |
| **Finnhub** | Candle docs y lista de símbolos con symbol/displaySymbol/MIC/FIGI; ISIN sólo para acciones EU y algunos mercados asiáticos, con entitlement. No implica ISIN en todos los ETFs.[17] | Candle OHLCV con timestamp/status. Pricing separa datos internacionales; la demora por venue no quedó confirmada en el texto de página recuperado: validar con soporte. No se estableció un adjusted close para este caso.[15][17] | ETF profile/holdings existe; planes estándar de ETFs/fondos son US; cobertura global es avanzada/enterprise.[16] | `documented`, no hay clave/demo público probado. |
| **marketstack** | V2 anuncia 125.000+ tickers, 72+ exchanges, ETFs y company fundamentals; la ficha de cada listing y crosswalk ISIN no se verificó.[32] | EOD ajustado anunciado; endpoints de splits/dividend y datos intraday. El intraday documentado para US se basa en IEX; no se confirmó frecuencia exacta ni ajuste de cada listing Euronext/Xetra.[31][32] | Basic lista ETF holdings; no se acreditó aquí la profundidad, fecha de corte o composición histórica necesaria para una ficha UCITS.[31] | `documented`; sin demo pública identificada ni request sin credenciales. |
| **Tiingo (alternativa)** | La pantalla de pricing habla de un universo global de securities, pero la documentación de precios limita acciones/ETF/fondos a EEUU y acciones de China.[35][36] | No se acreditó endpoint EOD europeo; docs declaran alcance distinto para precios. | ETFs/fondos son precios EEUU según symbology actual. | `unsuitable` como fuente de precio UCITS europeo; no se probó endpoint. |

## Precio mínimo, uso gratuito y permiso de publicación

| API | Free/prueba y mínimo de pago relevante | Display, redistribución y cache |
|---|---|---|
| **Twelve Data** | Basic gratis: 8 créditos/min y 800/día; para UE no presupuestar que sirva. Grow desde $29/mes con anual (precio mensual listado $79); Pro desde $99/mes anual; Venture business desde $149/mes según Trial.[1][4] | Individual es personal/interno, no permite display externo ni redistribución. Business permite usos de display externo sujetos a market licensing; precios EU fuera de US requieren aprobación y redistribución contrato separado. La nota EU ata la demora al entitlement. Venture menciona caché temporal; obtener por escrito duración, universo, visitantes y extracción de históricos.[5][7] |
| **EODHD** | Free: 20 calls/día + 500 bonus, 1 año EOD y uso personal. Paid individual desde $19,99/mes, full history.[13][40] | El plan comercial Internal Use cuesta $399/mes y sólo permite uso dentro de la empresa; Enterprise Scale & delivery figura en $2.499/mes. Confirmar en el contrato si incluye display público/redistribución y cuánto se puede persistir; no usar el plan personal en la web.[38][39] |
| **Finnhub** | Pricing lista $0, cuota gratuita actual no confirmada. Stocks: Basic $49,99/mes trimestral, Standard $129,99/mes trimestral y Professional $199,99/mes anual; ETF plans $500/mes anual (ETF-2 $1.000), con scope US. ETF global se cotiza advanced/enterprise.[15][16] | Los tiers del sitio son personal use; no compartir datos/derivados sin aprobación y borrar datos al finalizar suscripción. Enterprise declara commercial use + redistribución, a precio flexible no publicado. Cache de PostgreSQL debe estar cubierto por escrito.[19][20] |
| **FMP** | Free: 250 calls/día. Starter $29/mes o $19/mes anual (US); Premium $69 o $49/mes anual (UK/Canadá); Ultimate $139 o $99/mes anual (Global). Esos son tiers de API, no tarifa de sitio público.[21] | Display/redistribución necesita Data Display and Licensing Agreement específico. Términos estándar prohíben servir datos a terceros; al terminar contrato hay que borrar también lo cacheado. Cotización de licencia pública no publicada.[21][26] |
| **Alpha Vantage** | Free: 25 requests/día; ilimitado sólo para proyectos educativos/open-source verificados. Premium personal mínimo $49,99/mes por 75 rpm; comercial: contacto/cotización.[27][30] | Términos clasifican como comercial habilitar acceso a otras personas, incluso fuera del sector financiero. Verificación educativa puede ampliar llamadas, pero no equivale a permiso para mostrar datos en la web. No se halló regla pública de caché: solicitar autorización.[29] |
| **marketstack** | Pricing: Free 100 requests/mes, EOD, un año y no comercial. Basic $9,99/mes ($8,99 anual), 10.000/mes, EOD hasta 10 años, ETF holdings y etiqueta “Commercial Use”. Professional $49,99/mes para real-time updates.[31] | La página pública consultada no aclara redistribución, display a terceros ni duración de cache. Hasta obtener respuesta escrita, no exponer cotizaciones/cache persistente aunque el plan Basic diga “Commercial Use”.[31] |

> **Demora: no intercambiar EOD, delayed, realtime, precio de mercado y NAV.**
>
> - EODHD publica actualización normalmente 2–3 h después del cierre y avisa que algunos precios son indicativos.[9][10]
> - Twelve Data dice que EU puede ser real-time o delayed en Cboe Europe, con demora ligada al entitlement.[7]
> - Alpha Vantage indica que su quote por defecto se refresca al final del día; realtime/15-min documentado se refiere a mercado US.[28]
> - En Finnhub, FMP y marketstack falta validar por escrito la demora del listing Xetra/Euronext concreto antes de publicarlo.[15][21][31]

## Demos públicas leídas (sin claves privadas)

| Request público | Resultado observado | Qué prueba / qué no prueba |
|---|---|---|
| Twelve Data `/etfs?apikey=demo` | HTTP 200 JSON, `count=68.599`; contiene el registro real de CSPX UCITS en Euronext/XAMS, EUR. `isin` quedó como `request_access_via_add_ons`.[50] | Prueba catálogo, venue, MIC, moneda y bloqueo de ISIN en esa respuesta; **no** prueba series de precios. [Raw response](evidencia/twelvedata-etfs-demo.body). |
| EODHD EOD demo AAPL.US | HTTP 200 JSON con `date/open/high/low/close/adjusted_close/volume`, dos fechas.[10] | Prueba formato EOD y diferencia de campos; sólo AAPL.US, no Xetra/UCITS. [Raw response](evidencia/eodhd-aapl-eod-demo.body). |
| EODHD Fundamentals demo AAPL.US filtrado | HTTP 200; devolvió `General::Code/Name/Exchange/Currency/Type` (AAPL, NASDAQ, Common Stock).[52] | Prueba filtros y metadatos stock; no fundamentals de ETF ni Europa. [Raw response](evidencia/eodhd-aapl-fundamental-demo.body). |
| Alpha Vantage `TIME_SERIES_DAILY`, IBM demo | HTTP 200; `Meta Data` + `Time Series (Daily)`, OHLCV, `Last Refreshed=2026-10-23`, zona `US/Eastern`.[53] | Prueba el endpoint público y su forma; no UCITS ni series ajustada. [Raw response](evidencia/alphavantage-ibm-daily-demo.body). |

No hice llamadas sin autorización para Finnhub, FMP o marketstack; sus endpoints requieren token. Un 401 no se trató como evidencia de cobertura.

## Estrategia de caché compartida (sin crear DB)

- **Una tarea diaria de backend**, no una llamada por visitante: lista de instrumentos autorizados → descarga después del cierre de cada venue → `UPSERT` por clase/listing/fecha. Con 100 instrumentos y una request por instrumento son **100 requests/día, 3.000 por 30 días**; los 100 visitantes no multiplican eso si consultan la misma tabla cacheada.[13][31]
- Guarda por separado `isin`, `provider_symbol`, `exchange_code`, **MIC**, moneda de cotización, tipo de activo, `price_kind` (`traded_close` vs `NAV`), `adjustment_basis`, `source_as_of`, `fetched_at`, `source` y estado de licencia. No unir listings por ticker desnudo: `CSPX` o `EUNL` puede repetirse en más de una bolsa/moneda.[11][17][50]
- Persistir el JSON original sólo si el contrato autoriza cache/replay; los proveedores distinguen caché temporal, prohibición de redistribuir y borrado de datos al terminar.[5][19][26] Guardar fixture demo en `evidencia/` para pruebas. Nunca llamar al proveedor desde el navegador ni devolver su API key. Mantener `as_of` de mercado y `fetched_at` separados; no convertir un precio viejo en “actual” por volverlo a consultar.
- Fijar una sola regla de ajustes (raw, splits-only, split+dividend) y almacenar el campo original además del normalizado; los proveedores devuelven medidas distintas de close/adjusted close.[10][23][28] Para fondos, guardar NAV y último precio negociado como series distintas; no deducir moneda de clase cubierta a partir de la moneda de cotización.
- Antes del primer refresh productivo: conseguir autorización para usuarios externos, tipo de caché y retención, atribución, mercados/MIC, historial que se conserva, cancelación/borrado y coste por feed. Si no se concede, cargar un catálogo curado con datos de fuentes oficiales con licencia compatible y no publicar valores derivados que permitan reconstruir el feed.[5][19][21]

## Fuentes

## Sources

[1] https://twelvedata.com/pricing
[4] https://support.twelvedata.com/en/articles/5335783-trial
[5] https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage
[7] https://support.twelvedata.com/en/articles/12656239-european-equities-market-data
[9] https://eodhd.com/financial-apis/terms-conditions
[10] https://eodhd.com/financial-apis/api-for-historical-data-and-volumes
[11] https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours
[13] https://eodhd.com/financial-apis/api-limits
[15] https://finnhub.io/pricing-stock-api-market-data
[16] https://finnhub.io/pricing-etf-indices
[17] https://finnhub.io/docs/api
[19] https://finnhub.io/terms-of-service
[20] https://finnhub.io/pricing-startups-and-enterprise
[21] https://site.financialmodelingprep.com/developer/docs/pricing
[23] https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full
[24] https://site.financialmodelingprep.com/developer/docs/stable/search-isin
[26] https://site.financialmodelingprep.com/terms-of-service
[27] https://www.alphavantage.co/premium
[28] https://www.alphavantage.co/documentation
[29] https://www.alphavantage.co/terms_of_service
[30] https://www.alphavantage.co/support
[31] https://marketstack.com/pricing
[32] https://marketstack.com/documentation_v2
[35] https://www.tiingo.com/pricing
[36] https://www.tiingo.com/documentation/appendix/symbology
[38] https://eodhd.com/financial-apis/commercial-vs-personal-license-use
[39] https://eodhd.com/commercial-pricing
[40] https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds
[42] https://twelvedata.com/docs/llms/market-data/time-series.md
[44] https://twelvedata.com/docs/llms/asset-catalogs/etf-list.md
[50] https://api.twelvedata.com/etfs?apikey=demo
[52] https://eodhd.com/api/v1.1/fundamentals/AAPL.US?filter=General::Code,General::Name,General::Exchange,General::Currency,General::Type&api_token=demo&fmt=json
[53] https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo
