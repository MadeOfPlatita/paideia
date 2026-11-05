# Transcripción de condiciones — 2026-11-05

Transcripción literal de condiciones de producto desde páginas oficiales, con URL, título y fecha de consulta en cada dato. Documento de trabajo: **no se ha integrado nada en la aplicación** ni se ha modificado `data/condiciones.json`.

## Cifras

| Métrica | Valor |
|---|---|
| Candidatos en `docs/validacion-04/05-catalogo/candidatos.json` | 20 |
| Candidatos con condiciones ya transcritas en `data/condiciones.json` | 2 (DEP-02, DEP-03) |
| Candidatos transcritos en este documento | 18 |
| — completos (`ok`) | 10 |
| — parciales (`parcial`) | 8 |
| — sin fuente (`sin_fuente`) | 0 |
| Condiciones registradas | 223 |
| URLs de fuente distintas | 21 |
| Fuentes oficiales / secundarias | 223 / 0 |

**Corrección de alcance:** `data/condiciones.json` tiene 4 registros, pero dos (`DEP-EBN-12`, `DEP-SELF-12`) no son candidatos del catálogo. Solo DEP-02 y DEP-03 coinciden con `candidatos.json`, así que los candidatos sin condiciones eran **18, no 16**. Se han cubierto los 18.

## Estado por candidato

`ok` = están publicados todos los campos decisivos de condición (tipo, plazo, límites, liquidación, comisiones y garantía o riesgo). `parcial` = identidad y parte de las condiciones, con algún campo decisivo ausente. `sin_fuente` = ninguna página oficial accesible documenta el producto.

| ID | Producto | Estado | Cond. | Qué falta |
|---|---|---|---:|---|
| ACC-01 | Cuenta Contigo | ok | 13 | Modal de condiciones de nuevos clientes no accesible (se carga por JS). El PDF de `primary_url` está caducado (vigente hasta 20/10/2026) y solo se usa para cláusulas estructurales. Falta confirmación contractual de la liquidación mensual. |
| ACC-02 | Cuenta corriente remunerada | ok | 15 | Falta el TIN de los tramos 1,25 / 1,75 / 2,50 por inversión mensual y no se abrieron las bases legales enlazadas. |
| ACC-03 | Cuenta Remunerada Openbank | ok | 13 | Faltan las bases legales de la promoción OPEN325 (PDF enlazado, no abierto). La bonificación de 200 € por recibos es otro producto. |
| ACC-04 | Cuenta Remunerada Pibank | ok | 12 | Falta la fecha de vigencia del 2,02 % TAE: la página no la publica. |
| DEP-01 | Depósito Tú+ | ok | 14 | Falta confirmación de la frecuencia trimestral en el documento contractual; viene de la ficha web. El PDF sigue fechado «hasta 20/10/2026». |
| DEP-04 | Depósito Sinycon Plus | ok | 25 | Falta TIN inequívoco a 48 meses y frecuencia de liquidación inequívoca. El folleto precontractual 2026-09-29 enlazado no se abrió. |
| DEBT-01 | Letra del Tesoro — vencimiento 15-01-2027 | ok | 10 | Faltan comisiones de compra/venta y cotización secundaria: no aparecen en las páginas del Tesoro consultadas. |
| DEBT-02 | Letra del Tesoro — vencimiento 05-02-2027 | parcial | 3 | Sin precio ni tipo de subasta para este ISIN (no está en la tabla de últimas subastas). |
| DEBT-03 | Letra del Tesoro — vencimiento 05-03-2027 | parcial | 3 | Sin precio ni tipo de subasta para este ISIN. |
| DEBT-04 | Letra del Tesoro — vencimiento 09-04-2027 | parcial | 3 | Sin precio ni tipo de subasta para este ISIN. |
| FND-01 | Bestinver Bolsa, F.I. | parcial | 17 | Falta el indicador de riesgo sintético (SRI): el DFI imprime la escala 1-7 pero la extracción no identifica la clase marcada. |
| FND-02 | OLEA NEUTRAL, FI | parcial | 9 | Faltan NAV y fecha, comisiones, SRI, inversión mínima, moneda de la clase y condiciones de suscripción/reembolso. |
| FND-03 | Azvalor Internacional FI | parcial | 10 | Faltan comisión de depósito, ratio total de gastos, SRI, moneda de la clase y condiciones/horarios de suscripción y reembolso. |
| FND-04 | Bestinver Internacional, F.I. | parcial | 17 | Falta el indicador de riesgo sintético (SRI). |
| ETF-01 | iShares Core MSCI Europe UCITS ETF EUR (Acc) | ok | 15 | Faltan NAV actual y fecha, listados/tickers y disponibilidad por intermediario. |
| ETF-02 | Xtrackers S&P 500 Equal Weight UCITS ETF 2D | ok | 13 | Falta KID/DFI en español y los costes de operación del KID. |
| ETF-03 | State Street SPDR MSCI Europe Industrials UCITS ETF | parcial | 15 | Faltan SRI, KID en español y precio negociado. |
| ETF-04 | VanEck Semiconductor UCITS ETF | ok | 16 | Faltan KID/DFI en español, listados/tickers y precio negociado. |

