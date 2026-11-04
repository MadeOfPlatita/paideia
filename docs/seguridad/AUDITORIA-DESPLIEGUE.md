# Auditoría del despliegue público

Verificación independiente de que https://paideia-mu.vercel.app sirve el contenido del `HEAD`
del repositorio, con el chat de IA apagado y sin rutas ni datos expuestos.

- **Fecha de la auditoría:** 2026-11-04, 21:53–21:57 CET (20:53–20:57 UTC).
- **Commit auditado:** `a0e48fdda8277ebaa205023503df8e69f92cc351` (`a0e48fd`, rama `master`),
  «Evita fijar un hash que el propio commit invalida», 2026-11-04 21:36:08 +0100.
- **`origin/master`:** `a0e48fdda8277ebaa205023503df8e69f92cc351` (idéntico a `HEAD`).
- **Árbol de trabajo:** `git status --porcelain -- api vercel.json` vacío. Las modificaciones
  locales están en `prototipos/paideia-local/` y en documentación bajo `docs/`; ninguna entra en el
  despliegue, que solo empaqueta `api/` y `vercel.json`.
- **Método:** `curl` sin credenciales contra la web pública + `git show HEAD:api/_static/...`
  para el lado del repositorio. Nada se ha modificado en `api/` ni en `vercel.json`.

## Veredicto

**Coincide con el `HEAD`, con salvedades.**

El contenido servido es idéntico al del `HEAD` en los 15 ficheros estáticos y en la respuesta de
`/api/status`; la IA está apagada de extremo a extremo y no se ha encontrado ninguna ruta,
secreto ni ruta local expuesta. Las salvedades son de empaquetado y de cabeceras, no de
contenido:

1. **Los ficheros se sirven con CRLF.** El `HEAD` los guarda con LF. Tras normalizar los saltos
   de línea, los 15 ficheros son idénticos byte a byte. La diferencia es exactamente +1 byte por
   línea en todos ellos (tabla 2), así que es una conversión LF→CRLF del paso de empaquetado, no
   un cambio de contenido.
2. **Faltan cabeceras HTTP de seguridad.** Hay HSTS (la añade Vercel), pero no hay
   `Content-Security-Policy`, `X-Content-Type-Options` ni `Referrer-Policy` como cabeceras. La CSP
   y el `referrer` viajan solo como `<meta>` dentro del HTML, lo que no cubre respuestas que no
   sean HTML y no permite `frame-ancestors`.
3. **El JS se sirve como `text/javascript`**, no como `application/javascript`. Es equivalente
   según RFC 9239, pero no es el literal pedido.

Ninguna de las tres afecta a la conclusión de que lo publicado es el `HEAD` con la IA apagada.

## 1. Estado del servicio

`GET /api/status` → `200`, `application/json; charset=utf-8`, 394 bytes, `Cache-Control: no-store`.

```json
{
  "mode": "public_serverless",
  "ai": {
    "connected": false,
    "status": "not_configured",
    "message": "Chat IA no disponible en la versión pública; no se envía nada.",
    "capabilities": {"context": false, "history": false, "synthetic_only": true, "structured_education": false},
    "quota": null
  },
  "catalogue": {"candidate_count": 20, "publication_ready": 0},
  "storage": "bundled_snapshot_no_database"
}
```

La respuesta es **byte a byte** la que produce `_status()` en `HEAD:api/index.py`
(394 bytes, `sha256 de6760fd06fbf9883e5bdf0099fec3fcdc62f7c884fecf88fa18d27642a533fe`).
Eso incluye el orden de claves y el texto del mensaje: no es solo «un JSON parecido», es la misma
salida del mismo código.

- `catalogue.candidate_count` = 20 = `len(CANDIDATES)` en `api/_core/catalogue_data.py` del `HEAD`.
- `/api/catalogue` devuelve `count: 20`, 20 ítems y `not_for_publication: true`.
- `/api/conditions` lista 22 entradas: las 20 del catálogo más dos depósitos transcritos de
  `CURATED` (`DEP-EBN-12`, `DEP-SELF-12`) que no son candidatos del catálogo.
