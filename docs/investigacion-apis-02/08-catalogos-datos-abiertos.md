# Catálogos y datasets abiertos adicionales para Paideia

**Fecha de comprobación:** 26-10-2026.[3][21] Alcance de esta ronda: descubrimiento de metadatos y peticiones GET públicas, sin credenciales ni instalación. No se volvieron a listar como hallazgo los endpoints agregados del BdE/BCE ni las series de Eurostat que ya constan en `docs/investigacion/01-cuentas-depositos.md` y `docs/investigacion/00-SINTESIS.md`.

## Conclusión ejecutiva

- **Mejor dato maestro español encontrado: el registro CNMV de IIC.** La ficha pública de un fondo aporta ISIN, número/fecha de registro, fechas de folleto y reglamento, gestora y depositaria.[2][3]
  El GET de ejemplo devolvió HTTP 200 y HTML legible; no ofrece la ficha como API tabular ni incluye TAE de depósito, NAV/precio o todos los costes.[2][3]
- **Mejor complemento de instrumentos: ESMA FIRDS.** Publica ficheros XML de referencia, completos y de cambios, con universo de instrumentos admitidos/negociados en centros regulados, MTF, OTF o SI.[9][24]
  La clave mínima documentada es `(ISIN, MIC)`; no equivale a un catálogo de ofertas minoristas ni a precios/rendimientos de deuda.[9][24]
- **Registro europeo de entidades: ESMA MiFID/UCITS/AIFMD.** Permite exportar resultados CSV; la ayuda describe identificadores/descripciones, actividades actuales e históricas, sanciones y estados miembro anfitriones.[7] Es dato maestro de entidades autorizadas, no ficha de producto. ESMA avisa que el registro puede no contener aún todos los datos nacionales.[7][19]
- **Contexto macro: OECD CPI y BIS FX/tipo de política.** El CSV OECD para España llega en esta extracción hasta diciembre de 2025; queda corto para inflación actual en octubre de 2026.[21]
  BIS publica la serie mensual España EUR/USD `M.ES.EUR.A` hasta 2026-09 y la mensual área euro `M.XM` de política monetaria, porcentual anual, hasta 2026-09.[26][27]
  Son referencias de escenario, no TAE ni ofertas; las páginas son metadatos de series, no una descarga de observaciones API probada.[16][17][21]
- **No confundir catálogo con dataset.** La entrada de datos.gob.es sobre IIC apunta a una página CNMV XHTML.[2]
  El API de catálogo de datos.gob.es respondió con lista vacía a la búsqueda por título y la consulta por URI dio HTTP 400.[20][22]
  La ficha de data.europa.eu de MiFID/UCITS/AIFMD indica cero distribuciones.[13]
  Son índices de descubrimiento, no un recurso de datos utilizable por sí mismos.[1][11]

## Hallazgos priorizados

### 1. CNMV — IIC registradas: mejor ancla española para fondos y contrapartes

La ficha de catálogo describe fondos y sociedades, depositarias, gestoras y entidades delegadas; su única distribución es XHTML a `EntRegIIC.aspx`, no CSV/API.[2] La consulta por entidad que probé devolvió una ficha real de OLEA NEUTRAL, FI con ISIN `ES0118537002`, registro `4231`, alta `14/05/2010`, folleto `01/10/2026`, reglamento `08/06/2026`, gestora `277` y depositaria `211`.[3]

**Importable a Postgres (conservando campo/fuente):** `isin`, `cnmv_register_no`, `legal_name`, `fund_type`, `registered_on`, `prospectus_date`, `rules_date`, `manager_register_no/name/address`, `depositary_register_no/name/address`, `prospectus_url`, `dfi_url`, `rules_url`, `source_url`, `retrieved_at`.[3] Crear entidades de gestora/depositaria separadas y enlazarlas por número de registro; guardar los PDF y su fecha aparte.[3] No hay en la ficha probada TAE, comisiones estructuradas, valor liquidativo ni cotización.[3]

