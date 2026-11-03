# Deuda pública española: fuentes, endpoints y límites de comparación

**Consulta:** 26 de octubre de 2026. **Alcance:** Letras, Bonos y Obligaciones del Estado; fuentes públicas y reutilización educativa. No se construyó ni publicó una aplicación.

## Conclusiones ejecutivas

- **Mercado primario:** el Tesoro publica calendario y resultados por subasta en páginas HTML; el BOE publica resoluciones oficiales detalladas. Los GETs a páginas del Tesoro respondieron como HTML y la frecuencia de publicación es por subasta, no diaria.[1][3][7]
- **Mejor feed gratuito para series automatizables:** el Banco de España (BdE) ofrece API JSON (`favoritas`, `listaSeries`) y CSV con series de rendimientos secundarios por plazo y tipos de Letras adjudicados.[8][9][10]
- Son observaciones estadísticas fechadas, no un precio vigente de una referencia/ISIN ni una oferta ejecutable.[11]
- **BCE:** su API SDMX ofrece curvas estimadas diarias del área del euro.[13][14][15]
- El BCE también publica el tipo español de convergencia a 10 años, mensual.[16]
- La curva modelizada no es cotización de un título español concreto y los datos del dataset FM pueden estar sujetos a licencias restrictivas.[14][17]
- En esta revisión no se encontró una fuente gratuita oficial de bid/ask ejecutable por ISIN; el BdE publica rendimientos agregados y BME identifica el mercado AIAF, pero no se confirmó un feed abierto por título.[10][11][20]
- La curva del BCE tampoco sustituye un precio específico.[14]

## Fuentes oficiales y endpoints

