# Maquetas de comparación · Paideia

**Estado:** exploración visual para una elección futura. No es implementación, no sustituye la app y no se ha integrado ni publicado nada.

Tres maquetas autónomas de la pantalla **Comparar**, con datos, entidades, fuentes e importes ficticios. No contienen tasas, ofertas ni recomendaciones. Cada archivo es un HTML autocontenido: CSS y JavaScript inline, fuentes del sistema, SVG inline, CSP con `connect-src 'none'` y sin recursos externos.

## Qué muestra cada archivo

| Archivo | Dirección | Composición y foco |
|---|---|---|
| `a-cuaderno-comparar.html` | **A · Cuaderno de estudio** | Pliego editorial a tres columnas: índice, tabla de criterios y nota al margen de Pai. Fuentes como notas al pie, registro numerado, sellos textuales y mucha lectura. En móvil, la tabla se convierte en bloques por criterio. |
| `b-fintech-comparar.html` | **B · Fintech clara** | Mesa de comparación con columnas tipo tarjeta, cobertura `3/8 · 4/8 · 2/8`, diferencias marcadas y panel lateral de Pai que desplaza el contenido en escritorio. En móvil, fichas apiladas y barra inferior. |
| `c-atlas-comparar.html` | **C · Atlas de datos** | Matriz densa de tres paños: filtros, matriz e inspector de procedencia. Cada celda abre su fuente, estado, vigencia y exclusión. En móvil, filtros plegados, matriz con desplazamiento interno etiquetado y hoja inferior de procedencia. |

Las tres comparten el mismo caso ficticio: tres fichas de depósito a plazo (D-01 Alfa, D-02 Beta, D-03 Gamma), ocho criterios, coberturas 3/8, 4/8 y 2/8, una ficha no vigente y una solo con identidad. Ninguna muestra una TAE ni un importe de producto: los huecos se representan como `No consta`, `Sin dato`, `En conflicto` o `Solo identidad`.

## Capturas

Guardadas en `capturas/`:

- `a-desktop-1440.png` · `a-mobile-390.png`
- `b-desktop-1440.png` · `b-pai-1440.png` · `b-mobile-390.png`
- `c-desktop-1440.png` · `c-mobile-390.png` · `c-procedencia-390.png`

Las capturas de escritorio usan 1440×900 y las móviles 390×844 (página completa). `b-pai-1440.png` y `c-procedencia-390.png` muestran estados abiertos de Pai y del inspector.

## Verificación realizada

- Abiertas con Chromium local mediante `file://`; sin servidor propio ni peticiones de red. `performance.getEntriesByType('resource')` devolvió una lista vacía en las tres.
- Comprobado `scrollWidth == clientWidth` en 1440 px, 390 px y 320 px. En C móvil, la matriz usa desplazamiento horizontal **interno y etiquetado**; la página no desborda.
- Probados: botón «Solo diferencias» (8 → 5 criterios visibles), apertura y cierre con `Esc` de fichas nativas, retorno de foco al disparador, panel/hoja de Pai en B, consulta local de Pai en A y C, filtros y búsqueda de C, inspector de celdas y salto entre columnas en C móvil.
- Enlace de salto, foco visible, etiquetas y nombres accesibles básicos, `aria-live` para cambios de estado, diálogos nativos y objetivos táctiles principales de 44 px.
- No se modificó ningún archivo fuera de `docs/diseno-ideas/maquetas/`. Sin cambios en API, backend, estáticos de la app, tests, git ni despliegue.

## Limitaciones

- Solo está dibujada la pantalla **Comparar**. Las demás rutas de Paideia no forman parte de estas maquetas.
- Todos los productos, entidades, fuentes, fechas y estados son ficticios y sirven para probar jerarquía y trazabilidad. No acreditan condiciones reales ni ofertas publicables.
- Pai no está conectado a ninguna IA ni a ninguna red. Sus respuestas son texto local de maqueta y no varían según la pregunta.
- No hay integración con la API, el catálogo real ni el motor de cálculo; no se ha probado con datos de producción.
- Verificación limitada a Chromium de escritorio y emulación móvil. No hay certificación con lector de pantalla, dispositivo físico, Safari/Firefox ni prueba de impresión real.
- C móvil conserva la matriz completa con scroll interno; es una decisión de diseño, no una tabla convertida en fichas. A y B usan patrones distintos a propósito para comparar sensibilidades.
- Las capturas y este README son material de exploración; no son una propuesta aprobada ni un compromiso de implementación.

## Cómo abrir

Abrir cualquiera de los tres `.html` con doble clic o arrastrarlo al navegador. No requiere instalación, servidor ni conexión.