**Frescura y derechos:** el catálogo marca actualización «continua», pero su intervalo temporal publicado tiene inicio y fin iguales en 1985-11-26; no usarlo como timestamp fiable.[2]
La página contiene fechas de los documentos, no un campo estructurado de modificación.[3]
La nota legal CNMV permite uso privado y sujeta usos distintos a condiciones (reproducción fiel/no alterada; condiciones adicionales si se vende o cede la información); no es una licencia abierta CC.[4]
Revisión legal antes de republicar o automatizar.[4]

### 2. ESMA — FIRDS + registro de entidades: referencia europea, no economía contractual

FIRDS expone ficheros machine-readable completos, delta y cancelaciones; la documentación indica Full semanal (domingo antes de 09:00 CET) y Delta/cancelaciones diarias (antes de 09:00 CET).[24] El esquema se divide por ficheros XML y el conjunto se identifica por `(ISIN, MIC)`; el `LastUpd` y la bandera `IncnsstncyInd` solo se garantizan para el fichero completo destinado a NCA, no asumir que aparezcan en cada fichero público.[24] El portal explica que los cambios pueden publicarse a diario y que no garantiza integridad, exactitud o actualidad; conservar la fecha del fichero y hacer reconciliación.[9]

**Importable tras validar XSD:** `isin`, `mic`, `file_date`, `file_kind` (`FULINS`/`DLTINS`/cancelación), `record_action`, `raw_record jsonb`; añadir `RefData/TechAttrbts/LastUpd` y `IncnsstncyInd` solo si están efectivamente presentes en el archivo consumido.[24] Usar `ISIN+MIC+fecha/fuente` como clave versionada, no sobrescribir el histórico.[24] La documentación enlaza esquemas XML para FULINS, DLTINS y CANINS.[24]

El registro ESMA de entidades tiene exportación CSV; si se incluye metadata, la documentación dice que contiene timestamp actual, nombre del registro, disclaimer, columnas y resultados.[7]
La ayuda enumera identificador/descripción, actividades actuales, historial de actividades, sanciones y estados miembro anfitriones; validar en el CSV nombres técnicos de LEI/autoridad antes de mapearlos.[7]
El acceso M2M se describe para organizaciones de gran escala; ESMA advierte que algunos datos nacionales aún pueden faltar.[19]
La licencia/reutilización concreta de datos ESMA no quedó confirmada; el aviso legal asociado debe revisarse antes de publicar.[19]

### 3. Macro para escenarios — CPI OECD (histórico) y series BIS de FX/tipo identificadas

La petición de prueba a OECD fue HTTP 200, CSV SDMX, y el archivo incluyó 24 observaciones mensuales de crecimiento interanual y 24 del índice para `REF_AREA=ESP`, de 2024-01 a 2025-12.[21]
Para diciembre de 2025 la fila interanual trae `OBS_VALUE=2.924468`, `TRANSFORMATION=GY`, `UNIT_MEASURE=PA`; debe preservar la unidad y el periodo, no redondear ni presentar como cifra vigente en 2026.[21]
OECD declara API sin cargo sujeta a sus términos y limita el servicio a 60 descargas de datos por hora; además bloquea tráfico desde VPN/anónimo.[16][17]

BIS ya permite fijar dos series concretas desde sus páginas: `BIS,WS_XRU,1.0/M.ES.EUR.A`, tipo bilateral España EUR/USD, mensual, cobertura mostrada 1957-01–2026-09; y `BIS,WS_CBPOL,1.0/M.XM`, tipo de política del área euro, mensual y en porcentaje anual, 1999-01–2026-09.[26][27]
El dataset XRU expresa USD frente a monedas locales y combina fuentes oficiales; la serie de política no debe equipararse automáticamente a un único tipo BCE sin leer su metadata.[28][29]
Se extrajeron las páginas de serie, no las observaciones por SDMX; antes de conectar, validar convención de cotización, instrumento subyacente y condiciones de uso (la exportación remite a términos BIS).[26][27][30]
La especificación BIS es SDMX REST 2.1.[18] DBnomics sigue siendo agregador útil para series homogéneas; su documentación recomienda consultas focalizadas.[14] Sus términos mantienen licencia/términos del proveedor original, incluso cuando los agregados se publican bajo ODbL.[15]

