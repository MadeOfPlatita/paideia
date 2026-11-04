# Revisión independiente · capa visual 2 (jerarquía y superficies)

- **Fecha:** 2026-11-04
- **Objeto:** `prototipos/paideia-local/static/dark_theme.css` y su copia servida `api/_static/dark_theme.css`
- **Instantánea:** commit `3b67737`, sha256 `492c22cfe53884a8e26067184fbeb38e85b0929862cd80c5354e10a502bb6647` en ambas copias
- **Arranque:** `cd prototipos/paideia-local && python app.py --port 8771`
- **Navegador:** Chromium 156 (headless) por CDP; viewports 1440×900, 390×844 y 320×800
- **Estado de IA:** forzado a *no conectada* (`PAIDEIA_GROQ_ENABLED=0`, `GROQ_API_KEY` vacío) para que el aviso exista de verdad y no se confunda con el de "IA configurada"

## Veredicto

**Apto con salvedades.**

La capa 2 hace lo que dice en las superficies principales (fondo `#101112`, tarjetas `#1a1c1d`/`#1d2320`, borde `#303431`, radio 16 px, relleno 26–30 px, titular `clamp(36px,3.4vw,50px)` con `-.05em`, cuerpo 15 px, botones de 9 px), no introduce fallos de contraste ni desbordes, conserva todos los avisos y no toca impresión ni informe. No es un "apto" limpio porque **la superficie nueva no llega a dos componentes prominentes** —las tarjetas de producto de la biblioteca y el panel contextual— y porque la escala tipográfica interna se separa de la maqueta en varios títulos. Detalle en *Hallazgos*.

## Tabla de comprobaciones

| # | Comprobación | Resultado | Evidencia |
|---|---|---|---|
| 1 | Hash idéntico de las dos copias y cambio solo CSS | **Pasa** — `492c22cf…` en disco, copia servida y HTTP; commit de 65+65 líneas CSS y 1 JSON, 0 borrados | §1 |
| 2 | La hoja no afecta a impresión ni al informe | **Pasa** — informe de 6.648 B sin `#101112` ni capa nueva; PDF A4 de 3 páginas con esquinas `(255,255,255)`; en `@media print` el relleno vuelve a 22 px | §2 |
| 3 | Contraste AA en 8 rutas × 2 anchos, con sonda validada | **Pasa** — 3.519 nodos medidos, 0 fallos; sonda 0→1→0 en 1440 y 390 | §3 |
| 4 | Desbordamiento horizontal en 8 rutas × 3 anchos | **Pasa** — 24/24 a cero; también con comparación y escenarios poblados | §4 |
| 5 | Avisos de producto visibles y legibles | **Pasa** — consentimiento, simulación, IA no configurada, procedencia y datos desconocidos, con textos exactos y ratios 8,38–15,78:1 | §5 |
| 6 | Foco visible por teclado y `prefers-reduced-motion` | **Pasa** — 92 paradas, 0 sin anillo; anillo 10,62–12,56:1; cero transiciones nuevas | §6 |
| 7 | Comparación numérica con la maqueta | **Pasa con salvedades** — coincide el núcleo (radio 16, superficies, `h1`, cuerpo, botones); no coinciden tarjeta de producto, panel contextual, escala de `h2`/`h3`, ancho y `h1` móvil | §7 |

## 1. Instantánea y alcance del cambio

```console
$ sha256sum prototipos/paideia-local/static/dark_theme.css api/_static/dark_theme.css
492c22cfe53884a8e26067184fbeb38e85b0929862cd80c5354e10a502bb6647 *prototipos/paideia-local/static/dark_theme.css
492c22cfe53884a8e26067184fbeb38e85b0929862cd80c5354e10a502bb6647 *api/_static/dark_theme.css

$ curl -s http://127.0.0.1:8771/static/dark_theme.css | sha256sum
492c22cfe53884a8e26067184fbeb38e85b0929862cd80c5354e10a502bb6647 *-

$ git show --stat --format="%H%n%s" 3b67737
3b677373bce5d67b16c2ed90eeb766a70c39b839
Lleva la jerarquia y las superficies de la maqueta a la app real

 api/_static/dark_theme.css                     | 65 ++++++++++++++++++++++++++
 docs/diseno-hasta-bloqueo/contraste-capa2.json |  1 +
 prototipos/paideia-local/static/dark_theme.css | 65 ++++++++++++++++++++++++++
 3 files changed, 131 insertions(+)
```

