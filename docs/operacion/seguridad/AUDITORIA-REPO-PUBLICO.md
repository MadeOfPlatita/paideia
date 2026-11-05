# Auditoría de seguridad — repositorio público `MadeOfPlatita/paideia`

**Fecha:** 4/11/2026, 22:00 (UTC+01:00)
**Objeto:** verificación de la publicación del repositorio, antes privado, ahora `public`.
**Alcance:** árbol de trabajo (1.364 ficheros versionados), los 25 commits, **todos** los objetos Git (1.371 blobs), `.gitignore`, `.vercelignore`, artefactos de desarrollo, metadatos y superficie de la función desplegada en Vercel.

---

## Veredicto: **APTO CON CONDICIONES**

**No se ha encontrado ningún secreto real, ni en el árbol actual ni en la historia completa: no hay nada que rotar ni que purgar.** Las condiciones que se listan abajo son de higiene, datos personales y material de terceros; ninguna bloquea la publicación ni exige reescribir el repositorio.

La única credencial viva relacionada con el proyecto está en `app/.env`, **ignorado por Git y nunca versionado** (0 apariciones de su prefijo en los 1.371 blobs). El riesgo ahí no es GitHub, es empaquetar la carpeta a mano para entregarla.

---

## 1. Resumen de hallazgos

| ID | Gravedad | Hallazgo | Acción |
|---|---|---|---|
| A1 | **Media** | 7 ficheros de estado local de Wrangler versionados en `worker/.wrangler/`, incluido `cf.json` con ciudad, código postal y coordenadas de quien ejecutó `wrangler dev` | `git rm -r --cached worker/.wrangler` + ignorar la carpeta |
| A2 | **Media** | Nombre completo y correo personal en los metadatos de 14 de los 25 commits | Decidir: aceptar (autoría) o reescribir con `filter-repo`; el correo no aporta nada |
| A3 | **Media-baja** | 44 ficheros con la ruta absoluta `C:/Users/aleja` (revela cuenta de Windows y rutas del entorno de IA) | Sanear la prosa; los logs de evidencia pueden quedarse |
| A4 | **Media-baja** | Copias íntegras de páginas de terceros (3,5 MB de HTML en 10 páginas) y un PDF de Renault con el nombre de una empleada en los metadatos; contradice el propio `FUENTES-Y-PERMISOS.md` | Retirar o sustituir por extractos + URL |
| B1 | Baja | `api/build_core.py` vive dentro de `api/`, así que Vercel lo publica como función sin handler | Mover a `scripts/` |
| B2 | Baja | `.vercelignore` no excluye `.env*` ni `.vercel` (sí los excluye `.gitignore`) | Añadir 4 líneas |
| B3 | Baja | `.pytest_cache/` no está en `.gitignore`; `!.env.example` queda anulado por el `.env*` final | Reordenar y añadir patrón |
| B4 | Baja | 17,9 MB en un único volcado de API; un ZIP duplica documentación ya versionada | Podar o LFS, no urgente |
| C1 | Informativo | 1 blob inalcanzable en local (borrador de un cierre); no está en el remoto | Ninguna |
| C2 | Informativo | La documentación revela el uso de agentes (Hermes, `deleg_*`, rutas de venv) | Es divulgación, no seguridad: ya queda constancia |

**Lo que está bien y conviene no tocar:** cero credenciales en la historia, `secret_scanning` y `push_protection` activos en GitHub con 0 alertas, sin `node_modules`, sin claves de despliegue, sin `.env` versionado, y un despliegue que no empaqueta ni el contador ni el chat.

---

## 2. Secretos

### 2.1 Árbol actual — limpio

Se buscaron los patrones de los proveedores que el proyecto usa o ha usado, sobre los 1.364 ficheros versionados:

```bash
git grep -n -I -E 'gsk_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{20,}|github_pat_|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY' -- .
# sin resultados
```

> Nota de uso: `git grep` no admite mezclar un patrón posicional con `-e`; los patrones van todos dentro de una sola expresión `-E`.

Resultado: **0 claves de Groq, 0 de OpenAI, 0 de Google, 0 tokens de GitHub, 0 claves AWS, 0 claves privadas.**

Tampoco hay cadenas de conexión con credenciales ni JWT reales. Las únicas coincidencias son falsos positivos, detallados en 2.3.

### 2.2 Historia completa — limpia

