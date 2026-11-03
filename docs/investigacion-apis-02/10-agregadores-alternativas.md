# Agregadores, comparadores y feeds comerciales para el catálogo Paideia

> **Corrección del coordinador:** la cuota única de FundFacts indicada abajo no está cerrada: pricing publica 5/1.000 (Free/Pro), mientras docs/requests publica 15/9.000. Véase `00-SINTESIS.md`, con ambas fuentes y evidencia. Mantener la cuota efectiva como no verificada; este informe histórico no aprueba integración ni permiso de aula.

**Alcance:** revisión de solo lectura para España/EEE, prototipo académico de 100 personas, una semana y presupuesto de 0 €. Directorios, buscadores y GitHub se usaron solo para descubrir opciones; no se contactó a proveedores ni se usaron credenciales privadas.

## Resultado priorizado

El hueco más claro para solicitar permiso más adelante es **VDOS**, que documenta un catálogo profesional de fondos españoles pero no una API pública gratuita.[1]
**FinanceAds** declara feeds/API y herramientas white-label con actualización de productos y tipos de interés, bajo un modelo orientado a afiliación.[8]
**FundFacts API** es el único candidato de esta tanda cuyo endpoint pude probar sin cuenta: devuelve una ficha estructurada de ETF por ISIN.[7]
Su cuota Free es de 15 consultas mensuales; el uso comercial aparece en Pro, publicado a 49 USD/mes por 9.000 consultas.[4][5]

Finect publica fichas de fondos con comisiones y documentos enlazados.[2]
HelpMyCash muestra condiciones concretas de cuentas remuneradas.[14]
Kelisto y Rankia presentan comparadores y relaciones de afiliación/partners.[11][12]
En las páginas revisadas no encontré documentación de una API/feed reutilizable ni una licencia de redistribución para estos comparadores; deben tratarse como posibles interlocutores para pedir un export autorizado, no como fuentes para copiar.[2][11][12]
Awin documenta feeds CSV para los que un publisher tenga acceso, pero el ejemplo es genérico/retail y no prueba que existan ofertas financieras españolas en ese marketplace.[9][10]

ESMA documenta servicios máquina-a-máquina para consultar datos de registros y documentos regulatorios, útiles para identidad/estado registral pero no para condiciones comerciales de cuenta, depósito o crédito.[16][17]
ESMA también mantiene un paquete Python para buscar/descargar determinados conjuntos.[18]
La licencia EUPL-1.2 comprobada cubre el **código** del paquete, no automáticamente los datos servidos por ESMA.[19]

## Matriz de candidatos

