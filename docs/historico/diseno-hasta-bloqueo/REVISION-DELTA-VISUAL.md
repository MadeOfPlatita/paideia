# Revisión independiente · delta visual final (tarjetas homogéneas)

**Apto.** El delta `999820d0` está desplegado en la web pública y cumple las seis comprobaciones: las dos tarjetas comparten relleno, radio, borde y fondo; el contraste AA está limpio con sonda validada; no hay desbordes; los cinco avisos siguen visibles; el informe y la impresión soportada siguen en claro; y las cuatro cabeceras de seguridad están presentes. El único matiz tipográfico es que el `h2` del panel contextual conserva `700` por una regla más específica de la hoja base, no por este delta (ver *Observaciones*).

- **Fecha:** 2026-11-04, 22:29–22:40 (Europe/Madrid)
- **Objeto:** `app/static/dark_theme.css` y su copia `api/_static/dark_theme.css`
- **Instantánea:** commit del delta `540a032`; sha256 `999820d016fb85634749de63784da8be3b51be74d17e29740eaf6fa5214c9118` en disco, copia y respuesta HTTP (normalizando CRLF)
- **Web revisada:** <https://paideia-mu.vercel.app> (producción, no servidor local)
- **Navegador:** Chromium 156 headless por CDP; viewports 1440×900, 390×844 y 320×680; `Network.setCacheDisabled(true)` + `Network.clearBrowserCache` + recarga forzada antes de medir
- **Estado de IA:** el de la web pública, *IA no conectada*; no se usó Groq ni se envió ninguna consulta a un proveedor

## Tabla de comprobaciones

| # | Comprobación | Resultado | Evidencia |
|---|---|---|---|
| 1 | Hash local, copia y HTTP; `Content-Type`; regla nueva en el CSS servido | **Pasa** — `999820d0…` en las tres; `text/css`; regla `.product-card, .context-panel` presente y activa en CSSOM | §1 |
| 2 | `.product-card` y `.context-panel` en producción: 22 px / 16 px / `rgb(48,52,49)` | **Pasa** — ambos idénticos a 1440 y 390, fondo `rgb(26,28,29)`; 20 candidatos visibles | §2 |
| 3 | Contraste AA en 8 rutas × 1440/390, con sonda 0→1→0 | **Pasa** — 1.422 elementos por ancho, 0 fallos; sonda detectada con ratio 1,00 y retirada a 0 | §3 |
| 4 | Desbordes a 1440/390/320 en 8 rutas | **Pasa** — 24/24 `scrollWidth == clientWidth`; también con comparación y escenarios poblados a 1440/390 | §4 |
| 5 | Cinco avisos visibles; informe descargado e impresión en claro | **Pasa** — consentimiento, simulación, IA no conectada, fuentes y campos desconocidos visibles a 1440 y 390; informe real de 5.681 B sin rastro del tema oscuro; impresión clara | §5 |
| 6 | Cabeceras de seguridad nuevas | **Pasa** — las cuatro presentes en `/`, `/dark_theme.css` y `/api/status` | §6 |

## 1. Instantánea, despliegue y regla servida

```console
$ sha256sum app/static/dark_theme.css api/_static/dark_theme.css
999820d016fb85634749de63784da8be3b51be74d17e29740eaf6fa5214c9118 *app/static/dark_theme.css
999820d016fb85634749de63784da8be3b51be74d17e29740eaf6fa5214c9118 *api/_static/dark_theme.css

$ curl -sS https://paideia-mu.vercel.app/dark_theme.css | sed 's/\r$//' | sha256sum
999820d016fb85634749de63784da8be3b51be74d17e29740eaf6fa5214c9118 *-
```

La respuesta HTTP del CSS:

```http
HTTP/1.1 200 OK
Content-Type: text/css
Content-Length: 6553
Cache-Control: public, max-age=300
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
X-Frame-Options: SAMEORIGIN
Permissions-Policy: geolocation=(self), camera=(), microphone=()
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

No es un `200` de la SPA devolviendo HTML: el `Content-Type` es `text/css` y el cuerpo tiene 6.553 bytes. La regla nueva está en las líneas 121–127 del archivo servido:

```css
/* Un solo lenguaje de tarjeta: ficha de producto y panel de contexto también. */
.product-card, .context-panel {
  padding: 22px;
  border: 1px solid #303431;
  border-radius: 16px;
  background: var(--surface);
}
```

Y no solo está en el texto: el navegador la tiene cargada y aplicada. Leída desde `document.styleSheets` tras la recarga sin caché:

```json
{"href":"https://paideia-mu.vercel.app/dark_theme.css",
 "media":"screen",
 "selector":".product-card, .context-panel",
 "css":"padding: 22px; border: 1px solid rgb(48, 52, 49); border-radius: 16px; background: var(--surface);"}
