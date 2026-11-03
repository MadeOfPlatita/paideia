# APIs de catálogo para cuentas y depósitos — España/UE

> **Contraste del coordinador:** el JSON conservado de YieldMeister tiene 70 filas globales y solo 4 ES (dos benchmarks, una letra y un depósito). La fila Openbank indica 12 meses, pero enlaza a una oferta oficial de 6 meses con requisitos no recogidos en el feed. No promover esa fila a comparador sin resolverlo. Véase `00-SINTESIS.md`; endpoint probado no significa dato contractual verificado.

**Corte:** 26-10-2026. Alcance: ofertas comerciales de bancos y distribuidores; solo consultas GET públicas. No se crearon cuentas, no se usaron credenciales, no se hicieron pagos ni se intentó eludir controles. `endpoint-tested` significa únicamente que esa petición respondió y se inspeccionó; no prueba exactitud exhaustiva, continuidad ni permiso de redistribución.

## Veredicto breve

- **Mejor candidato para un piloto de bajo coste: YieldMeister.** La documentación describe endpoints REST para tasas actuales, filtros por mercado/tipo, detalle de producto y mercados.[9]
- En el GET público probado, YieldMeister respondió `200 application/json` sin `Authorization`; la respuesta incluía filas ES y un objeto de depósito con `market`, `currency`, `term_months`, `rate`, `captured_at`, `last_checked`, `stale`, `is_promo` y `source_url`.[14]
- Su plan Free publica 1.000 llamadas/mes, tasas actuales y ausencia de tarjeta; el historial es de pago.[10] Los términos limitan el uso a la propia aplicación, exigen atribución visible y prohíben redistribuir el dataset por separado.[12][13]
- **Mejor distribución de depósitos reales: Raisin / WeltSparen / Deposit Solutions, pero solo por relación B2B.** Raisin anuncia API e integración para mercados europeos, incluido España; la integración API se anuncia como gratuita, pero el modelo de distribución puede generar comisiones y requiere contacto de Partnerships.[5][6] Deposit Solutions se fusionó con Raisin DS; WeltSparen, Savedo y ZINSPILOT son marcas de ese grupo, no APIs públicas independientes.[8]
- **Open Banking no equivale a catálogo paneuropeo.** Open Banking UK publica especificaciones Open Data, pero la API Products de AIS está ligada a cuentas autorizadas.[1][3] La extensión británica para ahorros/depósitos aplica a cuentas de pago GBP ligadas al cliente, no a un catálogo abierto de ofertas.[4]
- **Australia sí tiene Product Reference Data público bajo CDR, pero no sirve para España/UE.** Gateway Bank publica API sin autenticación para referencia de productos; su GET de lista devolvió 200 e incluye savings/term deposits. La ruta de detalle directa devolvió 403 en esta prueba, sin reintento.[20][22]
- **Agregador australiano que expone datos de detalle:** CDR Compare documenta API read-only sin key ni rate limit; su GET de detalle probado devuelve tasas, tiers, fees, constraints, elegibilidad y upstream URL. El operador ofrece uso gratis con atribución, solo para el catálogo australiano.[21][23][24]
- **Negativos concretos:** DepositScout documenta un feed de ahorro británico (AER, Cash ISA, easy access, fixed/notice) y el GET sin clave respondió `401 Unauthorized`; no es España/UE.[15] Tink ofrece agregación de cuentas del usuario, no ofertas del mercado.[16] APYData es comparador web; su artículo describe actualización con fuentes oficiales y APIs de plataformas, pero no documenta un feed para terceros.[17]

## Candidatos evaluados

