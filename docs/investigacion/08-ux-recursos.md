# Paideia — referencias UX/UI y recursos visuales open source

**Investigación documental, España · consulta: 26/10/2026**  
**Límites:** no se ha construido ni ejecutado un prototipo; no se instalaron paquetes ni se consultaron servicios financieros externos. Se leyeron páginas primarias públicas de comparadores, entidades, educación financiera, documentación y licencias. Las páginas comerciales pueden cambiar; no se reutilizan sus tipos, tarifas, datos de mercado, textos de marca ni assets.

## Decisión resumida

Diseñar Paideia como un **mapa visual para aprender haciendo**, no como un banco ni un asesor automatizado: Pai hace de guía discreta; el perfil es breve, omitible y editable; las comparaciones ponen liquidez, plazo, riesgo y costes al mismo nivel que la rentabilidad; los gráficos responden a supuestos visibles; y el último paso es una **simulación ficticia** que nunca parece una contratación real. Todo producto, cifra y escenario de la demo debe ser sintético y rotulado como tal.[2][6][24]

## 1. Referencias financieras: qué tomar y qué no

| Referencia examinada | Evidencia de la página primaria | Patrón útil para Paideia / límite |
|---|---|---|
| **Raisin — comparación de ahorro** | Presenta depósitos y cuentas en tabla con campos como importe, país, tipo, plazo y banco; acompaña la selección con información del producto. La página explica el recorrido “compara, elige, transfiere”.[1] | Reutilizar la **lectura en paralelo** y el acceso a detalle; ordenar los datos para que una persona novata pueda comparar disponibilidad, plazo, condiciones y riesgo, no solo el interés. No imitar el look, los nombres, las tarifas o el CTA comercial “Contratar”. |
| **Indexa Capital — cuestionario de inversión** | El cuestionario público marca el paso y el total (“1 de 15 preguntas”), permite salir y continuar más tarde y ofrece “¿Por qué preguntamos?”.[2] | Buenas señales de progreso, explicación contextual y recuperación; quince preguntas son demasiadas para esta demo. Paideia debería usar cuatro preguntas cortas, permitir “No lo sé” y “Omitir”, y enseñar un resumen editable antes de comparar. No convertirlo en test de idoneidad ni en recomendación. |
| **inbestMe — recorrido típico de roboadvisor** | Su guía describe tres pasos: test de objetivos/situación/conocimientos, perfil y cartera, y apertura de cuenta.[3] | Tomar la secuencia como referencia de arquitectura, pero **separar aprendizaje de contratación**. Paideia termina en una elección ensayada, no abre cuenta ni asigna una cartera real. |
| **MyInvestor — niveles de riesgo y simulador** | La página de carteras describe cinco niveles y un test; la ficha Indie muestra aportación inicial y mensual, horizonte, tres escenarios, aportación acumulada y una advertencia de que las rentabilidades futuras no están garantizadas.[4][24] | Es la referencia más cercana para “muevo un supuesto y veo cambiar el resultado”. Copiar el patrón de controles sincronizados y la advertencia, no el gráfico, la metodología histórica, los datos ni la identidad visual. En Paideia las curvas serán **supuestos didácticos ficticios**, no pronósticos. |
| **Finizens — centro de ayuda** | El centro agrupa contenido por composición, apertura, seguridad, aportaciones, comisiones, política de inversión y posibilidad de cambiar perfil/cartera.[5] | Llevar riesgos, costes, retirada, plazo y “qué significa” junto al comparador, con detalle desplegable y glosario; no esconderlos en un FAQ final. Es una referencia de arquitectura de ayuda, no una inspección del cuestionario de alta. |
| **CNMV — decisiones de inversión** | La CNMV enfoca la decisión desde objetivo, plazo y riesgo.[6] | Empezar por la meta de la persona y explicar el concepto que necesita en ese momento; no dar una recomendación personalizada. |
| **Finanzas para Todos — educación** | La CNMV presenta el portal para niveles de conocimiento distintos.[7] Finanzas para Todos ofrece guías y herramientas interactivas, además de herramientas de presupuesto y planificación.[8][9] | Mantener “qué estoy suponiendo” y “qué no significa” a un clic; no dar una recomendación personalizada. |

