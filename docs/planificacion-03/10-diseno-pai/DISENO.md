---
version: alpha
name: "Paideia — Cuaderno de ruta (propuesta)"
description: "Dirección visual editorial y cálida para explorar decisiones financieras con datos, supuestos y límites visibles. Propuesta sin aprobación de marca."
status: propuesta-no-aprobada
colors:
  primary: "#3157B7"
  secondary: "#4F5E62"
  ink: "#18272D"
  tertiary: "#B74734"
  neutral: "#F7F5EF"
typography:
  h1:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 2rem
    fontWeight: 700
    lineHeight: 1.2
  h2:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 1.5rem
    fontWeight: 700
    lineHeight: 1.25
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: 8px
  md: 12px
  lg: 16px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    height: 48px
    padding: 16px
  button-secondary:
    backgroundColor: "{colors.tertiary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    height: 48px
    padding: 16px
  card:
    backgroundColor: "#FFFFFF"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: 24px
---

# Paideia — dirección visual propuesta

> **Propuesta de trabajo, no branding aprobado.** Define una dirección y piezas originales para revisión; no implementa una aplicación, no acredita datos financieros ni valida asesoramiento o cumplimiento legal.

## Overview

### Dirección: «Cuaderno de ruta financiera»

Una mesa editorial para aprender comparando: tinta sobre papel cálido, estructura de cuaderno y pequeñas marcas de recorrido que enlazan **objetivo → comparación → escenario → ensayo**. La interfaz transmite calma y precisión; no parece un banco, un colegio infantil ni un asesor que decide por la persona. El sistema usa jerarquía tipográfica, líneas y etiquetas descriptivas, no gradientes, brillo, rankings de «ganadores» ni urgencia comercial.

**Idea distintiva:** la ruta visual (hitos lineales, numerados y etiquetados) y Pai, un triángulo original que señala una explicación puntual. Pai acompaña; no habla por el usuario, no recomienda productos y no aparece en cada tarjeta.

### Qué está definido y qué no

- **Recogido como requisito, no como implementación:** nombre Paideia, español, web responsive (no app nativa), personas adultas con poca experiencia financiera, perfil resumido y editable, cinco familias prioritarias de productos y contratación solo simulada. Referencia: `docs/REQUISITOS.md`.
- **Propuesto aquí:** concepto visual, tokens, composición, jerarquía de pantallas, microcopy y tres SVG originales de Pai.
- **Pendiente de aprobación o validación:** dirección visual/branding, fuentes y fechas de datos, reglas de caducidad, proveedor de IA, lenguaje financiero/legal y cualquier salida que parezca recomendación. No presentar esta propuesta como marca aprobada ni como producto accesible ya auditado.

## Colors

La paleta base conserva el punto de partida de la investigación UX, con roles ampliados para estados. El azul es una acción serena; la terracota destaca decisiones o alertas sin usarla como sinónimo de rentabilidad; salvia es superficie, no señal única.

| Rol | Token | Uso |
|---|---|---|
| Lienzo | `#F7F5EF` | Fondo general «papel». |
| Superficie | `#FFFFFF` | Fichas, paneles y campos. |
| Tinta | `#18272D` | Texto principal y títulos. |
| Texto secundario | `#4F5E62` | Ayuda, fechas y metadatos legibles. |
| Acción primaria | `#3157B7` | Acción principal, enlaces subrayados y foco. |
| Terracota | `#B74734` | Acento, CTA secundario o escenario desfavorable; siempre con etiqueta. |
| Salvia | `#DDE9E2` | Fondo de nota/pausa; no significa por sí sola «seguro». |
| Borde de control | `#737D7D` | Límites de campos y controles sobre papel o blanco. |
| Estados | Verde `#22614F`; ámbar `#7F4400`; rojo `#A1362F`; azul `#3157B7` | Acompañar con texto e icono; nunca codificar significado solo por color. |

**Contraste calculado con Python** (luminancia relativa sRGB WCAG): tinta/papel **14,09:1**; texto secundario/papel **6,19:1**; blanco/botón azul **6,61:1**; blanco/botón terracota **5,30:1**; azul/superficie informativa **5,62:1**; verde/fondo de éxito **6,11:1**; ámbar/fondo de aviso **6,44:1**; rojo/fondo de error **5,55:1**; borde/blanco **4,24:1** y borde/papel **3,88:1**. El foco azul sobre blanco/papel da **6,61:1 / 6,06:1**. Todas las parejas de texto listadas superan 4,5:1; bordes y foco superan 3:1 en esas superficies. Verificación de paleta, no auditoría de una interfaz renderizada; probar de nuevo cualquier combinación nueva, texto superpuesto, transparencia, hover y estado deshabilitado.

