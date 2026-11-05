# Paideia — cuaderno de ruta financiera

Trabajo académico de Finanzas y Contabilidad (Universidad de Málaga). Paideia es
una aplicación web en español para explorar productos financieros con
explicaciones, comparar hipótesis y descargar un informe. No es un asesor
financiero, no ejecuta operaciones y no pide datos personales.

## Dónde se prueba

| Enlace | Qué es | IA |
| --- | --- | --- |
| **https://paideia-jg2n.onrender.com** | **La aplicación completa** (demo) | Sí, con Groq |
| https://paideia-mu.vercel.app | Escaparate estático que enlaza a la demo | No |

La demo de Render ejecuta el servidor real: biblioteca, comparador, escenarios,
informe y chat con Pai. El plan gratuito la duerme tras 15 minutos sin uso, así
que el primer acceso puede tardar cerca de un minuto. Tope propio: 300 llamadas
al día y 10 por minuto (`PAIDEIA_CALLS_PER_DAY`, `PAIDEIA_CALLS_PER_MINUTE`).

Vercel queda como escaparate: su función no ejecuta la app y solo sirve el
catálogo de la instantánea. No se mantiene en paralelo.

## Qué se puede hacer

- **Tu mapa:** 4 preguntas opcionales, con «No lo sé» y «Omitir», guardadas solo
  en el navegador y borrables. Solo viajan al chat los campos que marques.
- **Biblioteca:** 20 candidatos de investigación y **22 fichas con condiciones
  transcritas** (223 condiciones con URL, título y fecha de consulta). Cada tasa
  aparece con su estado: documentada, vencida, en conflicto o sin dato.
- **Comparar:** dos a cuatro productos. La comparación cuantitativa solo se
  activa cuando magnitud, plazo y vigencia coinciden; si no, dice por qué.
- **Escenarios:** dos hipótesis editables, motor determinista (interés simple y
  compuesto, aportaciones, inflación), gráficos, tabla e informe HTML.
- **Ensayo de contratación ficticia:** cinco pasos, sin operaciones.
- **Glosario** y ayuda contextual.
- **Pai (chat):** responde con Groq. Cuando una cifra o una atribución no está
  respaldada por datos locales, lo dice y muestra solo lo que sí lo está.

## Cómo ejecutarlo en local

Sin dependencias externas: Python 3.10 o superior.

```bash
cd prototipos/paideia-local
python app.py --port 8765
```

Abrir `http://127.0.0.1:8765/`. El chat se activa creando
`prototipos/paideia-local/.env` a partir de `.env.example` con `GROQ_API_KEY`.
Sin clave, la aplicación funciona igual: biblioteca, comparador, escenarios e
informe no dependen del modelo.

Pruebas: `python -m pytest tests -q` y `node --test tests/*.test.cjs` desde
`prototipos/paideia-local`. La puerta completa es
`python prototipos/paideia-local/tools/quality_gate.py`, que elige un Python con
pytest instalado.

## Qué es real y qué es simulado

- Los **cálculos** los hace un motor determinista propio; las cifras del informe
  salen de ese motor.
- Las **condiciones** proceden de fuentes públicas con URL y fecha, transcritas
  en `prototipos/paideia-local/data/condiciones.json`. Cuando no hay dato, se
  dice; no se rellena por inferencia.
- El **ensayo de contratación** es ficticio: no se envía nada a ninguna entidad.
- El **texto del modelo no se valida** semánticamente contra las fuentes: solo
  las citas de las herramientas y los cálculos locales son datos.
- El **catálogo no es publicable**: faltan permisos y, en algunos productos, la
  verificación oficial de la vigencia.

## Límites conocidos

- El cupo de llamadas vive en memoria: al redesplegar vuelve a cero. Detalle en
  `docs/CUPO-Y-LIMITES.md`.
- La comparación evalúa una métrica documentada, no la oferta contractual.
- No hay PDF generado: el informe se descarga en HTML autónomo.

## Estructura

- `prototipos/paideia-local/`: aplicación (servidor, interfaz, motor, Pai).
- `api/`: función de Vercel (escaparate) y copia de estáticos para el despliegue.
- `docs/`: requisitos, decisiones, evidencias e informes. Índice en
  `docs/INDICE.md`.
- `spikes/`: experimentos de apoyo.

## Ramas

- `master`: solo lo revisado y desplegado.
- `contador-mision-pendiente`: trabajo del contador de misión sin aprobación
  (N2 abierto). No se mezcla ni se despliega.

## Autoría y uso

Trabajo de Alejandro y José Manuel para la asignatura. El repositorio se publica
para que la profesora pueda corregirlo y descargarlo. No se concede licencia de
reutilización: los derechos quedan en los autores, salvo el material de terceros
citado como fuente.
