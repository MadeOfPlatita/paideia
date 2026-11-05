# Paideia en Render, con Pai conectada

`https://paideia-jg2n.onrender.com` ejecuta la app completa (servidor HTTP con estado),
no una función sin estado: el contador de llamadas, las sesiones y el catálogo viven
en el proceso.

## Cómo está desplegado

- Servicio `paideia`, plan gratuito, región Fráncfort, definido en `render.yaml`.
- Arranque: `python prototipos/paideia-local/app.py`; Render inyecta `PORT` y
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