**Lectura transversal:** los productos financieros reales suelen llevar la interfaz hacia test → selección → apertura.[3][4]  
Para Paideia conviene conservar la claridad del recorrido pero invertir el objetivo: que la persona termine pudiendo explicar por qué cambia un resultado cuando modifica plazo, liquidez o aportación.[2][6][24]  
La pantalla de perfil debe llamarse **“tu mapa para explorar”**, no “tu perfil inversor”.[2][6]

## 2. Dirección visual original para Pai

### Concepto: “cuaderno de ruta financiera”

Una interfaz editorial, cálida y contemporánea: tinta oscura sobre papel claro, títulos cortos, una retícula limpia y pequeños marcadores de ruta que señalan **objetivo → comparación → escenario → simulación**. Evitar el cliché de neobanco (neón, degradados, brillos, tarjetas flotantes sin jerarquía) y el tono escolar infantil.[7][21]

- **Pai:** crear un SVG original con una silueta triangular simple, un pliegue/flecha interior y una expresión mínima. Sin cuerpo, mejillas, ojos sobredimensionados, voz infantil ni poses de mascota de app. Funciona como guía en una explicación breve, un estado vacío o un aviso; no como avatar que interrumpe cada pantalla. El triángulo de marca debe ser propio, no una copia de un icono existente.
- **Paleta propuesta:** papel `#F7F5EF`; superficie `#FFFFFF`; tinta `#18272D`; texto secundario `#4F5E62`; azul `#3157B7`; terracota `#B74734`; salvia decorativa `#DDE9E2`. Cálculo preliminar de contraste de texto sobre papel: tinta **14,09:1**, secundario **6,19:1**, azul **6,06:1**, terracota **4,86:1**.[21] Las cuatro parejas superan 4,5:1; volver a probar estados hover/foco, componentes y textos sobre cada superficie antes de fijar tokens.[21]
- **Tipografía y datos:** sistema sans-serif (`system-ui`, sin descargar fuentes en la demo); titulares de tono editorial; números alineados con cifras tabulares. Formatear euros y decimales en español. Usar etiquetas de texto —“posible pérdida”, “disponible”, “plazo”— además del color.[11]
- **Componentes:** tarjetas blancas con borde visible y radio discreto; chips para tipo de producto; una acción principal por pantalla; explicación bajo demanda (“¿Qué significa?”).[1][5] Nada de modales de bienvenida repetidos.
- **Voz de Pai:** directa y adulta: “No hace falta saber de finanzas”; “Esto es un supuesto, no una promesa”; “Puedes omitirlo y seguir”. Evitar “Pai te recomienda invertir”.[7][8]
- **Assets:** dibujar a Pai y los gráficos desde cero. Para iconos funcionales, Lucide React puede ahorrar tiempo, pero el logotipo y la mascota se trazan aparte; respetar los avisos de licencia aplicables a los iconos elegidos.[15][16]

## 3. Recorrido demo potente (10 minutos)

**Aviso persistente desde la portada:** `SIMULACIÓN EDUCATIVA · Datos y productos ficticios. No se mueve dinero, no se contrata y no se envían datos.` En el encabezado de cada pantalla y del PDF debe seguir visible, no relegado a un pie legal.[24]