- `X-Vercel-Cache: MISS` en todas las peticiones: se está viendo el despliegue, no una caché previa.
- **Propagación:** la primera comprobación (21:53 CET) ya devolvió contenido del `HEAD`, así que no
  hubo que esperar reintentos. Una segunda pasada a las 21:56 devolvió el mismo `sha256` para
  `/index.html`, con `Age: 0` y el mismo edge (`cdg1`, París).

## 2. Comparación con el `HEAD` (byte a byte)

Comparación de `sha256` de lo servido contra `git show HEAD:api/_static/<fichero>`. La columna
«=» compara **después** de normalizar CRLF→LF.

Nota sobre el commit auditado: `a0e48fd` solo toca `docs/CIERRE-PAIDEIA-HASTA-BLOQUEO.md`;
`git diff HEAD~1 HEAD -- api vercel.json` está vacío, así que el contenido servible es el de
`1a66a53` («Declara el motivo real cuando Pai retiene una respuesta»), incluido en `HEAD`.

| Fichero | bytes HEAD | bytes servidos | Δ | sha256 HEAD (16) | sha256 servido (16) | = |
|---|---:|---:|---:|---|---|---|
| `index.html` | 4059 | 4132 | +73 | `011ac5888355cd5a` | `ff485b734c1d14b2` | sí |
| `styles.css` | 25667 | 26108 | +441 | `4df2d4d2794a5ffc` | `13544781fe20a708` | sí |
| `dark_theme.css` | 3689 | 3759 | +70 | `aedc42dc555b1217` | `b2a3f0218afbe6bd` | sí |
| `comparison_report.css` | 1407 | 1427 | +20 | `a1e76322cab0b6a8` | `2772acc3dd25ec27` | sí |
| `context_help.css` | 515 | 520 | +5 | `b7a61d3798d50319` | `021eac4853c731b0` | sí |
| `app.js` | 200267 | 203607 | +3340 | `ff7a311b5a42b931` | `5dd0296c9910f18e` | sí |
| `profile_model.js` | 32384 | 33019 | +635 | `0f24fb027b54b6e1` | `cde8d664358dd490` | sí |
| `comparison_report.js` | 23006 | 23266 | +260 | `0395d5a8ff2c7a34` | `09c4cf875dd015d0` | sí |
| `conditions_load.js` | 4038 | 4134 | +96 | `06dcc643f1505c9c` | `15425d6f614533cc` | sí |
| `context_help.js` | 4055 | 4120 | +65 | `c392638b1d5b9012` | `3369dd76fa05740f` | sí |
| `scenario_provenance.js` | 6384 | 6504 | +120 | `3beaff6704fede7d` | `153db86f554b2636` | sí |
| `structured_education_ui.js` | 5424 | 5478 | +54 | `860c1d4921501f27` | `ed26dfaac0b55836` | sí |
| `chat_context_model.js` | 1689 | 1706 | +17 | `77d03d3d54c33a11` | `e5f2d4613960a2d4` | sí |
| `chat_withheld_notice.js` | 2306 | 2335 | +29 | `53e244e65f90d6cb` | `d11e702c2c6a1aad` | sí |
| `assets/pai-neutral.svg` | 638 | 647 | +9 | `039965f728ddf786` | `693fa8e750b19de9` | sí |

Prueba de que el Δ es solo CRLF: en los 15 ficheros, `bytes servidos − bytes HEAD` es exactamente
el número de líneas del fichero (73, 441, 70, 20, 5, 3340, 635, 260, 96, 65, 120, 54, 17, 29, 9).
Un byte de más por línea, ni uno más. El `Content-Length` que declara el servidor coincide con lo
descargado en todos los casos, así que los CRLF están en el fichero servido, no los añade `curl`
al escribir en disco.