- Las tres copias (disco, copia servida y respuesta HTTP) coinciden en hash: el navegador midió exactamente el archivo revisado.
- El commit **solo añade CSS** (65 líneas por copia) y una línea de evidencia JSON. Cero borrados, cero HTML, cero JS, cero Python.
- Control de qué aporta el archivo: con `dark_theme.css` desactivada, la app vuelve a su base clara (`body` `#f7f5ef`, tarjetas blancas, radio 12 px, relleno 22 px, `h1` 40,8 px, cuerpo 16 px). Es decir, el tema oscuro —recoloreado de la capa 1 y jerarquía de la capa 2— lo produce íntegramente este archivo; no había una capa previa que ya lo diera.

## 2. Impresión e informe descargado

**Informe generado de verdad**, no simulado: en `#comparar` se compararon dos productos reales del catálogo (Cuenta Contigo · Renault Bank y Depósito Tú+), se sembró el escenario A con la tasa documentada del producto (2,61 %) desde «Explorar escenarios con esta tasa», se calculó A y B con el motor local (1.000 €, 5 años, 50 €/mes, inflación 2 %; B a 2 %) y se pulsó **Descargar informe (HTML)**. Se capturó el blob exacto que el ancla entrega al navegador (6.648 bytes).

```
sha256  1ec13ca132fe3d6b6fef9dcc64daa5a5ee391e2f2e4275b6e8919b85a2200921
```

Comprobación del CSS del informe descargado:

```console
$ for p in '#101112' '1a1c1d' '1d2320' '303431' 'clamp(' '3.4vw' 'paper-section' 'dark_theme'; do
    printf "%-14s %s\n" "$p" "$(grep -c -F "$p" informe-productos.html)"; done
#101112        0
1a1c1d         0
1d2320         0
303431         0
clamp(         0
3.4vw          0
paper-section  0
dark_theme     0

$ grep -oE "#[0-9a-fA-F]{3,6}" informe-productos.html | sort | uniq -c
      1 #111      2 #333      1 #777      1 #eee
```

El informe es autocontenido: **cero `<link>`**, una sola hoja embebida y cuatro colores, todos claros (`#111` texto, `#333` avisos, `#777` bordes, `#eee` cabeceras de tabla). No hereda nada de la app.

Impresión real a PDF con Chromium (`Page.printToPDF`, A4, `preferCSSPageSize`):

```console
$ pdfinfo informe-productos.pdf | grep -E "Pages|Page size"
Pages:           3
Page size:       594.96 x 841.92 pts (A4)

$ # esquinas y luminancia media por página (pdftoppm 60 dpi + Pillow)
inf-1.png esquinas [(255,255,255) ×5]  lum media 241.4  min 160.0
inf-2.png esquinas [(255,255,255) ×5]  lum media 242.4  min 181.0
inf-3.png esquinas [(255,255,255) ×5]  lum media 247.9  min 183.0
```

Fondo blanco puro en las cuatro esquinas de las tres páginas, luminancia media 241–248 y texto oscuro: **el fondo es claro**. La procedencia se conserva en el papel (`Fuente de la tasa: Cuenta Contigo · Renault Bank — Información precontractual global · https://doc.renaultbank.es/… · consultada 2026-10-26 · clase de fuente desconocida`).

Además, con `@media print` emulado sobre la app: `body` `rgb(255,255,255)`, panel `rgb(255,255,255)`, `.paper-section` con relleno **22 px** (no los 30 px de pantalla) y `h1` a 40,8 px. La capa 2 no existe en impresión.

**Límite preexistente, no imputable a la hoja:** imprimir una pantalla normal de la app sale en blanco. `comparison_report.css` contiene `body > :not(#comparison-report-print){display:none!important}` dentro de `@media print`, de modo que el único camino de impresión soportado es el botón del informe. Verificado que ocurre **igual con `dark_theme.css` desactivada** (1 página, 0 caracteres de texto en ambos casos).

## 3. Contraste WCAG AA (8 rutas × 2 anchos), con sonda validada

Sonda: `skills/software-development/visual-redesign-retrofit/scripts/contrast_audit.js`, ejecutada en página con `getComputedStyle` y composición alfa sobre el ancestro opaco. `#comparar` se auditó con dos productos y su tabla de metadatos; `#escenarios`, con A y B calculados. Ninguna de las dos en estado vacío.