No basta con el árbol: un secreto borrado sigue siendo público. Se escanearon **todos** los objetos Git, no solo los alcanzables:

```bash
git log --all --oneline -S'gsk_'                       # vacío
git log --all --oneline -S'AIza' -S'sk-proj'           # vacío
git cat-file --batch-all-objects --batch | grep -a -c -E 'gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}'
# 0
```

- 25 commits, 1.371 blobs, 49,4 MB de contenido sin comprimir: **0 claves de proveedor**.
- `git fsck --unreachable --dangling`: **0 commits inalcanzables**. Solo 1 blob suelto, que es un borrador de documentación sin secretos (C1).
- No hubo `force-push` ni reescritura publicada: `git ls-remote origin` devuelve `a0e48fd`, idéntico al `HEAD` local.
- La afirmación de `docs/ESTADO_Y_PLAN.md` («la clave que estaba pegada en `.gitignore` se movió a `.env`») es compatible con lo observado: la clave estuvo en un fichero de trabajo, pero **nunca entró en un commit**. El `.gitignore` inicial ya llevaba el comentario «clave retirada» y ninguna clave.

### 2.3 Falsos positivos (para que nadie los confunda con una fuga)

| Coincidencia | Dónde | Por qué no es un secreto |
|---|---|---|
| `sk-ind…` | `myinvestor-account.html` | Es `risk-indicator`, una clase CSS |
| `postgresql://<USER>:<PASSWORD>@db.[PROJECT-REF].supabase.co` | `quote-pages/10.txt`, `neon-driver.html` | Placeholders de la documentación de Neon/Supabase |
| `Liferay.authToken = '…'` | 3 HTML del Tesoro | Token anti-CSRF de un portal público, ligado a una sesión de servidor que no está en el repo. Inservible sin la cookie |
| `Bearer ***` / `Bearer OFFLINE_TEST_SECRET_ONLY` / `synthetic-boundary-token` | docs y tests | Marcadores y cadenas de prueba evidentes |
| `key=Paid…`, `key=prio…` | JS de tests | Nombres de campo (`key=priority`), no claves |

### 2.4 La credencial que sí existe (y su estado)

| Fichero | Contenido | ¿Versionado? | Estado |
|---|---|---|---|
| `app/.env` | `GROQ_API_KEY` real (56 caracteres, prefijo `gsk_`) | **No** — `.gitignore:14` (`.env*`) | Viva. Correcto que viva solo aquí |
| `.env.local` (raíz) | `VERCEL_OIDC_TOKEN` (JWT) | **No** — `.gitignore:14` | **Caducado** el 4/11/2026 a las 09:39 (vida de 12 h) |
| `.vercel/project.json` | `projectId`, `orgId` | **No** — `.gitignore:13` | Sin valor como credencial, pero no debe compartirse |
| `app/.env.example` | `GROQ_API_KEY=` **vacío** | Sí | Correcto: plantilla sin valor |

Verificado que ninguno de los tres primeros ha estado jamás en un commit:

```bash
git rev-list --objects --all | grep -c 'paideia-local/.env$'        # 0
git rev-list --objects --all | cut -d' ' -f1 | git cat-file --batch \
  | grep -a -c -E 'prj_VeFff|team_51ySBJ|VERCEL_OIDC_TOKEN'          # 0
```

**Consecuencia práctica:** no hay que rotar la clave de Groq por la publicación. Sí conviene rotarla si en algún momento se compartió la carpeta del proyecto comprimida, o si la clave se pegó en un chat o en una captura: el `.env` está al lado del repositorio, no dentro.

---

## 3. `.gitignore` y `.vercelignore`

### 3.1 Cobertura actual (abreviado)

```
.env
.env.local
.env.*.local
!.env.example
__pycache__/
*.pyc
.vercel
.env*
```

| Elemento | ¿Cubierto? | Evidencia |
|---|---|---|
| `.env` y variantes | Sí | `git check-ignore -v .env.local` → `.gitignore:14:.env*` |
| `.env` del prototipo | Sí | ídem |
| `.vercel/` | Sí | `.gitignore:13:.vercel` |
| `__pycache__/`, `*.pyc` | Sí | `api/_core/__pycache__` no está versionado |
| `.pytest_cache/` | **No** | Solo se salva porque pytest escribe su propio `.gitignore` con `*` |
| `worker/.wrangler/` | **No** | 7 ficheros versionados (A1) |
| `*.zip`, `*.sqlite`, `*.pdf`, capturas | **No** | Se versionan a propósito como evidencia |