## Typography

- **Sin descarga de fuentes:** `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`. Mantiene legibilidad y evita depender de assets externos. No usar tipografía monoespaciada en bloques largos.
- **Escala:** display 40/48 px; H1 32/38; H2 24/30; H3 20/26; cuerpo 16/24; secundario 14/20; etiqueta 12/16. En móvil, el H1 puede bajar a 28/34 px, no el cuerpo base.
- **Peso:** 400 texto, 500 controles, 600/H3, 700 titulares. Evitar párrafos enteros en versales.
- **Cifras:** `font-variant-numeric: tabular-nums`; alinear importes y porcentajes. Formato es-ES: `1.234,56 €`, fecha explícita y periodo al lado de cada tasa. Nunca presentar una cifra de ejemplo como cotización actual.

## Layout

### Composición desktop (desde 1.200 px)

- Marco de navegación lateral de **232 px**; cabecera superior de **64–72 px** con título de vista y aviso persistente de demo.
- Área de contenido centrada, máximo **1.168 px**, margen interior de **32–40 px**. En pantallas de lectura: columna principal de **min(840 px, disponible)** más panel contextual de **272–280 px**; el panel contextual desaparece si estrecha la lectura.
- Catálogo y comparación usan una retícula de 12 columnas: ficha de producto con ancho y campos alineados. Comparar 2–3 productos como máximo; el nombre de cada fila permanece visible. No convertir el rendimiento en único criterio de orden.
- Navegación fija solo en escritorio amplio. A 768–1.199 px pasa a menú superior/drawer con etiquetas; no dejar iconos sin nombre.

### Composición móvil (hasta 767 px)

- Una columna; márgenes de **16 px** (24 px en tablet), cabecera compacta con marca Pai, nombre de pantalla y acceso al menú. Sin scroll horizontal.
- Navegación inferior **en el flujo, no superpuesta**: Inicio, Chat, Explorar y Perfil, cada destino con icono y texto. Comparador y Escenarios se alcanzan desde fichas/Chat; el ensayo es un recorrido contextual. Así un teclado virtual o el foco no queda tapado por una barra fija.
- Comparación se transforma en bloques por producto con el mismo orden de atributos y etiquetas visibles; no esconder campos críticos en una tabla que obliga a deslizar lateralmente. El gráfico se apila sobre su tabla de valores.
- Inputs y botones principales de al menos **44 px** de alto, con separación suficiente. El compositor del chat permanece en el flujo y se desplaza a la vista al recibir foco.

### Ritmo y retícula

Base de **4 px**: 4, 8, 12, 16, 24, 32, 40, 48 y 64 px. Gaps de 24 px entre grupos y 8–12 px dentro de controles relacionados. Radios discretos: 8 px en elementos pequeños, 12 px en tarjetas, 16 px solo en paneles principales. Bordes de 1 px; evitar sombras flotantes. Reservar espacio para etiquetas de fuente, vigencia y supuestos.

## Elevation & Depth

Profundidad por capas de papel (lienzo cálido → superficie blanca → panel contextual salvia), bordes y espacio, no por sombras difusas. Tarjetas con un borde visible; panel destacado solo para el siguiente paso o una explicación. Evitar apilar tarjetas dentro de tarjetas. Separadores y líneas de ruta no deben sustituir encabezados ni etiquetas.

## Shapes

- Geometría base: rectángulos de radio moderado, marcas lineales de itinerario y un triángulo de Pai. Sin esquinas excesivamente redondas, neón ni patrones infantiles.
- Pai es un dibujo propio en tres SVG estáticos: neutro, pensando y alerta. Silueta triangular común, pliegue/acento superior y expresión breve. No lleva animación, tipografía remota ni dependencia externa. SVG con `title`/`desc`; si se coloca junto a su nombre, tratar el dibujo como decorativo para que el lector de pantalla no repita el contenido.
- Gráficos: curvas de escenarios con etiqueta y patrón distintos, además de color; ejes, unidades, resumen y tabla equivalente. El color no basta para distinguir escenarios.

## Components

### Componentes comunes

- **Aviso persistente:** `PROYECTO EDUCATIVO · Productos con fuente y fecha. Los escenarios y el ensayo de contratación son simulados; no se mueve dinero.` Debe aparecer en cabecera y en el paso final del ensayo; la paleta/dataset debe dejar inequívoco qué es ficticio.
- **Acción principal:** una por vista, botón lleno azul, mínimo 48 px en desktop y 44 px en móvil. Acción secundaria como enlace/borde; no dos botones igualmente dominantes.
- **Perfil:** título `Tu mapa para explorar`; preguntas de una en una, progreso discreto, botón `No lo sé`, `Omitir`, y `¿Por qué lo preguntamos?`. Resumen modificable antes de continuar; no llamar «perfil inversor» ni hacer pasar preguntas por test de idoneidad.
- **Datos de producto:** familia, liquidez, plazo, costes, posibilidad de pérdida/garantía, fuente y fecha del dato. Cada dato debe poder distinguirse de un supuesto; mostrar origen en contexto, no solo en el pie global.
- **Ayuda/glosario:** panel contextual `¿Qué significa?`, con una definición breve y opción de volver sin perder lo escrito. No abrir un modal repetitivo.

