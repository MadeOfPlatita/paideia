# Deuda soberana española por ISIN: catálogo, subastas y precios EOD

**Consulta:** 26-10-2026. **Ámbito:** deuda del Estado español; solo GET públicos, sin cuentas ni claves. Los endpoints se probaron como están indicados, no como garantía de cobertura completa ni de derechos de redistribución.[3][6][9]

## Tres hallazgos útiles

1. **El mejor catálogo de arranque es la página de Tesoro «Valores en circulación», no su XLSX estadístico.** El HTML ofrece ISIN, vencimiento, nominal vivo y, para bonos/obligaciones, el cupón aparece en la referencia; deuda indexada añade coeficiente y valor facial. El saldo lleva fecha efectiva y se actualiza en las fechas de liquidación.[3] El archivo `01.xlsx` descargable sí funciona, pero es una serie agregada por año/bucket de vencimiento, no filas por ISIN; úsese para control de totales, no como maestro de instrumentos.[1][2]

2. **Los términos y los resultados primarios se reconstruyen enlazando tres páginas del Tesoro.**
   - Los anuncios identifican ISIN, cupón, vencimiento, interés corrido, cupón corto e indexación.[5]
   - La página de resultados informa nominal solicitado/adjudicado, precio mínimo, precio medio ex-cupón, precio medio de compra y tipos marginal/medio.[6]
   - La página histórica enlaza resultados individuales por `entryId`; descubrir esos enlaces en cada refresco y no fijar IDs.[7]
   - Son datos de **subasta primaria**: su precio no es el cierre EOD del mercado secundario.[5][6]

3. **No verifiqué un proveedor gratuito de precio EOD por ISIN con derechos de reutilización claros.[unverified]**
   - BME documenta ficheros EOD/históricos, pero el boletín de deuda pública web se limita a resúmenes diarios/mensuales y pide contactar para contenido adicional.[11]
   - SIX documenta API y renta fija de ciclo completo, con precios evaluados diarios o intradía; no encontré tier gratuito ni licencia abierta, así que queda como alternativa sujeta a contrato.[14][15]
   - No sustituir precio por rentabilidad de benchmark ni por rendimiento de subasta.[6][17]

## Fuentes por papel

