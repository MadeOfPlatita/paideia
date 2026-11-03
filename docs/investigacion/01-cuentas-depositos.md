# Investigación: fuentes de datos para cuentas remuneradas y depósitos en España

**Consulta:** 26 de octubre de 2026. Alcance: residentes en España, fuentes públicas y APIs/documentación; no se crearon cuentas, no se usaron credenciales ni se reutilizó contenido en una aplicación.

## Conclusión ejecutiva

- **No encontré una API pública y gratuita suficiente para publicar diariamente ofertas reales** con TAE/TIN, plazo, límites, comisiones, requisitos, entidad, país y garantía[1][4][17]. Las APIs oficiales que sí funcionan devuelven tipos estadísticos agregados (mensuales); EBA/FGD cubren garantía, no ofertas[10][15][17]. Una petición de datos en datos.gob.es solicita precisamente abrir los tipos de ahorro comunicados por entidad: es una solicitud, no un dataset ni una respuesta oficial que pruebe por sí sola que no exista información adicional[3].
- **Las condiciones concretas sí aparecen en páginas/fichas de producto de bancos**[33][34]. La ficha precontractual de Openbank, por ejemplo, incluye TAE/TIN por condición, plazo, mínimos/máximos, requisito de ingresos, cancelación, comisiones y FGD[34]. Es información primaria legible, no un feed API ni un compromiso de publicación diaria[34].
- **Raisin y los comparadores son útiles para descubrir ofertas, no para asumir datos licenciados o en tiempo real**[8][11][26]. Raisin anuncia API para sus socios bancarios, pero no publica documentación/acceso anónimo para Paideia[8][11]. Kelisto actualiza su ranking con una fecha concreta y sus términos limitan comercializar o divulgar información del portal; no debe copiarse a una base de datos sin autorización[26][28].

## Opciones prioritarias