**Resultado financiero:** no apareció una fuente nueva de TAE/TIN de depósitos españoles por entidad/producto en los registros revisados.[2][5]
Para datos maestros reales, priorizar CNMV/ESMA; para escenarios, OECD/BIS/DBnomics claramente segregados.[2][9][21]
Las series macro mensuales/anuales no deben llenar campos de oferta.[21]
BdE/BCE y Eurostat quedan referenciados a la ronda anterior, sin duplicar su descripción aquí.

## Catálogos y rutas exactas

| Fuente | Recurso y endpoint exacto | Cobertura/actualización | Acceso, límites y derechos | Estado |
|---|---|---|---|---|
| Datos.gob.es API | `https://datos.gob.es/apidata/catalog/dataset/title/{title}?_format=json`; operaciones documentadas también `/catalog/dataset`, `/publisher/{id}`, `/theme/{id}`, `/keyword/{keyword}`, `/format/{format}` | Metadatos del catálogo, no datos fuente; formatos JSON/XML/RDF/TTL/CSV.[1] | No encontré cuota numérica. Condiciones dependen de cada distribución; no heredar licencia del portal.[1][2] | GET de búsqueda 200 JSON, 0 elementos; ruta por URI probada por separado, 400.[20][22] |
| CNMV — IIC | `https://www.cnmv.es/Portal/Consultas/EntRegIIC.aspx`; ejemplo de ficha `https://www.cnmv.es/portal/consultas/iic/fondo?lang=es&nif=V85962447` | IIC nacionales y entidades relacionadas. Catálogo dice «continuo»; ficha tiene fechas de documentos.[2][3] | XHTML, no endpoint tabular; CNMV sin licencia abierta y con condiciones de reproducción/uso.[2][4] | Ficha de fondo GET 200 HTML; registro real con ISIN/gestora/depositaria.[3] |
| CNMV — códigos ISIN | `https://www.cnmv.es/Portal/ANCV/ConsultaISIN.aspx` | ISIN asignados por ANCV (prefijo ES) y extranjeros admitidos a negociación en mercados oficiales españoles.[5] | Distribución catalogada como XHTML. Consulta, no feed masivo; condiciones CNMV.[5][4] | Documentado, no probado como servicio por ISIN en esta ronda. |
| CNMV — series estadísticas | `https://www.cnmv.es/Portal/Publicaciones/SeriesWeb/Inicio.aspx?codrama=952`; ficha catálogo: `https://datos.gob.es/es/catalogo/ea0042970-series-estadisticas-de-la-cnmv` | Catálogo anuncia >6.000 series de emisores/cotizadas, IIC y ESI y descarga Excel; `codrama=952` es la rama de Servicios de Inversión y no se verificó que sea una serie IIC.[23] | Excel/web, no API abierta identificada; derechos CNMV.[4][23] | Documentado. Más útil como contexto/series institucionales que como datos maestros de ofertas. |
| ESMA FIRDS | `https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_firds_files`; instrucciones `https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files` | Instrumentos reportados a ESMA por centros de negociación/autoridades; ficheros full, delta y cancelaciones, calendario semanal/diario según tipo.[8][9][24] | Portal público, ficheros voluminosos y particionados; sin cuota/tarifa abierta identificada. Permisos de redistribución sin confirmar; disclaimer niega garantía de integridad/actualidad.[9][24] | Documentado, archivo no descargado en esta prueba.[10] |
| ESMA entities | `https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_upreg` | Gestoras UCITS, AIFM, empresas de inversión y otras entidades; incluye datos de autorización/jurisdicción.[6][7][19] | CSV exportable; M2M señalado para grandes organizaciones; no encontré cuota ni licencia de reutilización publicada en el material extraído.[7][19] | Documentado; export no descargado. |
| data.europa.eu / DCAT-AP | SPARQL `https://data.europa.eu/data/sparql?locale=en` (GET o POST documentados); consultar DCAT Dataset/Distribution y `dcat:accessURL`/licencia | Metadatos RDF/DCAT-AP de catálogos/datasets europeos, no sus datos por defecto.[11] | Sin autenticación/cuota declaradas en la documentación consultada; permiso lo fija cada distribución.[11] | Documentado, no consultado en SPARQL. Dataset ESMA MiFID/UCITS mostrado por portal con **0 distribuciones**.[12][13] |
| DBnomics | Base `https://api.db.nomics.world/v22/`; patrones documentados `/providers/{provider}`, `/datasets/{provider}/{dataset}`, `/series/{provider}/{dataset}/{series}` | Series económicas de varios proveedores, no un maestro de fondos/depósitos.[14] | Sin límite numérico verificado; términos del proveedor original; ODbL para agregados DBnomics, no licencia automática de upstream.[14][15] | Documentado, sin llamada de datos en esta ronda. |
| OECD CPI / SDMX | Endpoint probado exacto: `https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,/.M.N.CPI.._T.N.GY+_Z?startPeriod=2024-01&dimensionAtObservation=AllDimensions&format=csvfilewithlabels` | CPI/HICP, en la extracción España 2024-01–2025-12; mensual, total, no ajustado, cambio interanual e índice.[21] | Sin cargo sujeto a términos OECD; máximo oficial indicado: 60 descargas/hora. No aceptar tráfico VPN/anónimo.[16][17] | GET 200 CSV; no suficientemente fresco para actualidad a octubre de 2026.[21] |
| BIS SDMX — FX y política monetaria | FX series page `https://data.bis.org/topics/CPMI_CT/BIS,WS_XRU,1.0/M.ES.EUR.A` (`BIS,WS_XRU,1.0`, key `M.ES.EUR.A`); policy page `https://data.bis.org/topics/CBPOL/BIS,WS_CBPOL,1.0/M.XM` (`BIS,WS_CBPOL,1.0`, key `M.XM`); API spec `https://stats.bis.org/api-doc/v2/` | FX mensual EUR/USD España: 1957-01–2026-09. Política monetaria mensual área euro: 1999-01–2026-09, `% per year`.[26][27] | Portal remite a términos de uso al exportar; cuota/precio/licencia de redistribución no comprobados.[26][27][30] | Páginas oficiales de serie extraídas y claves verificadas; no se descargaron observaciones SDMX. |


