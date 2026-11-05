# Paideia — direcciones visuales para el rediseño

**Documento de exploración · 4 de noviembre de 2026**

> **Estado:** propuesta abierta. No hay dirección aprobada, mockup, prototipo navegable ni cambio de código.
> **Alcance:** tres alternativas visuales, recorrido pantalla a pantalla, reglas de IA/datos/comparación, preferencia provisional y plan de prueba.
> **Fuera de alcance:** editar `api/_static/*`, API, datos, tests o despliegue; crear cuentas; usar credenciales o servicios de pago; publicar nada.
> **Referencias:** son webs públicas reales, consultadas el 4/11/2026. Se usan como inspiración de patrones, no como branding copiado ni como demos de Paideia.
> **Prioridad:** este documento no abre el rediseño. El equipo mantiene backend y funcionamiento primero; la decisión visual se toma al final, después de las pruebas.

---

## 0. Resumen en 60 segundos

| Dirección | Idea | Referencias | Cuándo tiene sentido |
|---|---|---|---|
| **A · Cuaderno de estudio** | Paideia como un cuaderno editorial: papel cálido, serif, notas al margen, fuentes como notas al pie. | Notion + Anthropic | Si el equipo quiere conservar el aire de «cuaderno», minimizar riesgo y construir rápido. |
| **B · Fintech clara** | Paideia como un producto financiero cercano: una sola voz visual, números grandes, tarjetas, pasos y comparación muy legible. | Wise + Coinbase | Si prioriza claridad para principiantes, impacto en la demo y una escena de comparación contundente. |
| **C · Atlas de datos** | Paideia como explorador de datos: tabla, filtros, panel de procedencia y citas; la IA es una herramienta, no un personaje. | Our World in Data + GOV.UK Design System | Si prioriza transparencia, diferenciación y escalabilidad del catálogo, y hay tiempo para tablas/gráficos. |

**Preferencia provisional:** **B**, con condiciones: la disciplina de procedencia de C, la calma editorial de A y cero lenguaje comercial. **A** es el refugio de menor riesgo; **C** es la apuesta más diferencial y la más cara. No es una decisión: se valida con las pruebas del apartado 8.

---

## 1. Lo que se conserva funcionalmente

El rediseño es de **presentación**. No cambia el producto, los datos ni las reglas.

| Área | Qué existe hoy | Qué debe seguir igual |
|---|---|---|
| Rutas | Inicio, Tu mapa, Biblioteca, Comparar, Escenarios, Ensayo ficticio, Glosario, Privacidad. | Las ocho rutas, el enrutado por hash, los títulos y el enlace «Saltar al contenido». |
| Perfil | Preguntas de una en una, «No lo sé», «Omitir», resumen editable, pausa y reanudación. | No inventar respuestas; no enviar el perfil automáticamente; permitir explorar sin perfil. |
| Biblioteca | Búsqueda, filtro por familia, 20 candidatos, fichas transcritas, estados de condición y fuente. | Mismos productos y mismos estados; no completar huecos; no convertir un candidato en oferta. |
| Comparador | 2–4 productos, filas de ISIN, liquidez, plazo, costes, garantía, pérdida, rendimiento, fecha y vigencia. | Mismo límite de 2–4; avisos de datos ausentes/vencidos; ninguna recomendación automática. |
| Escenarios | A/B, simple/compuesto, capital, tasa, 1–40 años, aportación, inflación, gráfico, tabla e informe HTML. | Mismos cálculos y supuestos; el resultado sigue siendo hipótesis, no predicción. |
| Ensayo | Cinco pasos: referencia, condiciones, importe, comprensión y justificante. | Mismos pasos; importe ficticio; ningún movimiento de dinero ni solicitud de datos bancarios. |
| Pai / chat | Consentimiento, campos seleccionables, límites, estados de error, procedencia y cálculo local. | Nada se envía sin acción explícita; la IA no calcula ni atribuye fuentes por su cuenta. |
| Glosario y ayuda | Definiciones y ayuda contextual. | Mismos términos y mismo tono educativo; no sustituyen la ficha del producto. |
| Privacidad | Qué sale del navegador, vista previa por campos, guardado local con consentimiento y borrado. | Misma lógica de consentimiento, revocación y borrado; sin registro. |
| Accesibilidad | Enlace de salto, foco visible, regiones vivas, objetivos de 44–48 px, movimiento reducido e impresión. | No perder ninguna de estas bases; el rediseño debe mejorar, no reducir. |

**Reglas de no regresión**

- No cambiar contratos de API, cálculos, estados de datos, consentimiento ni textos legales.
- No añadir productos, tasas, fechas, garantías ni «datos de ejemplo» que parezcan reales.
- No usar la IA para producir cifras, fuentes o recomendaciones; solo para explicar y orientar.
- No convertir «puede tener sentido» en «recomendado», «mejor» o «para ti».
- No pedir más datos personales ni crear cuenta donde hoy no la hay.
- No mostrar el perfil completo ni datos sensibles en pantallas públicas, URLs, capturas o mensajes de error.
- No usar logotipos de entidades financieras sin permiso; los nombres reales se muestran en texto.
- No inferir el perfil por el comportamiento ni usar «para ti» sin un perfil explícito y una regla trazable.
- «Tu mapa» es un resumen de recorrido, no un mapa geográfico ni una puntuación de idoneidad; si se visualiza, es opcional, con leyenda y texto alternativo.
- Si se migra por partes, conservar ids, landmarks y hooks que usan `app.js` y los tests; renombrarlos exige actualizar pruebas.

---

## 2. Criterios de diseño

1. **Principiante primero.** Una decisión por pantalla, frases cortas, ejemplos en euros y una salida clara: «no lo sé», «omitir», «volver».
2. **Confianza sin vender.** La credibilidad viene de la fuente y la fecha, no de un escudo, un azul bancario o una promesa.
3. **Procedencia visible.** Todo número relevante tiene fuente, tipo de fuente, fecha de consulta y estado; lo que falta se dice.
4. **IA humilde.** Pai explica, cita y reconoce límites; no decide, no calcula y no suplanta a un asesor.
5. **Cero patrones oscuros y cero personalización presuntiva.** Sin preselección, urgencia, escasez falsa, culpabilización por rechazo, salida escondida, salidas bloqueadas ni «para ti» sin perfil explícito.
6. **Accesibilidad estructural.** WCAG 2.2 AA, 320 px, 200 %, teclado, lector de pantalla y contraste; no un pulido final.
7. **Reutilizar patrones.** Tarjetas, tablas, pestañas, paneles y formularios conocidos; la identidad se construye con jerarquía, color y tono, no inventando interacciones.
8. **Demo legible en cuatro minutos.** La escena central —comparar y ver cambiar escenarios— debe entenderse sin explicación previa.

