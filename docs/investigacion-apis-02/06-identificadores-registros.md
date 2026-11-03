# Identificadores y registros: hallazgos de datos maestros

**Decisión:** integrar primero cuatro piezas complementarias: OpenFIGI, ESMA FIRDS, GLEIF y el registro de UCITS de CNMV.[1] El cruce es para identidad y presencia regulatoria; no es un comparador de ofertas.[9] EBA/ECB se conservan como siguiente bloque para bancos/DGS, después de resolver acceso al fichero vigente y su licencia.[10]

## Selección (4) y límites

| Fuente | Qué resuelve / formato y tamaño observado | Fecha/actualización | Coste, cuota y derechos | Estado |
|---|---|---|---|---|
| **OpenFIGI** | Identificador ISIN → FIGI y metadatos de listing/ticker/exchange. API JSON. El GET permitido `.../mapping/values/idType` devolvió 465 bytes y enumeró `ID_ISIN`, `TICKER`; **no hizo el mapping de un ISIN**. El mapping de instrumentos está documentado como POST, que no se usó por el límite GET-only.[1] | La respuesta de mapping no se probó, por tanto no se atribuye frescura ni cobertura. | Sin key: 25 requests/min y 10 jobs/request según la documentación; el FAQ permite exportar hasta 5.000 resultados CSV. La reutilización de FIGI symbology es libre; eso no convierte IDs propietarios de terceros en redistribuibles.[1][2] | Seleccionado; enum GET probado, mapping pendiente. |
| **ESMA FIRDS** | Registro regulatorio de referencia para valores admitidos/negociados; indexa ficheros full/delta/invalid/cancelled. El índice Solr JSON muestra `file_name`, `file_type`, `publication_date`, `download_link` y `checksum`; el tipo y fecha de archivo no son un registro de instrumento. Una respuesta de 3 filas ocupó 1.583 bytes; no se descargó ningún ZIP/XML.[13][16] | La consulta ordenada mostró `DLTINS` publicados con fecha 2026-10-26 y 2026-10-25. El índice mostraba 19.110 documentos en total, **no** 19.110 instrumentos activos. | Documentación de descarga XML; archivos enlazados como ZIP. No se midió tamaño de archivo, no se probó cuota ni se verificó licencia de redistribución; no bajar full files a ciegas.[13] | Seleccionado; index metadata GET probado, contenido del archivo pendiente. |
| **GLEIF LEI API v1** | ID de entidad y enlaces de Level 2: JSON con `lei`, `entity.legalName`, domicilios, jurisdicción, forma/estado legal y fechas de registro/renovación. Una consulta GET a un LEI devolvió un registro de 3.460 bytes; los campos `entity` y `registration` sí se observaron. No se probó un vínculo Level 2 concreto.[6] | Guardar `registration.lastUpdateDate`/estado del LEI además de `observed_at`; el tiempo de consulta no reemplaza la fecha del dato. | Sin key observado; 60 requests/min por usuario y sin coste según documentación. Los datos del Access Service están bajo CC0 1.0.[6][7] | Seleccionado; GET de registro probado. |
| **CNMV, listado de UCITS** | Página HTML pública; muestra nombre, número/fecha de registro oficial y enlace de detalle con NIF interno. Una página de 268.783 bytes mostraba 10 entradas y 124 páginas; no se bajó el listado entero ni se identificó un API estructurado.[9] | La muestra ofrece fechas de registro, no un timestamp fiable de actualización global; conservar la fecha de consulta y volver a verificar el registro. | No se encontró cuota/tarifa de API ni licencia explícita de reutilización en la nota legal consultada. La CNMV declara carácter informativo y limita su garantía sobre datos aportados por terceros; no presumir licencia abierta.[14] | Seleccionado para presencia en registro español, no para disponibilidad de contratación. |

