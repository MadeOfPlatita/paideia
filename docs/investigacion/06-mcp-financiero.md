# MCP financiero y APIs reutilizables para Paideia

**Revisión:** 26-10-2026. **Alcance:** servidores MCP, agregadores financieros, fuentes oficiales UE/España, búsqueda documental y cálculo. Se contrastaron README, manifiestos, licencias y fechas de actividad de GitHub obtenidas de su API. No se instaló ni ejecutó código de terceros.

## Conclusión ejecutiva

**Para una semana y presupuesto de 0 €, API directa más un pequeño catálogo curado es mejor que desplegar un agregador MCP.** MCP normaliza cómo un cliente de IA invoca herramientas o accede a recursos; no es una base financiera, no concede derechos sobre los datos y no actualiza nada por sí mismo.[1] OpenBB es el mejor candidato si luego Paideia necesitase exponer varios proveedores al LLM, pero sigue siendo software que hay que configurar y alojar y sus conectores heredan límites y términos del proveedor.[2][3]

Los endpoints oficiales de ECB y Eurostat sí sirven para estadísticas y contexto macro; Tesoro publica resultados de subastas y ficheros mensuales; BOE sirve para búsqueda documental. **Eso no equivale a una fuente pública única que mantenga diariamente cuentas/de depósitos, fondos/ETF y cotizaciones de deuda secundaria con derecho de redistribución.** En la búsqueda no se verificó una API pública gratuita que cubra ese catálogo comercial completo. Para MVP, limitar el universo, citar la fuente y fecha por campo, y no prometer actualización diaria para datos que no la tienen.

## Qué repositorios aportan valor

### Agregadores y datos de mercado

- **OpenBB ODP V5 — `OpenBB-finance/OpenBB`.** `openbb-mcp-server` convierte rutas de la REST API OpenBB en herramientas MCP; se instalan aparte los paquetes de proveedor elegidos.[2]  
  `openbb-ecb` figura sin credenciales, pero OpenBB declara que no aloja ni sirve los datos y que cobertura, límites y términos los determina cada fuente.[3]  
  V5 está bajo Apache-2.0; esa licencia cubre el software, no los datos conectados.[4]  
  La última actividad que devolvió GitHub para la ruta de su extensión MCP fue el 17-10-2026.[5] **Valor:** buen patrón de agregación y un conector reutilizable para ECB. **No elegir para esta semana:** requiere empaquetado Python y una instancia disponible; no aporta por sí solo catálogo español de ofertas.

- **Financial Datasets MCP — `financial-datasets/mcp-server`.** Es una envoltura del API de Financial Datasets (estados financieros, precios, noticias y cripto); su README pide `FINANCIAL_DATASETS_API_KEY` y propone `mcp[cli]` + `httpx`.[6]  
  La licencia del repositorio es MIT,[43] pero el API subyacente no es gratis para el caso: la página muestra créditos desde **$20 por 1.000 peticiones**, plan Personal de **$200/mes** y Profesional de **$2.000/mes**, con derechos de redistribución indicados en el plan comercial.[7]  
  El último commit consultado es del 05-06-2025.[8] **Descartar:** presupuesto incompatible y foco de mercado no acredita cobertura de productos bancarios españoles.

- **`narumiruna/yfinance-mcp`.** MIT; usa Yahoo Finance a través de `yfinance` y ofrece instrumentos bursátiles, ETF y fondos.[9]  
  El manifiesto requiere Python ≥3.12 y depende, entre otros, de `mcp`, `yfinance`, `matplotlib`, `tabulate` y `loguru`.[10]  
  La actividad sí es reciente: último commit devuelto por GitHub el 25-10-2026.[11]  
  El proyecto upstream `yfinance` advierte que no está afiliado a Yahoo, usa sus APIs públicas y que Yahoo Finance API está destinada a uso personal.[12] **No usar para servir cotizaciones/datos a usuarios públicos** salvo que se obtenga permiso de uso y redistribución; MIT del wrapper no sustituye esa autorización. Tampoco cubre cuentas remuneradas ni depósitos.

- **Brave Search MCP — `brave/brave-search-mcp-server`.** MIT; da búsqueda web/noticias a través de Brave Search, no datos financieros estructurados.[13]  
  El paquete TypeScript depende de MCP SDK, `commander`, `dotenv`, `express` y `zod`.[14]  
  El servidor requiere `BRAVE_API_KEY`; la tarifa publicada para Search es $5 por 1.000 peticiones con $5 de crédito gratuito al mes.[13][15]  
  GitHub devolvió un commit del 26-10-2026 que actualiza dependencias.[16] **Útil solo si Paideia necesita búsqueda web en vivo**; para bibliografía fija, índice local y fuentes aprobadas reducen coste, latencia y riesgo de que Pai cite páginas no fiables.