Consecuencia práctica: **comparar `sha256` en crudo falla**, y fallará siempre mientras el
empaquetado convierta a CRLF; la comprobación válida es sobre el contenido normalizado.

`/api/status` no tiene este problema: coincide en crudo, porque lo genera el código en ejecución.

## 3. IA apagada

| Comprobación | Resultado | Evidencia |
|---|---|---|
| `ai.connected` | `false` | `/api/status` |
| `ai.status` | `not_configured` | `/api/status` |
| Capacidades | `context`, `history`, `structured_education` en `false`; `synthetic_only: true` | `/api/status` |
| `GET /api/chat` | `404` `application/json` | 89 bytes, `{"error": {... "code": "NOT_FOUND" ...}}` |
| `POST /api/chat` | `405` `application/json` | `METHOD_NOT_ALLOWED` |
| `GET`/`POST /api/chat/queue` | `404` / `405` `application/json` | no existe la cola |
| `/api/chat/stream` | `404` `application/json` | no existe el streaming |
| `/api/ai`, `/api/llm` | `404` `application/json` | no hay endpoints de proveedor |
| Cliente | el formulario no llega a enviar | `chatIsConfigured()` exige `configured_not_verified` o `test_only`; con `not_configured` el `submit` retorna antes del `fetch` |
| Fugas de clave | ninguna | `/api/status` y `/api/conditions` sin `api_key`, `secret`, `bearer`, `sk-` |

El código de `app.js` conserva la ruta `API.chat = "/api/chat"`, pero es código muerto en esta
versión: el `submit` corta antes en `chatIsConfigured()` y el servidor no tiene handler para esa
ruta. Doble barrera; ninguna de las dos se abre con la configuración actual.

## 4. Cabeceras y tipos MIME

Cabeceras reales de `GET /` y `GET /api/status`:

| Cabecera | `/` | `/api/status` | Valoración |
|---|---|---|---|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | igual | correcto (la pone Vercel) |
| `Content-Security-Policy` | **ausente** | **ausente** | solo existe como `<meta http-equiv>` en el HTML |
| `X-Content-Type-Options` | **ausente** | **ausente** | sin `nosniff` |
| `Referrer-Policy` | **ausente** | **ausente** | solo `<meta name="referrer" content="no-referrer">` |
| `Permissions-Policy` | ausente | ausente | no hay funcionalidades sensibles que lo exijan |
| `X-Frame-Options` | ausente | ausente | la CSP no incluye `frame-ancestors` |
| `Cache-Control` | `no-store` (HTML) / `public, max-age=300` (estáticos) | `no-store` | razonable |

La CSP que sí llega, dentro del HTML:

```
default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self';
connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'
```

Es una política cerrada y sin `unsafe-inline`, pero al ir en `<meta>` no cubre respuestas que no
sean HTML ni puede declarar `frame-ancestors`; y al no haber `X-Frame-Options`, el sitio es
incrustable en un iframe de terceros. `vercel.json` del `HEAD` no tiene bloque `headers`, así que
esto es una carencia de configuración, no una desviación del despliegue.

Tipos MIME observados:

| Ruta | `Content-Type` | Esperado | |
|---|---|---|---|
| `/`, `/index.html` | `text/html` | `text/html` | correcto (charset por `<meta charset="utf-8">`) |
| `/dark_theme.css`, `/styles.css`, `/comparison_report.css`, `/context_help.css` | `text/css` | `text/css` | correcto |
| `/app.js` y demás JS | `text/javascript` | `application/javascript` | equivalente (RFC 9239), literal distinto |
| `/api/*` | `application/json; charset=utf-8` | JSON | correcto, nunca HTML |
| `/assets/pai-neutral.svg` | `image/svg+xml` | `image/svg+xml` | correcto |
| `/app.js.map` | `text/html` (shell) | no existe | correcto: no hay source map publicado |

## 5. Rutas sondeadas

