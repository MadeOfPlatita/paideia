# B9 — robustez y accesibilidad funcional: evidencia

Corrección de los trece defectos del diagnóstico (`DIAGNOSTICO.md`) sin rediseño: mismos colores, mismas rutas, misma jerarquía visual. Solo cambian comportamiento, foco, anuncios y un ajuste de ajuste de texto en el stepper.

## Qué se corrigió

- **Skip-link real.** `preventDefault` y foco en `#main-content` sin cambiar de ruta; los hashes desconocidos ya no reescriben la página; el render inicial no roba el foco al `h1`, así que el primer Tab llega al enlace y a la cabecera.
- **Timeout de red.** `AbortController` de 12 s que produce `LOCAL_TIMEOUT` reintentable, con limpieza del temporizador también durante la lectura del cuerpo.
- **Foco tras acciones asíncronas.** Helpers `captureFocus`/`restoreFocus` y `focusResultsRegion`: reintentar no deja el foco en `BODY` en biblioteca, ficha, comparador, escenarios ni catálogo del ensayo; el refresco de condiciones no lo roba y el botón que se deshabilita al calcular cede el foco a la región de resultado antes de desaparecer.
- **Anuncios.** Región persistente `#app-status` con `role=status` y `aria-live=polite` para carga y resultado, con texto corto; nunca listas largas. La región viva del informe no se reescribe si el texto no cambia.
- **Formularios.** `aria-invalid` y `aria-describedby` en los campos con error y foco en el primero inválido, replicando el patrón que ya tenía la búsqueda. Los formularios de escenarios y del importe del ensayo usan `novalidate` para que el envío vacío llegue al mismo patrón en vez de quedarse en la burbuja nativa.
- **Stepper a 320 px y 200 %.** Guiones suaves en las etiquetas largas (el navegador no trae diccionario de partición en español) y `overflow-wrap: anywhere` como red: la palabra se parte con guion y no queda una letra huérfana. La topbar envuelve y la nav permite reflujo, de modo que a 320 px + 200 % la página no gana scroll horizontal por esos dos bloques.
- **Tabla de escenarios.** Sin `aria-live` en la tabla; región corta que solo cambia con el estado, para no reanunciar la tabla entera al teclear.
- **Menores.** Foco al disparador en las confirmaciones en línea, reintento explícito en el error de escenarios con el envío bloqueado mientras calcula, `h2` en los resultados de biblioteca, chip de estado refrescado tras un éxito de API y recuperado con un único reintento automático cuando `/api/status` falla después de que el catálogo ya cargó, y guardia contra envíos duplicados en el comparador.

## Ciclo 2 (revisión independiente)

La revisión de B9 detectó tres bloqueantes y tres menores. Se corrigieron sin rediseño:

- **D1.** `buildScenarioOutput` y `renderSimulationCandidates` conservan el foco si estaba dentro del contenedor que se reemplaza: lo restauran en `#scenario-output` (`tabindex=-1`), en el botón de reintento si vuelve a fallar o en `#simulation-product` cuando reaparece.
- **D2.** Un éxito de API durante una comprobación de estado en vuelo habilita un único reintento automático de `/api/status` a los 1,5 s si esa comprobación falla; si el reintento también falla, no se repite.
- **D3.** `novalidate` en escenarios e importe del ensayo: el envío vacío ejecuta la validación propia y marca `aria-invalid`/`aria-describedby` con mensaje inline y foco.
- **D4.** Guiones suaves en las etiquetas del stepper y reflujo de topbar/nav: desaparece el scroll de 3 px a 320 px + 200 %.
- **D5.** `setText` en `comparison_report.js`: la región `role=status` del informe solo muta si el texto cambia.
- **D6.** Antes de `submitButton.disabled = true`, si el botón tiene el foco se mueve a `#scenario-output`.

## Verificación

- `node tests/b9_accessibility.test.cjs`: **32/32** (24 originales + B9-3c, 3d, 5d, 5e, 6c, 7b, 9c y 11b). Con la copia previa del ciclo 2, esas ocho comprobaciones fallan: D1 deja `BODY`, D2 no recupera, D3 no llega a marcar el campo, D4 desborda 334 px, D5 produce 5 mutaciones y D6 deja `BODY`.
- `node tests/b8_privacy_regression.test.cjs`: **28/28** (privacidad intacta).
- `node tests/b1_history_consent.test.cjs`: **59/59** (+2 observaciones).
- `python -m pytest tests -q`: **544 pruebas OK**, 453 subtests.
- `node tests/*.test.cjs` en `app`: 63 comprobaciones, 0 fallos.
- `diff -rq` entre `app/static` y `api/_static`: sin diferencias; `app.js`, `index.html`, `styles.css` y `comparison_report.js` idénticos por `cmp` y sha256.

## Efectos colaterales corregidos en pruebas

Al aceptar la puerta de envío de B8, dos pruebas heredadas construían la interfaz sin un estado de IA concluyente y dejaban de ejercitar el chat. Se actualizaron sus arneses (no la app) para declarar un proveedor configurado: `chat_frontend_contract.test.cjs` pasa de 1 a 8 comprobaciones y `b4_chat_provenance.test.cjs` de 0 a 6. Así la suite vuelve a probar lo que dice probar.

## Límites

Emulación de viewport por CDP, no dispositivo físico. El 200 % se aproxima con ventana reducida y con `font-size: 32px`. A 320 px y 200 % a la vez las etiquetas se parten en dos a cuatro líneas, con legibilidad limitada. La revisión final midió en escritorio con scrollbar clásica `clientWidth=305` y `scrollWidth=320`: persisten 15 px de desplazamiento horizontal por el mínimo preexistente; en emulación móvil la medición fue 320/320. Sin lector de pantalla real, táctil, Safari, Firefox ni alto contraste del sistema. Revisión independiente favorable para el alcance local en `REVISION-CICLO-2.md`; no equivale a certificación de accesibilidad general.