| Candidato | Cobertura y clase de datos | Acceso, coste y derechos | Estado / uso recomendado |
|---|---|---|---|
| **YieldMeister Rates API** | Europa; el GET inspeccionado incluía filas ES y también bonos, letras, benchmarks, cuentas de ahorro y depósitos. La fila ES observada distingue `term_deposit`, plazo, moneda, tasa y origen. No trae en la fila condiciones completas como TIN/TAE diferenciadas, importe mínimo/máximo, nómina requerida, comisiones, penalización por retirada anticipada o elegibilidad; no usar `rate` como TAE sin confirmar la definición. | Free: €0, 1.000 calls/mes, tasas actuales; sin tarjeta. Starter €29/mes (50.000 calls/mes e historial); Pro €99/mes (500.000 calls/mes). Los docs ofrecen clave gratuita y abren tasas actuales durante preview; la petición anónima también funcionó, pero confirmar auth antes de producción.[9][10] Términos: derecho limitado/revocable para usar en la propia aplicación, atribución visible requerida y enlace al proveedor cuando sea práctico; no redistribución independiente/masiva sin licencia escrita. Sin garantía de exactitud o actualidad; verificar oferta final con el banco.[13] | **endpoint-tested** — candidato de piloto con caché compartida y verificación oficial por oferta; no es un catálogo bancario exhaustivo ni una fuente contractual. |
| **Open Banking UK Open Data (PCA/BCA)** | Estándar de datos de cuentas corrientes personales y de empresa. El esquema PCA incluye grupos de producto, interés de crédito, descubierto, elegibilidad, beneficios y otros cargos; los detalles de producto son PCA/BCA. No es un feed general de depósitos a plazo de España/UE.[2][3] | Estándar/documentación pública; la entidad implementa y sirve cada endpoint. Enrolarse como API user es opcional si no se necesita soporte, pero cada proveedor controla sus datos. No encontré licencia de reutilización general ni tarifa/cuota uniforme publicada.[1] | **documented** — buena referencia de esquema, geografía incorrecta para Paideia; no se probó un endpoint bancario vivo. |
| **Australian CDR — API oficial de Gateway Bank** | Australia. Product Reference Data para cuentas transaccionales/de ahorro y term deposits. GET lista entrega `productId`, fechas de vigencia/actualización, categoría, nombre, marca y enlaces de solicitud/condiciones/tarifas.[19][20][22] | Página oficial dice API pública y sin autenticación; la lista GET con `x-v: 5` devolvió 200. La consulta de detalle directa para producto 27 devolvió 403, no repetí. No encontré cuota o licencia académica/reutilización uniformes en la página bancaria.[20] | **endpoint-tested** — lista oficial probada; detalle directo no validado. Mercado australiano, no EU/ES. |
| **CDR Compare Australia API** | Agrega catálogos de data holders CDR australianos. El detalle probado expone deposit rate type/rate/frecuencia/periodo, tiers, min/max balance, elegibilidad, fees, features, timestamps y URL de fuente.[24] | API read-only pública; documentación afirma sin key, auth ni rate limit y sin datos de consumidores. Gratis para cualquier uso, incluso comercial, con atribución al data holder y cita de la página CDR Compare consultada, incluido `lastUpdated`; no presentarlo como advice/ranking/recomendación y confirmar con el proveedor porque los datos pueden quedar incompletos o desactualizados.[21][25] | **endpoint-tested** — GET de lista y detalle respondieron 200; buena referencia técnica para la forma del catálogo, pero Australia solamente. |
| **Open Banking `GET /products` (Read/Write/AIS)** | Devuelve producto(s) de cuentas autorizadas. Incluye precios, cargos, intereses y funciones según el producto, pero el detalle completo es solo para BCA/PCA. La tabla de especificación marca `Authorization Code`, scope `accounts`; no es una lista anónima de las ofertas del mercado.[3] | Requiere flujo de AIS/consentimiento y acceso a la cuenta del usuario. La versión británica citada extiende las cuentas de pago GBP a cuentas flexibles de ahorro y depósito, manteniendo la naturaleza de datos ligados al cliente.[3][4] | **unsuitable** para catálogo sin transacciones/cuentas de usuarios; útil solo si se estuviera construyendo un servicio de agregación autorizado. |
| **Raisin / WeltSparen / Deposit Solutions** | Distribución de depósitos overnight, a plazo y notice, con mercados europeos y ofertas de bancos asociados; Raisin declara presencia en España y otros mercados.[5] | B2B: integración white-label/API o front-end co-branded, contacto comercial y modelo de distribución/commission. “API gratis” se refiere a la integración anunciada, no acredita un feed abierto con derechos de reutilización. La página no publica schema, auth, cuotas, precio para acceso académico ni términos de cache/display.[6] Afiliación es otro carril y no equivale a acceso API.[7] | **documented** — prometedor si se quiere intermediar/distribuir productos; no viable como fuente abierta y autoservicio dentro de una semana sin aprobación de Raisin. |
| **DepositScout API** | Catálogo estructurado británico: AER de Easy Access, Fixed Rate, Notice, Cash ISA y Regular Saver; documentación adicional de proveedores, FSCS y señales de elegibilidad.[15] | La guía requiere una clave Bearer; cuota, precio, derechos de republicación y acceso académico no aparecen en lo revisado. GET sin token: 401.[15] | **unsuitable** para el mercado Paideia actual (UK, con acceso comercial pendiente); guardar como alternativa si se abre una comparación UK. |
| **Tink Account Aggregation (y agregadores AIS similares)** | La cobertura incluye conexiones bancarias europeas; son posiciones reales del usuario, no el universo de productos anunciados por los bancos.[16] | Integración B2B y consentimiento del usuario para conectar su banco; no encontré feed de ofertas, tarifa pública ni licencia de catálogo en la ficha examinada.[16] | **unsuitable** para catálogo. No confundir nombres de producto “savings” en AIS con condiciones de oferta. |
| **APYData / comparadores web** | Comparador de productos de ahorro e inversión de España/Europa; afirma actualizar APY/TAE diariamente con fuentes oficiales y APIs de plataformas.[17] | Las páginas revisadas no publican API, CSV/JSON feed, cuotas ni licencia de reutilización. No tomar la página pública como autorización para scraping o republicación. | **unsuitable** como fuente API con evidencia actual; podría servir de contraste manual, citando sus límites. |
| **Catálogo público de banco (ej. Openbank)** | La página oficial en España muestra nombre, APR, NIR, liquidez, comisiones y enlace a información precontractual; es útil para comprobar condiciones comerciales directamente.[18] | Página web pública, no endpoint de catálogo REST/CSV identificado en esta revisión. Sin cuota de API ni permiso de extracción masiva establecido. | **unsuitable** como API; **documented** como fuente primaria manual por producto. No generalizar esta página a todos los bancos españoles. |