---

## 3. Tres direcciones

### A · Cuaderno de estudio

**Idea.** Paideia se lee como un cuaderno bien editado: una página con aire, un titular serif, una nota al margen y una fuente al pie. El producto no parece un banco ni un panel de control; parece material de estudio cuidado.

**Referencias verificables**

- **Notion** — https://www.notion.com/es — neutros cálidos, bordes de 1 px, etiquetas tipo píldora, contenido primero, ritmo vertical amplio.
- **Anthropic** — https://www.anthropic.com/ — papel cálido, titulares serif de peso medio, terracota como acento, interlineado generoso y estética editorial.

**Qué se toma / qué no se copia**

- Se toma: temperatura del papel, jerarquía serif/sans, bordes finos, notas y citas, sensación de lectura pausada.
- No se copia: logotipos, nombres, ilustraciones orgánicas, paleta exacta, tipografías propietarias ni textos. La mascota Pai y el nombre Paideia siguen siendo propios.

**Sistema visual (propuesta, no tokens finales)**

| Elemento | Propuesta |
|---|---|
| Color | Papel `#F7F3E8`; superficie `#FFFDF7`; tinta `#1C1B18`; secundario `#5C5A52`; acento terracota `#A9502F`; línea `#D9D3C5`; foco `#1F5FBF`. Verde salvia solo para estados positivos. |
| Tipografía | Titulares Georgia o Source Serif 4 (si se sirve localmente); UI y cuerpo `system-ui`/Inter; cuerpo 17 px, interlineado 1,6; metadatos 13–14 px. |
| Forma | Radios 8–12 px; bordes de 1 px; sombra de anillo, no sombras difusas; botones rectangulares redondeados, no tipo píldora en todo. |
| Movimiento | Aparición de 120–160 ms; sin parallax ni autoplay; respeta `prefers-reduced-motion`. |

**Estructura de escritorio.** Tres columnas: navegación 220 px, contenido 760–820 px, margen de Pai/fuentes 280 px; ancho máximo 1320 px. La columna derecha es una **nota al margen**, no un panel de chat permanente. El contenido manda; la navegación es una lista de texto, sin los números «00–07» como decoración.

**Estructura móvil.** Una columna, 20 px de margen lateral. La nota al margen se convierte en un bloque «Nota de Pai» después del párrafo relevante. Las fuentes se pliegan en `<details>` («Fuente y fecha»). Barra inferior sobria con cuatro destinos y «Más»; nunca un botón flotante que tape la acción principal.

**Pai.** «Pai en el margen»: una marca triangular pequeña, la etiqueta `Pai · IA` y una nota de 3–6 líneas con una cita al pie. El chat completo vive en una sección plegable al final de la página, no en un globo persistente. En móvil, las notas aparecen en línea, no en un panel lateral.

**Datos, fuentes y fechas.** Citas tipo nota al pie: un superíndice junto al número y un «Registro de fuentes» al final de la pantalla. Cada registro: fuente, tipo (oficial/secundaria), fecha de consulta y vigencia. Los estados se muestran como sello textual, no solo color. La fecha absoluta manda; «hace 3 días» solo como complemento.

**Comparaciones.** Una tabla editorial a dos páginas: criterios fijos a la izquierda, 2–3 productos a la derecha (4 como máximo), «lo que falta» como una fila más. Sin ganador, sin medalla, sin ordenar por tasa por defecto. En móvil, tarjetas apiladas con un botón «Ver diferencias» que abre una lista comparada.

**Balance**

- **Fortalezas:** transmite calma y credibilidad; excelente para explicar y para leer fuentes; coste de implementación bajo (sobre todo CSS y jerarquía); se distancia del típico panel de control financiero.
- **Riesgos:** puede parecer un blog o un clon de Notion; los principiantes pueden no encontrar el comparador; los metadatos pequeños y el serif exigen disciplina tipográfica; menos impacto en una demo de cuatro minutos.
- **Coste:** bajo-medio. **Cuándo elegirla:** si el equipo quiere conservar el concepto de cuaderno, reducir riesgo y tiene poco tiempo de implementación.

---

### B · Fintech clara

**Idea.** Paideia se comporta como un buen acogida de una fintech: una promesa corta, tres entradas claras, números grandes y una comparación que se lee de un vistazo. Cercano, no infantil; serio, no bancario.

**Referencias verificables**

- **Wise** — https://wise.com/es/ — fondo blanco cálido, tinta casi negra, un acento vivo, botones tipo píldora, tarjetas redondeadas, titulares de gran tamaño y tono directo.
- **Coinbase** — https://www.coinbase.com/es-ES — blanco/casi negro, un azul saturado como único acento, números protagonistas, secciones alternas y sensación de institución seria. Puede mostrar un muro de consentimiento o bloquear peticiones automatizadas; la referencia es la página pública, no una cuenta.

**Qué se toma / qué no se copia**

- Se toma: contraste fuerte, un solo acento, números legibles, tarjetas y píldoras, ritmo de secciones, claridad de la acción principal.
- No se copia: el verde lima de Wise, el azul exacto de Coinbase, sus logotipos, tipografías propietarias, ilustraciones ni lenguaje de «empieza a invertir». Paideia no es un banco ni un bróker.

**Sistema visual (propuesta, no tokens finales)**