### Documentos y cálculo

- **MCP Fetch — `modelcontextprotocol/servers/src/fetch`.** MIT; recibe una URL y extrae la página como Markdown; no busca documentos ni descubre URLs. Su README advierte que puede acceder a IP internas, así que no debe exponerse a URLs arbitrarias sin controles SSRF.[17]  
  Manifiesto Python: MCP SDK `<2`, `httpx`, `markdownify`, `protego`, `pydantic`, `readabilipy` y `requests`.[18]  
  El commit más reciente consultado para esa ruta fue 24-10-2026; el README todavía señala compatibilidad con SDK 1.x y port a v2 en progreso.[17][19] **Aprovechable como referencia de lectura, no como buscador ni backend público listo.**

- **Calculadora MCP — `cyanheads/calculator-mcp-server`.** Apache-2.0 y basada en `mathjs`; una herramienta evalúa expresiones, simplifica álgebra y deriva simbólicamente, pero no consulta precios ni verifica supuestos financieros.[20] El paquete requiere Node ≥24 o Bun ≥1.4 y depende de `mathjs`, MCP core y `zod`.[21] GitHub mostró versión 0.5.2 publicada el 25-10-2026.[22] **Paideia debería calcular interés, inflación y escenarios en código determinista propio con pruebas y supuestos visibles**; MCP calculator solo tendría sentido para una función matemática general invocada por el LLM.

- **`elcukro/bank-mcp` — no confundir con comparador de cuentas.** MIT, acceso de solo lectura a cuentas y transacciones personales con Plaid, Teller, Enable Banking y Tink; el README también lista un proveedor `Mock`.[23] Sus credenciales dependen del proveedor (p. ej. clave RSA/sesión, OAuth2, certificado o client ID/secret); el paquete usa MCP SDK, JWT y Zod.[23][24] El último commit consultado es 23-02-2026 y el repositorio no acredita las tarifas de cada proveedor.[25] **No encaja:** conecta cuentas del usuario y procesa información financiera personal; no ofrece catálogo de depósitos comerciales.

### Ejemplo que sí es mock

- **`DheerajGavhane/Mcp`** se presenta explícitamente como “Mock Financial Data MCP Server”; el README enumera `credentials.json` y directorios de datos de prueba, no un API financiero ascendente.[26] El `package.json` declara ISC y su test es un placeholder que termina con error; GitHub informa `license: null`, de modo que la licencia del repositorio queda sin confirmar, y su última subida registrada fue 21-11-2025.[27][28] **Excluir como fuente de datos y como dependencia de producción.** En otros repos, un modo mock puede ser solo para tests/demos: comprobar que la configuración activa consulta al proveedor real y nunca presentar respuestas de prueba como datos verificados.

## APIs primarias UE/España: qué cubren y qué no

- **ECB Data Portal.** API REST SDMX 2.1 para datos estadísticos y metadatos, con recuperación y descubrimiento.[29] El ECB permite reutilizar gratuitamente estadísticas públicas si se cita la fuente y no se alteran datos/metadatos; la excepción de terceros requiere permiso.[30] Es adecuada para referencias macro, tipos o series temporales, no para comparar condiciones comerciales de cada banco.

- **Eurostat.** Documenta APIs REST Statistics, SDMX 2.1/3.0 y Catalogue para datos, metadatos y descubrimiento.[31]  
  La API proporciona acceso programático gratuito; los datasets se actualizan dos veces al día solo cuando hay datos nuevos o cambios estructurales, no son cotizaciones intradía.[32][44]  
  Eurostat permite reutilizar datos con atribución, con derechos de terceros como excepción.[33]

- **Banco de España.** Servicio estadístico JSON por URL para consultar último dato o series; la respuesta documenta frecuencia D/M/Q/A, fecha de referencia y valor.[34] Útil para tipos y series españolas. La página API consultada no deja clara una licencia de redistribución; verificarla antes de publicar copias/cache.

- **Tesoro Público.** La página oficial de Letras publica fechas de subasta/vencimiento, precios y tipos marginales; son resultados de subasta, no precio secundario continuo de cada emisión.[35] El portal ofrece estadísticas mensuales de deuda, subastas y mercado secundario en PDF/XLSX; la página consultada no documenta un endpoint REST.[36] Buen origen oficial para un panel de subastas o serie histórica, con fecha/frecuencia explícitas; comprobar términos de reutilización antes de redistribuir.