| Tiempo | Momento | Interacción y mensaje |
|---|---|---|
| **0:00–0:45** | Entrada | Pai presenta una meta de ejemplo y el botón **“Explorar la demo”**. Se puede empezar sin registro; indicar que las respuestas de ejemplo se pueden borrar. |
| **0:45–2:30** | Perfil conversacional | Una pregunta por pantalla: (1) ¿qué quieres entender/alcanzar?, (2) ¿cuándo podrías necesitar el dinero?, (3) ¿cuánto valoras poder retirarlo?, (4) ¿qué te gustaría aprender del riesgo? Cada pregunta tiene “No lo sé”, “Omitir” y “¿Por qué lo preguntamos?”. Sin DNI, teléfono, cuenta bancaria ni importe patrimonial obligatorio. |
| **2:30–3:00** | Resumen editable | Mostrar objetivo, plazo y liquidez como tarjetas editables, y lo omitido como “sin respuesta”. Aclarar: **“Esto organiza la demo, no calcula idoneidad ni es asesoramiento.”** El enfoque de objetivo/plazo/riesgo es coherente con la guía educativa de la CNMV.[6] |
| **3:00–5:00** | Comparador | Mostrar cinco familias didácticas —cuenta, depósito, deuda pública, fondo y ETF—; permitir comparar 2–3 ejemplos ficticios a la vez. Columnas: liquidez, plazo, qué puede variar, costes, posibilidad de pérdida/garantía y supuestos usados. No ordenar solo por rentabilidad ni destacar un “ganador”. |
| **5:00–7:30** | Laboratorio de escenarios | Cambiar con slider/texto **aportación inicial**, **aportación mensual** y **horizonte**; actualizar a la vez capital aportado y tres resultados hipotéticos etiquetados bajo/central/alto. Pai explica una diferencia concreta; las cifras quedan junto al gráfico y en tabla. MyInvestor publica un simulador comparable con aportación inicial/mensual y escenarios, acompañado de un aviso de no garantía; Paideia debe usar solo la mecánica de exploración, no sus datos ni metodología.[24] |
| **7:30–9:00** | Contratación ficticia | CTA exacto: **“Ensayar los pasos de una contratación ficticia”**. Tres pantallas cortas: resumen del producto inventado → explicación de coste/riesgo → cierre. En cada paso, aviso “solo ensayo”. No pedir datos personales, no abrir enlaces comerciales ni usar botones “Firmar”, “Invertir” o “Contratar”. Final: **“Has terminado el recorrido. No se ha abierto nada ni movido dinero.”** |
| **9:00–10:00** | Recapitulación | Exportar/imprimir una hoja con respuestas elegidas, supuestos y gráficos; botón **“Borrar mi perfil local”** y volver a empezar. No incluir respuestas personales en el PDF sin una selección explícita. |

**Datos y privacidad del MVP:** sin login, backend financiero ni feed de ofertas; perfil local y borrable; dataset sintético versionado. Mostrar la fecha de revisión del dataset, no fingir cotizaciones actuales.[24] La demo debe presentar el perfil como herramienta de aprendizaje, no como evaluación regulatoria.[6][7]

## 4. Accesibilidad y responsive

- Formularios con etiquetas visibles y asociadas al control; no usar el placeholder como única etiqueta. Dar una instrucción breve y un estado de error comprensible.[22]
- Cumplir al menos WCAG 2.2 AA para texto: contraste mínimo 4,5:1 salvo las excepciones previstas. La propuesta cromática es un punto de partida calculado, no una auditoría completa.[21]
- WCAG fija 24 × 24 CSS px como mínimo para objetivos de puntero con excepciones; para las acciones principales de móvil, apuntar a 44 px de alto y separarlas más.[23]
- Todo el flujo funciona con teclado: orden de foco, foco visible, “Omitir”, editar y borrar; nada de avance automático. En móvil, una pregunta por vista, controles grandes, etiquetas encima de campos y sin scroll horizontal. En escritorio, comparador en columnas y controles al lado del gráfico; en móvil se apilan y se conserva la tabla de valores.[22][23]
- No depender solo del color: diferenciar escenarios con nombre, patrón de línea y etiqueta directa. Cada gráfico debe tener título, ejes/unidades, una frase resumen y una tabla equivalente; Chart.js usa `canvas`, cuyo contenido no llega por sí solo a lectores de pantalla.[11]
- Si se usa Motion, respetar `prefers-reduced-motion`; limitar la animación a transiciones breves de opacidad y desactivar desplazamientos/parallax cuando la persona lo solicite.[17][18]

## 5. Recursos concretos y licencias verificadas