| Elemento | Propuesta |
|---|---|
| Color | Fondo `#FAFAF7`; superficie `#FFFFFF`; tinta `#0F1412`; secundario `#56615C`; primario verde-teal `#0B6B5B`; menta `#DDF3E9`; ámbar `#9A5A00` sobre `#FFF1D6`; línea `#E2E5DF`. |
| Tipografía | Inter, DM Sans o `system-ui`; titulares 44–56 px, peso 700, interletraje cerrado; cuerpo 17–18 px, interlineado 1,55; cifras con `font-variant-numeric: tabular-nums`. |
| Forma | Tarjetas 16–20 px; campos 12 px; botones 12–14 px (no imitar el botón tipo píldora de Wise); píldoras 999 px; sombras mínimas o sombra de anillo. |
| Movimiento | 150–200 ms; al pasar el ratón, elevación mínima; sin animaciones de «dinero que crece» ni contadores. |

**Estructura de escritorio.** Barra superior de 68 px con marca, cinco destinos y «Preguntar a Pai». Contenido máximo 1160 px. Inicio con titular y tres tarjetas de entrada («Aprender», «Comparar», «Probar un escenario»). Biblioteca en dos columnas; comparador a ancho completo con columna de criterios fija; Pai en un panel lateral de 380 px que se abre desde la derecha sin tapar la tabla.

**Estructura móvil.** Barra inferior de cinco destinos: Inicio, Biblioteca, Comparar, Escenarios, Pai. Una columna; tarjetas de producto con TAE grande y sello de fuente; comparador en tarjetas apiladas con barra fija «2 seleccionados · Comparar»; Pai como hoja inferior a pantalla completa.

**Pai.** «Pai acompañante»: botón discreto en la esquina inferior derecha o en la barra superior; abre un panel lateral. Respuestas con etiqueta `Pai · IA`, tarjetas de fuente debajo y una etiqueta `Calculado localmente` cuando el número venga del motor. Píldoras de preguntas sugeridas, nunca respuestas automáticas. Si el usuario cierra, no vuelve a insistir.

**Datos, fuentes y fechas.** Sellos en la tarjeta: `Documentada · 3 nov 2026`, `Pendiente`, `No vigente`, `En conflicto`. Cada tasa lleva debajo una línea `Fuente: [nombre] · [oficial/secundaria] · consultado [fecha]`. Un banner global de frescura si el catálogo tiene datos viejos. El detalle abre un panel lateral con la tabla de procedencia.

**Comparaciones.** Tarjetas alineadas o tabla con 2–4 columnas; los números grandes mandan; una fila «Qué falta» y otra «Cobertura 7/9». Se destacan **diferencias**, no ganadores. Lenguaje neutral: «puede tener sentido si…», nunca «la mejor opción». En móvil, tarjetas con un selector «Comparar con…» y una vista de diferencias.

**Balance**

- **Fortalezas:** la más clara para principiantes; excelente para la escena central de demo; los números y la comparación se leen rápido; patrones conocidos y fáciles de implementar; buena percepción de producto.
- **Riesgos:** puede parecer una web comercial o un banco, y por tanto insinuar asesoramiento; el acento vivo y las tarjetas pueden tapar los datos ausentes; el panel de Pai puede volverse intrusivo; la apariencia de confianza no sustituye la procedencia.
- **Coste:** medio. **Cuándo elegirla:** si el equipo prioriza claridad, demo y público principiante, y acepta reglas estrictas de procedencia y lenguaje.

---

### C · Atlas de datos

**Idea.** Paideia es un explorador público de productos financieros: cada fila tiene coordenadas —fuente, fecha, vigencia, cobertura— y cada comparación se puede auditar. La IA es una lupa, no un personaje.

**Referencias verificables**

- **Our World in Data** — https://ourworldindata.org/ — datos primero, citas visibles, gráficos con contexto, tono explicativo y paleta restringida.
- **GOV.UK Design System** — https://design-system.service.gov.uk/ — lenguaje claro, contraste alto, formularios accesibles, componentes sin decoración y foco en la tarea.

**Qué se toma / qué no se copia**

- Se toma: jerarquía de datos, tablas legibles, panel de procedencia, lenguaje llano, patrones de formulario y foco visibles.
- No se copia: la identidad GOV.UK, la corona, los gráficos de OWID, sus paletas exactas ni su tono administrativo. Paideia sigue siendo una web educativa, no un servicio público.

**Sistema visual (propuesta, no tokens finales)**

| Elemento | Propuesta |
|---|---|
| Color | Fondo `#F3F6F5`; superficie `#FFFFFF`; tinta `#12201C`; secundario `#4E5F59`; primario verde profundo `#0B5D52`; acento ocre `#8F5500`; línea `#D5DEDA`; azul pizarra para datos `#5B6B7A`. |
| Tipografía | Inter o `system-ui`; cuerpo 16–17 px; titulares 30–36 px; cifras y fechas en mono/tabular; sin serif. |
| Forma | Radios 4–8 px; tablas densas con bordes de 1 px; sin sombras; iconos de 16–20 px; mucho contraste, poca decoración. |
| Movimiento | Prácticamente ninguno; solo transiciones de estado de 100–150 ms; tablas y filtros instantáneos. |

**Estructura de escritorio.** Tres zonas: columna de filtros 260 px, tabla/gráfico `minmax(0,1fr)`, panel de procedencia 320 px; ancho máximo 1440 px. Barra superior con búsqueda global y «Preguntar sobre esta tabla». La tabla es el centro; el panel derecho explica la fuente y la vigencia de la fila seleccionada.

**Estructura móvil.** Filtros en una hoja; tabla convertida en fichas con `data-label`; panel de procedencia como `<details>` bajo cada cifra; gráficos a ancho completo con desplazamiento solo dentro del gráfico; barra fija «2 seleccionados · Comparar».

**Pai.** «Pai como consulta»: una barra sobre la tabla («Preguntar sobre estos datos») y un panel de respuesta. Cada frase lleva cita `[1]`, `[2]`; arriba se separa `Dato local` de `Explicación IA`. Si no hay dato: «No encontrado», no una estimación. Enlace «Qué datos se enviaron» en cada respuesta.

**Datos, fuentes y fechas.** La procedencia es una columna más: `Fuente`, `Tipo`, `Consultado`, `Vigencia`, `Estado`. Cada producto muestra `Cobertura 7/9`. Los datos vencidos se excluyen de la comparación con el motivo visible. El panel derecho permite abrir la fuente y ver el conflicto si existe.