- **CNMV y BME para fondos/ETF.** La orientación CNMV explica que el valor liquidativo aplicable a un fondo suele publicarse al día siguiente; para ETF el precio de mercado es público durante la orden.[37] La página consultada no es una API de cotizaciones masiva. BME comercializa datos de mercados y su acuerdo de difusión incluye catálogo y lista de tarifas/precios.[38] BME mantiene una oferta diferenciada de fin de día/históricos con categorías que incluyen ETF.[39] **No asumir que un feed diario de ETF/fondos puede redistribuirse gratis.** Para el MVP, usar documentación CNMV/DFI y datos publicados por cada gestora con fecha, o reducir el alcance; cotizaciones secundarias requieren validar licencia/precio de BME u otro proveedor.

- **BOE para búsqueda documental.** Su API documenta búsquedas de legislación consolidada; la API REST permite acceder a sumarios diarios y enlaces a documentos PDF/XML/HTML.[40][41] Las condiciones del BOE permiten reutilización comercial y no comercial, pero obligan a respetar atribución y condiciones especiales aplicables.[42] Es una opción primaria para normativa/glosario documentado, no para datos de rendimiento.

## Recomendación de arquitectura de una semana

1. **No desplegar un MCP financiero ahora.** En una web pública, un proceso MCP local/stdio no sirve a los visitantes: la ruta OpenBB muestra que hay que arrancar el servidor y mantenerlo accesible por HTTP o lanzarlo como proceso del cliente.[2] Añadir un servidor remoto supone otro servicio, credenciales y controles; MCP no elimina ese trabajo.
2. **Integrar por HTTP directo solo lo que tenga fuente clara:** ECB/Eurostat para estadísticas europeas; Banco de España para series nacionales; Tesoro para subastas y XLSX; BOE para normas. Guardar para cada campo `source`, `retrieved_at`, fecha efectiva del dato y estado de frescura.  
   ECB y Eurostat sí documentan condiciones de reutilización.[30][33]  
   Para BDE/Tesoro confirmar las condiciones aplicables antes de redistribuir.[34][36]
3. **Para cuentas/de depósitos/fondos, seleccionar pocos productos verificables** desde fichas oficiales de bancos/gestoras y documentos CNMV, con captura de URL y fecha de revisión. No afirmar “actualizado diariamente” salvo que el proveedor publique realmente esa cadencia. Las condiciones comerciales, límites, comisiones, mínimos, disponibilidad y fecha efectiva deben ser campos separados.
4. **Separar precio/escenario de explicación.** Calcular importes en el frontend/backend de Paideia con funciones probadas y reglas explícitas. Pai puede explicar los supuestos y citar la ficha; no debe inventar un tipo o completar silenciosamente datos ausentes.
5. **Documentos:** BOE REST para corpus normativo seleccionado; buscar en biblioteca curada con índice local.[40][41]  
   Añadir Brave solo si hace falta búsqueda abierta y se acepta API key/cuota.[13][15]  
   Fetch no debe exponerse como proxy público sin protección SSRF.[17]
6. **No pedir ni procesar credenciales bancarias.** `bank-mcp` accede a cuentas/transacciones y no es una base de ofertas.[23][24]  
   No usar ejemplos de mock para contratación o datos reales; la contratación de Paideia sigue siendo una simulación explícita y sin operaciones reales.[26][27]

**Decisión:** prototipo con APIs directas + catálogo pequeño, no un agregador MCP. Reevaluar OpenBB/Brave cuando Paideia tenga un LLM con cliente MCP real, presupuesto para datos y alojamiento, y términos de redistribución resueltos. La investigación de repositorios fue documental; no se ejecutaron servidores, pruebas ni respuestas de APIs.

## Sources