**CKAN, sin atribuirle universalidad:** la guía de datos.gob.es documenta el portal CKAN del MITECO y su ruta de búsqueda `https://catalogo.datosabiertos.miteco.gob.es/catalogo/api/3/action/package_search?q=natura%202000&rows=3`.[25]
El catálogo trata medio ambiente, agua, energía y temas afines, no productos de inversión; por ello no entra en la shortlist financiera.[25]
CKAN Action API es específica de cada portal, no el endpoint de una fuente bancaria común.[25]

## Esquema Postgres inicial (propuesta, no todas las columnas están disponibles en cada fuente)

```sql
CREATE TABLE source_snapshot (
  source_id text NOT NULL,
  source_url text NOT NULL,
  retrieved_at timestamptz NOT NULL,
  published_at timestamptz,
  effective_period text,
  license_or_terms text,
  raw_sha256 text,
  PRIMARY KEY (source_id, retrieved_at)
);

CREATE TABLE cnmv_iic_class (
  isin char(12) PRIMARY KEY,
  cnmv_register_no integer,
  legal_name text NOT NULL,
  fund_type text,
  registered_on date,
  prospectus_date date,
  rules_date date,
  manager_register_no integer,
  manager_name text,
  manager_address text,
  depositary_register_no integer,
  depositary_name text,
  depositary_address text,
  prospectus_url text,
  dfi_url text,
  rules_url text,
  source_url text NOT NULL,
  retrieved_at timestamptz NOT NULL
);

CREATE TABLE esma_instrument_reference (
  isin text NOT NULL,
  mic text NOT NULL,
  file_date date NOT NULL,
  file_kind text NOT NULL,
  record_action text,
  raw_record jsonb NOT NULL,
  last_received_at timestamptz,
  inconsistency_flag boolean,
  source_url text NOT NULL,
  retrieved_at timestamptz NOT NULL,
  PRIMARY KEY (isin, mic, file_date, file_kind)
);

CREATE TABLE macro_observation (
  provider text NOT NULL,
  dataset_code text NOT NULL,
  ref_area text NOT NULL,
  frequency text,
  methodology text,
  measure text,
  unit_measure text,
  expenditure text,
  adjustment text,
  transformation text,
  time_period text NOT NULL,
  obs_value numeric,
  obs_status text,
  unit_mult text,
  base_period text,
  decimals integer,
  retrieved_at timestamptz NOT NULL,
  source_url text NOT NULL,
  series_key text NOT NULL,
  PRIMARY KEY (provider, dataset_code, series_key, time_period, retrieved_at)
);
```