### Seis pantallas — orden de lectura y composición

1. **Inicio / objetivo y mapa editable.** Primero: pregunta `¿Qué te gustaría entender o explorar?`; luego opciones y `No lo sé`/`Omitir`; finalmente progreso y privacidad. Pai pequeño, no protagonista. Resumen de objetivo, horizonte y liquidez editable antes de ir al chat o explorar sin perfil.
2. **Chat.** Primero: respuesta concreta y límite (`qué se sabe / qué falta`); segundo: supuesto y fuente/fecha cuando se cite un dato; tercero: una siguiente acción (`Ver en catálogo`, `Cambiar un supuesto`). Mensajes del usuario y Paideia diferenciados por etiqueta, no solo color. La IA explica; cálculos financieros deterministas y supuestos quedan fuera de la autoridad del texto generativo. Sin respuesta de producto por defecto.
3. **Catálogo.** Primero: búsqueda/filtros de las familias acordadas (cuentas remuneradas, depósitos, letras/deuda pública, fondos, ETF); segundo: ficha resumida del producto real con acceso a detalle; tercero: fecha/fuente y estado de datos. Filtros removibles y contadores legibles. No mostrar cobertura o actualidad no verificada.
4. **Comparador.** Primero: título de cada producto seleccionado y aviso de simulación/datos; después, filas en orden fijo: disponibilidad/liquidez, plazo, costes, condiciones/garantía y posible pérdida; por último, rendimiento con periodo/supuesto. CTA `Explorar escenarios`; nunca «mejor para ti» ni ranking que sugiera recomendación. Máximo tres fichas.
5. **Escenarios.** Primero: título `Prueba otros supuestos` y aviso `Resultados hipotéticos, no predicciones`; después, controles para importe inicial, aportación periódica y plazo; luego gráfico etiquetado bajo/central/alto con valores, aportado acumulado, unidad y tabla. Pai explica una diferencia concreta. El método/supuesto visible; no ocultar pérdidas posibles.
6. **Ensayo de contratación ficticia.** Flujo de cinco pasos, alineado con `11-simulacion-pdf/`: selección de producto real documentado → revisión de condiciones → importe ficticio → comprensión de riesgos → cierre simulado. Los hechos del producto mantienen fuente/fecha; solo los inputs y la operación del ejercicio son ficticios. Mantener marca persistente `ENSAYO FICTICIO`. CTAs `Continuar el ensayo`, `Volver al comparador`, `Terminar`. No botones `Firmar`, `Invertir` o `Contratar`; no pedir DNI, credenciales, tarjeta, cuenta ni pago; no enlazar a entidad real. Final: `Has terminado el ensayo. No se ha enviado una solicitud, abierto una cuenta ni movido dinero.`

## Do's and Don'ts

**Hacer**

- Usar texto directo para separar dato, fecha, fuente, supuesto y ejemplo.
- Tratar liquidez, plazo, coste y posibilidad de pérdida con una jerarquía igual de visible que la rentabilidad.
- Preservar respuestas al recuperar un error; informar cuándo falta un dato relevante y qué limita.
- Mantener visible `Borrar mi perfil local` y no pedir identificadores innecesarios.

**Evitar**

- No decir `Paideia te recomienda`, `tu inversión ideal`, `rentabilidad garantizada` o `contrata ahora`.
- No inferir valores de perfil que la persona haya omitido ni rellenar huecos con IA.
- No llamar actual al dato por el hecho de mostrar una fecha; no mezclar un producto ficticio con datos reales.
- No depender de color, hover, gesto de arrastre, temporizador o animación para completar una tarea.
- No usar assets de marcas financieras, fuentes remotas o imágenes de terceros para construir esta dirección.

## Estados de interfaz y microcopy