Ninguna ruta prohibida devuelve su contenido. Las que responden `200` devuelven **el shell de la
app**: 4132 bytes con `sha256 ff485b734c1d14b219aee10c0fd1900bc66f8a842aac047cf73809e8ead4d01e`,
idéntico a `/index.html`. Es el fallback de `vercel.json` (`/(.*) → /api/index`) y de `_static()`
para rutas que no son `/api`, no una fuga.

| Ruta | Código | Tipo | Qué devuelve |
|---|---:|---|---|
| `/api/chat` | 404 | JSON | `NOT_FOUND` |
| `/api/chat/queue` | 404 | JSON | `NOT_FOUND` |
| `/api/chat/stream` | 404 | JSON | `NOT_FOUND` |
| `/api/secure` | 404 | JSON | `NOT_FOUND` |
| `/api/mission` | 404 | JSON | `NOT_FOUND` |
| `/api/mission/status` | 404 | JSON | `NOT_FOUND` |
| `/api/missions` | 404 | JSON | `NOT_FOUND` |
| `/api/ai`, `/api/llm` | 404 | JSON | `NOT_FOUND` |
| `/api/health`, `/api/metrics` | 404 | JSON | `NOT_FOUND` |
| `/api/_core/domain.py` | 404 | JSON | `NOT_FOUND` |
| `/api/_core/catalogue_data.py` | 404 | JSON | `NOT_FOUND` |
| `/api/_core/__pycache__/domain.cpython-311.pyc` | 404 | JSON | `NOT_FOUND` |
| `/api/index.py` | 404 | JSON | `NOT_FOUND` |
| `/api/build_core.py` | 404 | JSON | `NOT_FOUND` |
| `/api/.env` | 404 | JSON | `NOT_FOUND` |
| `/.env` | 200 | HTML | shell (4132 B), no el fichero |
| `/.git/config`, `/.git/HEAD` | 200 | HTML | shell, no el repo |
| `/vercel.json` | 200 | HTML | shell, no la configuración |
| `/docs/`, `/docs/seguridad/` | 200 | HTML | shell, no la documentación |
| `/docs/seguridad/AUDITORIA-DESPLIEGUE.md` | 200 | HTML | shell: este informe **no** se publica |
| `/prototipos/`, `/artefactos/` | 200 | HTML | shell, no el árbol local |
| `/app.js.map` | 200 | HTML | shell, no hay source map |
| `/C:/Users/aleja/.env` | 200 | HTML | shell, no hay ruta local |
| `/%2e%2e/%2e%2e/etc/passwd` | 200 | HTML | shell: Vercel normaliza `..` antes de la función |
| `/api/%2e%2e/%2e%2e/etc/passwd` | 200 | HTML | shell, no el fichero |
| `/api/status/` (barra final) | 404 | JSON | `NOT_FOUND` |
| `/API/STATUS` | 200 | HTML | shell (rutas sensibles a mayúsculas) |
| `/api/foo/../status` | 200 | JSON | se normaliza a `/api/status` antes de entrar |
| `/api/unknown` | 404 | JSON | `NOT_FOUND` |
| `POST /api/status` | 405 | JSON | `METHOD_NOT_ALLOWED` |
| `POST /api/calculate` (cuerpo vacío) | 400 | JSON | `INVALID_REQUEST` |
| `OPTIONS /api/status` | 405 | JSON | sin cabeceras CORS: no hay `Access-Control-Allow-Origin` |

Que el despliegue no publique `/docs/` es coherente con `vercel.json`: `includeFiles` solo mete
`api/_core/**` y `api/_static/**`. El repositorio no se sirve, solo la función y sus estáticos.

## 6. Secretos y rutas locales

Búsqueda sobre el HTML público, los 15 estáticos descargados y los tres payloads de API
(`/api/status`, `/api/catalogue`, `/api/conditions`):

