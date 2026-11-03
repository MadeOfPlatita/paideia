# Paideia — cuaderno de ruta financiera

Trabajo académico de Finanzas y Contabilidad (Universidad de Málaga). Paideia es una aplicación web local, en español, para explorar productos financieros con explicaciones, comparar hipótesis y llevarse un informe descargable. No es un asesor financiero, no ejecuta operaciones y no solicita datos personales.

## Qué se puede hacer hoy

- **Tu mapa:** cuestionario opcional por preguntas, con «No lo sé» y «Omitir», guardado solo en el navegador y borrable.
- **Biblioteca:** 20 candidatos de investigación, más los productos cuya ficha se ha transcrito con fuente y fecha. Cada tasa aparece con su estado: documentada, vencida, en conflicto o sin dato.
- **Comparar:** dos a cuatro productos con criterios en orden fijo. La comparación cuantitativa solo se activa cuando la magnitud, el plazo y la vigencia coinciden; si no, dice por qué.
- **Escenarios:** dos hipótesis editables, cálculo del motor local (interés simple y compuesto, aportaciones al final de mes, inflación), gráficos, tabla e informe HTML descargable.
- **Ensayo de contratación ficticia:** cinco pasos, sin operaciones ni datos personales.
- **Glosario** y ayuda contextual.
- **Pai (chat):** responde con un modelo de Groq si se configura una clave; puede usar la calculadora local y recibir únicamente los campos del mapa que el usuario marque.

## Cómo ejecutarlo

No hay dependencias externas: solo Python 3.10 o superior.

```bash
cd prototipos/paideia-local
python app.py --port 8765
```

Después, abrir `http://127.0.0.1:8765/`.

El chat con IA está apagado por defecto. Para activarlo, crear `prototipos/paideia-local/.env` a partir de `.env.example` y rellenar `GROQ_API_KEY` con una clave propia. Sin clave, la aplicación funciona igual: biblioteca, comparador, escenarios e informe no dependen del modelo.

## Qué es real y qué es simulado

- Los **cálculos** los hace un motor determinista propio; las cifras del informe coinciden con ese motor.
- Las **condiciones de producto** proceden de fuentes públicas con URL y fecha de consulta, transcritas en `prototipos/paideia-local/data/condiciones.json`. Cuando no hay dato, la aplicación lo dice; no se rellena por inferencia.
- El **ensayo de contratación** es ficticio: no se envía nada a ninguna entidad.
- El **catálogo no es publicable**: las condiciones están pendientes de revisión de permisos y de verificación oficial en algunos casos.

## Límites conocidos

- No hay PDF generado desde el panel de vista previa; el informe se descarga en HTML autónomo.
- No hay persistencia de escenarios ni de filtros entre sesiones.
- La comparación evalúa una sola métrica documentada, no la oferta contractual completa.
- El enlace público para la Wiki queda pendiente de despliegue.

## Estructura

- `prototipos/paideia-local/`: aplicación (servidor Python, interfaz, motor de cálculo, herramientas de Pai).
- `docs/`: requisitos, decisiones, planes, evidencias de verificación e informes de revisión.
- `docs/DIARIO_DESARROLLO.md`: diario de desarrollo con prompts, decisiones y pruebas.
- `spikes/`: experimentos descartados o de apoyo.

## Autoría y uso

Trabajo de Alejandro y José Manuel para la asignatura. El repositorio se publica para que la profesora pueda corregirlo y descargarlo. No se concede licencia de reutilización: los derechos quedan en los autores, salvo el material de terceros citado como fuente.