| Prioridad | Candidato | Qué añade a PostgreSQL | Acceso, coste y derechos | Juicio para Paideia |
|---|---|---|---|---|
| 1 — negociación futura | **VDOS Data** | Identidad y datos de fondos, NAV, series, rentabilidad, documentación legal, MiFID y ASG. La página declara >60.000 productos y datos recibidos diariamente de gestoras y registros oficiales.[1] | No publica endpoint/API, autenticación, precio, cuota académica ni licencia para guardar/mostrar datos. **Precio desconocido**, no “gratis” ni “pago obligatorio” demostrado. | Mayor encaje para fondos españoles si ofrece API/feed y permiso de uso educativo. No es catálogo de depósitos/cuentas; cobertura ETF no quedó confirmada. Documentado, no probado. |
| 2 — negociación futura | **FinanceAds** | Declara comparadores white-label, API/interfaces y feeds de productos con actualización automática de productos y tipos de interés; categorías publicadas: cuentas corrientes/tarjetas prepago, tarjetas de crédito, inversión y seguros.[8] | Se orienta explícitamente a afiliados/monetización. Precio del feed, API, licencia de rehosting y disponibilidad de productos españoles no publicados en la página revisada. El registro “free” no acredita licencia de datos gratuita. | Buen candidato para pedir un feed de ofertas bancarias/tasas, pero verificar depósitos y préstamos, cobertura España, selección sesgada a partners y si exige enlaces/comisión. Documentado, sin endpoint probado. |
| 3 — prueba académica condicionada | **FundFacts API** | REST por ISIN para fondos UCITS/ETF: costes, SRRI, holdings, exposiciones, rentabilidades, métricas y fecha de referencia; los datos se derivan de documentos publicados por gestoras.[3] | Endpoint demo público probado: HTTP 200, `application/json`, con costes/TER, riesgo, exposiciones, calendario de rentabilidad y `dataAsOf`.[7] Gratis: 15 lookups/mes; Pro: 49 USD/mes, 9.000 requests/mes y uso comercial.[4][5] La licencia prohíbe revender el dataset bruto como feed competidor.[6] | Aporta más campos normalizados que un quote feed, pero solo fondos/ETF, no cuentas/deuda. La excepción educativa para 100 usuarios no está publicada: pedirla antes de integrar; **no cumple 0 € comercial/producción sin permiso explícito**. Un único ISIN probado no demuestra cobertura ni frescura general. |
| 4 — pedir export/colaboración | **Finect** | Una ficha pública de fondo muestra comisiones, gastos corrientes, fecha y descarga de factsheet/prospectus/KID, además de rentabilidad y riesgo; ejemplo revisado incluye gastos corrientes de 0,940 % y documentación fechada.[2] | Página pública, pero no se localizó API/export público ni licencia para guardar o republicar la ficha/documentos. No inferir que el dato del sitio sea de Finect propio ni que la lectura permita reutilizarlo. Precio/licencia: desconocidos. | Puede ayudar a estructurar el esquema de fondos; pedir feed autorizado o permiso de enlace/atribución. No usar scraping ni alojar PDFs sin permiso. |
| 5 — pedir export/colaboración | **HelpMyCash** | Sus fichas de cuentas ofrecen condiciones con valor de comparación: TAE/TIN, límite de saldo, duración, elegibilidad, bonificaciones, comisiones y garantía de depósitos. La página observada muestra una oferta con 3,25 % TAE durante 12 meses, elegibilidad de nuevo cliente y requisito Bizum.[14] | No se documentó API/feed ni derechos de exportación/redistribución. Precio y acceso académico: desconocidos. La página de consumo no es permiso para poblar una base de datos. | Buen ejemplo de campos necesarios para cuentas remuneradas y ofertas promocionales; solicitar CSV/API con fecha efectiva, requisitos y autorización de 100 usuarios. No asumir que “mejores” representa todo el mercado. |
| 6 — pedir feed a publisher/comparador | **Kelisto** | Mantiene comparadores para cuentas, hipotecas, préstamos, seguros y otros servicios; describe ofertas de partners y modelo de remuneración por derivación o contratación.[11] | No se encontró documentación pública de API/feed. La lista de partners incluida en la página indica actualización a 1 de julio de 2025, por lo que no sirve como inventario actual en 2026 sin confirmación.[11] Precio y uso educativo: desconocidos. | Posible fuente de oferta bancaria de partner, probablemente limitada a anunciantes; preguntar por feed completo vs afiliados y neutralidad/ordenación. No copiar los rankings. |
| 7 — pedir feed/uso educativo | **Rankia** | Enlaza comparadores de fondos, ETF, brokers y cuentas; declara acuerdos comerciales/afiliación, pero también que no todas las entidades mencionadas tienen acuerdo.[12] | La política pública explica publicidad y patrocinios para sostener contenido gratuito; no documenta API, exportación ni licencia de dataset.[12][13] Precio/descuento educativo desconocido. | Útil como posible partner editorial/comercial; pedir campo por campo, universo cubierto y derecho explícito a almacenar/mostrar. El contenido público no equivale a catálogo completo o neutral. |
| 8 — sólo oportunidad de marketplace | **Awin Product Feeds** | Hay lista CSV de feeds visibles para el partner, fecha de última importación, idioma/región y URL; la descarga se puede automatizar con una clave específica.[9][10] | Hace falta cuenta de publisher y acceso al feed del anunciante (por adhesión o permiso previo). Los campos del ejemplo son principalmente retail (precio, stock, entrega, `terms_of_contract` genérico); no hay evidencia de TAE, saldo, plazo o condiciones bancarias para España.[10] Precio y derechos de usar los datos fuera de afiliación: no confirmados. | No es candidato prioritario para catálogo financiero hasta ver un feed de banco español y obtener términos de uso educativo/cache. Podría servir para descubrir ofertas de anunciantes, no para el universo completo. |
| 9 — suplemento regulatorio | **ESMA Registers + `esma_data_py`** | Servicios A2A/M2M y un paquete oficial de búsqueda/descarga de ciertos conjuntos.[16][18] | El código de `esma_data_py` tiene EUPL-1.2 verificada en el archivo raíz.[19] No se confirmó licencia/redistribución de cada dataset, cuotas, ni endpoint concreto probado. | Complemento de identidad, estado registral y enlace a documentos, no términos de productos retail. Mejor evaluar el endpoint directo si se necesita un registro; revisar condiciones de cada conjunto por separado. |
| Excluido del catálogo | **Bankflip / Permisso** | La web trata de datos financieros/documentos de cada usuario con autorización —ingresos, impuestos, deuda/CIRBE y cuentas bancarias— no de ofertas de productos para comparar.[15] | Servicio de datos personales permissioned; la web invita a solicitar llamada. No se probó API ni condiciones comerciales. | No llena el hueco solicitado y añade tratamiento de datos personales; excluir del catálogo. Considerarlo solo en un alcance distinto y con base jurídica/consentimiento, no para el MVP de comparación. |