| Ruta | 1440 (nodos / fallos) | 390 (nodos / fallos) |
|---|---:|---:|
| `#inicio` | 146 / 0 | 146 / 0 |
| `#perfil` | 95 / 0 | 95 / 0 |
| `#biblioteca` | 645 / 0 | 606 / 0 |
| `#comparar` (2 productos) | 178 / 0 | 178 / 0 |
| `#escenarios` (A y B calculados) | 387 / 0 | 393 / 0 |
| `#simulacion` | 98 / 0 | 98 / 0 |
| `#glosario` | 97 / 0 | 97 / 0 |
| `#privacidad` | 130 / 0 | 130 / 0 |
| **Total** | **1.776 / 0** | **1.743 / 0** |

Nota: a 1440 el `clientWidth` real es 1425 por la barra de desplazamiento; la auditoría registra 1425, no 1440.

**Validación de la sonda (sin esto el cero no vale).** Se inyectó un `<p>` con `color:#101112` sobre fondo `#101112` y se retiró:

| Ancho / ruta | Antes | Con la violación | Detectada | Después |
|---|---:|---:|---|---:|
| 1440 / `#inicio` (146 nodos) | 0 | 1 | `p` «SONDA PLANTADA ILEGIBLE», ratio **1,00**, exigido 4,5 | 0 |
| 390 / `#privacidad` (130 nodos) | 0 | 1 | mismo nodo, ratio **1,00** | 0 |

Lectura: la sonda mide de verdad, encuentra lo que se le planta y vuelve a cero al retirarlo, en los dos anchos.

## 4. Desbordamiento horizontal (8 rutas × 3 anchos)

`document.documentElement.scrollWidth − clientWidth`, debe ser 0.

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

24/24 combinaciones a cero. Repetido con contenido denso: `#comparar` con dos columnas de producto da 0 a 1440/390/320 y `#escenarios` con las tres tablas calculadas da 0 a los tres anchos. Ninguna tabla ancha ni URL larga empuja la página.

## 5. Avisos de producto: siguen visibles y legibles

Todos se comprobaron renderizados (rect > 0, `visibility:visible`, opacidad 1) a 1440 y a 390, y con ratio calculado sobre su fondo real. Cifras medidas, no estimadas.

**5.1 Consentimiento del perfil** (`#privacidad`)

- Casilla: «Quiero permitir el almacenamiento local del mapa revisado en este dispositivo.» — 15 px, **15,78:1**.
- Texto de alcance: «Al marcar la casilla y pulsar Guardar se crea una copia local, incluidos los estados aún no preguntados. […] El almacenamiento local es independiente del procesamiento local y no autoriza ningún envío remoto. Revisa el mapa primero para activar el guardado opt-in.» — 13,44 px, **9,01:1**.
- Estado: «Ahora: solo memoria de esta pestaña.» y «Todavía no se ha guardado nada en esta visita.»

**5.2 Simulación hipotética**

- `#escenarios`, entradilla: «Los números describen una hipótesis tuya. El cálculo no usa tasas de producto y no es una predicción.» — 16 px, **9,96:1**.
- `#escenarios`, banda: «Hipótesis del usuario · no predicción · bruto, sin fiscalidad ni costes de producto. El método compuesto convierte la tasa anual efectiva a mensual; en simple la tasa anual se divide entre 12. Aportaciones al final de cada mes.» — 14,72 px, **9,93:1**.
- Junto al resultado: «Hipótesis introducida por ti · no es predicción · bruto, sin fiscalidad ni costes de producto.»
- `#simulacion`: «ENSAYO FICTICIO · No se enviará nada ni se moverá dinero. No introduzcas identificadores, credenciales, cuenta, tarjeta ni datos de pago.» — 14,72 px, **9,93:1**.

**5.3 IA no configurada** (estado forzado sin clave)

- Cabecera: «Prototipo local · IA no conectada» — 13,12 px, **13,59:1**.
- Panel lateral: «Chat IA no conectado. Los cálculos, la biblioteca y el glosario funcionan igual.» — 13,12 px, **8,38:1**.
- `#privacidad`: «Sin conexión a IA. Confirmar aquí no envía datos ni activa ningún chat. /api/context-preview se reserva para fixtures sintéticas; esta interfaz no lo llama.»

**5.4 Procedencia de fuentes** (`#biblioteca`, `#comparar`)