**ESMA/FITRS:** esta ronda probó FIRDS y el índice de sus ficheros.[13][16] FITRS no se validó de forma independiente (ni esquema, ni campos, ni descarga) y queda fuera de la selección; no mezclarlo con el maestro FIRDS hasta definir qué tabla de transparencia se necesita. El documento FIRDS consultado describe ficheros full por datos recibidos hasta un cut-off y registros activos en venues MiFIR.[13]

### Complemento evaluado: EBA/ECB (no entra en los cuatro iniciales)

- **EBA Credit Institutions Register:** clasifica entidades CRD, sucursales EEE y no-EEE y advierte que el vínculo a un DGS **no implica** que cualquier tipo o importe de depósito sea elegible; los registros nacionales pueden ser más detallados o actuales.[10]
- **EBA DGS data:** publicación estadística anual de fondos/depósitos cubiertos, con foto al 31 de diciembre; no representa cambios posteriores ni términos de una cuenta concreta.[11]
- **ECB MFI lists:** documentación indica actualización diaria de MFI y CSV tab-delimited.[12] No se validaron columnas o tamaño del fichero.[12] El intento a la página legacy devolvió 404 y otro alias del Data Portal redirigió a una página de non-bank financial corporations; por tanto el enlace vigente del CSV MFI sigue sin verificar.[12]
- **Pruebas de acceso:** el antiguo URL EBA respondió con una redirección a un formulario ajeno; el nuevo enlace EBA devolvió solo un shell SPA HTML de 685 bytes. No se llegó a filas/exportación. No se encontraron cuotas o licencias de reutilización de EBA/ECB en esta pasada.[10][11][12]

## Unión propuesta en PostgreSQL

1. **`legal_entity(lei PK, legal_name, country, legal_form, lei_status, registered_at, last_update_at, source_id, observed_at)`**: un LEI por entidad legal; conservar alias y domicilios en tablas hijas. **`entity_relationship(parent_lei, child_lei, relationship_code, relationship_status, valid_from, valid_to, source_id, observed_at)`**: conservar código y fechas tal como los comunica GLEIF, no inferir control si la relación no está reportada.[6][7]
2. **`security(isin, asset_type, cfi, name, issuer_lei nullable, source_record_id, effective_at, observed_at)`**: ISIN es identificador del instrumento/clase, no del ticker.[13] Si el registro trae LEI de emisor, unir exacto; si no, dejarlo pendiente de reconciliación, no hacer merge automático por nombre.[6][13]
3. **`share_class(class_id, isin UNIQUE, fund_entity_lei nullable, cnmv_registry_id nullable)`**: cada clase/serie de fondo conserva su ISIN propio.[13] **`listing(listing_id, isin, mic, figi, composite_figi, share_class_figi, ticker, quote_currency, valid_from, valid_to, source_id, observed_at)`**: clave natural de reconciliación `(ISIN, MIC, vigencia)`; permitir varias plazas/tickers y no usar ticker como PK. Usar FIRDS para identidad/estado del venue y OpenFIGI como crosswalk; mantener el payload por fuente y la multiplicidad de resultados.[1][13]
4. **`fund_registration(authority, registry_number, cnmv_nif, legal_entity_id, registration_date, status, source_record_id, checked_at)`**: el nº/NIF de CNMV no es ISIN ni debe reemplazar al LEI.[9] Solo enlazar a una clase cuando una fuente lo haga explícitamente; el listado probado presentó número/fecha y detalle, no una clave de clase verificada.[9]
5. **`bank_entity(bank_id, national_id, lei, country, authority_status, source_id)`**, **`bank_dgs_membership(bank_id, dgs_id, valid_from, valid_to, source_id, checked_at)`** y **`deposit_guarantee_scheme(dgs_id, jurisdiction, name, published_parameters, reference_date)`**: mantener pertenencia bancaria a DGS separada de elegibilidad de cada depósito.[10][11]
6. **`offer_availability(product_id, provider_id, country_of_residence, customer_segment, channel, minimum_balance, rate_terms, status, evidence_url, checked_at, valid_from, valid_to)`** debe venir de T&C/oferta del proveedor y discriminar titular, residencia, saldo, dinero nuevo, plazo y canal.[10] Ningún campo de FIGI/ISIN/LEI/registro sustituye esa evidencia.[10][14]