```

`--surface` resuelve a `#1a1c1d` (línea 8 del mismo archivo), que en cómputo es `rgb(26, 28, 29)`.

El delta `540a032` toca solo las dos copias del CSS (11 líneas cada una) y dos documentos; no toca HTML, JS ni Python. `540a032` es ancestro del `HEAD` actual (`06ad436`, solo documentación).

## 2. Tarjetas en producción: misma piel, dos componentes

Medido con `getComputedStyle` en la biblioteca pública, tras recarga forzada sin caché. La biblioteca devuelve **20 candidatos** (20 `.product-card`), no una muestra ni un estado vacío.

| Propiedad | `.product-card` a 1440 | `.context-panel` a 1440 | `.product-card` a 390 | `.context-panel` a 390 |
|---|---|---|---|---|
| `padding` | `22px` en los cuatro lados | `22px` en los cuatro lados | `22px` | `22px` |
| `border-radius` | `16px` | `16px` | `16px` | `16px` |
| `border-top` | `1px solid rgb(48, 52, 49)` | `1px solid rgb(48, 52, 49)` | `1px solid rgb(48, 52, 49)` | `1px solid rgb(48, 52, 49)` |
| `background-color` | `rgb(26, 28, 29)` | `rgb(26, 28, 29)` | `rgb(26, 28, 29)` | `rgb(26, 28, 29)` |
| Ancho medido | 996 px | 272 px | 358 px | 358 px |

Comprobado en la primera y en la última ficha, no solo en una: las 20 tarjetas comparten la regla y el panel contextual también. Los dos lenguajes de tarjeta que motivaron la salvedad anterior han desaparecido.

La jerarquía declarada también se aplica:

- `h2` de sección: `26px/650` («Empieza por la biblioteca») y `23.2px/650` («Tu selección», «Diagnóstico cuantitativo»).
- `h3` de ficha: `20px/620` en todas las tarjetas.
- Matiz: el `h2` del panel contextual («Pai») computa `19px/700` porque `.context-heading h2` de `styles.css` usa un `font` shorthand más específico. No es una regla del delta ni afecta a la unificación de las tarjetas; se anota para que la afirmación «h2 pasa a 650» no se lea como universal.

## 3. Contraste WCAG AA: 8 rutas × 2 anchos, con sonda validada

Script: `skills/software-development/visual-redesign-retrofit/scripts/contrast_audit.js`, ejecutado en la página con `getComputedStyle`, composición alfa sobre el ancestro opaco y umbral 4,5:1 (3:1 para texto grande). Cada ruta se navegó por hash y se esperó su render; `#comparar` y `#escenarios` se auditaron también con datos densos, no solo en estado vacío.

| Ruta | 1440: elementos / fallos | 390: elementos / fallos |
|---|---:|---:|
| `#inicio` | 146 / 0 | 146 / 0 |
| `#perfil` | 95 / 0 | 95 / 0 |
| `#biblioteca` (20 fichas) | 601 / 0 | 601 / 0 |
| `#comparar` (estado vacío) | 67 / 0 | 67 / 0 |
| `#escenarios` (formulario) | 188 / 0 | 188 / 0 |
| `#simulacion` | 98 / 0 | 98 / 0 |
| `#glosario` | 97 / 0 | 97 / 0 |
| `#privacidad` | 130 / 0 | 130 / 0 |
| **Total** | **1.422 / 0** | **1.422 / 0** |

Estados densos adicionales, también a cero:

| Estado | 1440 | 390 |
|---|---:|---:|
| `#comparar` con dos productos y tabla de metadatos | 178 / 0 | 178 / 0 |
| `#escenarios` con A y B calculados y tablas | 392 / 0 | 392 / 0 |

Nota de anchura: a 1440 el `clientWidth` real es 1425 por la barra de desplazamiento de Chromium; la auditoría registra 1425. A 390 se usó viewport móvil con barras superpuestas y `clientWidth = 390` exacto.

**Validación de la sonda (sin esto el cero no vale).** Se inyectó un `<p>` con color igual al fondo de la página y se retiró:

| Ancho / ruta | Antes | Con la violación | Nodo detectado | Después |
|---|---:|---:|---|---:|
| 1440 / `#biblioteca` | 0 | 1 | `p` «Sonda de contraste plantada», ratio **1,00**, exigido 4,5, `fg` y `bg` `rgb(16,17,18)` | 0 |
| 390 / `#biblioteca` | 0 | 1 | `p` «Sonda movil plantada», ratio 1,00 | 0 |

La sonda encuentra lo que se le planta y vuelve a cero al retirarlo en los dos anchos. El cero de la tabla anterior es un cero medido, no un selector roto.