| Recurso | Licencia observada | Encaje en una semana | Decisión recomendada |
|---|---|---|---|
| **Chart.js** (gráficos) | MIT.[10] | Arranque sencillo para línea/área de escenarios; hace resize desde un contenedor dedicado.[12] | Primera opción si el futuro frontend necesita una sola curva interactiva. Añadir tabla y resumen accesibles; `canvas` no sustituye el equivalente textual.[11] |
| **Apache ECharts** (alternativa de gráficos) | Apache-2.0; el repositorio advierte que hay subcomponentes con avisos/licencias separados.[14][25] | Más opciones de interacción y render SVG/Canvas; la página oficial describe optimización móvil y generación automática de descripciones de accesibilidad.[13] | Alternativa si el gráfico interactivo se vuelve el centro del producto; para una demo de una semana, Chart.js más tabla es más acotado. Revisar `NOTICE` y dependencias al adoptar ECharts. |
| **Lucide React** (iconos) | ISC; la licencia identifica un subconjunto derivado de Feather con aviso MIT.[15][16] | Iconos SVG de interfaz con trazo coherente; no es una biblioteca de mascotas/ilustraciones. | Usar solo iconos necesarios y conservar las licencias/avisos de la versión fijada. Dibujar el Pai original fuera de la librería. |
| **Motion for React** (animación) | MIT; su guía ofrece `reducedMotion="user"` y `useReducedMotion`.[17][18] | Útil para un cambio de pantalla sutil y respetuoso; añade dependencia si no hay ya React. | No instalar para la investigación. En la demo, priorizar CSS y `prefers-reduced-motion`; Motion solo si el stack futuro ya lo usa. |
| **`window.print()`** (PDF básico) | Función nativa del navegador; sin dependencia de terceros. | CSS de impresión para una hoja A4 de escenarios/decisiones. | Primera opción: menos riesgo y alcance claro para una semana; probar saltos de página, gráficos y tildes. |
| **jsPDF** (PDF programático) | MIT; su repositorio lo describe como biblioteca JavaScript para generar PDF.[19] | Adecuado para dibujar un documento sencillo desde datos; exige controlar maquetación y fuentes. | Alternativa para exportación client-side muy acotada; no convertir el gráfico en una captura ilegible. |
| **`@react-pdf/renderer`** (PDF basado en componentes) | MIT; genera PDF en navegador y servidor.[20] | Permite una plantilla de documento en React, pero añade diseño y pruebas de otra salida. | Elegirlo solo si un PDF de marca bien maquetado es requisito del MVP; si no, CSS de impresión. |

**Licencias y assets:** el estado anterior se comprobó en documentación/repositorios oficiales el 26/10/2026; las ramas `main/master` pueden cambiar.[10][14][18]  
Antes de programar, fijar versiones y revisar su `LICENSE`/`NOTICE` y dependencias transitivas.[15][16][25]  
“Open source” no convierte automáticamente en reutilizables los logos, capturas, ilustraciones o textos comerciales de Raisin, Indexa, Finizens, MyInvestor o CNMV. No copiar esos assets.

## 6. Alcance realizable en una semana (recomendación, no implementación)

1. **Día 1:** definir el guion de diez minutos, textos de seguridad y dataset didáctico estático para las cinco familias; aprobar campos de comparación.[6][8][24]
2. **Día 2:** cerrar paleta/tipografía y dibujar el Pai original; montar navegación responsive y aviso de demo.[15][16][21]
3. **Día 3:** implementar el flujo conversacional de cuatro preguntas, saltar/“no sé”, resumen editable y borrado local.[2][22][23]
4. **Día 4:** comparador con 2–3 productos de ejemplo y detalle de liquidez, plazo, coste y riesgo.[1][5][6]
5. **Día 5:** inputs de escenarios, cálculo determinista con supuestos visibles, gráfico + tabla accesible.[10][11][24]
6. **Día 6:** recorrido ficticio de tres pasos, hoja de impresión, teclado/contraste/reduced-motion y revisión móvil.[17][18][19]
7. **Día 7:** probar el guion con personas adultas sin conocimientos financieros, corregir confusiones y preparar el recorrido para hasta 100 personas con datos locales/sintéticos. No instrumentar respuestas personales.[7][8]

