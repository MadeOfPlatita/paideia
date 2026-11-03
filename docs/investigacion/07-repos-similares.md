# Repositorios open source similares a Paideia

## Conclusión ejecutiva

No encontré, en la muestra revisada, un repositorio que reúna para principiantes españoles perfil financiero, educación, chat con fuentes, comparador de cuentas/depósitos/deuda pública/fondos y datos diarios sin coste. Los proyectos se reparten entre asistentes de presupuesto, trackers de patrimonio, comparadores de un país/activo y plataformas profesionales.[3][25][30]

**Prioridad para un MVP Paideia:**
- Del comparador portugués tomar el esquema de producto, filtros de elegibilidad y trazabilidad, reescribiendo datos, fiscalidad y condiciones para España.[34][37][39]
- De *Which ETF?*, tomar la interacción de shortlist/compare y las fechas/calidad del dato, no sus precios.[30]
- De FinGenius, separar cálculos deterministas de la generación de texto.[9][11]
- Añadir RAG local sólo si el tiempo y el despliegue admiten Ollama/Qdrant.[1][6]
- Actual Budget, Wealthfolio y Ghostfolio sirven de referencias de presupuesto/gestión patrimonial, no de comparadores bancarios españoles.[18][22][25]
- FinRobot es referencia de cálculo/procedencia, no UX para principiantes.[15]

**Método y límites:** se leyeron README, licencia raíz y archivos fuente/manifiestos indicados en cada caso; también se consultó el último commit público de GitHub. No se clonó, instaló ni ejecutó ningún proyecto. Las operaciones de cálculo de FinGenius y del comparador portugués se observaron en código, pero no se probaron numéricamente. En los demás, las capacidades proceden de README/manifiestos: no se tratan capturas, vídeos o claims como prueba de comportamiento. Las licencias indicadas cubren el código de los archivos revisados, no automáticamente dependencias, marcas, datasets ni datos financieros de terceros.

## Selección (8 proyectos)

### 1. [FinGenius — asesor personal con herramientas](https://github.com/anujdevsingh/financial_genius_agent)
- **Licencia:** MIT comprobada en `LICENSE`.[4]
- **Stack:** Python/FastAPI, LangGraph, LangChain, Chroma y un dashboard web sencillo según el README.[3]
- **Diseño visto en código:** herramientas deterministas, retriever Chroma y agente ReAct con memoria por `thread_id`.[9][10][11]
- **Funcionalidad comprobada:** `calculators.py` contiene herramientas para presupuesto 50/30/20, fondo de emergencia, deuda, crecimiento de inversión y cuota de préstamo; `knowledge_base.py` inicializa una base financiera Chroma. La app está orientada a extractos/gastos personales, no a comparar productos españoles.[9][10]
- **Coste/credenciales:** `.env.example` marca `OPENAI_API_KEY` como requerida. OpenAI embeddings/modelo implican dependencia de proveedor y coste variable; no es una solución de coste cero tal cual.[12]
- **Mantenimiento:** último commit observado: 2026-06-26.[13]
- **Componente reutilizable:** la frontera entre calculadoras deterministas y LLM, más el patrón de registrar cada cálculo como tool. Reescribir fórmulas/supuestos, validar casos límite y adaptar idioma/moneda antes de usar; no presentar sus proyecciones como asesoramiento.[9][11]

### 2. [RukiAI — asistente personal local-first con RAG](https://github.com/anupPradhan0/Ruki_Ai)
- **Licencia y stack:** MIT comprobada en `LICENSE`. README describe React/TypeScript y Python/FastAPI con Mongo/Beanie, Qdrant y BM25; el manifest confirma `qdrant-client` y `rank-bm25`.[1][2][7]
- **Funcionalidad comprobada en la guía técnica:** separa base de conocimiento financiera y memoria por usuario; embeddings locales con Ollama; enrutado KNOWLEDGE/MEMORY/BOTH; recuperación híbrida vector + BM25, RRF/MMR y decaimiento temporal de memoria. El README ofrece Gemma local por defecto y proveedores cloud opcionales.[1][6]
- **Coste/credenciales:** con Ollama no se necesita API cloud para el modelo local, pero sí instalar/operar modelos y asumir el coste de cómputo; las opciones cloud requieren credenciales del usuario.[1][6]
- **Mantenimiento:** último commit observado: 2026-05-18.[8]
- **Componente reutilizable:** patrón de recuperación híbrida y memoria separada por usuario. No reutilizar su contenido financiero como fuente española: la base y los ejemplos están orientados a India; la arquitectura completa añade servicios que exceden una semana.[1][6]