### 3.2 Dos defectos de forma

1. **El orden anula la excepción.** `!.env.example` está en la línea 5 y `.env*` en la 14; como gana la última regla, la plantilla queda ignorada para ficheros nuevos. Hoy no rompe nada porque `.env.example` ya está versionado, pero si alguien recrea el repo, la plantilla se pierde.
2. **`.vercel` y `.env*` se añadieron tarde** (commit `b1bedef`), después de que el proyecto ya estuviera en marcha. No hubo daño — nada entró — pero el patrón llegó por reacción, no por diseño.

Ninguno de los dos afecta a lo ya publicado.

---

## 4. Datos personales

### 4.1 Nombre y correo en los metadatos de Git — **el hallazgo más visible**

```bash
git log --all --format='%an <%ae>' | sort | uniq -c
```

| Commits | Autor | Correo |
|---|---|---|
| 8 | `Alejandro` | `alejanmarpla0506@gm•••.com` |
| 6 | `Alejandro M… P…` (nombre y dos apellidos) | `alejanmarpla0506@gm•••.com` |
| 7 | `Alejandro M… P…` | `307587994+MadeOfPlatita@users.noreply.github.com` |
| 4 | `Alejandro` | `alejandro@example.invalid` |

*(Correo enmascarado a propósito en este informe; el valor exacto se ve con el comando de arriba.)*

- **Nombre completo:** aparece en 13 commits y en la API de GitHub (`/commits`, `/contributors`). Para un trabajo académico firmado es **aceptable e incluso deseable**: la autoría debe ser verificable.
- **Correo de Gmail:** en 14 commits. No aporta nada a la autoría y es recolectable. Es el dato que conviene quitar si se hace limpieza.
- **Correo `noreply` de GitHub:** 7 commits. Inofensivo, ya es público por diseño.

**Matiz importante antes de reescribir:** varios documentos citan hashes concretos (`c051749`, `a0e48fd`, `f3729d4`). Un `filter-repo` cambia todos los SHA y deja esas referencias muertas, además de exigir `push --force`. A menos que el correo sea un problema real, **no merece la pena reescribir la historia a un día de la entrega**. Alternativa barata: activar «Keep my email addresses private» en GitHub para los commits futuros y dejar los 25 actuales como están.

### 4.2 Rutas con nombre de usuario — 44 ficheros

```bash
git grep -l -I 'C:[/\\]Users[/\\]aleja' -- . | wc -l   # 44
```

Reparto: 13 en `docs/` (GOAL, CIERRE, contratos), 4 en `docs/overnight-ampliado/…/A`, 3 en `docs/ia-groq-estructurada/…`, y el resto en logs de pruebas y evidencias.

Qué revela: el nombre de la cuenta de Windows (`aleja`, derivado del nombre), la estructura del disco y —en varios logs— rutas del entorno de IA (`AppData/Local/hermes/...`, `venv/Scripts/python.exe`). No hay credenciales, pero es huella innecesaria.

**Valoración:** aceptable en un trabajo académico; no es un dato sensible (no hay DNI, teléfono, IBAN ni dirección postal). Se puede sanear la prosa sin tocar los logs:

```bash
git grep -l -I 'C:/Users/aleja' -- 'docs/*.md' \
  | xargs sed -i 's#C:/Users/aleja#<USUARIO>#g'
```

Los logs de pytest y las capturas de consola es mejor dejarlos: son evidencia y sanearlos los vuelve menos fiables.

### 4.3 `worker/.wrangler/cache/cf.json` — ubicación aproximada

Este fichero, **versionado**, es la huella de una petición que pasó por `wrangler dev`:

| Campo | Valor (enmascarado aquí) |
|---|---|
| `city` / `region` | Madrid / Madrid |
| `postalCode` | `280**` |
| `latitude` / `longitude` | `40.41**` / `-3.70**` |
| `timezone` | `Europe/Madrid` |
| `asn` / `asOrganization` | `34977` / PROCONO S.A. |

No es la dirección de nadie por sí solo, pero es un dato de localización asociado a la máquina que ejecutó el comando, y no pinta nada en un repositorio académico. Se elimina con A1.

### 4.4 Datos de terceros