| Estado | Presentación y texto sugerido | Acción/seguridad |
|---|---|---|
| Cargando | Esqueleto que conserva la estructura; `Cargando la información del producto…` | `aria-busy="true"`; no mostrar cifras de muestra con apariencia real. Anunciar una vez, no cada cambio del esqueleto. |
| Error | `No se pudo cargar esta información.` | Mantener selección/entrada; acciones `Intentar de nuevo` y `Volver al catálogo`; explicar si no hay conexión cuando se sepa. No simular éxito. |
| Sin datos | `No hay resultados con estos filtros.` | `Quitar filtros` y `Ver todas las familias`. Distinguir de un error y no rellenar con supuestos ocultos. |
| Dato obsoleto | `Último dato verificado: [fecha] · Fuente: [nombre]. Puede haber cambiado.` | Enseñarlo junto al dato. Excluirlo de comparaciones si su antigüedad puede inducir a error; no inventar el umbral de caducidad antes de definirlo. |
| IA agotada/no disponible | `Ahora no puedo responder con IA. No voy a inventar una respuesta.` | Conservar el mensaje; `Reintentar` y `Seguir en el catálogo`. Mantener cálculos deterministas accesibles y marcar que la explicación generativa no está disponible. No aparentar que un texto de reserva fue generado por IA. |
| Ensayo ficticio | Cinta visible `ENSAYO FICTICIO · No se enviará nada.` | Mostrar progreso 1/5, revisar y finalizar sin captura de datos personales. Confirmación final explícita de que no hubo operación ni solicitud real. |

## Accesibilidad, teclado y movimiento

- Objetivo de diseño: **WCAG 2.2 AA**, pendiente de auditoría real. Texto normal ≥4,5:1 y texto grande ≥3:1 (1.4.3); información visual de controles/estados y objetos gráficos esenciales ≥3:1 contra adyacentes (1.4.11). No certificar conformidad a partir del cálculo de una paleta.
- Etiquetas visibles asociadas a campos; placeholder nunca es la única etiqueta. Instrucciones y error en texto, enlazados al campo. Estados en vivo (`role="status"`/`aria-live="polite"`) solo para cambios relevantes, no anuncios repetidos; foco al inicio del error o al título tras navegación.
- Todo operable por teclado: orden de tabulación DOM, sin trampas, foco persistente visible, Escape cierra el panel y devuelve foco al activador. Los botones «Omitir»/«No lo sé» y borrar están disponibles sin ratón; usar controles nativos cuando sea posible. Ningún elemento enfocable queda tapado por navegación fija.
- Indicador de foco: contorno sólido de 3 px en azul `#3157B7` con separación de 2 px; respetar el contorno en todos los controles. Las acciones principales tienen mínimo 44 × 44 CSS px (objetivo de comodidad, más generoso que el mínimo AA de tamaño).
- Gráfico siempre acompañado de frase interpretativa y tabla con los mismos valores; anunciar el resumen, no cada actualización del control. Escenarios diferenciados por nombres, trazos y etiquetas. Pai lleva alternativa textual adecuada al contexto.
- Sin movimiento necesario para entender o completar el flujo. No animar Pai. Si se añaden transiciones, limitarlas a opacidad breve; con `prefers-reduced-motion: reduce`, quitar desplazamientos, zoom, parallax, animaciones de entrada y scroll suave. No comunicar estados solo mediante movimiento.

## Fuentes y evidencia

- **Requisitos locales:** [`docs/REQUISITOS.md`](../../REQUISITOS.md), especialmente §§15–41, 43–60 y 66–79: público, idioma, web responsive, familias de producto, privacidad, simulación ficticia y asuntos pendientes.
- **Base de dirección visual:** [`docs/investigacion/08-ux-recursos.md`](../../investigacion/08-ux-recursos.md), §§26–62: concepto «cuaderno de ruta financiera», paleta preliminar, Pai original y patrones de teclado/responsive. Esta especificación lo desarrolla; no reutiliza marcas ni activos de sus referencias comerciales.
- [W3C — WCAG 2.2, Contrast Minimum (1.4.3)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html): texto normal 4,5:1; texto grande 3:1. [Non-text Contrast (1.4.11)](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html): controles/estados y gráficos necesarios 3:1.
- [W3C — Keyboard (2.1.1)](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html): funcionalidad operable mediante interfaz de teclado; [Focus Visible (2.4.7)](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html): debe existir modo con foco visible; [Focus Not Obscured (Minimum, 2.4.11)](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html): el foco no queda enteramente oculto por contenido de autor.
- [W3C WAI — técnica C39 para `prefers-reduced-motion`](https://www.w3.org/WAI/WCAG22/Techniques/css/C39): técnica para permitir suprimir movimiento mediante preferencia del sistema; no se presenta como certificación WCAG por sí sola.

**Límite de la evidencia:** las razones cromáticas se calcularon con la fórmula de luminancia relativa sRGB de WCAG y las parejas listadas. No se ha renderizado ni auditado una UI, lector de pantalla, teclado físico, zoom o estados interactivos. La paleta es propuesta; la conformidad exige validar implementación futura.