### 3. [Portugal Term Deposit Comparator — comparador de depósitos](https://github.com/ricardoserodio/portugal-term-deposit-comparator)
- **Licencia y stack:** MIT comprobada en `LICENSE`; Python, Streamlit, pandas, Plotly y datos CSV.[34][35][36]
- **Funcionalidad comprobada en `src/calculator.py`:** filtra por importe, plazo, banco, elegibilidad de nuevos clientes/dinero y retirada anticipada; calcula interés bruto, retención, interés neto y monto final, y ordena resultados. README/CSV muestran enlace por producto a fuente y campos auditados.[37][39]
- **Coste/credenciales:** la comparación usa dataset local; `openai` aparece como dependencia para el flujo opcional de propuestas de validación asistida, no como requisito para calcular/rankear productos.[34][36]
- **Mantenimiento y frescura:** último commit observado: 2026-05-08. `metadata.json` fija referencia en 2026-05-08, avisa que no es tiempo real y deja pendientes algunas validaciones oficiales.[38][40]
- **Componente reutilizable:** patrón fuerte para Paideia: filtros de elegibilidad, cálculo bruto/neto y alertas se ven en código; README/CSV documentan fuentes y aprobación humana.[34][37][39]
- **No copiar:** dataset, tasa fiscal portuguesa (README usa 28%) ni condiciones bancarias: no son datos de España y requieren confirmación vigente.[34][38]

### 4. [Which ETF? — comparador/screener de ETFs](https://github.com/violettance/etf-dashboard)
- **Licencia y stack:** MIT comprobada en `LICENSE`; Next.js, React, TypeScript, Tailwind, Recharts, Zod y Vitest según README.[30][31]
- **Funcionalidad descrita:** buscador/filtros, shortlist y comparación de hasta cuatro fondos; detalle con historial Stooq y métricas de retorno, volatilidad, drawdown y Sharpe. La página declara que no recomienda fondos; el README describe un directorio de 4.148 fondos con captura histórica.[30]
- **Coste/credenciales y limitación clave:** screener/directorio sin API key; Alpha Vantage es opcional para sentimiento. Pero los 4.148 productos vienen de una captura Yahoo Finance de 2025-05-25; README advierte que campos de activos, yield, volumen y retornos son históricos. El historial Stooq puede fallar. El último commit de código observado es posterior, 2026-10-17: código reciente no equivale a dataset actualizado.[30][32]
- **Componente reutilizable:** interacción de comparación, visualización de fecha/fuente y separar campos verificados de desconocidos. No usar su universo/precios como datos actuales ni asumir derechos de redistribución de Yahoo/Stooq; sólo cubre ETFs cotizados en EE. UU.[30][31]

### 5. [FinRobot — investigación financiera con agentes](https://github.com/AI4Finance-Foundation/FinRobot)
- **Licencia:** Apache-2.0 comprobada en `LICENSE` raíz, `finrobot_desktop/LICENSE` y `pyproject.toml` de V2.[14][16][43]
- **Qué hace realmente según el subproyecto:** V2 es estación de investigación de renta variable con backend FastAPI/PydanticAI, React/Tauri/Rust, proveedores externos y operadores Python deterministas; el README declara auditoría de narrativa y pipeline tipado. V1 es un generador web de informes. El README de V0 lo clasifica como educativo y dice expresamente que no tiene cómputo determinista ni seguimiento de procedencia; no confundir generaciones.[5][15][42]
- **Coste/credenciales:** V1 pide claves OpenAI y Financial Modeling Prep; V2 también depende de proveedores de datos, por lo que no se debe suponer coste cero o funcionamiento offline completo.[41][44]
- **Mantenimiento:** último commit observado: 2026-10-24; V2 `pyproject.toml` lo marca como alpha pese al lenguaje de “production” del README.[16][17]
- **Componente reutilizable:** separación de cálculo, explicación y auditoría/procedencia como guía de diseño. No incorporar agentes de trading/backtesting ni replicar el stack profesional: es demasiado grande para dos personas/una semana y no es una UX para principiantes.[15][16]