## Pruebas GET conservadas

| URL | Resultado | Campos observados | Evidencia local |
|---|---|---|---|
| `https://yieldmeister.com/api/v1/rates` | `200`, `application/json`; no se envió `Authorization`. La respuesta se parseó: `updated`, `count`, `attribution`, `terms`, `rates`; filas incluyen esquema comercial descrito arriba. | `provider`, `provider_name`, `product`, `product_id`, `kind`, `market`, `currency`, `term_months`, `rate`, `source`, `captured_at`, `last_checked`, `stale`, `is_promo`, `source_url` | `docs/investigacion-apis-02/evidence/yieldmeister-headers.txt`, `yieldmeister-body.txt` |
| `https://api.depositscout.com/v1/rates` | `401`, `application/json; charset=utf-8`; petición anónima, sin clave. No se intentó obtener credenciales. | `message`, `request_id` | `docs/investigacion-apis-02/evidence/depositscout-headers.txt`, `depositscout-body.txt` |
| `https://public.cdr-api.gatewaybank.com.au/cds-au/v1/banking/products` | `200`, `application/json; charset=utf-8`; GET con cabecera `x-v: 5`. | `products[]`: `productId`, `effectiveFrom`, `lastUpdated`, `productCategory`, `name`, `brand`, URLs de solicitud/fees/terms. | `docs/investigacion-apis-02/evidence/gateway-products-headers.txt`, `gateway-products-body.txt` |
| `https://public.cdr-api.gatewaybank.com.au/cds-au/v1/banking/products/27` | `403`; no se guardaron headers/cuerpo y no se reintentó. | Ninguno | `docs/investigacion-apis-02/evidence/gateway-detail-403.txt` |
| `https://www.cdrcompare.au/api/v1/brands` | `200`, `application/json; charset=utf-8`. | `data.brands[]`, `links`, `meta`; incluye Gateway Bank y `productReferenceDataUri`. | `docs/investigacion-apis-02/evidence/cdrcompare-brands-headers.txt`, `cdrcompare-brands-body.txt` |
| `https://www.cdrcompare.au/api/v1/brands/gateway-bank/products/27` | `200`, `application/json; charset=utf-8`; detalle CDR de un depósito a plazo. | `productCategory`, `name`, `features`, `constraints`, `eligibility`, `fees`, `depositRates` (tipo, tasa, frecuencia, plazo/tiers), `additionalInformation` | `docs/investigacion-apis-02/evidence/cdrcompare-detail-headers.txt`, `cdrcompare-detail-body.json` |
| `https://openapi.natwest.com/open-banking/v3.1/aisp/personal-current-accounts` | `404`, JSON. Era una ruta tentativa, no una URL de proveedor confirmada; **inconcluso**, no prueba que el estándar o el banco no tengan API. | `status`, `title`, `description` | `docs/investigacion-apis-02/evidence/natwest-headers.txt`, `natwest-body.txt` |

## Conclusión de acceso académico, reutilización y España/UE