## 4. Desbordamiento horizontal: 8 rutas × 3 anchos

Criterio: `document.documentElement.scrollWidth === document.documentElement.clientWidth`. También se comprobó que ningún elemento visible tuviera `right > clientWidth + 1`.

| Ruta | 1440 | 390 | 320 |
|---|---:|---:|---:|
| `#inicio` | 0 | 0 | 0 |
| `#perfil` | 0 | 0 | 0 |
| `#biblioteca` | 0 | 0 | 0 |
| `#comparar` | 0 | 0 | 0 |
| `#escenarios` | 0 | 0 | 0 |
| `#simulacion` | 0 | 0 | 0 |
| `#glosario` | 0 | 0 | 0 |
| `#privacidad` | 0 | 0 | 0 |

24/24 combinaciones a cero. Con contenido denso: `#comparar` con dos productos da `1425/1425` a 1440 y `390/390` a 390; `#escenarios` con A y B calculados da `1425/1425` y `390/390`. Ninguna tabla ancha ni URL larga abre scroll horizontal.

## 5. Avisos, informe descargado e impresión

### 5.1 Los cinco avisos siguen visibles

Se comprobaron las cinco categorías y sus textos asociados (siete textos en total) en 1440 y 390: elemento encontrado, `display:block` (o `flex` en la etiqueta), `checkVisibility({checkOpacity:true,checkVisibilityCSS:true}) === true`, rectángulo propio y `elementFromPoint` dentro del propio aviso (sin solapamiento). Todos se llevaron al centro del viewport con `scrollIntoView` antes de medir.

| Aviso | Ruta | Texto exacto comprobado | 1440 | 390 |
|---|---|---|---|---|
| Consentimiento | `#privacidad` | «Quiero permitir el almacenamiento local del mapa revisado en este dispositivo.» + «Al marcar la casilla y pulsar Guardar se crea una copia local…» | visible | visible |
| Simulación | `#simulacion` | «ENSAYO FICTICIO · No se enviará nada ni se moverá dinero. No introduzcas identificadores, credenciales, cuenta, tarjeta ni datos de pago.» | visible | visible |
| Simulación (banda) | `#simulacion` | «Los escenarios y el ensayo son simulados; no se mueve dinero.» | visible | visible |
| IA no conectada | cabecera | «Versión pública · IA no conectada» | visible | visible |
| IA no conectada | `#context-panel` | «Chat IA no conectado. Los cálculos, la biblioteca y el glosario funcionan igual.» | visible | visible |
| Fuentes | `#biblioteca` | «Solo se muestran tasas documentadas con fuente y fecha…» + «Fuente primaria: https://…» | visible | visible |
| Campos desconocidos | `#biblioteca` | «Campos desconocidos:» + lista (divisa, saldo máximo, frecuencia de liquidación, tipo posterior a la promoción, derechos de copia/cache/display) | visible | visible |

La casilla `profile-persist-toggle` está deshabilitada mientras el mapa no esté revisado, como explica el propio texto («Revisa el mapa primero para activar el guardado opt-in»); el aviso de consentimiento, su explicación y el estado «Ahora: solo memoria de esta pestaña» siguen visibles. No es un aviso oculto.

### 5.2 Informe descargado: sigue siendo la hoja clara

Se generó un informe real desde la web pública: `#escenarios` → «Cargar ejemplo ficticio en A» → «Calcular escenario A» → «Copiar A a B» → «Calcular escenario B» → «Descargar informe (HTML)». Se interceptó el `Blob` que el ancla entrega al navegador, sin fabricar datos:

- Tamaño: **5.681 bytes**; sha256 `6b2523203ce86e0bd87cc43360ae30a692299fea669d32517eac99c30f4db3a3`.
- Contiene `<!doctype html>`, una única hoja `<style>` embebida y **cero** referencias a `dark_theme`, `#101112`, `1a1c1d` o `303431`.
- `body`: `color: rgb(17,17,17)`, `font-family: Arial, sans-serif`, `font-size: 16px`.
- Cabeceras de tabla `th`: `background: rgb(238,238,238)`; bordes `td`: `rgb(119,119,119)`.

Abrir el HTML descargado en una pestaña limpia y emular `@media print` da `body` a 12 px, texto `rgb(17,17,17)`, `th` `rgb(238,238,238)` y tabla legible; la captura muestra el informe en blanco y negro, legible, sin navegación ni tema oscuro.

### 5.3 Impresión de la app: la capa no alcanza el papel

Con medio `print` emulado por CDP sobre la app pública:

| Medio | `body` fondo | `body` texto | `--paper` | `h1` |
|---|---|---|---|---|
| `screen` | `rgb(16, 17, 18)` | `rgb(245, 246, 244)` | `#101112` | claro |
| `print` | `rgb(255, 255, 255)` | `rgb(0, 0, 0)` | `#F7F5EF` | `rgb(0, 0, 0)` |

La hoja oscura está íntegramente dentro de `@media screen`; en impresión cae a la paleta clara de `styles.css`. También se probó el camino real del botón, no solo la emulación sobre la app vacía: en `#escenarios`, con A y B calculados, se interceptó `window.print` y se pulsó «Imprimir / guardar como PDF». El botón montó `#comparison-report-print` con el informe (4.823 caracteres de HTML); con medio `print` emulado, `body` quedó en `rgb(255,255,255)` sobre texto `rgb(0,0,0)`, el artículo del informe en `rgb(17,17,17)` y `#comparison-report-print` en `display:block`. La captura muestra ese informe claro y legible, sin la interfaz oscura.

**Límite preexistente, no imputable al delta:** imprimir una pantalla normal de la app (por ejemplo `#inicio`, sin informe montado) sale en blanco porque `comparison_report.css` contiene `body > :not(#comparison-report-print){display:none!important}` dentro de `@media print`. El camino soportado es el botón del informe, que sí monta el contenido y sale claro; el delta no cambia esa regla.

## 6. Cabeceras de seguridad

Comprobadas con `GET` (el servidor responde `405` a `HEAD`, así que las cabeceras se leen de la respuesta real). Presentes y con los valores esperados en los tres puntos:

| Endpoint | Estado | `Content-Type` | `X-Content-Type-Options` | `Referrer-Policy` | `X-Frame-Options` | `Permissions-Policy` |
|---|---|---|---|---|---|---|
| `/` | 200 | `text/html` | `nosniff` | `strict-origin-when-cross-origin` | `SAMEORIGIN` | `geolocation=(self), camera=(), microphone=()` |
| `/dark_theme.css` | 200 | `text/css` | `nosniff` | `strict-origin-when-cross-origin` | `SAMEORIGIN` | `geolocation=(self), camera=(), microphone=()` |
| `/api/status` | 200 | `application/json; charset=utf-8` | `nosniff` | `strict-origin-when-cross-origin` | `SAMEORIGIN` | `geolocation=(self), camera=(), microphone=()` |

También está presente `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`. No hay duplicados ni valores contradictorios en las respuestas revisadas.

## Observaciones y límites

- **Matiz de `h2` contextual:** `.context-heading h2` («Pai») computa `19px/700`, no `650`, por el shorthand más específico de `styles.css` (regla preexistente). Los `h2` de sección sí computan `650`; los `h3` de ficha, `20px/620`. No afecta a la unificación de tarjetas ni a ninguna de las seis comprobaciones, pero la afirmación «h2 pasa a 650» no es universal.
- **Impresión directa de la app:** sale en blanco por la regla preexistente de `comparison_report.css`; el informe descargado y su botón de impresión sí salen en claro. Se documenta para no atribuir al delta un comportamiento que ya existía.
- **Estado del árbol:** `HEAD` avanzó a `06ad436` (solo documentación) después del delta; `540a032` sigue siendo ancestro. El árbol de trabajo tiene cambios ajenos sin confirmar (incluido `static/app.js`, 7 líneas). Producción sirve el `app.js` de `HEAD` (`9197b298…`), no esa modificación local; el CSS de producción sí coincide con el árbol y con `api/_static`. No se modificó ningún archivo del repositorio salvo este informe.
- **Ancho 1440:** el layout mide 1425 px por la barra de desplazamiento de Chromium; el viewport de la ventana es 1440. A 390 se usó viewport móvil exacto (`clientWidth = 390`); a 320, `clientWidth = 320`.
- **Alcance:** Chromium headless, emulación de viewport y de medio `print`; no es un dispositivo físico ni una auditoría con lector de pantalla. El contraste es calculado, no percibido. No se usó Groq ni se enviaron datos a un proveedor de IA.

## Veredicto

**Apto.** La corrección de las dos tarjetas está desplegada y medida en producción: `.product-card` y `.context-panel` comparten `22px` de relleno, `16px` de radio, borde `rgb(48,52,49)` y fondo `rgb(26,28,29)` a 1440 y 390. El contraste AA queda limpio en las 8 rutas y 2 anchos (1.422 elementos por ancho, 0 fallos), con sonda que demuestra que el auditor detecta una violación real. No hay desbordes en 24/24 combinaciones. Los cinco avisos siguen visibles, el informe descargado y la impresión soportada siguen en claro, y las cuatro cabeceras de seguridad están presentes. El matiz del `h2` contextual es una regla preexistente más específica, no una regresión del delta.
