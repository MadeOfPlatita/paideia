# QA exploratoria: biblioteca, comparador y navegación

Sesión aislada `qa-user-library-mobile-165536`, aplicación local http://127.0.0.1:8765; escritorio 1440×900 y emulación móvil 390×844. Sin perfil, proveedor de IA, operaciones reales ni cambios de código. Es una exploración, no una validación exhaustiva.

## Hallazgos

### 1. Home móvil desborda horizontalmente — media, diseño/accesibilidad
- Pasos: abrir Inicio a 390×844 y desplazarse hasta los campos ficticios de contexto de la prueba de chat.
- Esperado: contenido legible dentro del viewport sin desplazamiento lateral involuntario.
- Real: `documentElement.clientWidth=390`, `scrollWidth=448`, `innerWidth=448`, `visualViewport.width=390`. Dos `span` visibles exceden el borde: `respuestas.objetivo...` llega a x=448.17 y `detalle_economico.importe_objetivo...` a x=430.11; ambos empiezan en x=83. La captura evidencia texto largo sobresaliente y recorte lateral. Se identifica el contenido desbordado, no se afirma una causa CSS sin análisis adicional.
- Captura: [home-desbordamiento.png](screenshots/home-desbordamiento.png). En biblioteca y diagnóstico móvil medidos: clientWidth=scrollWidth=390.
- Consola: no se dispone de una captura fiable de eventos de consola; no se afirma ausencia de errores.

### 2. La recarga reinicia selección y filtro sin advertencia clara — baja, UX
- Pasos: biblioteca → filtrar Depósito → seleccionar Depósito Tú+ y Depósito Open 6 meses → recargar la página.
- Esperado: si la selección es temporal, un aviso que explique que se pierde al recargar; alternativamente conservación si el producto así lo define.
- Real: filtro vuelve a todas las familias y selección pasa de 2/4 a 0/4. La página indica «La selección no cambia sin que pulses aquí», pero no aclara la excepción de recargar. No se ha establecido un requisito de persistencia: se señala la falta de claridad, no se exige guardar datos.
- Consola no registrada de forma verificable. El estado previo y posterior se recoge en `evidence.json`.

## Experiencias observadas
- Home dice que no hace falta completar perfil para explorar. Biblioteca y comparación se usaron sin perfil ni IA; «IA no conectada» se muestra en la interfaz. No se ha auditado tráfico de red ni persistencia completa.
- Biblioteca: 20 registros, avisos explícitos de candidatos internos no publicables, identidad separada de condiciones pendientes y ausencia de tasas/NAV. Detalle Cuenta Contigo distingue identidad, fuente, campos desconocidos y falta de condiciones validadas. No se abrió ninguna fuente externa.
- Filtro Depósito devolvió 4; búsqueda Pibank dentro de ese filtro devolvió 1 tras evento de entrada. Texto observado: «1 candidato devueltos» (discordancia menor de redacción). El primer intento mediante fill sin evento observable no filtró; se repitió con evento input, por lo que no se atribuye a la aplicación.
- Selección de 2 (cuenta y depósito), 4, y quitar: funciona; al llegar a 4 los botones restantes de añadir aparecen deshabilitados. La selección se mantiene al filtrar/navegar hasta recargar. No se ejecutó la comparación con 3 o 4 elementos.
- Comparación mixta de 2: metadatos en orden, sin ranking ni rendimiento inventado; se indica explícitamente que las familias tienen distinta naturaleza. Sin depósitos exclusivamente, el diagnóstico no se ofrece. Con dos depósitos se habilita; para ambos indica no elegibles y los motivos reales `FRESHNESS_POLICY_NOT_CONFIGURED` y `METRIC_MISSING`, sin ranking ni tasas. [Captura diagnóstico](screenshots/diagnostico-movil.png).
- Glosario y volver atrás por historial abren las vistas. En una ayuda contextual TAE, abrir y pulsar Escape oculta el panel, cambia `aria-expanded` a false y conserva foco en el botón. [Ayuda abierta](screenshots/ayuda-abierta.png). Los cuatro signos «?» en texto extraído son botones de ayuda etiquetados, no caracteres corruptos.
- Navegación móvil muestra ocho enlaces en dos filas; cajas medidas dentro de x=16–374. La lectura visual de fichas en móvil muestra fuentes y controles [captura](screenshots/biblioteca-movil.png). Se observó foco en H1 tras navegación de comparación; no se hizo auditoría completa de teclado/lector de pantalla.

## Límites
No se verificaron 3/4 candidatos en resultado, búsqueda vacía/sin coincidencias/límites de 100 caracteres, todas las fichas, todas las ayudas ni todas las rutas, PDF, enlaces externos, persistencia documentada en especificación, consola histórica ni lectores de pantalla. No se ejecutaron suites ni se probaron proveedores reales. Errores de selección de controles en automatización se corrigieron y no se atribuyen a la aplicación. La captura `detalle-ayudas.png` no es prueba del detalle: se conservó solo como registro de navegación y no sustenta un hallazgo.