## Detalle de lo que falta y preguntas para una solicitud futura

No se envió ninguna consulta; para una eventual petición, describir el uso académico, temporal y no comercial para 100 estudiantes y PostgreSQL, y pedir acceso de solo lectura.

1. **Producto y cobertura:** ¿incluye España y qué familias (cuenta corriente/remunerada, depósito, préstamo/hipoteca, fondo registrado, ETF UCITS)? ¿Feed completo o solo partners/anunciantes? ¿Por ISIN/clase, entidad y producto con exclusiones documentadas?[1][8][14]
2. **Campos contractuales:** TAE/TIN y periodicidad; plazo/vencimiento; importe mínimo/máximo y tramo remunerado; elegibilidad (nuevo cliente, nómina, Bizum, país/residencia); comisiones; permanencia/penalización; bonificación y vigencia; FGD; divisa/clase, costes KID/PRIIPs y riesgo; documentos y enlaces oficiales.[2][3][14]
   Pedir definición/unidad, valores nulos y diferencia entre dato no aplicable/no publicado.[2][3]
3. **Frescura y procedencia:** `source_url`, `source_name`, fecha de publicación/observación y `valid_from`/`valid_to`; frecuencia real de actualización y SLA; historial/cambio de condiciones; política ante datos faltantes o caducados; fecha de corte por registro, no solo la hora de descarga.[1][3][8]
4. **Integración y cuota:** REST/CSV/JSON/OpenAPI, autenticación, sandbox, paginación/batch, cuota mensual y burst, exportaciones permitidas, límites de almacenamiento y disponibilidad.[4][9][16]
   ¿Se puede mantener un snapshot en Postgres y actualizarlo con un job compartido, en vez de que cada estudiante llame al proveedor?[4][9]
5. **Derechos y precio:** ¿permiten reproducir valores/campos en una web educativa para 100 usuarios, cachear versiones, crear cálculos derivados y publicar la demo solo dentro del aula?[6][8][11]
   ¿Se permite export/backup, mostrar registros individuales y enlaces a documentación? ¿Qué atribución, duración, borrado, subcontratistas, región y proceso de corrección exigen?[6][8][11]
   Pedir precio neto y cualquier **exención académica/no lucrativa**; distinguir registro gratuito, prueba técnica, feed y licencia de visualización/redistribución.[5][6][8]
6. **Afiliación/conflicto:** ¿requieren enlace de contratación, tracking, conversión, exclusividad o volumen?[8][9][12]
   ¿La afiliación limita los productos mostrados, altera ranking/condiciones o impide comparar productos sin acuerdo comercial? ¿Se puede usar el feed sin promocionar/contratar?[8][9][12]

### Preguntas específicas por proveedor