**Comparaciones.** Matriz de criterios × productos, con celdas `Sin dato` tramadas (no rojas, no cero), selector «Ver solo diferencias», y un aviso de validez si algún dato está vencido. Sin puntuación agregada, sin ranking, sin «mejor». En móvil, fichas comparadas y un botón «Ver tabla completa» que abre una región con desplazamiento etiquetada.

**Balance**

- **Fortalezas:** la más diferencial; hace visible la procedencia; escala bien a más productos y familias; excelente para escenarios y comparaciones; encaja con un discurso de transparencia.
- **Riesgos:** alta carga cognitiva para principiantes; puede sentirse fría o administrativa; requiere más ingeniería (tablas, filtros, estados, adaptación a móvil); en una demo de cuatro minutos puede abrumar; el «atlas» puede atraer a perfiles financieros más que a principiantes.
- **Coste:** alto. **Cuándo elegirla:** si hay tiempo, el equipo quiere una identidad difícil de confundir y la prioridad es la trazabilidad más que la simpatía.

---

## 4. Recorrido pantalla a pantalla

El recorrido funcional es el mismo en A, B y C. Cambia la puesta en escena.

| Pantalla | Lo que el usuario necesita | Contenido y acción | A | B | C |
|---|---|---|---|---|---|
| **00 Inicio** | Saber qué puede hacer sin registrarse ni dar datos. | Promesa corta; tres entradas: explorar, comparar, probar; estado de datos; Pai opcional. | Portada de cuaderno con índice. | Portada + tres tarjetas grandes. | Tablero con buscador y estado del catálogo. |
| **01 Tu mapa** | Entender para qué sirve el perfil y que es opcional. | Preguntas de una en una; progreso; «No lo sé»/«Omitir»; resumen editable; aviso de que no se envía. | Cuestionario con notas al margen. | Indicador de pasos con tarjetas. | Formulario estilo GOV.UK, una pregunta por pantalla. |
| **02 Biblioteca** | Encontrar productos reales y distinguir lo documentado de lo pendiente. | Buscador, filtro por familia, 20 candidatos, sellos de estado, selección 2–4. | Lista editorial con metadatos. | Tarjetas con TAE grande y sello. | Tabla con filtros y columna de cobertura. |
| **03 Ficha de producto** | Ver identidad, condiciones, fuente, fecha y qué falta. | Nombre, entidad, familia, ISIN, condiciones, fuente, vigencia, «añadir a comparar», «probar en escenario». | Ficha a página completa con notas al pie. | Ficha en panel lateral/tarjeta con etiquetas. | Ficha con panel de procedencia. |
| **04 Comparar** | Comparar 2–4 alternativas y ver los huecos sin sentirse empujado. | Criterios alineados, diferencias, cobertura, aviso de datos vencidos, quitar/añadir, imprimir. | Tabla editorial a dos páginas. | Tarjetas/columnas con números grandes. | Matriz con celdas «sin dato» y filtro de diferencias. |
| **05 Escenarios** | Probar supuestos propios y entender que es una hipótesis. | A/B; capital, tasa, años, aportación, inflación, método; gráfico, tabla, resumen nominal/real; informe. | Página de cálculo con notas. | Panel de control con tarjetas y gráfico. | Laboratorio de datos con tabla y gráfico. |
| **06 Ensayo ficticio** | Recorrer una contratación simulada sin miedo ni datos reales. | Cinco pasos; producto real; importe ficticio; comprensión; justificante; «no se ha enviado nada». | Guion de cuaderno con sello. | Indicador de pasos con tarjetas y recibo. | Formulario por pasos con resumen de datos. |
| **07 Glosario** | Entender una palabra sin salir del contexto. | Definiciones breves; enlaces desde la ficha y desde Pai. | Glosario editorial. | Tarjetas/buscador. | Tabla de términos + ayuda contextual. |
| **08 Privacidad** | Saber qué sale, qué se guarda y cómo borrarlo. | Consentimiento de chat, vista previa por campos, guardado local con consentimiento, borrado. | Página de notas con lista de comprobación. | Sección clara con interruptores. | Panel de transparencia con detalle. |
| **Pai (transversal)** | Preguntar sin perder el contexto ni la fuente. | Respuesta breve, fuentes, incertidumbre, qué se envió, estados y alternativa. | Nota al margen + chat plegable. | Panel lateral/hoja inferior. | Barra «preguntar sobre esta tabla» + panel lateral. |

**Escena central de demo (4 minutos)**

1. **Inicio:** «No hace falta perfil para explorar». Se ve el estado del catálogo y la entrada a la biblioteca.
2. **Biblioteca:** filtro «Depósitos»; se abren dos fichas; se señala la fuente, la fecha y el aviso de fuente secundaria.
3. **Comparar:** dos productos; se ve la tabla, la cobertura y la fila «qué falta». Se dice en voz alta: «esto no es una recomendación».
4. **Escenarios:** se cambia la tasa o el horizonte; el gráfico y la tabla muestran nominal, real y aportado; se descarga el informe.
5. **Pai:** pregunta «¿qué significa TAE?» o «¿por qué falta este dato?». La respuesta enseña la etiqueta IA, la cita y el límite.
6. **Privacidad:** se muestra que el perfil no se envió y que se puede borrar.

---

## 5. Reglas transversales: IA, datos y comparaciones

### 5.1 Cómo mostrar la IA

**Contrato mínimo, común a las tres direcciones**

| Elemento | Regla | Ejemplo |
|---|---|---|
| Etiqueta | Pai siempre visible como IA, nunca como persona. | `Pai · IA` |
| Respuesta | 3–6 líneas; una idea por párrafo; sin muros de texto. | «La TAE incluye el coste del dinero…» |
| Cálculo | Los números vienen del motor local; la IA solo los explica. | `Calculado localmente · supuestos A` |
| Fuentes | Cada afirmación factual lleva cita o «no consta». | `[1] Ficha EBN · consultado 3 nov 2026` |
| Incertidumbre | Se dice «no lo sé» o «no consta»; no se rellena el hueco. | «No hay una condición documentada para ese plazo.» |
| Datos enviados | Desplegable con lo que sale del navegador; nada automático. | `Se envía: tu pregunta + 2 campos marcados` |
| Estados | Cargando, respuesta progresiva, detenido, tiempo agotado, sin configurar, límite, sin resultado, error. | Ver tabla de estados más abajo |
| Alternativa | Biblioteca, comparador y escenarios funcionan sin Pai. | «Pai no está disponible; puedes seguir explorando.» |