## Conflictos e incoherencias detectadas

Se conservan los dos literales; no se corrige ninguno en silencio.

1. **ACC-02 MyInvestor — dos tarifas en la misma página.** El titular y las bases legales dan 2,50 % TAE / 2,472 % TIN los 6 primeros meses y 0,30 % desde el séptimo; el paso 2 del alta dice «una rentabilidad del 1,25 % TAE el primer año hasta 70.000 € sin condiciones».
2. **DEP-04 EBN — el titular no coincide con su tabla.** La cabecera promete «hasta el 2,85 % TAE», mientras la tabla de plazos llega a 3,10 % TAE a 48 meses y el bloque de depósitos combinados anuncia 3,50 % TAE.
3. **DEP-04 EBN — dos TIN para el mismo plazo.** La tarjeta de 48 meses dice «(3,06 % TIN)»; la nota al pie de ejemplos, para el mismo plazo, dice «2,97 % TIN».
4. **DEP-04 EBN — liquidación de intereses.** El texto legal dice «La liquidación de intereses se realiza al vencimiento del depósito»; la FAQ de la misma página dice «Puede elegir que le ingresemos lo devengado de manera trimestral o al vencimiento».
5. **ACC-01 Renault — el PDF de `primary_url` está caducado.** Declara «Condiciones vigentes hasta el 20/10/2026» y 2,27 % TAE; la web publica 2,61 % TAE / 3,00 % TIN. Se usan los tipos de la web y el PDF solo para cláusulas estructurales, advertido en cada condición.
6. **FND-01 y FND-04 Bestinver — costes de dos documentos de fechas distintas.** La ficha (30/09/2026) da cifra anual de gastos 1,86 % y 1,84 %; el DFI (31/12/2025) da 1,9 % + 0,6 % y 1,8 % + 0,5 %. No se promedian ni se elige uno.
7. **DEP-03 Pibank (ya en `condiciones.json`, fuera de este encargo) — oferta vencida.** La página mantiene el 3,03 % TAE pero la nota dice «Oferta válida hasta el 31/10/2026». A fecha de hoy ese tipo no debería presentarse como vigente.

## Vigencias declaradas y caducidad próxima

| Producto | Vigencia declarada en la fuente | Situación a 2026-11-05 |
|---|---|---|
| ACC-01 Cuenta Contigo (promo) | Contratación hasta 18/11/2026; TIN 3,00 % hasta 31/03/2027 | Vigente, 13 días de alta |
| ACC-03 Cuenta Remunerada Openbank | Código OPEN325 hasta 16/11/2026; tipo durante 12 meses | Vigente, 11 días de alta |
| DEP-01 Depósito Tú+ | «Condiciones válidas hasta el 18/11/2026» | Vigente, 13 días |
| DEP-03 Depósito Pibank | «Oferta válida hasta el 31/10/2026» | **Vencida** |

ACC-02, ACC-04, DEP-04 y los cuatro ETF no publican fecha de vigencia: se registra `effective_from/to = null` y se advierte en `notes`. No se ha inventado ninguna.

## Método y verificación

- Lectura con `web_extract` y, cuando la página se renderiza por JS (Renault Bank, Bestinver), con navegador real sobre el DOM. Los modales «*Condiciones Depósito Tú+ 12/24/36» solo existen tras clic, y se leyeron así.
- Cada condición lleva `source_url` exacta, `source_title`, `accessed: 2026-11-05`, `source_kind` y `value_literal` con el fragmento textual que la sostiene. Las cifras se copiaron tal cual, sin normalizar separadores.
- `value: null` se usa solo cuando la fuente declara algo sin cifra («sin límite máximo», «desde el primer euro») o cuando el dato no está; el literal y la nota explican cuál de los dos casos es.
- **Verificación de literales:** 210 de 223 fragmentos coinciden carácter a carácter con los ficheros de extracción guardados. Los 13 restantes se leyeron en el DOM del navegador (9 de los modales de Renault Bank, 1 NAV de Bestinver Bolsa) o en páginas cuya extracción no generó fichero (3 de Pibank); en esos casos el contraste es contra la salida literal de la herramienta en esta sesión, no contra un fichero.
- Los importes de saldo vivo de las Letras se convierten de «8.780,5» a 8780.5 millones EUR, conservando el literal en el registro.