[1] https://modelcontextprotocol.io/introduction — What is the Model Context Protocol (MCP)?
[2] https://docs.openbb.co/odp/python/quickstart/mcp — MCP Server | OpenBB Docs
[3] https://docs.openbb.co/odp/python/extensions/providers — Providers | OpenBB Docs
[4] https://docs.openbb.co/odp/python/faqs/license — License | OpenBB Docs
[5] https://api.github.com/repos/OpenBB-finance/OpenBB/commits?path=openbb_platform/extensions/mcp_server&per_page=1 — GitHub API — latest commit touching OpenBB MCP extension
[6] https://github.com/financial-datasets/mcp-server/blob/main/README.md — Financial Datasets MCP Server README
[7] https://financialdatasets.ai/pricing — Pricing | Financial Datasets
[8] https://api.github.com/repos/financial-datasets/mcp-server/commits?per_page=1 — GitHub API — latest Financial Datasets MCP commit
[9] https://github.com/narumiruna/yfinance-mcp — narumiruna/yfinance-mcp — GitHub repository
[10] https://raw.githubusercontent.com/narumiruna/yfinance-mcp/main/pyproject.toml — narumiruna/yfinance-mcp pyproject.toml
[11] https://api.github.com/repos/narumiruna/yfinance-mcp/commits?per_page=1 — GitHub API — latest yfinance-mcp commit
[12] https://github.com/ranaroussi/yfinance/blob/main/doc/source/index.rst — yfinance legal disclaimer
[13] https://github.com/brave/brave-search-mcp-server — brave/brave-search-mcp-server — GitHub repository
[14] https://raw.githubusercontent.com/brave/brave-search-mcp-server/main/package.json — Brave Search MCP package.json
[15] https://brave.com/search/api — Brave Search API pricing
[16] https://api.github.com/repos/brave/brave-search-mcp-server/commits?per_page=1 — GitHub API — latest Brave Search MCP commit
[17] https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/fetch/README.md — Model Context Protocol fetch server README
[18] https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/fetch/pyproject.toml — Model Context Protocol fetch server pyproject.toml
[19] https://api.github.com/repos/modelcontextprotocol/servers/commits?path=src/fetch&per_page=1 — GitHub API — latest fetch server commit
[20] https://github.com/cyanheads/calculator-mcp-server — cyanheads/calculator-mcp-server — GitHub repository
[21] https://raw.githubusercontent.com/cyanheads/calculator-mcp-server/main/package.json — cyanheads calculator server package.json
[22] https://api.github.com/repos/cyanheads/calculator-mcp-server/commits?per_page=1 — GitHub API — latest calculator MCP commit
[23] https://github.com/elcukro/bank-mcp — elcukro/bank-mcp — GitHub repository
[24] https://raw.githubusercontent.com/elcukro/bank-mcp/main/package.json — elcukro/bank-mcp package.json
[25] https://api.github.com/repos/elcukro/bank-mcp/commits?per_page=1 — GitHub API — latest bank-mcp commit
[26] https://raw.githubusercontent.com/DheerajGavhane/Mcp/main/README.md — DheerajGavhane/Mcp README — Mock Financial Data MCP Server
[27] https://raw.githubusercontent.com/DheerajGavhane/Mcp/main/package.json — DheerajGavhane/Mcp package.json
[28] https://api.github.com/repos/DheerajGavhane/Mcp — GitHub API — DheerajGavhane/Mcp repository metadata
[29] https://data.ecb.europa.eu/help/api/overview — ECB Data Portal API overview
[30] https://ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html — Policy regarding the reuse of ESCB statistics
[31] https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started — Eurostat API — Getting started
[32] https://ec.europa.eu/eurostat/data/web-services — Web services | Eurostat
[33] https://www.ec.europa.eu/eurostat/en/help/copyright-notice — Copyright notice and free re-use of data | Eurostat
[34] https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html — Servicio web de Estadísticas (API) | Banco de España
[35] https://tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas/letras-del-tesoro — Resultado de últimas subastas | Tesoro Público
[36] https://www.tesoro.es/deuda-publica/estad%C3%ADsticas-mensuales — Estadísticas Mensuales | Tesoro Público
[37] https://cnmv.es/portal/inversor/fondos-como-invertir?lang=en — CNMV — How to invest in funds: subscriptions, redemptions and transfers
[38] https://www.bolsasymercados.es/en/bme-exchange/prices-and-markets/market-data-services.html — Market Data Services | BME Exchange
[39] https://www.bolsasymercados.es/en/bme-exchange/prices-and-markets/market-data-services/end-of-day-and-historical-services.html — End of day and historical | BME Exchange
[40] https://www.boe.es/datosabiertos/api/api.php — API de datos abiertos | BOE
[41] https://www.boe.es/datosabiertos/faq/boe.php — FAQ de datos abiertos | BOE
[42] https://www.boe.es/informacion/aviso_legal/index.php — Aviso legal y condiciones de reutilización | BOE
[43] https://api.github.com/repos/financial-datasets/mcp-server — GitHub API — Financial Datasets MCP repository metadata
[44] https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction — API - Introduction | Eurostat
