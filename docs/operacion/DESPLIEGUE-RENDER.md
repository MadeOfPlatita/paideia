# Paideia en Render, con Pai conectada

`https://paideia-jg2n.onrender.com` ejecuta la app completa (servidor HTTP con estado),
no una función sin estado: el contador de llamadas, las sesiones y el catálogo viven
en el proceso.

## Cómo está desplegado

- Servicio `paideia`, plan gratuito, región Fráncfort, definido en `render.yaml`.
- Arranque: `python app/app.py`; Render inyecta `PORT` y
  `RENDER_EXTERNAL_URL`, que la app usa como origen público exacto.
- Variables: `PAIDEIA_GROQ_ENABLED=1`, `PAIDEIA_GROQ_MODEL=openai/gpt-oss-120b` y
  `GROQ_API_KEY` (marcada `sync: false`: se pega en el panel y no está en el repositorio).
- Cada `push` a `master` redespliega automáticamente. Comprobado: el cambio `ef596f7`
  pasó a producción sin intervención manual.

## Qué se comprobó en el despliegue real

- `GET /api/status` responde `mode: public_demo`, `ai.status: configured_not_verified`
  y cupo `6/min`, `60/día`.
- La cabecera dice «Versión pública · IA configurada»; el pie, «Demostración».
- El mismo origen (HTTPS del proxy) pasa la comprobación de origen; un `Origin` ajeno
  sigue recibiendo `ORIGIN_REJECTED`.
- Dos preguntas reales con datos ficticios: TAE frente a TIN, y qué es un depósito a
  plazo. Ambas respondieron en prosa y el contador pasó de 0 a 1 dentro del proceso.

## Límites que siguen en pie

- El cupo de 60 llamadas al día vive en memoria: al reiniciar o redesplegar vuelve a 0.
  Es un freno de coste, no una cuota contable.
- El plan gratuito duerme el servicio tras 15 minutos sin tráfico; el primer acceso
  tarda alrededor de un minuto.
- Cualquiera con el enlace puede consumir esas llamadas. Si hiciera falta, se protege
  con contraseña o se limita por IP en una capa delante.
- El texto del modelo no se valida contra las fuentes; lo que se sostiene son las
  citas de la herramienta y los cálculos locales.

## Vercel queda de escaparate

`https://paideia-mu.vercel.app` no ejecuta la app: es una función que sirve el
catálogo de la instantánea y los estáticos. No puede sostener el chat con estado
ni las condiciones transcritas. Desde `api/index.py` se inyecta un aviso en la
portada que enlaza aquí. No se mantiene en paralelo: cualquier cambio de producto
va a la app y a esta demo.

## Cambiar de proveedor del chat

Tres destinos compatibles con OpenAI, los tres anclados en código
(`providers.py`). La clave del proveedor elegido es la única que puede viajar, y
solo a ese host:

| `PAIDEIA_LLM_PROVIDER` | Host | Clave | Modelo por defecto |
| --- | --- | --- | --- |
| `groq` (por defecto) | `api.groq.com` | `GROQ_API_KEY` | `openai/gpt-oss-20b` |
| `vercel` | `ai-gateway.vercel.sh` | `AI_GATEWAY_API_KEY` | `reflection/beam-free` |
| `commandcode` | `api.commandcode.ai` | `COMMANDCODE_API_KEY` | `deepseek/deepseek-v4.1-flash` |

En el panel de Render, en *Environment*:

1. `PAIDEIA_LLM_PROVIDER` con el nombre del proveedor.
2. Pega la clave correspondiente como secreto.
3. `PAIDEIA_LLM_MODEL` es opcional; si falta se usa el de la tabla. El nombre
   antiguo `PAIDEIA_GROQ_MODEL` solo se lee cuando el proveedor es Groq.

`reflection/beam-free` es Beam 1.0 por la puerta de Vercel, gratis mientras dure
la oferta de lanzamiento: la ruta `-free` deja de servir al terminar, así que no
puede generar factura. Vercel no lo marca como sin retención ni sin
entrenamiento, de modo que no conviene enviarle datos personales (la app ya lo
prohíbe).

Guardar las variables reinicia el servicio y aplica el cambio. Si la clave falta,
la app arranca con el chat apagado en vez de fallar: `/api/status` lo dice con
`ai.status = not_configured`.

Aviso de producto: si el proveedor es una suscripción personal, el cupo del
plan lo consume cualquiera que use el enlace público. Es una decisión de quién
paga, no un detalle técnico.