- «Fuente primaria: https://doc.renaultbank.es/documentacion-legal/informacion-precontractual-global-publico-RenaultBank.pdf · Se abre solo si eliges el enlace.» — 13,76 px, **15,78:1**.
- «Fuente de las condiciones: https://www.openbank.es/deposito-a-plazo-fijo · consultada el 2026-11-03».

**5.5 Etiquetas de dato desconocido**

- «Campos desconocidos:» seguido de la lista visible: *divisa de la cuenta explícita · saldo máximo remunerado · frecuencia pactada de liquidación · tipo aplicable después de la promoción · derechos de copia/cache/display* — 13,6 px, **15,78:1**.
- «No indicado en el metadato» (ISIN), «Desconocida en los metadatos disponibles.», «Sin tasa documentada para este producto.», «No disponible en la respuesta de comparación.», «No disponibles; no se infieren.»
- Insignias: «Condiciones pendientes» — 12,32 px, **9,93:1**; «Identidad verificada» — **11,08:1**.

Ninguno de los avisos citados quedó oculto ni con `aria-hidden`: todos conservaron rectángulo propio a 1440 y a 390.

## 6. Foco visible y movimiento

- Recorrido con `Tab` real (CDP, no `.focus()`) en **las 8 rutas a 1440 y a 390**, 6 pulsaciones por ruta y ancho: **92 paradas efectivas, 0 sin anillo**, todas con `outline: solid 3px rgb(169,216,255)` y `outline-offset: 2px`. (En `#simulacion` y `#glosario` una pulsación cayó sobre el documento y no cuenta como parada.) Recorrido largo adicional en `#inicio`, `#biblioteca` y `#privacidad` (27 / 45 / 28 paradas; en `#biblioteca` se cortó en 45, tope de la prueba con 20 fichas y dos enlaces cada una): tampoco apareció ninguna parada sin anillo.
- Contraste del anillo (componente no textual, mínimo 3:1): **12,56:1** sobre `#101112`, **11,36:1** sobre `#1a1c1d`, **10,62:1** sobre `#1d2320`.
- Enlace «Saltar al contenido» enfocado: texto `#15251c` sobre `#b7e6d5` = **11,64:1**, con el mismo anillo.
- `prefers-reduced-motion: reduce` emulado: `transition-duration` y `animation-duration` máximos **0,01 ms** (regla global preexistente en `styles.css`), `scroll-behavior: auto`. `dark_theme.css` no declara ni una `transition`, `animation` ni `@keyframes`: la capa 2 no añade movimiento.
- Observación: al cargar cada ruta el `h1` aparece con anillo de foco (la app enfoca el titular al cambiar de ruta). **Es previo**: con la hoja desactivada el anillo sigue ahí, en azul `#3157B7`. La capa 2 solo lo repinta al `#a9d8ff` de la maqueta.

## 7. Comparación numérica con la maqueta

Medidas computadas en el navegador a 1440, no leídas del CSS: `docs/diseno-ideas/maquetas/paideia-oscura-recorrido.html` frente a la app.

| Elemento | Maqueta | App (capa 2) | ¿Coincide? |
|---|---|---|---|
| Fondo / tinta | `#101112` / `#f5f6f4` | `#101112` / `#f5f6f4` | Sí |
| Cuerpo | 15 px / 1.5 | 15 px / 1.5 | Sí |
| `h1` | 48,96 px · `-.05em` · 650 · 1.08 | 48,96 px · `-.05em` · 650 · 1.08 | Sí (idéntico) |
| Entradilla | 16 px, `#b6baba` | 16 px, `#b6beba` | Sí (Δ4 en verde) |
| Superficie panel | `#1a1c1d` | `#1a1c1d` | Sí |
| Superficie destacada | `#1d2320` | `#1d2320` | Sí |
| Borde de tarjeta | `#303431` | `#303431` | Sí |
| Radio de tarjeta | 16 px | 16 px en `.paper-section`, `.data-panel`, `.question-panel`, `.home-actions section`, `.route-strip` | Sí |
| Relleno | 30 / 27 / 23 / 22 px según bloque | 30 px secciones, 26 px chat y bienvenida, 20/18 px móvil | Parcial |
| Botón | 13 px · 600 · radio 9 · `0 15px` · `#d2eee0`/`#173025` · alto 44 | 13 px · 600 · radio 9 · `0 15px` · `#d2eee0`/`#173025` · alto 46 | Sí |
| *Eyebrow* | 11 px · `.12em` · 650 · `#b7e6d5` | 11 px · `.12em` · 650 · `#b7e6d5` | Sí |
| Foco | `#a9d8ff` | `#a9d8ff` | Sí |
| Línea interna | `#353a38` | `#343a37` | Casi (Δ1) |
| **Tarjeta de producto** | **16 px · 23 px · borde `#303431`** | **12 px · 18 px · borde `#343a37`** | **No** |
| **Panel contextual** | **16 px · 22 px · `#1a1c1d` · borde `#303431`** | **12 px · 18 px · `#1b2420` · borde `#3c5145`** | **No** |
| `h2` de sección | 17 px · 650 · `-.02em` | 19 px · 700 · `-.035em` | No |
| `h2` de bienvenida | 27 px · 620 | 23,2 px · 700 | No |
| `h3` de producto | 21 px · 620 · `-.035em` | 17,28 px · 700 | No |
| `h2` del panel contextual | 15 px | 19 px | No |
| Ancho de contenido | 1.344 px a 1440 | 1.296 px a 1440 | No (−48 px) |
| `h1` móvil | 38 px (≤760) | 32 px (≤480) | No |

