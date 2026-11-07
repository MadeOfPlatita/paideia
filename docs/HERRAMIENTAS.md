# Herramientas utilizadas

Lista simple de lo que se usó en Paideia, para qué sirvió y dónde viven las
claves. No incluye el relato del proyecto: eso está en `DIARIO-DESARROLLO.md`.
Aquí no hay claves, tokens ni datos personales.

## Trabajo y pruebas

| Herramienta | Para qué |
| --- | --- |
| Hermes Agent | Orquestar el trabajo: leer y editar el repositorio, ejecutar pruebas, desplegar y verificar |
| Subagentes de Hermes (`delegate_task`) | 12 pruebas en paralelo: práctica, catálogo, contrato, UI, seguridad, accesibilidad, rendimiento, cobertura, DTO y documentación |
| Python 3.11 / 3.14 | Aplicación, herramientas de catálogo y suites de prueba |
| `pytest` / `unittest` | 775 pruebas de backend, catálogo, perfil, privacidad y redacción |
| Node.js (`node --test`) | 109 pruebas del modelo de perfil y de la interfaz |
| Chromium por CDP (Browser Use) | Recorridos reales, medidas en píxeles, capturas y generación de PDF |
| Git + GitHub CLI (`gh`) | Historial por hitos, rama `master`, visibilidad y búsqueda de secretos |
| `curl`, PowerShell, `grep` | Comprobar respuestas HTTP, detener procesos y buscar en el código |
| Markdown → HTML/CSS → Chrome | Componer este documento y el diario completo en A4 |
| PyMuPDF | Contar páginas y comprobar que el PDF generado tiene contenido |

## Modelos de lenguaje

| Proveedor | Modelo | Uso | Estado |
| --- | --- | --- | --- |
| Command Code (`api.commandcode.ai/provider/v1/chat/completions`) | `deepseek/deepseek-v4.1-flash` | Chat de producción en Render | Activo |
| Groq (`api.groq.com/openai/v1/chat/completions`) | `openai/gpt-oss-20b` en local y `openai/gpt-oss-120b` en Render | Desarrollo y alternativa | Configurable; no es producción |
| Vercel AI Gateway (`ai-gateway.vercel.sh`) | `reflection/beam-free` | Prueba de proveedor gratuito | Probado; no se usa |
| LM Studio (`127.0.0.1:1234`) | Qwen local y `minicpm-ocr-1.0` | Pruebas de proveedor local y OCR de capturas | Solo local |

Beam (`reflection/beam:free`) se probó como modelo puntual y se volvió a
deepseek por decisión del objetivo.

## Despliegue y servicios

| Servicio | Para qué | Nota |
| --- | --- | --- |
| Render | App completa (Python + estáticos), variables y despliegues | Servicio `srv-dbltti56e07s73afrle0`; plan gratuito, se duerme sin tráfico |
| Vercel | Escaparate de solo lectura | Congelado en un build anterior; no recibe los cambios de `master` |
| GitHub | Repositorio `MadeOfPlatita/paideia` | Público a 7/11/2026; historial con correo personal en los commits |
| Cloudflare Python Workers | Prueba de despliegue alternativo | Descartado: el entorno no incluía el módulo `workers` |

## Datos financieros

| Fuente | Qué se tomó |
| --- | --- |
| CNMV | Registro, folletos y fechas de fondos |
| Tesoro Público | Letras: ISIN, vencimiento, subasta, saldo vivo y nominal adjudicado |
| Openbank, Pibank, EBN Banco, Self Bank, Renault Bank, MyInvestor | Cuentas y depósitos: TAE, TIN, mínimos, liquidación, garantía y vigencia |
| Bestinver, Azvalor, Olea Gestión | Fondos: ISIN, comisiones, SRI, patrimonio y folleto |
| BlackRock (iShares), DWS (Xtrackers), SSGA (SPDR), VanEck | ETF: TER, SRI, divisa, réplica y reparto |

Cada condición guarda su URL, la fecha de consulta y el literal del que sale. Lo
que la fuente no publica queda como «sin dato documentado».

## Dónde están las claves

- **Local**: `app/.env`, ignorado por git. Nunca se versiona.
- **Render**: variables del servicio en el panel; la clave no está en el repositorio.
- **Token de la API de Render**: `~/.cache/paideia/render.token`, usado solo por API y nunca impreso.
- **Vercel**: variables del proyecto; el escaparate no tiene chat encendido.

Ninguna clave se ha escrito en el código, en un commit, en una captura ni en el
chat. El asistente no lee, copia ni pega secretos: el usuario pega la clave en el
campo correspondiente.

## Lo que no se usa

Sin pagos, sin base de datos, sin cuentas de usuario, sin analítica de terceros y
sin operaciones reales. El ensayo y el justificante son ficticios.
