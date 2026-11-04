# Maquetas visuales · Paideia

**Estado:** exploración visual para una elección futura. No es implementación, no sustituye la app y no se ha integrado ni publicado nada.

Cuatro maquetas autónomas de **Comparar** y un recorrido visual de **Inicio, Biblioteca, Pai y Escenarios**, con datos y fuentes ficticios. No contienen ofertas ni recomendaciones. Las tasas y cantidades del recorrido son exclusivamente supuestos ficticios de escenario. Cada archivo es HTML autocontenido, con `connect-src 'none'` y sin recursos externos.

## Qué muestra cada archivo

| Archivo | Dirección | Composición y foco |
|---|---|---|
| `a-cuaderno-comparar.html` | **A · Cuaderno de estudio** | Pliego editorial a tres columnas: índice, tabla de criterios y nota al margen de Pai. Fuentes como notas al pie, registro numerado, sellos textuales y mucha lectura. En móvil, la tabla se convierte en bloques por criterio. |
| `b-fintech-comparar.html` | **B · Fintech clara** | Mesa de comparación con columnas tipo tarjeta, cobertura `3/8 · 4/8 · 2/8`, diferencias marcadas y panel lateral de Pai que desplaza el contenido en escritorio. En móvil, fichas apiladas y barra inferior. |
| `c-atlas-comparar.html` | **C · Atlas de datos** | Matriz densa de tres paños: filtros, matriz e inspector de procedencia. Cada celda abre su fuente, estado, vigencia y exclusión. En móvil, filtros plegados, matriz con desplazamiento interno etiquetado y hoja inferior de procedencia. |
| `b-oscura-concepto.html` | **B oscura · Comparación contemporánea** | Evolución de B: tarjetas en tonos grafito, acento menta contenido y panel lateral de Pai; en móvil las tarjetas se apilan y Pai aparece después. Inspirada en claridad y jerarquía visual, sin copiar identidad de Apple. |
| `paideia-oscura-recorrido.html` | **Recorrido oscuro · cuatro vistas** | Extiende B oscura a Inicio, Biblioteca, Pai y Escenarios; enlaza la maqueta separada de Comparar, incluye navegación, filtros de ejemplo y campos editables, sin IA ni cálculo conectado. |

Las tres primeras comparten un caso ficticio con tres fichas y ocho criterios. La B oscura presenta una selección más breve de criterios. Ninguna muestra una TAE ni un importe de producto: los huecos se representan como `No consta`, `Sin dato`, `En conflicto` o `Solo identidad`.

## Capturas

Guardadas en `capturas/`:

- `a-desktop-1440.png` · `a-mobile-390.png`
- `b-desktop-1440.png` · `b-pai-1440.png` · `b-mobile-390.png`
- `c-desktop-1440.png` · `c-mobile-390.png` · `c-procedencia-390.png`
- `b-oscura-desktop.png` · `b-oscura-movil.png` (capturas del viewport, no de página completa).
- `recorrido-{inicio,biblioteca,pai,escenarios}-{desktop,movil}.png` (capturas del viewport).

Las capturas de escritorio usan 1440×900 y las móviles 390×844 (página completa). `b-pai-1440.png` y `c-procedencia-390.png` muestran estados abiertos de Pai y del inspector.

## Verificación realizada

- Abiertas con Chromium local mediante `file://`; sin servidor propio ni peticiones de red. `performance.getEntriesByType('resource')` devolvió una lista vacía en las tres.
- Comprobado `scrollWidth == clientWidth` en 1440 px, 390 px y 320 px. En C móvil, la matriz usa desplazamiento horizontal **interno y etiquetado**; la página no desborda.
- Probados: botón «Solo diferencias» (8 → 5 criterios visibles), apertura y cierre con `Esc` de fichas nativas, retorno de foco al disparador, panel/hoja de Pai en B, consulta local de Pai en A y C, filtros y búsqueda de C, inspector de celdas y salto entre columnas en C móvil.
- Enlace de salto, foco visible, etiquetas y nombres accesibles básicos, `aria-live` para cambios de estado, diálogos nativos y objetivos táctiles principales de 44 px.
- No se modificó ningún archivo fuera de `docs/diseno-ideas/maquetas/`. Sin cambios en API, backend, estáticos de la app, tests, git ni despliegue.
- En la nueva B oscura se comprobó por separado Chromium local en escritorio y emulación 390/320 px, sin desbordamiento horizontal; los botones de diferencias y de ayuda de Pai alternan sus estados. No se verificaron las demás interacciones ni se auditó la accesibilidad completa.
- En el recorrido oscuro se verificaron las cuatro vistas a 1440, 390 y 320 px sin desbordamiento de página; se revisaron filtros, búsqueda con y sin tildes, navegación, mensajes de maqueta y edición de campos. La navegación mueve el foco al título de la vista y Comparar enlaza a la maqueta separada con un enlace de regreso. No hay conexión a la app ni prueba de lector de pantalla o dispositivo físico.

## Limitaciones

- El recorrido nuevo cubre **Inicio, Biblioteca, Pai y Escenarios**; la pantalla **Comparar** se conserva en la maqueta B oscura separada. No se han diseñado aquí todas las rutas de Paideia.
- Todos los productos, entidades, fuentes, fechas y estados son ficticios y sirven para probar jerarquía y trazabilidad. No acreditan condiciones reales ni ofertas publicables.
- Pai no está conectado a ninguna IA ni a ninguna red. Sus respuestas son texto local de maqueta y no varían según la pregunta.
- No hay integración con la API, el catálogo real ni el motor de cálculo; no se ha probado con datos de producción.
- Verificación limitada a Chromium de escritorio y emulación móvil. No hay certificación con lector de pantalla, dispositivo físico, Safari/Firefox ni prueba de impresión real.
- C móvil conserva la matriz completa con scroll interno; es una decisión de diseño, no una tabla convertida en fichas. A y B usan patrones distintos a propósito para comparar sensibilidades.
- Las capturas y este README son material de exploración; no son una propuesta aprobada ni un compromiso de implementación.

## Cómo abrir

Abrir cualquiera de los archivos `.html` con doble clic o arrastrarlo al navegador. Para navegar entre el recorrido y Comparar, conservar `paideia-oscura-recorrido.html` y `b-oscura-concepto.html` en la misma carpeta. No requiere instalación, servidor ni conexión.
