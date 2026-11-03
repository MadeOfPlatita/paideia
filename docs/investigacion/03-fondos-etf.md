# 03 — Fondos y ETF para Paideia

**Corte de investigación: 26-10-2026.** La investigación se acotó a fuentes primarias de CNMV, Vanguard, BlackRock/iShares y Amundi.[1][3][5]
Se extrajeron documentos oficiales y se probaron dos endpoints públicos mediante solicitudes de lectura.[6][7]
El alcance no permite concluir cobertura exhaustiva del mercado ni disponibilidad minorista en España.[2][3][8]

## Conclusión ejecutiva

En el conjunto limitado de fuentes y pruebas consultadas **no se validó un proveedor único agregado** que cubra catálogo, atributos/KID, costes, riesgo, NAV y precios, con derechos de acceso y redistribución verificados.[1][5][6]
Stooq no devolvió un CSV utilizable y la prueba de Yahoo se limitó a un ticker.[6][7]
Ninguna de las dos llamadas verificó licencia, cuotas o uso comercial.[6][7]

Para el comparador, identificar cada producto por **ISIN de la clase**, no por ticker.[1][8]
Mantener separados nombre del fondo y clase, acumulación/distribución, condición UCITS/OICVM y domicilio, divisa base/de clase, divisa de negociación, cobertura de divisa y cada bolsa/ticker.[3][8]
La ficha de Vanguard muestra una clase acumulativa USD con ISIN IE00BK5BQT80 y líneas en bolsas/divisas distintas, incluida VWCE en EUR en Deutsche Börse.[3][4]
Por tanto, ticker y moneda de cotización no sustituyen al ISIN ni bastan para describir la divisa de la clase o su cobertura.[3][8]

## Qué verifican las fuentes oficiales

- **CNMV / DFI.** La CNMV indica que el DFI identifica el fondo, incluye ISIN y gestora, y permite consultar información relevante para comparar productos.[1]
  La página describe un perfil de riesgo en escala 1–7 y gastos corrientes TER.[1]
  Para el esquema de Paideia, guardar clase, documento y fecha de cada cifra es más seguro que asumir que un campo estático sirve para todas las clases.[1]
- **KID PRIIPs de BlackRock/iShares.** El documento español para *iShares Core MSCI Europe UCITS ETF EUR (Acc)* identifica la clase EUR acumulativa con ISIN **IE00B4K48X80**, como OICVM/ETF OICVM; la fecha del documento es **03-09-2026**.[8]
  El indicador resumido de riesgo del KID es **4/7** y puede cambiar.[8]
  Los costes se separan en **0,12 % anual** de gestión y costes administrativos/operativos y **0,01 %** estimado de costes de operación.[8]
  Conservar ambos componentes y no fusionarlos bajo una etiqueta genérica de TER.[8]
  El KID también advierte que el precio de mercado secundario puede diferir del valor de las acciones.[8]
- **Vanguard.** La ficha del *FTSE All-World UCITS ETF* identifica la clase acumulativa en USD, ISIN **IE00BK5BQT80**, UCITS domiciliado en Irlanda y OCF de **0,14 %**.[3]
  En esa ficha, VWCE.DE aparece en EUR en Deutsche Börse y se enumeran otras líneas de negociación.[3]
  La ficha está fechada **31-08-2026** y restringe su uso a inversores profesionales, por lo que no sustituye al KID/DFI para una experiencia minorista.[3]
  El KIID separado consultado confirma la denominación de clase USD acumulativa; se conserva como KIID y no se equipara automáticamente al KID PRIIPs español.[4]
- **Amundi.** La ficha mensual de *Amundi Prime Global UCITS ETF Acc* (ISIN **IE0009DRDY20**) declara UCITS, clase acumulativa y moneda de referencia USD.[5]
  La ficha relaciona el SRI 4/7 con el KID y publica “management fees and other administrative or operating costs” de **0,05 %**.[5]
  Muestra VL de **45,84 USD** y AUM a **31-08-2026**, y declara frecuencia de cálculo NAV diaria.[5]
  El archivo es una ficha fechada para inversores profesionales, no una API ni un histórico NAV probado.[5]
  La ficha remite al KID para el conjunto completo de costes.[5]

**No equiparar etiquetas de costes.** CNMV usa TER, Vanguard publica OCF y Amundi presenta gastos de gestión y otros gastos administrativos/operativos.[1][3][5]
El KID de BlackRock separa los costes recurrentes de los costes de operación.[8]
Guardar el nombre exacto, valor, clase, moneda, fecha y documento de origen; comparar cifras solo cuando la definición y el periodo sean compatibles.[1][5][8]

**Riesgo KID.** La CNMV señala que el nivel 1 no significa ausencia de riesgo.[1]
El KID de BlackRock advierte que su 4/7 no está garantizado y puede cambiar.[8]
La ficha Vanguard informa SRRI 6, mientras que la ficha de Amundi presenta SRI 4/7; conservar etiqueta y documento, en vez de tratarlos como una clasificación homogénea sin verificar su metodología.[3][5]

## NAV y precio negociado: campos distintos

La página de iShares consultada mostraba VL de **103,45 EUR a 23-10-2026**.[2]
La ficha de Amundi publica NAV/AUM a **31-08-2026** y dice que el cálculo NAV es diario.[5]
Son valores publicados en páginas/fichas con fecha efectiva, no prueba de API pública de NAV diario o serie histórica reutilizable.[2][5]

El KID de iShares advierte que el precio de mercado secundario puede diferir del valor de las acciones.[8]
Por ello, una cotización de bolsa obtenida por ticker debe etiquetarse como precio de mercado y no como VL/NAV.[6][8]

## Pruebas de endpoints públicos