**Reparto de decisiones**

| Decisión | Responsable | Qué ve el usuario |
|---|---|---|
| Calcular importes y escenarios | Motor local | `Calculado localmente` + supuestos |
| Estado y fecha de una condición | Catálogo y fuente | Sello de procedencia |
| Elegibilidad o encaje | Reglas y datos; nunca la IA | «No hay recomendación automática» |
| Explicar un concepto o un resultado | Pai | `Pai · IA` + fuentes |
| Decidir qué contratar | La persona | Sin contratación real |

**Anatomía de un mensaje**

1. Etiqueta `Pai · IA`.
2. Respuesta directa, en lenguaje llano.
3. Evidencia: fuente, fecha y alcance.
4. Límite: qué no se sabe o qué no se ha comprobado.
5. Acción: «Ver ficha», «Ver cálculo», «Añadir a comparar».
6. «Qué se envió» y «Detener»/«Reintentar» cuando aplique.

**Estados y microtextos**

| Estado | Qué se muestra |
|---|---|
| Cargando | «Pai está consultando el catálogo local…» solo si hay una operación real en curso; sin teatro. |
| Respuesta progresiva | Texto progresivo + botón «Detener»; `aria-live="polite"`. |
| Sin configurar | «Pai no está conectado en esta versión. La biblioteca, el comparador y los escenarios siguen funcionando.» |
| Límite | «Has alcanzado el límite de preguntas por ahora. Puedes seguir sin Pai.» |
| Sin resultado | «No encuentro una condición documentada para eso. No la voy a estimar.» |
| Tiempo agotado | «La respuesta tardó demasiado. Reintentar o seguir sin Pai.» |
| Error | «No se pudo completar la consulta. No se ha guardado nada.» |

**Dónde vive Pai**

- **A:** nota al margen y chat plegable; nunca tapa el contenido.
- **B:** panel lateral/hoja inferior; botón discreto; se cierra y no insiste.
- **C:** barra «preguntar sobre esta tabla» + panel lateral; citas en línea.

**Lo que no se hace**

- No simular «pensando» con animaciones largas ni frases tipo «déjame pensar…» si no hay espera real.
- No usar un avatar humano, una voz de asesor ni un nombre propio que sugiera persona.
- No presentar a Pai como asesor financiero, fiscal o jurídico ni como una entidad regulada.
- No usar la IA para decidir elegibilidad, calcular cifras o elegir un producto; esas decisiones son del motor y de las reglas.
- No decir «te recomiendo», «lo mejor para ti» o «deberías».
- No inventar cifras, fuentes, fechas ni condiciones; no completar tablas vacías.
- No enviar el perfil ni campos no marcados; el historial, si existe, se explica y se limita a la pestaña.
- No prometer memoria o historial persistente: en la web pública el historial está desactivado; si se muestra, debe decir «solo esta pestaña» y coincidir con el backend.
- No poner datos del perfil, la pregunta o el historial en la URL, el título de la página o un parámetro compartible.
- No ocultar el botón de detener, reintentar o salir.

### 5.2 Cómo mostrar datos, fuentes y fechas

**Sello de procedencia.** Todo dato relevante lleva, como mínimo:

| Campo | Regla |
|---|---|
| Fuente | Nombre de la fuente y enlace; `oficial`, `secundaria`, `mixta` o `desconocida`. |
| Fecha de consulta | Fecha absoluta, `3 nov 2026`; `datetime` en ISO; zona `Europe/Madrid`. |
| Vigencia | Fecha efectiva o «sin fecha de vigencia»; no confundir con «consultado». |
| Estado | `Documentada`, `Documentada no vigente`, `En conflicto`, `Desconocida`, `Solo identidad`. |
| Alcance | Qué condición cubre y qué no; por ejemplo, «TAE de depósito a 12 meses». |

**Estados, con texto además de color**

| Estado | Significado | Tratamiento visual |
|---|---|---|
| Documentada | Hay fuente y fecha; el dato es utilizable. | Verde + check + texto. |
| Documentada no vigente | Hay fuente, pero la condición ha caducado. | Ámbar + reloj + texto; excluida de comparación. |
| En conflicto | Dos fuentes no coinciden. | Rojo + señal + texto; no se elige una en silencio. |
| Desconocida | No hay dato documentado. | Gris + interrogación + «Sin dato». |
| Solo identidad | Se sabe qué producto es, no sus condiciones. | Azul info + texto; no se infiere. |

**Reglas de fecha y frescura**

- Fecha absoluta siempre; relativa solo como apoyo («hace 3 días» junto a «consultado el 1 nov 2026»).
- «Actualizado» no es una fecha: mostrar hora y zona (`4 nov 2026, 08:40, Europe/Madrid`).
- Un dato vencido no se compara; se muestra el motivo y la última fecha válida.
- La comparación lleva un aviso de validez si algún campo está vencido o en conflicto.
- El informe impreso incluye fuentes, fechas y una nota de alcance; no solo cifras.

**Reglas de «sin dato»**

- `Sin dato` es un estado visible, no una celda vacía, un cero o un guion.
- No se infiere por familia, por reputación de la entidad ni por el aspecto de la web.
- No se usa el dato de otro producto «parecido» para rellenar.
- Si falta un dato que cambia la comparación, se dice qué falta y cómo limita la conclusión.

**Anatomía de una ficha**

1. Identidad: nombre, entidad, familia, ISIN si existe.
2. Condición principal: TAE/plazo, con unidad y alcance.
3. Sello: fuente, tipo, consultado, vigencia, estado.
4. Qué falta: costes, liquidez, garantía, pérdida, etc.
5. Acciones: comparar, probar escenario, ver fuente.
6. Aviso: «candidato de investigación; no es una oferta publicable».