- No encontré una exención o cuota académica publicada para los proveedores B2B revisados; describo la falta de mención en las páginas consultadas, no una negativa contractual.[5][6][15]
- YieldMeister publica plan Free, pero el API gratuito también queda sujeto a sus términos de uso y atribución; no es licencia abierta de dataset.[10][12][13]
- CDR Compare declara uso gratuito para cualquier fin, incluso comercial, sujeto a atribución del proveedor y a la URL/fecha de consulta; es una condición favorable, pero únicamente para productos australianos.[21]
- En Open Banking UK, el enrolamiento del API user es opcional para recibir soporte; eso no concede licencia paneuropea ni derechos generales de republicación.[1]
- YieldMeister declara una tarea diaria que consulta páginas de proveedores/fuentes oficiales y conserva snapshots timestamped; es la metodología del proveedor, no una verificación independiente.[11]

El intento de inspeccionar `https://developer.caixabank.es` fue bloqueado por la capa de extracción como URL de red privada/interna. Es un fallo de herramienta, no una respuesta de CaixaBank ni evidencia de que no haya API; queda **unverified**.

**Recomendación acotada:**
- Para una demo Paideia, probar YieldMeister detrás de una actualización backend/cacheada y conservar `source_url` y `last_checked`.[9][10][14]
- Mostrar atribución y un botón “verificar con el banco”; no presentar las tasas como oferta contractual ni ocultar que faltan condiciones completas.[12][13]
- Antes de ampliar el catálogo, pedir a Raisin una propuesta de API **solo lectura** con catálogo España/UE, esquema, cuota y derechos de display/cache.[5][6]
- Contrastar cada oferta española con la ficha/contrato oficial del banco, como muestra el catálogo público de Openbank.[18]
- Ninguna conexión queda validada como sistema de producción por estas pruebas aisladas.[14][15]

## Sources

[1] https://openbanking.org.uk/open-data-apis — Open Data API Specs – Open Banking
[2] https://openbanking.atlassian.net/wiki/spaces/DZ/pages/1103233939/PCA+API+Specification_v2.3.0 — PCA API Specification v2.3.0 – Open Banking
[3] https://openbanking.atlassian.net/wiki/spaces/DZ/pages/1077805443/Products+v3.1.2 — Products v3.1.2 – Open Banking
[4] https://openbanking.atlassian.net/wiki/spaces/DZ/pages/127009221/Read+Write+Data+API+Specification+-+v2.0.0 — Read/Write Data API Specification v2.0.0 – Open Banking
[5] https://raisin.com/become-a-partner — Become a Partner – Raisin
[6] https://www.raisin.com/en/corporate/become-a-distribution-partner — Become a Distribution Partner – Raisin
[7] https://www.raisin.com/en/corporate/become-an-affiliate-partner — Affiliate Program – Raisin
[8] https://raisin.com/corporate/press/Deposit-Solutions-And-Raisin-Merge — Deposit Solutions and Raisin merge – Raisin
[9] https://yieldmeister.com/developers — YieldMeister Rates API – Developers
[10] https://yieldmeister.com/pricing — YieldMeister API pricing
[11] https://yieldmeister.com/about — YieldMeister methodology
[12] https://yieldmeister.com/terms — YieldMeister Terms of Service
[13] https://yieldmeister.com/api-terms — YieldMeister API Terms
[14] https://yieldmeister.com/api/v1/rates — YieldMeister Rates API GET response
[15] https://depositscout.com/developers/getting-started-with-the-depositscout-api — Getting Started with DepositScout API
[16] https://tink.com/products/account-aggregation — Tink Account Aggregation
[17] https://apydata.com/en/blog/apydata-que-es-que-comparamos-y-como-usarlo — APYData product comparison
[18] https://www.openbank.es/en/savings-accounts — Openbank Savings Accounts
[19] https://consumerdatastandardsaustralia.github.io/standards — CDR Data Standards – Australian Banking APIs
[20] https://gatewaybank.com.au/important-information/consumer-data-right-cdr — Gateway Bank Consumer Data Right
[21] https://cdrcompare.au/developers — CDR Compare Developers & API terms
[22] https://public.cdr-api.gatewaybank.com.au/cds-au/v1/banking/products — Gateway Bank Product Reference Data API GET
[23] https://www.cdrcompare.au/api/v1/brands — CDR Compare brands API GET
[24] https://www.cdrcompare.au/api/v1/brands/gateway-bank/products/27 — CDR Compare Gateway Bank product detail API GET
[25] https://cdrcompare.au/terms — CDR Compare Terms