**Reglas de ingestión:** no convertir `last_modified` HTTP en fecha efectiva del dato; conservar `TIME_PERIOD`/fechas de documento, unidad y estado de observación; versionar ficheros FIRDS por publicación; no rellenar TAE con CPI, MIR, TEDR ni otro benchmark macro.[3][21][24]
Antes de producción, añadir parser XLS/PDF/XML y validación de XSD, licencias y elegibilidad España.[4][24]

## Pruebas mínimas GET y evidencias guardadas

Se probaron tres rutas fuente (catálogo datos.gob, ficha CNMV y CPI OECD).[20][3][21]
La respuesta vacía de catálogo motivó una única comprobación adicional por URI, que dio 400; no se insistió.[20][22]
Las respuestas exitosas originales están guardadas sin reserializar:

1. **Datos.gob, búsqueda IIC:** HTTP 200, `application/json`; JSON Linked Data API con claves `format`, `version`, `result`; `result.items=[]`, `itemsPerPage=10`.[20]
   No demuestra que no exista el dataset: solo que esta búsqueda exacta no lo devolvió.[20]
   `evidence/01-datosgob-iic-api.raw`.[20]
2. **CNMV OLEA NEUTRAL, FI:** HTTP 200, `text/html; charset=utf-8`, 222.579 bytes.[3]
   Se observaron `ISIN`, Nº registro/fecha, fecha último folleto/reglamento, gestora y depositaria.[3]
   `evidence/02-cnmv-olea-neutral-register.raw`.[3]
3. **OECD CPI:** HTTP 200, CSV SDMX, 793.575 bytes.[21]
   Cabeceras concretas: `REF_AREA`, `FREQ`, `METHODOLOGY`, `MEASURE`, `UNIT_MEASURE`, `EXPENDITURE`, `ADJUSTMENT`, `TRANSFORMATION`, `TIME_PERIOD`, `OBS_VALUE`, `OBS_STATUS`, `UNIT_MULT`, `BASE_PER`, `DECIMALS` (además de labels).[21]
   Se filtró localmente `REF_AREA=ESP`, sin otra petición; periodo observado 2024-01–2025-12.[21]
   `evidence/03-oecd-cpi-spain.raw`.[21]
4. **Diagnóstico datos.gob por URI:** HTTP 400.[22]
   La excepción se registró, pero su cuerpo no se guardó; no se presenta como evidencia de cobertura.[22]
   `evidence_path=null`.[22]

## Próximos ensayos decisivos

1. Extraer tres fichas CNMV (fondo, sociedad y depositario), comparar URLs/fechas y conservar el PDF original; confirmar autorización de reutilización para una web no privada.[3][4]
   No interpretar la fecha del documento como actualización del portal.[2][3]
2. Descargar solo un fichero pequeño FIRDS desde el buscador público; comprobar XML/XSD, contenido España/MIC, fechas, actualizaciones y permisos.[8][24]
   Si no se puede seleccionar tamaño pequeño sin superar límites, parar antes de importar lote.[24]
3. Ejecutar query SPARQL por publisher CNMV para identificar qué distribuciones reales ofrece el grafo europeo; no confiar en un registro con `distributions=0`.[11][13]
4. En OECD, probar query acotada explícitamente a España y confirmar publicación 2026.[16][21]
   En BIS/DBnomics identificar primero el dataflow exacto de FX y tipo de referencia y comprobar unidad/licencia.[14][18]
   Mantener fuentes macro en esquema distinto al catálogo contractual.[21]