### 6. [Wealthfolio — tracker local de inversiones y patrimonio](https://github.com/wealthfolio/wealthfolio)
- **Licencia y stack:** AGPL-3.0 comprobada en `LICENSE`; frontend TypeScript/React y app Tauri/Rust con almacenamiento SQLite según README y estructura/manifiesto.[18][19][20]
- **Funcionalidad descrita:** cuentas y activos, CSV, retornos time-weighted/money-weighted, benchmark, objetivos y simulaciones. El README asegura almacenamiento local sin cuenta; no se inspeccionó el módulo de simulación, así que esa parte queda como claim del proyecto, no como cálculo validado.[18]
- **Coste/credenciales:** seguimiento manual/CSV gratis; sincronización de más de 30 brokers en modo solo lectura y sync multidispositivo cifrado son un servicio opcional de suscripción. No necesita un LLM.[18]
- **Mantenimiento:** último commit observado: 2026-10-26.[21]
- **Componente reutilizable:** referencia fuerte para privacidad, cartera multi-activo y UX de objetivos; sólo copiar código si Paideia acepta las obligaciones copyleft de AGPL para una aplicación ofrecida por red. La marca/activos de marca tienen tratamiento separado.[18][19]

### 7. [Ghostfolio — gestión patrimonial open source](https://github.com/ghostfolio/ghostfolio)
- **Licencia y stack:** AGPL-3.0 comprobada en `LICENSE`; aplicación web TypeScript organizada como workspace Nx según README.[22][23]
- **Funcionalidad descrita:** seguimiento de acciones, ETFs y cripto para gestión de patrimonio personal; es tracker/analytics, no chatbot educativo ni comparador de condiciones bancarias.[22]
- **Coste/credenciales:** no requiere LLM. El README presenta Ghostfolio Premium como servicio cloud de pago y enumera claves CoinGecko Demo/Pro opcionales; self-hosting no garantiza datos profesionales gratuitos.[22]
- **Mantenimiento:** último commit observado: 2026-10-25.[24]
- **Componente reutilizable:** referencia de producto para dashboard, datos multi-activo y privacidad; AGPL-3.0 hace que sea mejor benchmark que código base si no se quiere asumir reciprocidad de licencia.[22][23]

### 8. [Actual Budget — finanzas personales local-first](https://github.com/actualbudget/actual)
- **Licencia y stack:** MIT comprobada en `LICENSE.txt` (no en `LICENSE` sin extensión); Node.js/monorepo y API pública `@actual-app/api`.[25][26][27]
- **Funcionalidad descrita:** presupuesto por sobres, cuentas personales, sincronización/local-first y clientes desktop. No es cartera de inversión ni comparador de productos.[25]
- **Coste/credenciales:** puede ejecutarse local/self-hosted sin API de LLM ni proveedor de mercado; hosting gestionado puede costar. Su API es una vía real para integrar un presupuesto, no una fuente de cotizaciones.[25][27]
- **Mantenimiento:** último commit observado: 2026-10-26; release v26.10.0 publicado el 2026-10-02.[28][29]
- **Componente reutilizable:** el paquete API y patrones de privacidad/onboarding/finanzas locales; MIT es permisiva con conservación de avisos. La lógica de presupuesto se reaprovecha mejor como contexto del perfil que como motor de recomendaciones de inversión.[26][27]

## Decisión para Paideia

1. **Prototipo de comparador:** implementar en código propio un esquema de producto con elegibilidad, restricciones, cálculo determinista, fecha de referencia, fuente primaria y estado de validación, tomando el patrón del comparador portugués; validar cada campo contra documentación oficial española. No usar su dataset ni su tipo impositivo.[37][38][39]
2. **UX de comparación:** adoptar de *Which ETF?* la búsqueda, filtros y paneles comparativos; mostrar explícitamente fecha, cobertura y campos no verificados. El README es una advertencia concreta contra confundir refresco de código con frescura financiera.[30][32]
3. **Chat educativo:** empezar con herramientas propias pequeñas (interés compuesto, depósitos, coste de deuda, escenarios) y devolver explicación, supuestos y fuente.
   - FinGenius muestra la separación entre tools y cálculos deterministas.[9][11]
   - Su `.env.example` exige OpenAI, así que no cumple coste cero sin cambiar el proveedor.[12]
   - RukiAI ofrece una opción posterior de RAG local si se acepta la carga operacional.[1][6]