> **Límite de elegibilidad:** ni una cotización/listing español ni la inscripción de un fondo como UCITS acredita que ese ISIN/clase pueda contratarse desde cada broker o para cada cliente.[9] El registro CNMV es un estado regulatorio; la disponibilidad minorista es una entidad/oferta/canal/cliente/fecha distinta.[14] Del mismo modo, pertenecer a un DGS no prueba que todos los tipos o importes estén cubiertos.[10]

## Solicitudes mínimas (solo GET, sin key)

Los cuerpos/headers relevantes están guardados en `docs/investigacion-apis-02/evidencia/`; el detalle máquina-legible está en `06-hallazgos.json`.

| Prueba | Resultado observado | Lectura |
|---|---|---|
| OpenFIGI `GET /v3/mapping/values/idType` | 200 JSON, 465 B; `values[]` incluye `ID_ISIN`, `TICKER`. | Confirma enum, no prueba correspondencia ISIN→ticker. El mapping documentado requiere POST y se dejó sin llamar.[1] |
| GLEIF `GET /api/v1/lei-records?filter[lei]=HWUPKR0MPOU8FGXBT394&page[size]=1` | 200 JSON, 3.460 B; Level 1: `entity`, `registration`, `lei`; muestra Apple Inc. | Una entidad real funciona sin key; no extrapolar al registro entero ni a Level 2.[6] |
| CNMV listado `id=26` | 200 HTML, 268.783 B; 10 etiquetas de número/fecha y página de 124 páginas. | Es una lista navegable, no un dump/clase-ISIN verificado.[9] |
| ESMA FIRDS index, `rows=3&sort=publication_date desc` | 200 JSON, 1.583 B; metadata de DLTINS 2026-10-26 y 2026-10-25. | Buen primer paso para descubrir descargas; no se descargó el contenido XML/ZIP.[13][16] La consulta sin `sort` devolvió primero un archivo antiguo de 2017, demostrando que hay que ordenar por fecha.[16] |
| EBA CIR / ECB | EBA: redirect antiguo a formulario y nuevo shell SPA de 685 B; ECB legacy MFI 404, Data Portal alias acabó en HTML non-bank de 646.135 B. | La documentación confirma la existencia/periodicidad de las listas, pero el endpoint directo de datos sigue pendiente.[10][12] |

**Pendiente decisivo:** recuperar una muestra de clase ISIN de fondo, un XML FIRDS de tamaño acotado y los enlaces/formatos actuales EBA/ECB; comprobar términos de reutilización CNMV/ESMA/EBA/ECB.[9][13][12] Ninguno de estos límites invalida las consultas públicas ya probadas; impiden afirmar que el catálogo o la descarga completa estén integrados.

## Sources

[1] https://openfigi.com/api/documentation
[2] https://openfigi.com/docs/faqs
[6] https://api.gleif.org/docs
[7] https://gleif.org/en/meta/lei-data-terms-of-use
[9] https://www.cnmv.es/portal/consultas/mostrarlistados.aspx?id=26&lang=es
[10] https://eba.europa.eu/risk-analysis-and-data/credit-institutions-register
[11] https://eba.europa.eu/activities/single-rulebook/regulatory-activities/depositor-protection/deposit-guarantee-schemes-data
[12] https://www.ecb.europa.eu/stats/financial_corporations/list_of_financial_institutions/html/index.en.html
[13] https://www.esma.europa.eu/sites/default/files/library/esma65-8-5014_firds_-_instructions_for_download_of_full_and_delta_reference_files.pdf
[14] https://www.cnmv.es/portal/Utilidades/NotaLegal.aspx
[16] https://registers.esma.europa.eu/solr/esma_registers_firds_files/select?q=%2A&wt=json&indent=true&start=0&rows=3&sort=publication_date+desc
