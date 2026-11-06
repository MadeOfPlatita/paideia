# Paideia

Aplicación web en español para **explorar productos financieros con criterio**:
biblioteca de fichas con fuente, comparador honesto, escenarios con calculadora
determinista y un asistente educativo (Pai) que dice lo que no puede respaldar.

Trabajo académico de Finanzas y Contabilidad (Universidad de Málaga). No es un
asesor financiero, no ejecuta operaciones, no pide datos personales y no guarda
nada en un servidor.

| Entorno | URL | Qué es |
| --- | --- | --- |
| Demo completa | **https://paideia-jg2n.onrender.com** | El servidor real: biblioteca, comparador, escenarios, informe y chat |
| Escaparate | https://paideia-mu.vercel.app | Versión estática que enlaza a la demo |

El plan gratuito de Render duerme el servicio tras 15 minutos sin uso: el primer
acceso puede tardar cerca de un minuto.

## Qué incluye

- **Biblioteca.** 20 candidatos de investigación y **22 fichas con condiciones
  transcritas**: 113 condiciones visibles en las fichas y 223 registros en la
  transcripción de origen, cada una con URL, título y fecha de consulta. Cada
  tasa aparece con su estado: documentada, vencida, en conflicto o sin dato.
- **Comparador.** De dos a cuatro productos. Solo compara cifras cuando
  magnitud, plazo y vigencia coinciden; si no, explica por qué no.
- **Escenarios.** Dos hipótesis editables, motor determinista propio (interés
  simple y compuesto, aportaciones, inflación), gráficos, tabla e informe HTML
  autónomo.
- **Tu mapa.** Cuatro preguntas opcionales, con «No lo sé» y «Omitir». Se quedan
  en el navegador y al chat solo viaja lo que autorices campo a campo.
- **Pai.** Chat educativo. Cuando una cifra o una atribución no está respaldada
  por datos locales, lo dice: no rellena huecos por inferencia.
- **Ensayo de contratación ficticia**, glosario y ayuda contextual.

## Arranque rápido

Sin dependencias: solo Python 3.10 o superior (probado en 3.11 y 3.12).

```bash
cd app
python app.py --port 8765
```

Abre <http://127.0.0.1:8765/>. La aplicación funciona completa sin clave de
modelo: biblioteca, comparador, escenarios e informe no dependen de la IA.

Para encender el chat, copia `app/.env.example` como `app/.env` y rellena
`GROQ_API_KEY`. Ese archivo está ignorado por git y nunca debe subirse.

### Pruebas

```bash
python app/tools/quality_gate.py
```

La puerta elige un intérprete con `pytest`, lanza las pruebas Python y después
las de Node. En esta instantánea: **728 pruebas Python y 108 de Node**.

## Configuración

| Variable | Para qué | Por defecto |
| --- | --- | --- |
| `PAIDEIA_GROQ_ENABLED` | Enciende el chat | `0` |
| `PAIDEIA_LLM_PROVIDER` | `groq`, `commandcode` o `vercel` | `groq` |
| `GROQ_API_KEY` / `COMMANDCODE_API_KEY` / `AI_GATEWAY_API_KEY` | Credencial del proveedor elegido | — |
| `PAIDEIA_LLM_MODEL` | Modelo cuando el proveedor no es Groq | el del proveedor |
| `PAIDEIA_GROQ_MODEL` | Modelo de Groq | `openai/gpt-oss-20b` |
| `PAIDEIA_GROQ_TIMEOUT` | Segundos de espera por respuesta | `20` |
| `PAIDEIA_CALLS_PER_DAY` / `PAIDEIA_CALLS_PER_MINUTE` | Tope propio de llamadas | `300` / `10` |
| `PAIDEIA_PUBLIC_ORIGIN` | Origen público declarado (proxy HTTPS) | solo local |

Las claves viven solo en el panel del proveedor de despliegue o en `app/.env`.
El código solo puede enviar la clave al host del proveedor elegido.

## Diario de desarrollo

El recorrido completo —encargos, herramientas, APIs, decisiones, pruebas y
límites— está en [`docs/DIARIO-DESARROLLO.md`](docs/DIARIO-DESARROLLO.md).

## Estructura

```
app/                 aplicación completa
  app.py             servidor HTTP (sin frameworks)
  static/            interfaz: HTML, CSS y JS sin dependencias
  data/              catálogo curado (condiciones y fuentes)
  tests/             pruebas Python y de Node
  tools/             puerta de calidad
api/                 función WSGI del escaparate en Vercel
docs/                documentación y datos de investigación
render.yaml          blueprint de Render
vercel.json          configuración del escaparate
```

Detalle de cada carpeta y por qué se conserva: [`docs/README.md`](docs/README.md).

## Datos y trazabilidad

- Las **condiciones** se transcriben de fuentes públicas con URL, título y fecha
  en `app/data/condiciones.json`. Lo que la fuente no publica se muestra como
  desconocido; no se estima.
- La instantánea y el ledger que la app lee en ejecución viven en
  `docs/validacion-04/05-catalogo/`; el benchmark de contexto, en
  `docs/validacion-04/03-benchmark/`.
- El **texto del modelo no se valida** semánticamente contra las fuentes: solo
  las citas de las herramientas y los cálculos locales son datos.
- El **catálogo no es publicable** todavía: faltan permisos y, en algunos
  productos, la verificación oficial de vigencia.

## Despliegue

- **Render:** `render.yaml` define el servicio (plan gratuito, Fráncfort,
  `python app/app.py`, comprobación en `/api/status`). Las claves se pegan en el
  panel y quedan marcadas `sync: false`.
- **Vercel:** `api/index.py` sirve el escaparate estático; no ejecuta la app.
- El despliegue de Render se dispara con cada push a `master`.

## Límites conocidos

- El contador de llamadas vive en memoria: al redesplegar vuelve a cero.
  Detalle en [`docs/producto/CUPO-Y-LIMITES.md`](docs/producto/CUPO-Y-LIMITES.md).
- La comparación evalúa una métrica documentada, no la oferta contractual.
- No se genera PDF: el informe se descarga en HTML autónomo.
- El plan gratuito duerme el servicio y puede tardar en responder al despertar.

## Autoría y uso

Trabajo de Alejandro y José Manuel para la asignatura. El repositorio se publica
para que pueda corregirse y descargarse. No se concede licencia de reutilización:
los derechos quedan en los autores, salvo el material de terceros citado como
fuente.