| Fuente | Endpoint exacto y formato | Cobertura / periodicidad | Acceso, derechos y decisión |
|---|---|---|---|
| **Tesoro — valores en circulación** | `https://tesoro.es/en/deuda-publica/valores-del-tesoro/valores-en-circulacion` — HTML, tablas | Letras y bonos/obligaciones vivos: ISIN, vencimiento, nominal pendiente; referencia de los bonos con cupón; coeficiente de indexación y valor facial donde aplica. La página muestra la fecha efectiva; el saldo cambia en la liquidación correspondiente.[3] | GET público, sin clave observada; cuota no publicada. **Endpoint probado 200.** La página es pública, pero no encontré aquí una licencia explícita de redistribución: conservar fuente/fecha y validar condiciones antes de mostrar masivamente. Fuente preferida para el primer catálogo por ISIN. |
| **Tesoro — XLSX estadístico 01** | Página de índice `https://www.tesoro.es/deuda-publica/estad%C3%ADsticas-mensuales`; enlace actual `https://www.tesoro.es/documents/d/tesoro/01-xlsx` — XLSX/ZIP | Publicación estadística mensual; `01` muestra deuda nominal agregada por año de emisión/buckets (p. ej. Letras, plazos de bonos, divisas), sin ISIN. La misma página publica `11.xlsx` (nominal emitido y rendimientos 2026–2025) y `14.xlsx` (perfil anual de vencimientos), igualmente agregados.[1] | GET público, sin clave ni cuota publicada; `01.xlsx` probado 200. El antiguo patrón `.../sites/default/files/estadisticas/01.xlsx` dio 404; el vínculo Liferay `/documents/d/tesoro/01-xlsx` es el actual. Uso recomendado: reconciliar totales/perfil, no alimentar términos individuales.[1][2] |
| **Tesoro — anuncios de emisión** | Muestra: `https://tesoro.es/en/deuda-publica/noticias/treasury-announces-bonos-and-obligaciones-will-be-issued-october-1st-2026` — HTML | Antes de cada subasta identifica ISIN y características ofertadas; trae cupón, vencimiento, interés corrido, importe de cupón corto y coeficiente de indexación cuando aplica.[5] No asumir que la fecha del anuncio/subasta es la fecha original de emisión si es una reapertura. | GET público; cuota no publicada. **Documentado; la muestra se extrajo**, el flujo completo no se integró. No se encontró API estable: descubrir noticias desde la sección de subastas y guardar el HTML fuente. Derechos de redistribución no aclarados en esta consulta. |
| **Tesoro — resultados de subastas** | Últimas: `https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/obligaciones-del-estado`; históricas: `https://www.tesoro.es/en/deuda-publica/subastas/resultados-subastas-anteriores` — HTML | Resultado por plazo/tipo y fecha: fecha subasta/liquidación/vencimiento, nominal solicitado y adjudicado, precio mínimo, precio medio ex-cupón, precio medio de compra, tipos y ratio de cobertura.[6][7] La página histórica enlaza el resultado específico mediante `entryId` y tipo de instrumento. | GET público; cuota no publicada. **Página de últimas subastas probada 200.** No vi API pública documentada. Unir al ISIN del anuncio/operación correspondiente; conservar por separado precio limpio, importe total de compra e IRR/tipo de subasta. Estos campos no son cotización secundaria EOD. |
| **BOE — sumario diario y documentos** | `GET https://boe.es/datosabiertos/api/boe/sumario/{YYYYMMDD}`; ejemplo probado `https://boe.es/datosabiertos/api/boe/sumario/20261001` — JSON o XML mediante `Accept`; el sumario apunta a documentos HTML/XML/PDF | Un registro por publicación diaria; permite localizar resoluciones/órdenes sobre emisión y extraer condiciones contractuales o fechas de pago desde el documento primario. El BOE publica sumarios todos los días salvo domingos, con excepciones extraordinarias.[9] | GET público sin cuenta/clave; la respuesta fue 200 JSON (285 030 bytes). No se encontró límite de llamadas publicado. La licencia general permite usos comerciales y no comerciales, combinación y obras derivadas, con cita y sin desnaturalizar; algunos documentos pueden tener condiciones especiales, así que excluir los que no se sometan a la licencia general.[10] Excelente fuente documental de confirmación, no catálogo de precios. |
| **ESMA — FIRDS / referencia** | Base candidata probada: `https://registers.esma.europa.eu/solr/esma_registers_firds/select`; se intentó `?q=Id%3A%22ES0000012S22%22&wt=json&rows=3` — se esperaba JSON | Candidato UE para validación de referencia regulatoria por instrumento/ISIN; **esta ronda no confirmó la consulta, el esquema ni los campos**. La prueba devolvió 400, así que no atribuyo cupón, nominal emitido ni calendario a esta respuesta. No confundir el registro de referencia FIRDS con los archivos FITRS de resultados de transparencia: el documento consultado trata de resultados completos/delta, no de precios de cierre.[18] | No se usó credencial; acceso directo no validado (400). Frecuencia, límites y derechos de redistribución de esta consulta quedan sin verificar. Próximo test: obtener del portal de registros ESMA el enlace vigente de fichero completo/delta de **reference data**, descargar un fichero pequeño y contrastar un ISIN español contra Tesoro/BOE; no ingerir hasta validar esquema y términos. |
| **ECB — Securities Issues Statistics (CSEC)** | Ficha y catálogo de series: `https://data.ecb.europa.eu/data/datasets/csec/data-information`; catálogo ZIP/CSV: `https://data.ecb.europa.eu/data/datasets/csec/download`; las observaciones se distribuyen como series temporales SDMX | Agregado de stocks y flujos por país/sector, moneda, tipo de cupón y vencimiento; se compila a partir de datos micro security-by-security de CSDB, pero el producto CSEC publicado son **series agregadas**, no fichas ni flujos por ISIN.[17] Periodicidad mensual, desde 2020-12; primera difusión de t-1 con retraso t+10 días laborables y revisiones retrospectivas de hasta 36 periodos.[17] | Página pública; la consulta al enlace de catálogo expiró a los 40 s sin respuesta HTTP, por lo que no afirmo el formato/descarga observado. Autenticación, cuota y derechos de redistribución no se verificaron. Útil para control macro de nominal por país/tipo/plazo, no para el catálogo ISIN ni el precio EOD. |
| **BME — fin de día/histórico** | `https://www.bolsasymercados.es/en/bme-exchange/prices-and-markets/market-data-services/end-of-day-and-historical-services.html`; boletín enlazado `https://www.bolsasymercados.es/bme-exchange/en/Prices-and-Markets/Statistics/Public-Debt-Trades-Bulletin` — ficheros/boletines | La documentación enumera ficheros EOD e históricos para instrumentos BME; para deuda pública, el contenido publicado en la web es solo resumen diario y mensual. El acceso a contenido adicional requiere contacto.[11] | No requiere clave para leer el documento público, pero no se verificó un feed gratis de precios ISIN ni permiso de redistribución; GET de página desde este entorno falló por validación TLS del certificado, no por respuesta del endpoint. **Candidato de precio EOD solo con oferta/licencia BME explícita**, no dentro del presupuesto cero. |
| **SIX — APIs / renta fija** | Portal API: `https://web.apiportal.six-group.com/portal/bfi/catalog/instrumentBase`; diccionario: `https://web.apiportal.six-group.com/portal/bfi/data-dictionary`; producto: `https://www.six-group.com/dam/download/financial-information/reference-pricing-data/fixed-income-data/six-fixed-income-data.pdf` | Servicio de referencia para instrumentos; brochure de renta fija describe cobertura de ciclo completo desde términos de emisión hasta vencimiento/reembolso y precios evaluados diarios o intradía.[14][15] | No probé un endpoint API de cliente: el portal/documentación pública no reveló un nivel gratuito ni derechos de redistribución. El GET directo a páginas SIX falló por validación TLS en este entorno. **Candidato comercial**, no viable para 0 € hasta confirmar coste, cobertura ISIN español y derecho de exhibición/redistribución. |