- `docs/investigacion-apis-02/evidence/renault-precontractual.pdf`: metadatos `Author = GARCIA Maria-Luisa`. Es el nombre de una empleada del banco en un documento público; no es ilícito, pero es PII de terceros que no hace falta redistribuir.
- Los HTML copiados de MyInvestor, Neon, Supabase y Tesoro contienen correos de atención al cliente y nombres de empleados en el marcado. Son datos publicados por esas empresas; el problema no es la PII, es la copia (A4).
- **No hay** DNI/NIE, IBAN, teléfonos ni direcciones postales en el repositorio. Las coincidencias de los buscadores son hashes de tests y titulares del BOE.

### 4.5 Conclusión de la sección

Para un trabajo académico de acceso público, el nivel de datos personales es **aceptable**. Lo único que yo cambiaría: el correo de Gmail en los commits (o su reescritura, con el coste de SHA ya explicado) y la ruta `C:/Users/aleja` en la documentación de prosa. El nombre completo, no.

---

## 5. Artefactos y metadatos

### 5.1 `.vercel/` — **no publicado** (correcto)

Está en disco, pero ignorado y **nunca commiteado**:

```bash
git log --all --oneline -- .vercel        # vacío
git check-ignore -v .vercel/project.json  # .gitignore:13:.vercel
```

Contiene `projectId` y `orgId`. No son credenciales — no permiten desplegar ni leer el proyecto — pero la propia documentación de Vercel recomienda no compartirlos. Al no estar en la historia, no hay nada que hacer.

### 5.2 `worker/.wrangler/` — **publicado y no debería** (A1)

```
worker/.wrangler/cache/cf.json
worker/.wrangler/state/v3/cache/miniflare-CacheObject/metadata.sqlite
worker/.wrangler/state/v3/d1/miniflare-D1DatabaseObject/metadata.sqlite
worker/.wrangler/state/v3/flagship/miniflare-flagship-FlagshipObject/metadata.sqlite
worker/.wrangler/state/v3/kv/miniflare-KVNamespaceObject/metadata.sqlite
worker/.wrangler/state/v3/observability/miniflare-wobs-trace-store/metadata.sqlite
worker/.wrangler/state/v3/r2/miniflare-R2BucketObject/metadata.sqlite
```

Los seis `.sqlite` son metadatos vacíos de Miniflare: una sola tabla `_cf_ALARM` con **0 filas**. No hay datos, ni KV, ni D1 real. El problema es `cf.json` (§4.3) y el ruido.

Entraron en `9c97411` («Prepara el Worker de Cloudflare con la API portada») y siguen ahí. Están también en la historia; como su contenido no es sensible, **no compensa reescribir**: basta con borrarlos de `HEAD`.

### 5.3 Lo que no hay (verificado)

- `node_modules`: **0** ficheros versionados.
- Claves de despliegue, tokens de Vercel o `wrangler` en claro: **0**.
- Submódulos y Git LFS: no hay `.gitmodules`.
- `.pytest_cache/`: presente en disco, fuera de Git (por el `.gitignore` interno de pytest).

### 5.4 Volumen

| Métrica | Valor |
|---|---|
| Ficheros versionados | 1.364 (1.067 en `docs/`, 243 en `prototipos/`, 21 en `api/`) |
| Tamaño del `.git` | 21 MB (16,2 MiB de objetos sueltos) |
| Mayor fichero | `docs/investigacion-apis-02/evidencia/twelvedata-etfs-demo.body`, **17,9 MB** |
| Capturas PNG | 80 |
| PDF | 5 |
| ZIP | 2 (`Paideia-investigacion.zip` duplica documentación ya presente) |

No es un problema de seguridad, pero un clon de 20 MB para revisar un TFG es incómodo, y el volcado de 18 MB de TwelveData no aporta nada que no esté ya resumido en los `.md`.

---

## 6. Riesgo de la función pública (Vercel)

### 6.1 Qué se empaqueta

`vercel.json`:

```json
"functions": {
  "api/index.py": { "includeFiles": "{api/_core/**,api/_static/**}" }
}
```

`.vercelignore` excluye `.git`, `docs`, `spikes`, `worker`, `prototipos`, `*.zip` y `paideia-security-*.txt`.

**Conclusión: el contador no se despliega.** `mission_ledger.py` y `provision_mission.py` viven en `app/`, que queda fuera tanto por `includeFiles` como por `.vercelignore`. Lo mismo vale para los tests y la documentación. Ojo: `.env` **no** figura en `.vercelignore` (solo en `.gitignore`), que es el hueco B2.