4. **No copiar como base:**
   - Wealthfolio/Ghostfolio sirven de referencia de producto, pero AGPL y desajuste de alcance hacen que no sean una base directa.[18][19][22]
   - FinRobot tiene coste/proveedores y stack profesional; usarlo sólo como referencia de procedencia y cálculo.[15][41][44]
   - Actual Budget es referencia local-first para finanzas personales, no para inversión.[25][27]
5. **Riesgo abierto:** “datos diarios y gratis” no queda resuelto por licenciar la aplicación. Un repo MIT no da derechos sobre precios, datos de bancos, marca o servicios de terceros. Antes de integrar cualquier proveedor, validar términos de uso, límites, redistribución y disponibilidad; mantener fallback manual/estático con fecha de corte y enlaces oficiales.[30][34][38]

## Sources

[1] https://raw.githubusercontent.com/anupPradhan0/Ruki_Ai/main/README.md
[2] https://raw.githubusercontent.com/anupPradhan0/Ruki_Ai/main/LICENSE
[3] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/README.md
[4] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/LICENSE
[5] https://raw.githubusercontent.com/AI4Finance-Foundation/FinRobot/master/README.md
[6] https://raw.githubusercontent.com/anupPradhan0/Ruki_Ai/main/docs/RAG.md
[7] https://raw.githubusercontent.com/anupPradhan0/Ruki_Ai/main/backend/requirements.txt
[8] https://api.github.com/repos/anupPradhan0/Ruki_Ai/commits?per_page=1
[9] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/fingenius/tools/calculators.py
[10] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/fingenius/rag/knowledge_base.py
[11] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/fingenius/agent/graph.py
[12] https://raw.githubusercontent.com/anujdevsingh/financial_genius_agent/main/.env.example
[13] https://api.github.com/repos/anujdevsingh/financial_genius_agent/commits?per_page=1
[14] https://raw.githubusercontent.com/AI4Finance-Foundation/FinRobot/master/LICENSE
[15] https://raw.githubusercontent.com/AI4Finance-Foundation/FinRobot/master/finrobot_desktop/README.md
[16] https://raw.githubusercontent.com/AI4Finance-Foundation/FinRobot/master/finrobot_desktop/pyproject.toml
[17] https://api.github.com/repos/AI4Finance-Foundation/FinRobot/commits?per_page=1
[18] https://raw.githubusercontent.com/wealthfolio/wealthfolio/main/README.md
[19] https://raw.githubusercontent.com/wealthfolio/wealthfolio/main/LICENSE
[20] https://raw.githubusercontent.com/wealthfolio/wealthfolio/main/package.json
[21] https://api.github.com/repos/wealthfolio/wealthfolio/commits?per_page=1
[22] https://raw.githubusercontent.com/ghostfolio/ghostfolio/main/README.md
[23] https://raw.githubusercontent.com/ghostfolio/ghostfolio/main/LICENSE
[24] https://api.github.com/repos/ghostfolio/ghostfolio/commits?per_page=1
[25] https://raw.githubusercontent.com/actualbudget/actual/master/README.md
[26] https://raw.githubusercontent.com/actualbudget/actual/master/LICENSE.txt
[27] https://raw.githubusercontent.com/actualbudget/actual/master/packages/api/README.md
[28] https://api.github.com/repos/actualbudget/actual/commits?per_page=1
[29] https://api.github.com/repos/actualbudget/actual/releases?per_page=1
[30] https://raw.githubusercontent.com/violettance/etf-dashboard/main/README.md
[31] https://raw.githubusercontent.com/violettance/etf-dashboard/main/LICENSE
[32] https://api.github.com/repos/violettance/etf-dashboard/commits?per_page=1
[34] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/README.md
[35] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/LICENSE
[36] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/requirements.txt
[37] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/src/calculator.py
[38] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/data/metadata.json
[39] https://raw.githubusercontent.com/ricardoserodio/portugal-term-deposit-comparator/main/data/source_links.csv
[40] https://api.github.com/repos/ricardoserodio/portugal-term-deposit-comparator/commits?per_page=1
[41] https://raw.githubusercontent.com/AI4Finance-Foundation/FinRobot/master/finrobot_equity/README.md
[42] https://raw.githubusercontent.com/AI4Finance-Foundation/FinRobot/master/finrobot_autogen/README.md
[43] https://raw.githubusercontent.com/AI4Finance-Foundation/FinRobot/master/finrobot_desktop/LICENSE
[44] https://raw.githubusercontent.com/AI4Finance-Foundation/FinRobot/master/finrobot_equity/core/config/config.ini.example