## Plan de combinación en PostgreSQL

1. **`security`**: clave `isin`; tipo (letra/bono/obligación/indexado/segregado), emisor/país, cupón/tipo, fecha de emisión, vencimiento, nominal vivo, coeficiente de indexación y valor facial.[3] Seed con Tesoro circulación; extraer cupón de la referencia y marcar el campo como parseado, no como columna fuente independiente.[3]
2. **`security_field_source`** o estructura equivalente: una fila por campo/observación con `source_url`, fecha efectiva publicada, `retrieved_at`, texto/valor original y estado de verificación.[3][5] No colapsar fecha de publicación y fecha a la que se refiere el saldo: el Tesoro informa de saldos que se actualizan por liquidación.[3]
3. **`auction_result`**: evento independiente con fecha de subasta y liquidación, ISIN enlazado desde el anuncio, nominal solicitado/adjudicado, precio ex-cupón, precio de compra y tipos marginal/medio. Mantener los resultados de subasta como precio/tipo primario, no como `market_eod_quote`.[5][6][7]
4. **`cashflow`**: no inventar fechas de cupón desde solo el vencimiento.[4]
   Tesoro describe pago anual para bonos/obligaciones, pero hay que resolver la fecha inicial, cupones cortos y términos no estándar por resolución/folleto; guardar fecha/importe y fuente documental por flujo.[4][5][9]
5. **`market_eod_quote`**: tabla vacía hasta contratar/probar un feed por ISIN con licencia de exhibición.[11][15]
   No rellenarla con rendimiento de bono benchmark, estadística mensual, precio de subasta ni precio teórico.[6][17]
   Si se licencia BME/SIX, conservar fuente, mercado, divisa, fecha de cierre y tipo de precio (clean/dirty/evaluated).[11][15]
6. **Refresco**:
   - Consultar Tesoro circulación semanal o tras liquidaciones/subastas y guardar el `as-of` que publica.[3]
   - Usar XLSX estadístico mensual para reconciliar.[1]
   - Recorrer resultados históricos por los enlaces vigentes.[7]
   - Consultar BOE por fecha de publicación para documentos nuevos.[9]
   - Usar ECB mensual para contraste agregado.[17]
   - Activar ESMA solo tras resolver feed y términos.[18]
   - Incorporar precios BME/SIX solo tras resolver endpoint y licencia.[11][15]

## Límites de esta ronda

Probé GET de Tesoro XLSX, página de valores vivos y resultados recientes.[2][3][6]
El sumario BOE devolvió 200 JSON.[9]
La query directa de ESMA devolvió 400.[unverified]
Los GET directos de BME/SIX fallaron por validación TLS del cliente; sus páginas se evaluaron mediante documentación oficial, no con cotización descargada.[unverified]
El GET al catálogo CSEC expiró sin estado HTTP.[unverified]
No se probó cotización EOD individual ni se confirmó licencia gratuita de redistribución.[11][14][15]

## Sources

[1] https://www.tesoro.es/deuda-publica/estad%C3%ADsticas-mensuales — Tesoro: estadísticas mensuales
[2] https://www.tesoro.es/documents/d/tesoro/01-xlsx — Tesoro: XLSX nominal en circulación
[3] https://tesoro.es/en/deuda-publica/valores-del-tesoro/valores-en-circulacion — Tesoro: valores en circulación
[4] https://tesoro.es/deuda-publica/los-valores-del-tesoro/bonos-y-obligaciones-del-estado — Tesoro: bonos y obligaciones
[5] https://tesoro.es/en/deuda-publica/noticias/treasury-announces-bonos-and-obligaciones-will-be-issued-october-1st-2026 — Tesoro: anuncio de emisión, 1 octubre 2026
[6] https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/obligaciones-del-estado — Tesoro: últimas subastas de obligaciones
[7] https://www.tesoro.es/en/deuda-publica/subastas/resultados-subastas-anteriores — Tesoro: resultados históricos de subastas
[9] https://boe.es/datosabiertos/faq/boe.php — BOE FAQ reutilización
[10] https://www.boe.es/informacion/aviso_legal/index.php — BOE: condiciones de reutilización
[11] https://www.bolsasymercados.es/en/bme-exchange/prices-and-markets/market-data-services/end-of-day-and-historical-services.html — BME: servicios EOD e históricos
[14] https://www.six-group.com/en/products-services/financial-information/delivery-methods/api.html — SIX: APIs financieras
[15] https://www.six-group.com/dam/download/financial-information/reference-pricing-data/fixed-income-data/six-fixed-income-data.pdf — SIX: datos de renta fija
[17] https://data.ecb.europa.eu/data/datasets/csec/data-information?destination=/data/datasets/csec/data-information — ECB: CSEC Securities Issues Statistics
[18] https://esma.europa.eu/sites/default/files/2023-12/ESMA65-8-5240_FIRDS_Transparency_Download_Instructions.pdf — ESMA: descargas FITRS transparency results