*Ejemplo interno ya documentado en el proyecto: EBN 3,10 % frente a Self Bank 2,75 % a 12 meses, con la segunda fuente marcada como secundaria. No reutilizar sin volver a comprobar fecha y vigencia; aquí sirve solo para probar la jerarquía visual, no como oferta.*

### 5.3 Cómo mostrar comparaciones

- **2–4 productos.** Ni uno solo ni una tabla infinita; el límite actual se mantiene.
- **Sin ganador por defecto.** No hay «mejor», «recomendado», medalla, corona ni orden por tasa al cargar.
- **Sin puntuación agregada.** No inventar un «score Paideia» que mezcle riesgo, coste y rentabilidad.
- **Unidades consistentes.** TAE anual, plazo en meses, importes en EUR; no mezclar nominal y real sin etiqueta.
- **Cobertura visible.** «Cobertura 7/9» y una fila «Qué falta»; el hueco es parte del resultado.
- **Diferencias, no veredictos.** Resaltar lo que cambia entre columnas; no colorear una columna como «ganadora».
- **Lenguaje educativo.** «Puede tener sentido si…», «conviene comprobar…», «no es una recomendación».
- **Validez.** Si un dato está vencido o en conflicto, la comparación lo dice y excluye el campo.
- **Móvil.** Tarjetas apiladas o tabla con desplazamiento interno etiquetado; nunca desplazamiento horizontal de toda la página.
- **Impresión.** Criterios, productos, fuentes, fechas y aviso; sin botones ni elementos interactivos.

**Anatomía de una comparación**

1. Cabecera: productos, familia, número de columnas, fecha de la comparación.
2. Aviso de alcance: «datos documentados cuando existen; no es una oferta».
3. Tabla: criterios fijos, celdas con valor + sello, `Sin dato` explícito.
4. Cobertura: cuántos campos faltan por producto y por comparación.
5. Cierre: «qué haría falta para decidir» y enlace a glosario/escenario.

**Microtextos que funcionan**

- `Comparación de 3 productos · cobertura 7/9 · actualizada el 4 nov 2026`
- `Sin dato documentado. No se estima.`
- `Este campo queda fuera de la comparación: la fuente tiene 94 días y supera el límite de la familia.`
- `No hay un producto «mejor»: depende de tu situación. Esta pantalla no decide por ti.`
- `Para quién puede tener sentido` (nunca `Recomendado para ti`).

**Patrones oscuros que se evitan**

- Productos preseleccionados o «recomendados» sin regla trazable.
- Ordenar por «más popular» sin datos de popularidad.
- Cuentas atrás, «solo hoy», «últimas plazas», «no te lo pierdas».
- Testimonios, logos de terceros o cifras de usuarios no verificadas.
- «¿Seguro que quieres irte?», salida enterrada, borrado difícil.
- Chat que reaparece tras cerrarlo o que bloquea la biblioteca.
- «Completa tu perfil para ver resultados» cuando la biblioteca es pública.
- IA que se presenta como humana o que afirma haber comprobado lo que no ha comprobado.

---

## 6. Estructura y accesibilidad

### 6.1 Estructura por dirección

| | A · Cuaderno | B · Fintech | C · Atlas |
|---|---|---|---|
| **Escritorio** | 220 navegación / 760–820 contenido / 280 margen; máx. 1320. | Barra superior 68; contenido 1160; panel lateral 380. | 260 filtros / 1fr tabla / 320 procedencia; máx. 1440. |
| **Tablet (768–1024)** | 200 navegación / contenido; margen debajo. | Navegación compacta; tarjetas 2 col; panel lateral 360. | Filtros en botón; procedencia debajo; tabla con desplazamiento interno. |
| **Móvil (360–430)** | Una columna; notas en línea; barra 4 + «Más». | Barra 5; tarjetas; fija «Comparar». | Filtros en hoja; fichas; fija «Comparar». |
| **Navegación** | Lista de texto, sin decoración numérica. | Cinco destinos + «Pai». | Búsqueda global + filtros; cinco destinos. |
| **Pai** | Nota al margen + chat plegable. | Panel lateral/hoja inferior. | Barra sobre tabla + panel lateral. |
| **Comparar** | Tabla editorial. | Tarjetas/columnas con números grandes. | Matriz con celdas «sin dato». |

**Reglas comunes**

- Ancho máximo y `minmax(0, 1fr)` para evitar desbordes; nada de `width: 100vw`.
- Márgenes laterales de 20 px móvil, 24–32 tablet, 32–48 escritorio.
- Objetivos táctiles de 44×44 px como estándar de producto (el mínimo AA de WCAG 2.2 es 24×24); separación de 8 px.
- Nada de desplazamiento horizontal de página; solo regiones de tabla/gráfico con etiqueta y foco.
- Elementos fijos solo si no tapan contenido, foco ni teclado virtual; respetar `safe-area-inset-bottom`.
- Sin depender de pasar el ratón como única vía para ver fuente, estado o acción.

### 6.2 Accesibilidad: objetivo y criterios

**Objetivo:** WCAG 2.2 AA en las pantallas nuevas, sin certificar nada que no se haya probado. Los pares de color principales de las propuestas se han revisado para texto normal en sus fondos (≥4.5:1); la implementación debe verificar cada combinación real, incluidos estados y superficies tintadas.

- **Estructura:** `lang="es"`, un `h1` por pantalla, orden de encabezados, regiones (`header`, `nav`, `main`, `footer`), enlace de salto.
- **Color:** contraste 4.5:1 en texto y 3:1 en UI; estados con texto e icono, nunca solo color; foco visible con contraste.
- **Teclado:** recorrido completo de perfil, biblioteca, comparación, escenarios, chat y borrado; foco gestionado al cambiar de ruta y al abrir/cerrar paneles; sin trampas de foco.
- **Formularios:** etiqueta visible, ayuda asociada, errores específicos con `aria-invalid` y texto; «No lo sé» y «Omitir» como acciones reales; sin campos obligatorios innecesarios.
- **Tablas:** `<caption>`, `th scope`, celdas con `data-label` en móvil; no convertir la tabla en imágenes.
- **Gráficos:** tabla alternativa, texto alt, etiquetas directas y patrones además de color; sin depender de pasar el ratón.
- **Movimiento:** `prefers-reduced-motion`; sin reproducción automática; respuesta progresiva con botón de detener.
- **Lenguaje:** frases cortas, voz activa, sin jerga sin glosario; ayuda consistente; sin límites de tiempo.
- **Móvil:** 320 px sin desplazamiento horizontal; 200 % de zoom sin recorte; teclado virtual sin tapar el campo.