### 6.2 Qué expone la función

Rutas reales en `api/index.py`:

```
GET  /api/status
GET  /api/conditions
GET  /api/catalogue
GET  /api/products/<id>
POST /api/compare
POST /api/calculate
```

- **No existe `/api/chat`.** Una petición a esa ruta cae en el manejador de estáticos y devuelve `404 {"code": "NOT_FOUND"}`. El mensaje «Chat IA no disponible en la versión pública» que aparece en `_status()` es informativo, y `ai.connected` es siempre `false`. El frontend (`api/_static/app.js`) conserva la UI de chat y llama a `/api/chat`: código muerto, sin fuga.
- **Ningún endpoint acepta credenciales.** `grep -rn 'os.environ|getenv|Authorization|Bearer' api/` no devuelve **nada**: la función no lee variables de entorno ni cabeceras de autorización. No hay forma de que un usuario aporte una clave.
- **Superficie acotada:** cuerpo máximo `MAX_BODY = 16384`, IDs de producto validados con `PRODUCT_ID.fullmatch`, y el servidor de estáticos normaliza la ruta y comprueba el prefijo antes de abrir (`if not candidate.startswith(os.path.abspath(STATIC_ROOT))`).
- **Sin estado ni base de datos:** `"storage": "bundled_snapshot_no_database"`.

**Salvedad honesta:** esta verificación es estática. El encargo prohíbe red salvo `gh` y `git`, así que **no** se ha consultado `https://paideia-mu.vercel.app/api/status`. Si se quiere cerrar el círculo, basta un `curl -s https://paideia-mu.vercel.app/api/status | jq` y comprobar `mode: "public_serverless"` y `ai.connected: false`.

### 6.3 Un endpoint no previsto

`api/build_core.py` es un **script de generación** (lee `docs/validacion-04/...` y `prototipos/.../condiciones.json`), pero está dentro de `api/`, y el runtime de Vercel publica cada `api/*.py` como función. No tiene `handler` ni `app`, así que `/api/build_core` devolverá un 500 genérico. No filtra nada —sus rutas de origen no están en el bundle— pero es superficie innecesaria y un fallo de build esperando a ocurrir.

---

## 7. Acciones, por orden

### Inmediatas (10 minutos, antes de dar el enlace a la profesora)

```bash
# 1. Sacar el estado local de Wrangler del repositorio
git rm -r --cached worker/.wrangler
printf '\n# Estado local de Wrangler\n.wrangler/\n' >> .gitignore

# 2. Cerrar los huecos de .gitignore y .vercelignore
printf '.pytest_cache/\n' >> .gitignore
printf '.env*\n.vercel\n.pytest_cache/\n*.sqlite\n' >> .vercelignore

# 3. Mover el script de build fuera de la carpeta de funciones
mkdir -p scripts
git mv api/build_core.py scripts/build_core.py
# `ROOT = Path(__file__).resolve().parents[1]` sigue apuntando a la raíz del repo.
```

### Recomendadas (antes de la entrega)

4. **Decidir sobre el correo de Gmail.** Si se queda: activar «Keep my email addresses private» para el futuro y no reescribir. Si se va: `git filter-repo --mail-map` + `push --force`, asumiendo que los hashes citados en `docs/` dejan de resolver.
5. **Sanear `C:/Users/aleja` en la prosa** (`docs/*.md`), dejando intactos los logs de evidencia.
6. **Revisar la redistribución de terceros (A4):** retirar los HTML completos y el PDF de Renault, o sustituirlos por extractos de 10-20 líneas con URL y fecha. En cualquier caso, corregir la frase de `docs/catalogo-hasta-bloqueo/FUENTES-Y-PERMISOS.md` que afirma que no se redistribuyeron documentos originales, porque el repositorio los contiene.
7. **Podar el volcado de 17,9 MB** de TwelveData y el ZIP duplicado si no se necesitan para la corrección.

### Si se empaqueta la carpeta para entregar

**No comprimir el directorio de trabajo.** Usar `git archive`, que solo incluye lo versionado:

```bash
git archive --format=zip -o paideia-entrega.zip HEAD
```

Un `.zip` de la carpeta metería `app/.env` (clave de Groq viva), `.env.local` (token caducado) y `.vercel/` (IDs de proyecto). Ese es, hoy, el único camino realista por el que la clave puede salir de la máquina.