## Sources

[1] https://datos.gob.es/es/apidata — API - Datos.gob.es
[2] https://datos.gob.es/es/catalogo/ea0042970-instituciones-de-inversion-colectiva-iic-registradas-en-la-cnmv — Instituciones de Inversión Colectiva registradas en CNMV
[3] https://www.cnmv.es/portal/consultas/iic/fondo?lang=es&nif=V85962447 — CNMV OLEA NEUTRAL FI — registro y documentos
[4] https://www.cnmv.es/portal/Utilidades/NotaLegal?lang=es — CNMV Nota legal
[5] https://datos.gob.es/es/catalogo/ea0042970-consulta-de-codigos-isin-de-valores-en-la-cnmv — Consulta de códigos ISIN CNMV
[6] https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_upreg — ESMA MiFID/UCITS/AIFMD register search
[7] https://registers.esma.europa.eu/publication/helpPage — ESMA Registers — help
[8] https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_firds_files — ESMA FIRDS reference files search
[9] https://registers.esma.europa.eu/publication/details?core=esma_registers_firds — ESMA FIRDS register
[10] https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files — ESMA FIRDS download instructions
[11] https://data.europa.eu/en/about/sparql — data.europa.eu SPARQL documentation
[12] https://data.europa.eu/data/datasets/financial-instruments-reference-data-system?locale=en — data.europa.eu — ESMA FIRDS dataset
[13] https://data.europa.eu/data/datasets/fgfgfgfg?locale=en — data.europa.eu — MiFID/UCITS/AIFMD entities
[14] https://docs.db.nomics.world/web-api — DBnomics Web API docs
[15] https://docs.db.nomics.world/legal-terms — DBnomics legal terms
[16] https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html — OECD data via API
[17] https://www.oecd.org/en/data/insights/data-explainers/2024/11/Api-best-practices-and-recommendations.html — OECD API best practices
[18] https://stats.bis.org/api-doc/v2 — BIS Stats API v2
[19] https://registers.esma.europa.eu/publication/details?core=esma_registers_upreg&docId=ae47135 — ESMA MiFID/UCITS/AIFMD entity register detail
[20] https://datos.gob.es/apidata/catalog/dataset/title/Instituciones%20de%20Inversi%C3%B3n%20Colectiva%20(IIC)%20registradas%20en%20la%20CNMV?_format=json — Test API catálogo datos.gob.es: búsqueda IIC
[21] https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,/.M.N.CPI.._T.N.GY+_Z?startPeriod=2024-01&dimensionAtObservation=AllDimensions&format=csvfilewithlabels — Test OECD: CPI mensual
[22] https://datos.gob.es/apidata/catalog/dataset/http%3A%2F%2Fdatos.gob.es%2Fcatalogo%2Fea0042970-instituciones-de-inversion-colectiva-iic-registradas-en-la-cnmv?_format=json — Test datos.gob.es: acceso por URI (400)
[23] https://datos.gob.es/es/catalogo/ea0042970-series-estadisticas-de-la-cnmv — Series estadísticas de la CNMV
[24] https://www.esma.europa.eu/sites/default/files/library/esma65-8-5014_firds_-_instructions_for_download_of_full_and_delta_reference_files.pdf — ESMA FIRDS Reference Data System — download instructions
[25] https://datos.gob.es/ca/blog/api-en-las-administraciones-publicas-cuales-hay-y-como-utilizarlas — APIs en las Administraciones Públicas — datos.gob.es, CKAN/MITECO
[26] https://data.bis.org/topics/CPMI_CT/BIS,WS_XRU,1.0/M.ES.EUR.A — BIS XRU monthly Spain EUR/USD series
[27] https://data.bis.org/topics/CBPOL/BIS,WS_CBPOL,1.0/M.XM — BIS euro area central bank policy rate series
[28] https://data.bis.org/topics/XRU — BIS bilateral exchange rates topic
[29] https://data.bis.org/topics/CBPOL — BIS central bank policy rates topic
[30] https://data.bis.org/help/legal — BIS Data Portal — terms of permitted use