**Criterios de aceptación medibles**

1. 320 px y 200 %: `scrollWidth <= clientWidth` en la página; la tabla puede tener desplazamiento interno etiquetado.
2. 200 %: ningún texto esencial recortado; el indicador de pasos no parte palabras en 3–4 líneas.
3. Todos los controles: 44×44 px y foco visible.
4. Contraste AA en texto, botones, etiquetas y estados.
5. Recorrido de teclado completo sin ratón en las ocho rutas.
6. Lector de pantalla: nombres accesibles en navegación, formularios, tabla, chat y borrado.
7. `aria-live` para carga, respuesta progresiva, error y confirmación; sin mutaciones redundantes.
8. Informe impreso con fuentes, fechas y aviso de alcance.

**Estado actual que el rediseño debe resolver**

- Desbordamiento de 15 px a 320 px con barra clásica y zoom 200 %.
- Etiquetas del indicador de cinco pasos en 2–4 líneas, con legibilidad limitada.
- Sin certificación con lector de pantalla ni dispositivo móvil físico.
- La base ya incluye enlace de salto, foco visible, `aria-live`, objetivos de 44–48 px, `prefers-reduced-motion` y estilos de impresión; no se debe perder.

---

## 7. Preferencia provisional

**Primera preferencia: B · Fintech clara, con condiciones.**

Es la que mejor equilibra las prioridades actuales: principiantes, comparación como escena central, demo de cuatro minutos y un producto que se percibe terminado. No se elige por «gustar más», sino porque reduce la distancia entre «entiendo la web» y «entiendo la comparación».

**Condiciones para que B funcione**

1. **Procedencia de la dirección C:** sello de fuente/fecha/vigencia en cada tarjeta y en cada comparación, no escondido en un modal.
2. **Calma editorial de A:** titulares y textos sin exageración, sin signos de urgencia, sin «empieza ya».
3. **Cero lenguaje comercial:** nada de «mejor», «recomendado», «para ti», «oferta», «última oportunidad».
4. **Pai discreto:** se abre, se cierra y no insiste; la biblioteca y el comparador funcionan sin IA.
5. **Paleta propia:** verde-teal, no el lima de Wise; sin el azul exacto de Coinbase; sin logotipos de entidades.
6. **Prueba con principiantes:** si B se percibe como banco o como recomendación, se corrige o se cae a A.

**Matriz cualitativa (para discutir, no para fingir precisión)**

| Criterio | A | B | C |
|---|---|---|---|
| Claridad para principiante | Alta | Muy alta | Baja |
| Confianza por procedencia | Alta | Media (depende del sello) | Muy alta |
| Diferenciación visual | Media | Media | Alta |
| Coste/velocidad de implementación | Bajo | Medio | Alto |
| Impacto en demo | Medio | Alto | Alto |
| Riesgo de parecer asesoramiento | Bajo | Medio-alto | Bajo |

**Por qué no A como primera opción.** A es la más segura y la más fácil de implementar, pero el equipo ya rechazó el diseño actual, que se presenta como «cuaderno»; sin un cambio claro de jerarquía y tipografía, A puede repetir el problema. Es el refugio si B no convence en las pruebas.

**Por qué no C como primera opción.** C es la más diferencial y la que mejor enseña fuentes, pero exige más tiempo y puede abrumar a un principiante en la primera visita. Es la apuesta si el equipo quiere una identidad difícil de confundir y puede construir el sistema de tablas/gráficos con cuidado.

**Qué haría cambiar la recomendación**

- Si ≥2 de 5 principiantes interpretan B como «me están vendiendo algo» o «me recomiendan contratar», B no pasa sin rediseño de textos/procedencia.
- Si A no permite encontrar el comparador o la fuente en menos de 30 s, A no pasa.
- Si C no permite completar una comparación en 5 min, C no pasa para principiantes (podría quedar como modo avanzado).
- Si cualquier dirección falla un criterio crítico de teclado, lector de pantalla o 320 px, se corrige antes de comparar.

---

## 8. Cómo testear después

**Cuándo.** Después de que el equipo elija 1–2 direcciones y antes de tocar producción. No se prueba sobre la app actual ni se despliega nada.

**Con quién.** 5–6 personas adultas sin formación financiera (mezcla de edades, móvil y escritorio) para tareas; 8–10 para la prueba de preferencia visual. Si se puede, 1–2 estudiantes de Finanzas solo para revisar contenido, no para usabilidad.

**Cómo.** Tableros estáticos de las mismas pantallas (Inicio, Biblioteca, Comparar, Escenarios, Privacidad), en orden aleatorio, sin nombres de dirección. En portátil y en móvil. Pensar en voz alta, 25–30 min, sin datos personales ni grabaciones sin consentimiento.

### 8.1 Prueba de preferencia (visual)

Mostrar A/B/C en orden aleatorio y preguntar, sin decir cuál es cuál:

1. ¿Qué te transmite cada una en los primeros 5 segundos?
2. ¿Dónde buscarías la fuente y la fecha de un dato?
3. ¿Cuál parece una web que te está recomendando contratar? ¿Por qué?
4. ¿Cuál usarías en el móvil para comparar dos productos?
5. ¿Qué palabra o elemento te ha hecho desconfiar?

No preguntar solo «¿cuál te gusta más?». La preferencia estética no decide; la comprensión y la confianza sí.

### 8.2 Prueba de tareas (dirección preferida)

