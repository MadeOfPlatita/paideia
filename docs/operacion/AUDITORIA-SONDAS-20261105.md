# Auditoría con sondas propias (5/11/2026)

No se pudieron lanzar los 50 subagentes: el guardarraíl de la sesión los bloqueó
por haber alcanzado el tope de delegaciones del turno. El trabajo se hizo con dos
baterías locales que no dependen de proveedores ni de producción:

- `sonda_paideia.py`: levanta la app en un puerto efímero y sondea HTTP (rutas,
  métodos, traversal, cabeceras, cuerpos inválidos, tamaños, unicode, fichas,
  paridad de estáticos y referencias de `index.html`).
- `sonda_admision.py`: cupo por minuto y por día, cola, `max_concurrent`, TTL de
  ticket y de claim, promoción al completar y reapertura al cambiar de día, con
  reloj controlado.

## Defecto encontrado y corregido

**Cuerpo grande: 413 sin cuerpo legible.** Con `Content-Length` por encima de
`MAX_BODY_BYTES` (16 KB) el servidor respondía 413 y cerraba sin consumir el
cuerpo declarado. En una conexión real el cliente recibía
`ConnectionAbortedError` al leer la respuesta, así que el error no llegaba: la UI
mostraba un fallo genérico. Reproducido con un servidor en proceso separado y un
cuerpo de 2 MB.

Corrección en `app/app.py`:

- `_drain_request_body()` descarta el cuerpo declarado, con tope de 8 MiB, antes
  de rechazar. Cubre también los rechazos previos por origen, tipo o longitud.
- `_send_json` añade `Connection: close` cuando la conexión se va a cerrar, para
  que el cliente sepa que no habrá más respuestas.
- Prueba nueva `app/tests/test_body_limit.py`: 2 MB devuelve 413 con JSON
  `BODY_TOO_LARGE` y `Connection: close`; un cuerpo normal no se ve afectado.

Verificado además con el servidor en proceso separado: 40 KB y 2 MB responden 413
legible; antes el cliente perdía la conexión.

## Comprobado sin hallazgos

- Traversal en `/static` (`../`, `%2e%2e`, barras invertidas, rutas absolutas):
  ninguna variante devuelve ficheros fuera de `static/`.
- Métodos y rutas: `POST /api/status`, `GET /api/chat`, `DELETE /api/catalogue`
  no producen 500 ni cortan la conexión.
- Cuerpos inválidos (JSON roto, array, texto, `null`, 600 niveles de anidación):
  4xx sin trazas ni rutas del sistema.
- Cabeceras de seguridad completas: CSP, `X-Content-Type-Options`,
  `X-Frame-Options`, `Permissions-Policy`, `Referrer-Policy`, `Cache-Control`.
- Consentimiento: sin `context_consent` el contexto se rechaza con 403; con la IA
  apagada no se acepta contexto.
- Límites de contexto: mínimo mayor que máximo, moneda distinta de EUR, importes
  con tres decimales, negativos, claves desconocidas y estado sin valor se
  rechazan.
- `profile_echo`: formatos `0`, `1.000`, `1.000.000`, `1.500,50`; los estados
  `no_se`, `omitido` y `sin_preguntar` no generan texto.
- Redacción de cifras: una frase con `3,5 %` se descarta; un texto sin cifras no
  se toca; las cifras escritas con palabras también cuentan.
- Admisión: 2 llamadas/día admitidas, la tercera queda en cola con
  `quota_exhausted`, la cola se promueve al completar, un claim abandonado libera
  al vencer su TTL y al cambiar de día UTC el cupo se reabre.
- Fichas de producto y `/api/catalogue`: sin `undefined`, `null` ni `NaN` en el
  JSON; paridad `app/static` ↔ `api/_static` correcta; sin referencias rotas en
  `index.html`.
- Datos: sin ids duplicados, sin mínimos mayores que máximos y sin fuentes sin
  URL.

## Límites de esta auditoría

- No cubre JS de navegador real (solo el arnés VM existente y análisis estático).
- No mide concurrencia con carga alta ni latencia de red real.
- Las baterías se quedaron en `scratch/` y no se versionan; el defecto corregido
  sí lleva prueba permanente.