**Criterio de cierre:** alguien puede omitir el perfil, comparar dos productos, cambiar un supuesto, explicar que los resultados son hipotéticos y terminar el ensayo sin creer que contrató algo.[2][6][24] Si falla cualquiera de esas cinco comprobaciones, reducir decoración y añadir explicación antes de añadir funciones.

## Alcance y límites de la verificación

La comparación se basa en texto extraído y DOM público, no en una auditoría visual de píxeles ni responsive; no se recorrieron altas, no se enviaron datos y no se accionaron los sliders. La herramienta MyInvestor se pudo leer en su ficha, pero el navegador devolvió 403 y no se verificó el cálculo en vivo. Finizens mostró una comprobación anti-bot en navegador y Finanzas para Todos bloqueó la navegación directa; sus páginas primarias sí se leyeron mediante extracción textual. En “Mi presupuesto” el extractor devolvió variables de plantilla (`{{…}}`) y una descripción poco coherente con el título, por lo que solo se toma como referencia de etiquetas/periodicidad, no como validación del significado de la herramienta.[9]

## Sources

[1] https://www.raisin.es/productos — Productos de ahorro: depósitos y cuentas | Raisin
[2] https://indexacapital.com/es/esp/questions/funds — Conoce tu perfil inversor | Indexa Capital
[3] https://www.inbestme.com/es/es/nosotros/robo-advisor — Guía informativa sobre Robo Advisors | inbestMe
[4] https://myinvestor.es/inversion/carteras-automatizadas/myinvestor — Carteras indexadas MyInvestor
[5] https://ayuda.finizens.com/hc/es/categories/4409325814289-Plan-de-Inversi%C3%B3n — Plan de Inversión | Finizens
[6] https://cnmv.es/portal/inversor/decisiones-inversion?lang=es — Cómo tomar decisiones de inversión | CNMV
[7] https://cnmv.es/portal/inversor/plan-educacion?lang=es — Plan de Educación Financiera | CNMV
[8] https://www.finanzasparatodos.es/gestiona-tus-finanzas-personales-con-las-herramientas-gratuitas-de-finanzas-para-todos — Herramientas gratuitas para gestionar finanzas | Finanzas para Todos
[9] https://www.finanzasparatodos.es/herramientas/mipresupuesto — Mi presupuesto | Finanzas para Todos
[10] https://www.chartjs.org/docs/latest — Chart.js
[11] https://www.chartjs.org/docs/latest/general/accessibility.html — Accessibility | Chart.js
[12] https://www.chartjs.org/docs/latest/configuration/responsive.html — Responsive Charts | Chart.js
[13] https://echarts.apache.org/en/feature.html — Features | Apache ECharts
[14] https://github.com/apache/echarts/blob/master/package.json — echarts package.json
[15] https://github.com/lucide-icons/lucide/blob/main/LICENSE — Lucide LICENSE
[16] https://github.com/lucide-icons/lucide/blob/main/packages/lucide-react/README.md — Lucide React README
[17] https://motion.dev/docs/react-accessibility — Create accessible animations in React | Motion
[18] https://github.com/motiondivision/motion/blob/main/LICENSE.md — Motion LICENSE
[19] https://github.com/parallax/jsPDF — jsPDF repository and documentation
[20] https://github.com/diegomura/react-pdf — React PDF repository and documentation
[21] https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — Understanding Contrast Minimum | WAI
[22] https://www.w3.org/WAI/tutorials/forms/labels — Labeling Controls | WAI
[23] https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html — Understanding Target Size Minimum | WAI
[24] https://myinvestor.es/inversion/carteras-automatizadas/myinvestor/indie — Cartera Indie | MyInvestor
[25] https://github.com/apache/echarts/blob/master/LICENSE — ECharts LICENSE