| Tarea | Éxito | Qué se observa |
|---|---|---|
| Encuentra un depósito y di de dónde sale el dato y de cuándo es. | Producto + fuente + fecha correctos. | ¿Abre la ficha? ¿Confunde «actualizado» con «consultado»? |
| Compara dos productos y di qué información falta. | Identifica al menos un hueco real. | ¿La tabla oculta el hueco? ¿Cree que «sin dato» es cero? |
| ¿Esta pantalla te está recomendando contratar? | Responde «no, es educativo». | Si dice «sí», el diseño falla. |
| Cambia la tasa al 3 % y explica qué pasa. | Cambia el campo y lee el gráfico/tabla. | ¿Entiende que es una hipótesis? |
| Pregunta a Pai por una condición y comprueba la fuente. | Abre la cita y ve la etiqueta IA. | ¿Confía sin fuente? ¿Detecta que no hay dato? |
| Borra tu perfil. | Llega a Privacidad y borra. | ¿El borrado está escondido? ¿Hay culpabilización por rechazo? |
| Busca «TAE» en el glosario. | Encuentra la definición. | ¿Vuelve al contexto? |

### 8.3 Métricas y umbrales

| Métrica | Umbral orientativo |
|---|---|
| Tarea 1 (fuente + fecha) | ≥80 % éxito. |
| Tarea 2 (comparar + hueco) | ≥80 %. |
| Tarea 3 («no es recomendación») | ≥90 %; es crítico. |
| Tarea 4 (escenario) | ≥80 %. |
| Tarea 5 (Pai + fuente) | ≥80 %. |
| Tarea 6 (borrado) | ≥90 %. |
| SUS | ≥70. |
| UMUX-Lite | ≥75. |
| Accesibilidad | 0 bloqueantes críticos; teclado, 320 px, 200 %, contraste y lector de pantalla. |
| Móvil | ≥70 % de las tareas 1–4 en un móvil real o emulado con pantalla táctil. |

**Cualitativo:** frases literales, puntos de confusión, momentos de desconfianza, errores de interpretación de «sin dato», «no es una oferta» y «puede tener sentido».

### 8.4 Accesibilidad y QA antes de publicar

- Teclado solo: ocho rutas, comparación, escenario, chat, borrado.
- NVDA + Chrome y VoiceOver + Safari; nombres, estados y tablas.
- Zoom 200 % y 400 %; ancho 320 px; texto espaciado; sin recortes.
- Contraste con herramienta gratuita; estados sin color.
- `prefers-reduced-motion`; respuesta progresiva con detener; sin reproducción automática.
- Impresión: fuentes, fechas, aviso y páginas.
- Herramientas gratuitas: axe DevTools, Lighthouse, NVDA, VoiceOver. Sin servicios de pago.

### 8.5 Reglas de la prueba

- Nada de datos financieros reales; perfiles sintéticos o tareas con datos del catálogo.
- Nada de cuentas, credenciales, pagos ni despliegues.
- Nada de analítica con datos personales; notas agregadas y anónimas.
- No incluir datos personales en URLs, capturas, notas ni analítica; el perfil y el chat no deben aparecer en enlaces compartibles.
- No mostrar la app en producción si no está aprobada; tableros estáticos primero.
- No cambiar código durante la prueba; registrar y priorizar después.

---

## 9. Riesgos y decisiones pendientes

| Tema | Riesgo | Decisión pendiente |
|---|---|---|
| Tipografías | La CSP actual solo permite `self`; Google Fonts no cargaría. | Usar pilas del sistema o servir OFL localmente (Inter, Source Serif 4) con licencia comprobada. |
| Marcas | Usar logos de entidades puede sugerir afiliación. | Nombres en texto; sin logos sin permiso; revisar uso de marcas. |
| «Mapa» | Puede convertirse en una puntuación de idoneidad o en una metáfora vacía. | Definir si es resumen/navegación o visualización; si es mapa, que sea opcional y con leyenda. |
| Datos | Estados, caducidad y conflictos aún tienen criterios pendientes. | Cerrar la regla de frescura por familia antes de diseñar etiquetas definitivas. |
| Legal | El lenguaje de orientación y la IA necesitan revisión. | Revisar «no es asesoramiento», límites y textos de consentimiento antes de publicar. |
| Accesibilidad | No hay certificación con lector de pantalla ni móvil físico. | Incluir QA accesible como requisito de aceptación, no como extra. |
| Alcance | Un rediseño completo puede comerse el tiempo de la entrega. | Migración por componentes; primero la estructura, luego biblioteca/comparación, luego Pai. |
| Identidad | Parecerse demasiado a Wise/Coinbase/Notion/Anthropic anula a Paideia. | Paleta, tipografía y mascota propias; referencias solo como principio. |

---

## 10. Referencias

| Referencia | URL | Qué se toma | Qué no se copia |
|---|---|---|---|
| Wise | https://wise.com/es/ | Ritmo amplio, acento único, botones/tarjetas, tono directo. | Verde lima, tipografía, logo, textos, componentes exactos. |
| Coinbase | https://www.coinbase.com/es-ES | Contraste, azul único, números grandes, secciones alternas. | Azul exacto, logo, imágenes cripto, lenguaje de inversión. |
| Notion | https://www.notion.com/es | Neutros cálidos, bordes finos, etiquetas, contenido primero. | Logo, ilustraciones, textos, tipografía propietaria. |
| Anthropic | https://www.anthropic.com/ | Papel cálido, serif editorial, terracota, lectura pausada. | Logotipo, paleta exacta, ilustraciones, textos. |
| Our World in Data | https://ourworldindata.org/ | Datos primero, citas, gráficos con contexto. | Gráficos, paleta y textos concretos. |
| GOV.UK Design System | https://design-system.service.gov.uk/ | Lenguaje claro, contraste, formularios accesibles. | Identidad GOV.UK, corona, componentes literalmente copiados. |
| WCAG 2.2 | https://www.w3.org/TR/WCAG22/ | Criterios de accesibilidad y niveles AA. | — |

**Nota de uso.** Estas páginas son referencias públicas consultadas el 4/11/2026; no son clientes, socios ni demos de Paideia. No se ha creado ninguna web de demostración ni se ha atribuido a estas marcas una relación con el proyecto. Cualquier parecido debe quedarse en el principio de diseño (jerarquía, densidad, claridad, procedencia), no en la marca.

**Presupuesto.** Las tres direcciones se pueden implementar sin servicios de pago: fuentes del sistema u OFL autoalojadas, iconos SVG locales, ilustraciones propias y componentes CSS. No se ha llamado a ningún servicio de pago ni se han usado credenciales.