| Patrón | Coincidencias |
|---|---:|
| `C:/Users`, `C:\Users` | 0 |
| `127.0.0.1`, `localhost` | 0 |
| `.env` | 0 |
| `sk-…` (claves) | 0 |
| `api_key`, `apikey` | 0 |
| `secret` | 0 |
| `bearer` | 0 |
| `/home/`, `prototipos/` | 0 |

El HTML público solo enlaza estáticos relativos (`./app.js`, `./styles.css`, `./assets/...`) y no
incluye comentarios con rutas, versiones ni identificadores de despliegue.

## 7. Salvedades y recomendaciones

| # | Hallazgo | Riesgo | Recomendación |
|---|---|---|---|
| 1 | Estáticos servidos en CRLF (Δ = +1 byte/línea) | bajo: no altera el contenido, pero rompe la comparación por hash y delata una copia con conversión de saltos | empaquetar en binario (`cp`/`robocopy` sin traducción) para que el `sha256` coincida en crudo |
| 2 | Sin `Content-Security-Policy` como cabecera | medio: la CSP de `<meta>` no aplica a respuestas no HTML ni permite `frame-ancestors` | añadir bloque `headers` en `vercel.json` con la misma política + `frame-ancestors 'none'` |
| 3 | Sin `X-Content-Type-Options: nosniff` | bajo: los tipos se declaran explícitamente, pero un navegador podría sniffar | añadir `nosniff` en `vercel.json` |
| 4 | Sin `Referrer-Policy` como cabecera | bajo: el `<meta>` cubre el HTML, no el resto | añadir cabecera `no-referrer` |
| 5 | JS como `text/javascript` | informativo: válido desde RFC 9239 | ninguno, o forzar `application/javascript` si se exige el literal |
| 6 | Rutas desconocidas devuelven `200` con el shell | bajo: no expone nada, pero genera soft-404 y confunde a scanners | devolver `404` para rutas fuera de la lista de vistas, si se quiere limpieza |
| 7 | Cliente conserva `API.chat` | informativo: inalcanzable por el corte en `chatIsConfigured()` y por el 404/405 del servidor | dejar como está mientras la IA siga apagada |

## 8. Reproducción

```bash
R="C:/Users/aleja/Downloads/App Financiera"
W="$HOME/auditoria-deploy"; mkdir -p "$W"; cd "$W"

# 1. Estado e IA
curl -s https://paideia-mu.vercel.app/api/status | python -m json.tool

# 2. Hash servido vs HEAD (normalizando CRLF)
for f in index.html dark_theme.css chat_withheld_notice.js app.js; do
  curl -s "https://paideia-mu.vercel.app/$f" -o "live_$f"
  printf '%-26s HEAD=%s LIVE=%s\n' "$f" \
    "$(git -C "$R" show "HEAD:api/_static/$f" | sha256sum | cut -c1-16)" \
    "$(tr -d '\r' < "live_$f" | sha256sum | cut -c1-16)"
done

# 3. Cabeceras
curl -s -o /dev/null -D - https://paideia-mu.vercel.app/

# 4. Rutas prohibidas
for p in /api/chat /api/chat/queue /api/secure /api/mission /api/_core/domain.py /.env /docs/; do
  printf '%-24s ' "$p"; curl -s -o /dev/null -w '%{http_code} %{content_type}\n' "https://paideia-mu.vercel.app$p"
done
```

## 9. Conclusión

Lo publicado es el `HEAD` (`a0e48fd`, igual a `origin/master`): los 15 estáticos coinciden byte a
byte tras normalizar CRLF y `/api/status` coincide en crudo. La IA está apagada de extremo a
extremo (`not_configured`, sin rutas de chat, con corte también en el cliente). No hay secretos,
rutas locales, código fuente, `.env`, `.git` ni documentación accesibles; todo lo que no es API
cae en el shell de la app.

Quedan tres salvedades que no cambian el veredicto pero sí el grado de rigor: la conversión CRLF
del empaquetado, la ausencia de CSP/`nosniff`/`Referrer-Policy` como cabeceras HTTP y el
`text/javascript` en lugar de `application/javascript`.