| Opción | Acceso, coste y permisos | Cobertura/frescura | Valor para Paideia |
|---|---|---|---|
| **1. API/CSV del Banco de España** | Consultas HTTP públicas sin clave: probé `favoritas` y `listaSeries`; respondieron HTTP 200. La documentación consultada no indica tarifa, cuota ni licencia de reutilización; no asumir permiso comercial por ser una URL pública.[1][18][19] | Tabla 19.7 y series contienen **TEDR mensual** para depósitos por categoría. El capítulo identifica el total de entidades de crédito/EFC, no ofertas por banco o producto.[2][10] | Buen **benchmark agregado**. No da TAE/TIN contractual, importe, plazo de una oferta, comisiones, requisitos, país de garantía ni disponibilidad para cada residente. No sirve como catálogo de ofertas diarias. |
| **2. API SDMX del BCE (MIR)** | Documentación pública y consulta CSV anónima probada con HTTP 200. No vi precio, autenticación o licencia de reutilización especificados en la documentación extraída.[4][20] | MIR es mensual, pondera por volúmenes y expresa tipos como AAR/NDER. La observación consultada para España fue de agosto de 2026; no es un producto individual.[17][20] | Referencia secundaria para contexto/validación macro, no para comparar las condiciones anunciadas por bancos. |
| **3. EBA + FGD nacional** | EBA ofrece un Excel descargable; el enlace respondió HTTP 200 a una petición HEAD anónima. El FGD tiene un buscador público de entidades adheridas; en la inspección de la página no encontré API pública documentada.[6][7][15][27] | La publicación EBA es anual y el fichero cubre 2015–2025. EBA/FGD ayudan a identificar el esquema y la cobertura; las entidades de la UE pueden depender del sistema de garantía de su país de origen.[14][15] | Útil para **validar entidad, país del fondo y límite de garantía**; no contiene TAE, TIN, plazos, importes de oferta ni requisitos. Asociar cada marca comercial a la entidad jurídica y a su fondo requiere verificación. |
| **4. Web y fichas precontractuales del banco** | Página y PDF públicos, sin registro para leerlos. No se halló un feed/API de ofertas. El documento de Openbank consultado dice «Vigente desde 08.10.2026» y muestra una oferta por tramos, mínimo de 1 €, sin máximo, requisito de ingresos para el tipo superior, cancelación anticipada y garantía española.[33][34] | Es la mejor fuente primaria para la condición contractual actual. Hay que revisar qué documento está vigente y si el producto admite expresamente al perfil/residente elegido; la ficha consultada no explicita residencia en el fragmento extraído. | **Opción recomendada para los datos que se muestran al usuario**, pero con un universo pequeño, captura/fecha de comprobación y revisión humana. No existe garantía de que una página pública se actualice a diario ni de que los términos permanezcan iguales. |
| **5. Raisin (marketplace y posible vía B2B)** | Sus páginas de ofertas son públicas. La página española anuncia API «de forma gratuita» en el contexto de **bancos colaboradores**; la página B2B describe integraciones white-label por API. No vi documentación, precio del acuerdo, registro técnico ni derechos de redistribución para una app estudiantil.[8][11] | Su catálogo cubre productos de bancos colaboradores; las páginas muestran campos útiles y una fecha editorial (la de depósitos consultada indicaba 2/10/2026), no una cadencia diaria contractual.[12][13] | **No tratar como API gratis abierta.** Si interesa, pedir a Raisin por escrito acceso, campos, frecuencia, coste total, cobertura de residentes españoles, permiso de almacenamiento/republicación y SLA antes de diseñar sobre ello. |
| **6. Comparadores (Kelisto / HelpMyCash)** | Sus fichas públicas muestran información legible, pero no se encontró documentación de API ni licencia de datos para Paideia. Kelisto prohíbe en sus términos comercializar o divulgar información obtenida del portal; pedir autorización antes de extraer, almacenar o republicar.[26][28][29] | Kelisto etiqueta el ranking como actualizado el 23/10/2026; HelpMyCash ofrece un ranking de octubre y describe como filtro que un nuevo cliente residente en España pueda contratar. Son rankings editoriales, no garantías de actualización diaria ni de elegibilidad contractual.[28][29] | **Solo descubrimiento/manual QA.** No usar para poblar ni entrenar el comparador de Paideia sin permiso; validar cada oferta en el banco. Kelisto además marca ofertas patrocinadas.[28] |

## Cobertura de los campos solicitados

| Campo | APIs oficiales | Página/ficha del banco | Comparadores / marketplace |
|---|---|---|---|
| TAE/TIN | **No por oferta.** BDE devuelve TEDR agregado; MIR publica AAR/NDER agregados. No son equivalentes a la TAE/TIN de una oferta concreta.[10][17] | **Sí**, a veces con varios tramos y condiciones. La ficha consultada muestra un tipo nominal y TAE distintos según se cumpla el requisito.[34] | A menudo sí en tablas públicas, pero deben confirmarse en la entidad y no se ha verificado permiso de reutilización.[28][29] |
| Plazo, saldo mínimo/máximo | No en las series agregadas. | **Sí**, en la ficha contractual revisada (6 meses; mínimo 1 €; sin máximo).[34] | Frecuentemente publicados como campos de ficha.[28][29] |
| Comisiones y cancelación | No. | **Sí**, en ficha/folleto de producto y documentos de comisiones; la ficha consultada detalla cancelación anticipada.[33][34] | Puede resumirse, pero no siempre sustituye el tarifario/contrato del banco.[28][29] |
| Requisitos/promoción | No. | **Sí**: dinero nuevo, ingresos recurrentes, nómina/pensión y plazo de cumplimiento aparecen en la ficha oficial examinada.[34] | Suelen presentarse, pero la elegibilidad es editorial y puede depender de detalles no visibles en la tarjeta.[28][29] |
| Entidad, país y garantía | BDE/ECB no dan la garantía asociada a una oferta; EBA/FGD aportan datos del sistema, no de cada oferta.[6][7][17] | La ficha revisada identifica Open Bank S.A. y el FGD español, con el límite por depositante.[34] | Algunas fichas exponen país/fondo, pero hay que validar que la entidad jurídica y el esquema sean correctos.[28] |
| Residencia elegible | No. | Debe comprobarse en las condiciones de contratación y onboarding; no inferirlo por el dominio `.es`. | HelpMyCash afirma que usa residencia española como criterio para su ranking, pero no equivale a autorización del banco para cada cliente/perfil.[29] |
| Actualización diaria | No: BDE/ECB son mensuales; EBA publica datos DGS anuales.[10][15][17] | No hay API/cadencia diaria verificada. Se puede vigilar una página diariamente, pero la fuente puede no cambiar o puede alterar la estructura sin aviso. | Las páginas consultadas llevan fecha editorial (mes/día), sin promesa de API o actualización diaria.[12][28][29] |