## Fuentes utilizadas

- <https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf> — Renault Bank — Información precontractual Cuenta Contigo / Depósito Tú+ (RCI Banque)
- <https://etf.dws.com/en-lu/IE000CXLGK86-s-p-500-equal-weight-ucits-etf-2d> — Xtrackers (DWS) — Xtrackers S&P 500 Equal Weight UCITS ETF 2D
- <https://myinvestor.es/cuentas-tarjetas/cuentas/> — MyInvestor — Cuenta corriente remunerada
- <https://renaultbank.es/> — Renault Bank — Inicio (depósitos Tú+)
- <https://renaultbank.es/cuenta-contigo-nuevos-clientes/> — Renault Bank — Cuenta Contigo, landing nuevos clientes
- <https://www.azvalor.com/fondos-de-inversion/azvalor-internacional> — Azvalor — Azvalor Internacional FI
- <https://www.bestinver.es/fondos-de-inversion/bestinver-bolsa> — Bestinver — Bestinver Bolsa, F.I. (página del fondo)
- <https://www.bestinver.es/wp-content/uploads/bestinver_bolsa_fi_datos_fundamentales.pdf> — Bestinver — Documento de datos fundamentales Bestinver Bolsa, F.I. (31/12/2025)
- <https://www.bestinver.es/wp-content/uploads/bestinver_bolsa_fi_ficha_fondo.pdf> — Bestinver — Ficha del fondo Bestinver Bolsa, F.I. (datos a 30/09/2026)
- <https://www.bestinver.es/wp-content/uploads/bestinver_internacional_fi_datos_fundamentales.pdf> — Bestinver — Documento de datos fundamentales Bestinver Internacional, F.I. (31/12/2025)
- <https://www.bestinver.es/wp-content/uploads/bestinver_internacional_fi_ficha_fondo.pdf> — Bestinver — Ficha del fondo Bestinver Internacional, F.I.
- <https://www.blackrock.com/es/profesionales/literature/kiid/eu-priips-ishares-core-msci-europe-ucits-etf-eur-acc-ie00b4k48x80-es.pdf> — iShares — Documento de datos fundamentales IE00B4K48X80 (03/09/2026)
- <https://www.cnmv.es/portal/consultas/iic/fondo?lang=es&nif=V85962447> — CNMV — OLEA NEUTRAL, FI. Datos generales (datos a 2026-11-02)
- <https://www.ebnbanco.com/ahorro/deposito-sinycon-plus/> — EBN Banco — Depósito Sinycon Plus
- <https://www.openbank.es/cuenta-remunerada> — Openbank — Cuenta Remunerada Openbank
- <https://www.pibank.es/cuenta-remunerada/> — Pibank — Cuenta Remunerada Pibank
- <https://www.ssga.com/se/en_gb/intermediary/etfs/state-street-spdr-msci-europe-industrials-ucits-etf-stq-fp> — State Street SPDR — State Street SPDR MSCI Europe Industrials UCITS ETF (STQ FP)
- <https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/letras-del-tesoro> — Tesoro Público — Resultado de últimas subastas: Letras del Tesoro
- <https://www.tesoro.es/en/deuda-publica/valores-del-tesoro/valores-en-circulacion> — Tesoro Público — Valores en circulación (Letras del Tesoro)
- <https://www.vaneck.com/globalassets/home/ucits/documents/kids/KIID_VanEck-Semiconductor-UCITS-ETF_en-UK.pdf> — VanEck — Key Investor Information IE00BMC38736 (20/03/2026)
- <https://www.vaneck.com/uk/en/investments/semiconductor-etf/overview?al=en&audience=retail&disclaimer=true> — VanEck — VanEck Semiconductor UCITS ETF (SMH)

## Qué no se ha tocado

- `prototipos/paideia-local/data/condiciones.json`: intacto.
- Ningún otro fichero de la aplicación, ni configuración, ni endpoints, ni tests.
- Solo se han escrito `docs/catalogo/transcripcion-2026-11-05.json` y este informe.
- No se ha usado la API de Groq ni se ha abierto `.env`.

## Siguiente paso sugerido

Los 18 registros están listos para una capa de condiciones separada de la lista de identidad (mismo `candidate_id`, `source_url` y fecha). Antes de mostrarlos en la app conviene: (1) decidir si los `parcial` se muestran con su hueco marcado en vez de ocultarse; (2) resolver el SRI de los dos fondos Bestinver (FND-01, FND-04) leyendo el PDF del DFI; (3) revisar permisos de display/cache, que siguen sin evaluar y este documento no concede.