---

## 8. Anexo: evidencia reproducible

```bash
# --- Estado del repositorio y del remoto ---
git remote -v                                  # origin → MadeOfPlatita/paideia.git
git rev-list --all --count                     # 25
git ls-remote origin                           # a0e48fd = HEAD local (sin divergencia)
gh api repos/MadeOfPlatita/paideia --jq '{private,visibility,size,forks_count}'
# {"private":false,"visibility":"public","size":14669,"forks_count":0}

# --- Secretos en árbol e historia ---
git grep -n -I -E 'gsk_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}' -- .   # vacío
git log --all --oneline -S'gsk_'                                                             # vacío
git cat-file --batch-all-objects --batch-check='%(objecttype) %(objectsize)' \
  | awk '$1=="blob"{n++;s+=$2} END{print n" blobs, "s" bytes"}'   # 1371 blobs, 49.463.704 bytes
git cat-file --batch-all-objects --batch | grep -a -c -E 'gsk_[A-Za-z0-9]{20,}'               # 0
git fsck --unreachable --dangling                                                             # 1 blob, 0 commits

# --- Secret scanning de GitHub ---
gh api repos/MadeOfPlatita/paideia --jq '.security_and_analysis'
# secret_scanning: enabled · push_protection: enabled · 0 alertas
gh api repos/MadeOfPlatita/paideia/secret-scanning/alerts    # []

# --- Credenciales locales ---
git check-ignore -v .env.local app/.env .vercel/project.json
# .gitignore:14:.env*  (las dos primeras) · .gitignore:13:.vercel
git rev-list --objects --all | grep -c 'paideia-local/.env$'                 # 0
git rev-list --objects --all | cut -d' ' -f1 | git cat-file --batch \
  | grep -a -c -E 'prj_VeFff|team_51ySBJ|VERCEL_OIDC_TOKEN'                  # 0

# --- Datos personales ---
git log --all --format='%an <%ae>' | sort | uniq -c
git grep -l -I 'C:[/\\]Users[/\\]aleja' -- . | wc -l                        # 44
git grep -n -I -E '\b[0-9]{8}[ -]?[A-Z]\b|\bES[0-9]{2}([ ]?[0-9]{4}){5}\b' -- .   # sin DNI/IBAN

# --- Artefactos ---
git ls-files worker/.wrangler | wc -l                                       # 7
git ls-files | grep -c node_modules                                         # 0
git ls-files -z | xargs -0 -I{} du -k "{}" | sort -rn | head -3
# 17532 docs/investigacion-apis-02/evidencia/twelvedata-etfs-demo.body
#  1164 docs/planificacion-03/03-capacidad-ia/scenarios.json
#  1040 docs/diseno-ideas/maquetas/capturas/b-mobile-390.png

# --- Despliegue ---
cat vercel.json                       # includeFiles: api/_core/**, api/_static/**
cat .vercelignore                     # excluye prototipos → fuera el contador
ls api/*.py                           # build_core.py, index.py
grep -rn -E 'os\.environ|getenv|Authorization|Bearer' api/    # sin resultados
```

### Metadatos consultados por API

| Comprobación | Resultado |
|---|---|
| Visibilidad | `public`, `private: false` |
| Fork / estrellas | 0 / 0 |
| Deploy keys | `[]` |
| Alertas de secret scanning | `[]` |
| Push protection | `enabled` |
| Validación de secretos | `disabled` (solo detecta, no comprueba vigencia) |
| Wiki / Projects | `true` / `true` (vacíos) |
| Licencia | `null` — coherente con «no se concede licencia de reutilización» del README |

Un apunte sobre `secret_scanning_validity_checks: disabled`: GitHub no comprobará si una clave detectada sigue viva. No cambia nada hoy (no hay ninguna), pero activarlo es gratis y evita falsos positivos en el futuro.

---

## 9. Conclusión

El repositorio **puede seguir público**. No contiene credenciales, ni en el presente ni en su historia; la función desplegada no lleva el contador, no lleva el chat y no acepta claves de usuario. Lo que queda por resolver es presentación: sacar el estado local de Wrangler, decidir qué hacer con el correo personal de los commits, sanear rutas y revisar el material de terceros que se redistribuye. Ninguna de esas tareas exige rotar nada ni reescribir la historia, y todas caben en una sesión corta antes de la entrega.