**Distinción clave:** el valor `TEDR` de BDE y las series `AAR/NDER` del BCE son estadísticas agregadas. No deben publicarse como si fueran la TAE/TIN vigente de una cuenta o depósito comercial.[10][17]

## Repositorios existentes

La búsqueda pública de GitHub por «cuentas remuneradas» devolvió tres resultados[21]. La consulta exacta «depositos Spain interest» devolvió cero resultados[22]. Esto es exploratorio, no un censo de GitHub[21][22].

- [`ignacioisocial/mejores-cuentas-remuneradas`](https://github.com/ignacioisocial/mejores-cuentas-remuneradas): snapshot/artículo sobre 2025, no un feed de ofertas[21][24]. La etiqueta de GitHub y el archivo LICENSE dicen CC0, pero el README declara CC BY-NC 4.0 y enlaza una publicación de Finect; **hay conflicto de licencia y derechos de origen no aclarados**[24][31]. No reutilizar sin aclaración/autorización[24][31].
- [`OliverMp28/ahorro-tranquilo`](https://github.com/OliverMp28/ahorro-tranquilo): calculadora que declara no tener base de datos y no recomendar bancos; no es una fuente de tipos vigentes.[25]
- `smanriquezr/dashboard-rem-tenpo`: el resultado de GitHub lo describe solo como «cuenta remunerada» y no declara licencia; no se verificó cobertura española. No lo usaría para las ofertas de Paideia.[21]

## Recomendación operativa

1. Usar **BDE/ECB solo como contexto estadístico**, separado de las ofertas comerciales.[10][17]
2. Empezar con una lista deliberadamente acotada de bancos/productos que acepten residentes en España[29][34]. Para cada uno, guardar URL de la página y documento contractual, fecha de captura, fecha de vigencia, entidad jurídica, jurisdicción y fondo de garantía; modelar cada tramo/requisito como condición separada[14][34].
3. Programar una comprobación diaria de las fuentes oficiales seleccionadas, conservar snapshots/diferencias y marcar claramente «última comprobación»[33][34]. Eso es una **rutina propia de monitorización**, no una actualización diaria ofrecida por una API bancaria; automatización de páginas está condicionada a términos/licencias del sitio[1][17][26].
4. Usar el buscador oficial FGD/EBA para verificar la garantía y el documento de información al depositante del banco para confirmar el esquema concreto[6][7]. Para entidades extranjeras, no asumir que responde el FGD español[14].
5. Antes de importar cualquier comparador o repositorio, obtener permiso explícito cuando no haya una licencia clara[26][31]. Para un feed B2B, pedir a Raisin campos, alcance para residentes españoles, frecuencia, precio total y derechos de almacenamiento/republicación por escrito[8][11][31].

**Resultado:** con presupuesto cero, la combinación más viable es fichas oficiales de un conjunto pequeño + verificación FGD/EBA + BDE/ECB como referencia agregada[1][7][17]. No hay evidencia revisada de una API gratuita suficiente para mantener diariamente todo el mercado con datos contractuales verificables[1][4][15].

## Sources

[1] https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html — Servicio web de Estadísticas (API) - Banco de España
[2] https://www.bde.es/webbe/es/estadisticas/otras-clasificaciones/publicaciones/boletin-estadistico/capitulo-19.html — Boletín Estadístico, capítulo 19 - Banco de España
[3] https://datos.gob.es/es/solicitud-de-datos/historico-de-tipos-de-interes-de-productos-hipotecarios-y-de-ahorro-comunicados-por — Petición de apertura de tipos de ahorro comunicados al Banco de España - datos.gob.es
[4] https://data.ecb.europa.eu/help/api/data — ECB Data API - Data
[6] https://www.eba.europa.eu/activities/single-rulebook/regulatory-activities/depositor-protection/deposit-guarantee-schemes-data — Deposit Guarantee Schemes data - EBA
[7] https://www.fgd.es/entidades-adheridas — Buscador de entidades adheridas - FGD
[8] https://www.raisin.es/colabora-con-raisin — Colabora con Raisin
[10] https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1907.csv — Series temporales 19.7 - Banco de España
[11] https://www.raisin.com/en/corporate/become-a-distribution-partner — Become a Distribution Partner - Raisin
[12] https://raisin.es/depositos-a-plazo-fijo — Depósitos a plazo fijo - Raisin España
[13] https://raisin.es/cuenta-ahorro — Cuentas de ahorro - Raisin España
[14] https://www.fgd.es/wp-content/uploads/2025/04/triptico-depositos-protegidos-es-fgd.pdf — Tus depósitos están protegidos - FGD
[15] https://www.eba.europa.eu/publications-and-media/press-releases/eu-deposit-guarantee-scheme-funds-protect-depositors-against-bank-failures-continue-grow-and-have — EU DGS annual data 2025 - EBA
[17] https://data.ecb.europa.eu/data/datasets/MIR/data-information — MIR dataset information - ECB
[18] https://app.bde.es/bierest/resources/srdatosapp/favoritas?idioma=es&series=DN_1TI1T0010,DN_1TI2T0026 — Respuesta API BDE: tipos medios agregados de depósitos
[19] https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=es&series=DN_1TI2T0026&rango=30M — Respuesta API BDE: historial de TEDR de depósitos a plazo
[20] https://data-api.ecb.europa.eu/service/data/MIR/M.ES.B.L22.A.R.A.2250.EUR.N?lastNObservations=1&format=csvdata — Respuesta API BCE: intereses depósitos hogares España
[21] https://api.github.com/search/repositories?q=cuentas+remuneradas — Búsqueda pública de repositorios GitHub: cuentas remuneradas
[22] https://api.github.com/search/repositories?q=depositos+Spain+interest — Búsqueda pública de repositorios GitHub: deposits Spain interest
[24] https://github.com/ignacioisocial/mejores-cuentas-remuneradas — mejores-cuentas-remuneradas - GitHub
[25] https://github.com/OliverMp28/ahorro-tranquilo — ahorro-tranquilo - GitHub
[26] https://www.kelisto.es/terminos-de-uso — Términos de uso - Kelisto
[27] https://www.eba.europa.eu/sites/default/files/2026-06/dc34bbd2-f4d1-48d2-884e-f9217fb072fb/DGSD%20data%20-%20public%20file%20-%202015-2025_0.xlsx — DGSD data - public file 2015-2025 - EBA
[28] https://kelisto.es/depositos/mejor-compra/los-mejores-depositos-2854 — Los mejores depósitos a plazo fijo - Kelisto
[29] https://www.helpmycash.com/mejores-depositos — Mejores depósitos - HelpMyCash
[31] https://github.com/ignacioisocial/mejores-cuentas-remuneradas/blob/main/LICENSE — LICENSE - mejores-cuentas-remuneradas - GitHub
[33] https://www.openbank.es/deposito-a-plazo-fijo — Depósito a Plazo Fijo - Openbank
[34] https://www.openbank.es/assets/static/pdf/Productos/302_923_31_Deposito_6/302_923_31_Deposito_6.pdf — Ficha del Depósito Open 6 meses - Openbank