| Endpoint | Resultado observado | Estado y límite |
|---|---|---|
| Yahoo Finance chart, `VWCE.DE`, rango 5 días y frecuencia diaria | GET HTTPS de solo lectura, sin credenciales; HTTP 200, `application/json`. La respuesta incluyó `currency=EUR`, `symbol=VWCE.DE`, `exchangeName=GER`, `instrumentType=ETF`, `regularMarketPrice=170.0` y campos OHLCV con cinco marcas temporales (20, 21, 22, 23 y 26-10-2026). Es **precio de mercado**; la respuesta no proporcionó ISIN, TER/OCF, KID/SRI ni un campo NAV identificado como tal.[6] | **Endpoint probado** para un ticker y una consulta. No se verificaron documentación contractual, límites/cuotas, continuidad, cobertura, licencia de visualización/redistribución ni capacidad para 100 usuarios. Una respuesta sin clave no equivale a permiso comercial ni a un feed gratuito autorizado. |
| Stooq daily CSV, `vwce.de` | HTTP 200, pero el cuerpo fue HTML con un aviso de verificación JavaScript (“This site requires JavaScript to verify your browser”), no un CSV utilizable.[7] | **No probado como feed de datos** en este entorno. No se repitió la llamada; se cambió a Yahoo para completar una prueba alternativa. |

## Recomendación de implementación para el MVP

1. Crear una lista inicial pequeña de clases verificadas por ISIN y adjuntar KID/DFI, ficha, fecha y URL a cada atributo.[1][8]
   La muestra confirma campos útiles de fondos UCITS, pero no prueba que cada clase esté distribuida para minoristas en España.[3][8]
2. Conservar **cifras documentales** (clase, costes, riesgo, divisa y NAV publicado) separadas de **cotizaciones** (bolsa/ticker, moneda, OHLCV y marca temporal).[6][8]
   Mostrar origen, fecha efectiva y tipo de precio; marcar datos caducados o no disponibles en lugar de sustituir NAV por precio de bolsa.[2][5][6]
3. Tratar Yahoo solo como candidato técnico para un prototipo de un ticker.[6]
   Antes de mostrar o cachear sus datos para usuarios, resolver términos, licencia, cuotas y redistribución con el proveedor; una respuesta HTTP 200 no resuelve esos puntos.[6]
   No inferir cobertura ni capacidad para 100 usuarios de una llamada aislada.[6]
4. Si Paideia necesita comparar condiciones accionables, validar por separado KID/folletos vigentes y elegibilidad/distribución en España.[1][8]
   En esta investigación no se confirmó una fuente única que entregue y licencie todos esos datos.[1][5][6]

## Sources

[1] https://www.cnmv.es/portal/inversor/fondos-dfi?lang=es — CNMV — Documento de datos fundamentales (DFI)
    > "Muestra denominación del fondo, código ISIN, Nº de registro en CNMV e identificación de la gestora."
    > "Por un lado se incluye el indicador de los gastos corrientes TER (Total expense ratio) como media de los gastos totales que soporta el fondo."
    > "Ofrece un dato indicativo del riesgo del fondo en una escala de 1 a 7 niveles."
[2] https://www.blackrock.com/es/profesionales/productos/251861/ishares-msci-europe-ucits-etf-acc-fund — BlackRock iShares Core MSCI Europe EUR Acc — página de producto
    > "Valor liquidativo a 23 oct 2026 EUR 103,45"
[3] https://fund-docs.vanguard.com/FTSE_All-World_UCITS_ETF_USD_Accumulating_9679_EU_INT_UK_EN.pdf — Vanguard FTSE All-World USD Acc — factsheet 31-08-2026
    > "Ongoing Charges Figure†          0.14%"
    > "Deutsche Börse EUR VWCE BJVR0R9 VWCE.DE"
[4] https://fund-docs.vanguard.com/ie00bk5bqt80-en.pdf — Vanguard FTSE All-World USD Acc — KIID
    > "**(USD) Accumulating Shares**"
[5] https://www.amundietf.com/pdfDocuments/monthly-factsheet/IE0009DRDY20/ENG/LUX/INSTITUTIONNEL/ETF/20260831 — Amundi Prime Global UCITS ETF Acc — factsheet 31-08-2026
    > "We have classified this product as 4 out of 7, which is a medium risk class."
    > "Management fees and other administrative or operating costs * 0.05%"
    > "NAV and AUM as of 31/08/2026"
    > "Frequency of NAV calculation Daily"
[6] https://query1.finance.yahoo.com/v8/finance/chart/VWCE.DE?range=5d&interval=1d — Yahoo Finance chart endpoint — prueba VWCE.DE
    > "Vanguard FTSE All-World UCITS ETF USD Accumulation"
[7] https://stooq.com/q/d/l/?s=vwce.de&i=d — Stooq daily CSV endpoint — prueba VWCE.DE
    > "This site requires JavaScript to verify your browser."
[8] https://www.blackrock.com/es/profesionales/literature/kiid/eu-priips-ishares-core-msci-europe-ucits-etf-eur-acc-ie00b4k48x80-es.pdf — BlackRock iShares Core MSCI Europe EUR Acc — PRIIPs KID 03-09-2026
    > "Hemos clasificado este producto en la clase de riesgo 4 en una escala de 7"
    > "0.12% del valor de su inversión al año."
    > "El precio de mercado vigente al que se negocian las acciones en el mercado secundario puede diferir del valor de las Acciones."
    > "El Fondo es un OICVM de tipo fondo cotizado, un «ETF OICVM»."
    > "La moneda base del Fondo es el euro."
    > "iShares Core MSCI Europe UCITS ETF EUR (Acc)"
    > "La fecha de este documento es 03 septiembre 2026."
    > "0.01% del valor de su inversión al año."