| Fuente | Endpoint/serie | Qué entrega, unidad y frecuencia | Evaluación |
|---|---|---|---|
| **Tesoro — últimas subastas** | [`/resultado-ultimas-subastas/letras-del-tesoro`](https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/letras-del-tesoro), [`/bonos-del-estado`](https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/bonos-del-estado) | Tablas por plazo con fecha de subasta, vencimiento, liquidación, nominal solicitado/adjudicado, precio y tipos marginal/medio; nominales en **millones de euros**, precio y tipos en **porcentaje**. Actualización al publicarse cada subasta.[1][2] | Fuente primaria. El dato describe el resultado de esa subasta; no permanece como precio disponible para comprar después. GET probado: `200 text/html`.[1][2] |
| **Tesoro — calendario** | [`/deuda-publica/subastas/calendario`](https://www.tesoro.es/deuda-publica/subastas/calendario) | Fechas por producto; para Letras incluye vencimiento/amortización, fechas límite de peticiones, pagos y emisión. Es calendario anual, no serie de tipos.[3] | Útil para alertas y fechas; usar la fecha efectiva publicada, no extrapolar periodicidades. El Tesoro describe Letras generalmente en martes y Bonos/Obligaciones el primer y tercer jueves, pero el calendario anual manda.[3][6] |
| **Tesoro — historial y especificaciones** | [`/resultados-subastas-anteriores`](https://www.tesoro.es/deuda-publica/subastas/resultados-subastas-anteriores); páginas de [Letras](https://www.tesoro.es/deuda-publica/los-valores-del-tesoro/letras-del-tesoro) y [Bonos/Obligaciones](https://tesoro.es/deuda-publica/los-valores-del-tesoro/bonos-y-obligaciones-del-estado) | Historial navegable por subasta. Letras: 3, 6, 9 y 12 meses, descuento/prima, reembolso de 1.000 € por unidad y petición mínima de 1.000 €, en múltiplos de 1.000. Bonos/Obligaciones: plazo mayor de 2 años, cupón anual; mínimo nominal de petición/negociación 1.000 €. [4][5][29] | El historial y las fichas son páginas web; la petición mínima no debe confundirse con el tamaño de un precio cotizado. Letras usa convención ACTUAL/360 para expresar el tipo efectivo anual.[4][6] |
| **BOE — resolución de resultados** | Ejemplo: [`BOE-A-2026-21773`](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-21773) | Resolución jurídica de la subasta de Letras a 6 y 12 meses celebrada el 6/10/2026, emitidas el 9/10/2026: nominales, vencimientos, tipos máximos/medios y precios. Nominal en millones de euros; precios y tipos en porcentaje.[7] | Fuente de contraste y archivo oficial detallado. Es publicación por resolución; no una cotización en curso. |
| **BdE — API JSON** | `GET https://app.bde.es/bierest/resources/srdatosapp/favoritas?idioma=es&series=<códigos>`; `GET https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=es&series=<códigos>&rango=3M` | `favoritas` devuelve último valor, fecha, frecuencia, unidad/decimales y descripción. `listaSeries` devuelve fechas, valores e información de serie; para diaria admite rangos 3M/12M/36M. Frecuencia `D` significa diaria, pero debe conservarse `fechaValor` y manejar fechas sin dato.[8] | API documentada por el BdE, sin registro en los endpoints probados. Mejor opción para una actualización automatizada de series estadísticas, con control de último día publicado y valores ausentes.[8][24][25] |
| **BdE — CSV y catálogo** | [`ti_1_3.csv`](https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/ti_1_3.csv) (secundario); [`catalogo_ti.csv`](https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/catalogo_ti.csv) (metadatos) | CSV de series por fecha. El catálogo asigna código, descripción, fuente, unidad, decimales y frecuencia. Para resultados de subasta, el catálogo identifica series `D_DTED...` y el archivo `TI_1_4.csv`; se pueden solicitar también por `listaSeries`.[9][10] | CSV público probado; encabezado distingue los códigos. El catálogo marca la serie de 10 años `D_G0B1F0ZP` como diaria, porcentaje, media ponderada, operaciones simples al contado; no implica cotización de un ISIN.[9][10] |
| **BCE — API SDMX** | `https://data-api.ecb.europa.eu/service/data/{FLOW}/{KEY}?lastNObservations=N&format=csvdata` | API SDMX 2.1. Permite CSV/JSON/XML, rangos temporales y observaciones recientes. Series concretas abajo. | Endpoint público probado con HTTP 200 para YC e IRS; las claves/códigos de dimensión son parte esencial del dato, no deben tratarse como etiquetas autoexplicativas.[13][26][27] |
| **BCE — curva diaria del área del euro** | [Serie 10Y AAA](https://data.ecb.europa.eu/data/datasets/YC/YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y); API: `.../service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y?lastNObservations=5&format=csvdata` | Tipo spot 10 años **AAA del área del euro**, unidad porcentaje anual, diaria por días hábiles. Curva cero cupón estimada; el BCE deriva curvas forward y par. Actualización objetivo al mediodía CET en días hábiles TARGET, con posibles retrasos.[14][15][26] | Buena referencia de curva común; no representa España ni una obligación concreta. El BCE advierte que no debe utilizarse para calcular cotizaciones precio/rentabilidad ni para identificar oportunidades de negociación.[14] |
| **BCE — rentabilidad española de convergencia** | [Serie `IRS.M.ES.L.L40.CI.0000.EUR.N.Z`](https://data.ecb.europa.eu/data/datasets/IRS/IRS.M.ES.L.L40.CI.0000.EUR.N.Z); API: `.../service/data/IRS/M.ES.L.L40.CI.0000.EUR.N.Z?lastNObservations=3&format=csvdata` | España, deuda emitida, categoría 10 años, promedio de observaciones del periodo, **mensual**, porcentaje; fuente ESCB.[16][27] | Referencia para convergencia/comparación macro, no una cotización diaria ni un ISIN. En la consulta API, septiembre de 2026 devolvió 3,927 %.[16][27] |
| **BCE — dataset FM** | [Metadatos FM](https://data.ecb.europa.eu/data/datasets/FM/data-information) | Contiene datos de mercados financieros; frecuencia de recogida diaria y, cuando corresponda, precios/yields bid y ask.[17] | Advertencia material: el BCE indica que los datos obtenidos en MDP pueden estar sometidos a licencias que impiden su difusión fuera del BCE/SEBC. No asumir permiso de redistribución comercial o pública.[17] |
| **Eurostat — 10 años** | Dataset `irt_lt_gby10_m`; endpoint probado: `.../statistics/1.0/data/irt_lt_gby10_m?geo=ES&lang=en&sinceTimePeriod=2026-06` | Dataset de rendimientos de bonos a 10 años, mensual.[18][28] | La respuesta API fue HTTP 200 pero sin observaciones para `geo=ES` (`size` de dimensión geo = 0); no lo recomendaría como feed español sin corregir/verificar el mapeo. La serie histórica `irt_h_cgby` está marcada por Eurostat como no actualizada.[19][28] |
| **BME AIAF — deuda pública** | [Página AIAF Deuda Pública](http://www.bmerf.es/esp/aspx/comun/posiciones.aspx?Mercado=SDP) | La página de BME identifica negociación de Bonos/Obligaciones y publica referencias a “emisiones en circulación” y “boletín diario”.[20] | Vía potencial para investigación de mercado secundario; en esta revisión no se comprobó un endpoint abierto de precios/quotes, su formato ni licencia de reutilización. No presentarlo como API de cotización validada. |

### Códigos BdE útiles

- **Mercado secundario (rentabilidad por plazo):** `D_DTES00B7` (Letras 1–3 meses), `D_DTES00S7` (6 meses), `D_DTES00T7` (6–12 meses), `D_DTES00U7` (1 año), `D_G0B1F0ZN` (Bonos 3 años), `D_G0B1F0ZO` (5 años), `D_G0B1F0ZP` (Obligaciones 10 años). La serie de 10 años se describe como media ponderada de operaciones al contado y no segregadas; su unidad es porcentaje y su frecuencia diaria.[9][10][25]
- **Mercado primario (tipo de Letras):** `D_DTED0C0G` (3 meses), `D_DTED0E0G` (6), `D_DTED0I0G` (9), `D_DTED0G0G` (12). El catálogo las clasifica como series de mercado primario y frecuencia `D`.[10]

No debe suponerse que `fechaValor` sea la fecha de subasta: en la solicitud probada varios tipos aparecían con `fechaValor` 23/10/2026, mientras que las últimas subastas por plazo mostradas por el Tesoro fueron 6 y 13/10.[1][24]

No se verificó si ese campo representa fecha estadística, de publicación o emisión; para enlazar resultados de un evento usar calendario/resolución del Tesoro/BOE.[8][24]

## Solicitudes públicas probadas

Todas fueron GET de lectura; no se enviaron órdenes ni se modificaron datos.

1. **Tesoro últimas Letras:** HTTP `200`, `text/html`. La tabla mostraba subastas de 13/10/2026 (3 y 9 meses) y 06/10/2026 (6 y 12 meses), con vencimiento, liquidación, nominal, precio y tipos.[1]
2. **BdE `favoritas`:** HTTP `200`, JSON comprimido (`gzip`), sin autenticación. La respuesta incluyó 11 series. Ejemplos: `D_G0B1F0ZP` = 4,07 % con fecha 22/10/2026; `D_DTES00S7` = 2,83 % con fecha 19/10/2026; tipos primarios de Letras de 3/6/9/12 meses = 2,645/2,798/2,968/3,026 % con fecha 23/10/2026.[24] La diferencia de fechas confirma que hay que mostrar “a fecha de”, no asumir sincronización intradía.[24]
3. **BdE `listaSeries`:** HTTP `200`, JSON. La serie 10 años declara “datos diarios”, unidad porcentaje y último valor 4,07 % al 22/10/2026; el rango de 3 meses devuelve fechas con `null` entre observaciones.[25]
4. **BdE CSV:** `ti_1_3.csv` devolvió HTTP `200`, `text/csv`; el encabezado contiene códigos secundarios como `D_G0B1F0ZP`. El catálogo CSV devuelve metadatos de tipo, frecuencia y fuente.[9][10]
5. **BCE API YC e IRS:** ambos GET devolvieron HTTP `200`, `text/csv`. La curva AAA 10 años devolvió 3,3844008945 % para 22/10/2026; la serie española IRS devolvió 3,927 % para 2026-09.[26][27]
6. **Eurostat `irt_lt_gby10_m`:** HTTP `200`, JSON, pero `geo=ES` no devolvió datos en la respuesta consultada.[28]
7. **Página HTML del Tesoro:** la respuesta fue HTTP `200` y `text/html`, no JSON. No se localizó una API pública estructurada documentada del Tesoro en las páginas oficiales examinadas.[1][2][3]

## Qué sí permite comparar y qué no

### Rentabilidad de subasta

Una subasta da el coste/rendimiento de emisión para esa fecha, vencimiento y condiciones. En la subasta de Letras a 6 meses del 6/10/2026 el BOE publicó 2,798 % máximo aceptado, 2,769 % medio ponderado y precios equivalentes 98,606 y 98,620; la emisión fue 9/10/2026 y el vencimiento 9/04/2027.[7] Es buen dato histórico para contrastar subastas del mismo plazo y para una simulación educativa de suscripción; no es un precio al que comprar hoy.[1][7]

En Bonos/Obligaciones el resultado separa precio medio **ex-cupón** y precio medio de compra. En el resultado mostrado por Tesoro, el plazo de 3 años da precio medio ex-cupón 95,212 y precio de compra 95,842, con tipo medio 3,430 %; el de 5 años muestra 85,704 y 85,984, con tipo medio 3,558 %.[2] No comparar sólo el cupón nominal: el precio, cupón corrido, fecha de liquidación y flujos futuros determinan la rentabilidad efectiva.[5][6]

### Rentabilidad secundaria y cotización

Las series BdE secundarias son promedios/rendimientos por intervalos de vencimiento calculados con operaciones del mercado. Sirven para ver tendencia y una curva aproximada por plazo, pero no identifican precio comprador/vendedor actual de un ISIN ni garantizan que una operación pueda hacerse a ese rendimiento.[10][11] Una obligación “a 10 años” de la serie BdE tampoco equivale necesariamente a cualquier Bono/Obligación con aproximadamente diez años hasta amortización: se deben respetar definición y ventana de vencimiento de la serie.[10]

### Tipos de referencia

La curva YC del BCE es modelizada y corresponde al conjunto del área del euro.[14][15]

La IRS española es una media mensual de convergencia a diez años.[16]

Ambas sirven como referencias agregadas, no como cotización individual.[14][16]

Los tipos oficiales del BCE (facilidad de depósito, refinanciación, crédito) son tipos de política monetaria, no rendimientos de Letras o Bonos soberanos.[23]

El antiguo dataset Eurostat `irt_h_cgby` no debe usarse como feed actual; su metadata dice que dejó de actualizarse.[19]

Para una simulación de compra secundaria que no induzca a error faltaría obtener, como mínimo, **ISIN, precio de compra específico y su fecha/hora, clean/dirty price y cupón corrido, fecha de liquidación, flujos/cupones, vencimiento, comisiones y fiscalidad**; los agregados BdE y las curvas BCE no aportan por sí solos esa ficha de compra individual.[10][14][20]

Si no hay precio individual, rotular el valor BdE/BCE como **referencia estadística indicativa**, no “precio actual”, “rentabilidad contratada” ni “cotización de compra”.[14][17]

La rentabilidad a vencimiento depende del precio y de los flujos futuros; no equivale al cupón nominal.[2][5]

## Licencia, límites y código abierto

- **BdE:** estadísticas disponibles sin coste; exige preservar integridad/significado, citar Banco de España, indicar fecha de actualización cuando esté disponible y asumir responsabilidad de uso. No cubre datos de terceros y no garantiza continuidad sin interrupciones.[12]
- **BCE:** distinguir YC/IRS públicos de `FM` y sus datos de mercado licenciados. El BCE limita expresamente el propósito de la curva YC: no calcular cotizaciones ni identificar oportunidades; confirmar condiciones antes de redistribuir datos del dataset FM.[14][17]
- **Tesoro/BME/Eurostat:** no se validó una licencia de API/reutilización masiva para las tablas HTML del Tesoro ni para los datos de mercado BME consultados. Revisar aviso legal y condiciones de cada fuente antes de replicar o redistribuir datos; el acceso web público no basta para inferir una licencia de feed.[1][2][20]
- **Implementación genérica:** `pandaSDMX` (Apache-2.0) implementa SDMX y soporta proveedores como BCE y Eurostat; no resuelve claves, semántica financiera ni derechos de datos.[21]

`ecb-mcp` (MIT) adapta el API del BCE a un servidor MCP y puede ser útil para consultas de Pai, pero es comunitario y debe evaluarse antes de depender de él en producción.[22]

No se localizó un cliente oficial ni una biblioteca mantenida específica para extraer las subastas del Tesoro en la búsqueda acotada; las páginas oficiales examinadas son HTML.[1][2][3]

## Recomendación para Paideia

Usar Tesoro/BOE para **calendario, características y resultados del primario**.[1][3][7]

Usar BdE para **series históricas de rendimientos por plazo** y guardar la fecha observada devuelta por el API.[8][10][11]

Usar BCE IRS/YC sólo como **referencias separadas y claramente etiquetadas**.[14][16]

En cada registro guardar proveedor, código/ISIN si existe, tipo de serie, unidad, frecuencia declarada, fecha de observación, fecha de consulta y URL.[8][13]

Actualizar las páginas del Tesoro según calendario/eventos, no anunciar que sus tipos se actualizan a diario; para BdE mostrar la última fecha realmente publicada y tolerar retrasos/ausencias.[3][6][8]

No afirmar “precio de contratación” mientras no exista una fuente de precio individual y una licencia válida para mostrarlo.[14][17][20]

## Sources

[1] https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/letras-del-tesoro — Tesoro — últimas subastas de Letras
[2] https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/bonos-del-estado — Tesoro — últimas subastas de Bonos y Obligaciones
[3] https://www.tesoro.es/deuda-publica/subastas/calendario — Tesoro — calendario anual de subastas
[4] https://www.tesoro.es/deuda-publica/los-valores-del-tesoro/letras-del-tesoro — Tesoro — características de Letras
[5] https://tesoro.es/deuda-publica/los-valores-del-tesoro/bonos-y-obligaciones-del-estado — Tesoro — características de Bonos y Obligaciones
[6] https://www.tesoro.es/deuda-publica/preguntas-frecuentes — Tesoro — preguntas frecuentes de subastas
[7] https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-21773 — BOE — resultados oficiales subasta de Letras
[8] https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html — Banco de España — API estadística
[9] https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/ti_1_3.csv — Banco de España — series CSV secundario
[10] https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/catalogo_ti.csv — Banco de España — catálogo de series de tipos
[11] https://datos.bde.es/datos/es/datasets/000/035.html — Banco de España — ficha Síntesis de indicadores
[12] https://bde.es/wbe/en/estadisticas/recursos/terminos/terminos-de-uso.html — Banco de España — términos de reutilización
[13] https://data.ecb.europa.eu/help/api/data — BCE — API de datos SDMX
[14] https://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_area_yield_curves/html/index.es.html — BCE — metodología, frecuencia y aviso curvas
[15] https://data.ecb.europa.eu/data/datasets/YC/YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y — BCE — serie curva spot AAA 10 años
[16] https://data.ecb.europa.eu/data/datasets/IRS/IRS.M.ES.L.L40.CI.0000.EUR.N.Z — BCE — tipo largo español de convergencia
[17] https://data.ecb.europa.eu/data/datasets/FM/data-information — BCE — dataset FM y licencias
[18] https://ec.europa.eu/eurostat/cache/metadata/en/irt_lt_gby10_esms.htm — Eurostat — metadatos 10 años
[19] https://ec.europa.eu/eurostat/cache/metadata/en/irt_h_cgby_esms.htm — Eurostat — serie histórica no actualizada
[20] http://www.bmerf.es/esp/aspx/comun/posiciones.aspx?Mercado=SDP — BME — AIAF Deuda Pública
[21] https://github.com/dr-leo/pandaSDMX — pandaSDMX — cliente SDMX
[22] https://github.com/scka-de/ecb-mcp — ecb-mcp — MCP comunitario
[23] https://data.ecb.europa.eu/data/data-categories/ecbeurosystem-policy-and-exchange-rates/official-interest-rates — BCE — tipos oficiales de política monetaria
[24] https://app.bde.es/bierest/resources/srdatosapp/favoritas?idioma=es&series=D_DTES00B7,D_DTES00S7,D_DTES00T7,D_DTES00U7,D_G0B1F0ZN,D_G0B1F0ZO,D_G0B1F0ZP,D_DTED0C0G,D_DTED0E0G,D_DTED0I0G,D_DTED0G0G — Banco de España API — datos observados deuda
[25] https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=es&series=D_G0B1F0ZP&rango=3M — Banco de España API — serie diaria 10 años
[26] https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y?lastNObservations=5&format=csvdata — BCE API — solicitud real curva 10 años
[27] https://data-api.ecb.europa.eu/service/data/IRS/M.ES.L.L40.CI.0000.EUR.N.Z?lastNObservations=3&format=csvdata — BCE API — solicitud real España 10 años
[28] https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/irt_lt_gby10_m?geo=ES&lang=en&sinceTimePeriod=2026-06 — Eurostat API — solicitud de prueba geo ES
[29] https://www.tesoro.es/deuda-publica/subastas/resultados-subastas-anteriores — Tesoro — resultados de subastas anteriores