- **VDOS:** ¿existe API/CSV para centros educativos?, ¿qué campos de costes/clase/documentos cubre y qué derechos tienen sobre NAV, datos de gestoras y métricas propietarias?, ¿permiten una copia local de lectura para una clase de 100 por una semana a 0 €?[1]
  La página declara datos diarios, pero no publica contrato, precios, endpoint, autenticación o licencia.[1]
- **FinanceAds:** ¿hay cuentas y depósitos españoles (no solo cuentas corrientes), TAE y condiciones por tramo, fechas de vigencia y ofertas no afiliadas?, ¿API frente a iframe white-label?, ¿admite comparar sin monetizar tráfico?[8]
  ¿Existe sandbox/CSV autorizado y acceso de aula sin conversión/fees?[8]
- **FundFacts:** ¿puede una universidad/centro acceder gratis o con licencia de evaluación para 100 usuarios no comerciales?, ¿el plan Pro permite cachear los campos seleccionados y mostrarlos a usuarios sin revelar la API key?, ¿qué límites aplican a fondos españoles, extracción de KID y datos derivados?[4][5][6]
  La respuesta demo prueba forma y campos de una única clase, no la cobertura completa ni la excepción educativa.[7]
- **Awin:** ¿hay feeds de bancos españoles con campos financieros estructurados, no solo fichas retail?, ¿qué autorización requiere cada feed y permite conservar snapshots y mostrar precios/condiciones en una web educativa fuera de una campaña afiliada?[9][10]
- **Finect / HelpMyCash:** solicitar export/API autorizado y derechos de caché/visualización de campos/documentos; probar 10 ofertas con fechas de validez antes de plantear integración.[2][14]
- **Kelisto / Rankia:** pedir cobertura de ofertas no afiliadas, derechos de retención/atribución y autorización expresa; no automatizar páginas públicas.[11][12][13]
- **ESMA:** confirmar derechos de reutilización y cuotas para cada registro y qué consulta cubre fondos/UCITS, comercialización transfronteriza, prospectos o instrumentos.[16][17]
  No confundir EUPL del código con licencia de los datos.[18][19]

## Decisión provisional

Para una semana y 0 €, tratar **VDOS y FinanceAds como opciones comerciales por negociar**; precio y licencia no están publicados en las páginas revisadas.[1][8]
**FundFacts** tiene un endpoint demo probado, pero el uso gratuito tiene límites y no se halló excepción académica; pedir autorización antes de usarlo en el aula.[3][4][5]
Sus términos también restringen la redistribución del feed bruto.[6]
Los comparadores editoriales son opciones para pedir export autorizado, no para raspar.[2][11][12]
ESMA puede complementar identidad/documentación, pero se deben confirmar los derechos del dataset.[16][17]
La licencia del código ESMA no sustituye los derechos de datos.[18][19]
Ningún candidato documenta todas las condiciones de las cuatro familias con permiso de publicación para este caso.[1][3][8]
Un endpoint probado no significa integración de producción ni cobertura completa.[7]

## Sources

[1] https://www.vdos.com/es/datos.html
[2] https://finect.com/fondos-inversion/LU2123307360-Visionfund__emerging_mkts_eq_ieur_h
[3] https://fundfactsapi.com/docs
[4] https://fundfactsapi.com/docs/requests
[5] https://fundfactsapi.com/pricing
[6] https://fundfactsapi.com/terms
[7] https://fundfactsapi.com/api/v1/demo/funds/IE00B4L5Y983
[8] https://www.financeads.com/tools
[9] https://success.awin.com/s/article/How-can-I-access-a-Product-Feed
[10] https://help.awin.com/developers/docs/product-feed-list-download
[11] https://www.kelisto.es/partners-kelisto
[12] https://www.rankia.com/rankia/politica-de-afiliados
[13] https://www.rankia.com/rankia/publicidad
[14] https://www.helpmycash.com/cuentas/cuentas-remuneradas
[15] https://bankflip.io
[16] https://registers.esma.europa.eu/publication/helpApp
[17] https://www.esma.europa.eu/publications-and-data/databases-and-registers
[18] https://github.com/European-Securities-Markets-Authority/esma_data_py
[19] https://raw.githubusercontent.com/European-Securities-Markets-Authority/esma_data_py/master/LICENSE.md