Lo que **sí** trae la capa 2 y antes no estaba: titular a escala de portada, cuerpo de 15 px, tarjetas con superficie y borde, radio 16 px, separación de 16 px entre secciones, botones de 9 px. Eso es el núcleo de la maqueta y está bien ejecutado.

## Hallazgos y salvedades

1. **Las tarjetas de producto no reciben la superficie nueva.** En `#biblioteca` y `#comparar`, `.product-card` sigue a 12 px de radio, 18 px de relleno y borde `#343a37`; la maqueta las dibuja como `.panel.product` (16 px, 23 px, `#303431`). Es el componente más repetido de la ruta más densa: la página se ve con dos lenguajes de tarjeta a la vez.
2. **El panel contextual tampoco.** `.context-panel` mantiene 12 px / 18 px / `#1b2420` / borde `#3c5145`, frente a 16 px / 22 px / `#1a1c1d` / `#303431`. La capa 1 solo recoloreó su borde; la capa 2 no lo incluyó en la lista de superficies.
3. **Escala tipográfica interna distinta de la maqueta:** 19 px/700 donde la maqueta pone 17 px/650, 23,2 px/700 donde pone 27 px/620, 17,28 px/700 donde pone 21 px/620, y 19 px en el panel contextual donde pone 15 px. La jerarquía es coherente consigo misma, pero no es la aprobada.
4. **Móvil:** el `h1` cae a 32 px por debajo de 480 px; la maqueta baja a 38 px y su punto de ruptura es 760 px. En 390 la portada pierde bastante presencia frente al diseño aprobado.
5. **Ancho:** el contenido útil a 1440 es 1.296 px (max-width 1392 con 48 px de relleno) frente a 1.344 px de la maqueta. Las tarjetas quedan 48 px más estrechas.
6. **Cobertura de la evidencia del autor:** `contraste-capa2.json` registra `#comparar` con **67 nodos**, que es el estado vacío. Con dos productos comparados son **178** y el resultado sigue en 0 fallos, pero la cifra publicada medía menos pantalla de la que sugiere. No invalida el cero; sí lo hace menos representativo.
7. **Ruido previo, no de esta capa:** el anillo de foco sobre el `h1` al cargar y la impresión en blanco de las pantallas de la app. Ambos reproducen con la hoja desactivada.

## Límites de esta revisión

- **Emulación, no dispositivo real.** Chromium headless con métricas de dispositivo; no he probado iOS Safari, Firefox ni un teléfono físico. Los 320 px son solo de desbordamiento, no de contraste.
- **Contraste calculado no es auditoría de lector de pantalla.** No hay recorrido con NVDA/VoiceOver, ni axe/WAVE, ni prueba con zoom 200 %/400 %, ni modo de alto contraste de Windows. La sonda compone alfa y mide texto con nodos propios; no evalúa texto en pseudoelementos, en `canvas` ni controles deshabilitados.
- **El PDF es de Chromium/Skia**, no de una impresora física ni de otro motor de impresión.
- **La descarga se capturó del blob**, no del diálogo de guardado (Chrome headless no escribe el archivo). Los 6.648 bytes son exactamente el documento que el ancla entrega; `sha256 1ec13ca1…`.
- **No he revisado** el resto de la app (backend, contratos, tests funcionales): esta revisión es visual y de accesibilidad de la capa 2 sobre la instantánea indicada.
