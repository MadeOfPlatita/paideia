# QA exploratoria: informe y guardado

**Resultado: exportación NO COMPROBADA; no es un PASS.** Sesión de navegador `qa-user-export-165536`, demo existente `http://127.0.0.1:8765/#escenarios`, datos sintéticos. No se sustituyó `window.print`, no se llamó a `Page.printToPDF`, no se tocó el preview del usuario y no se creó PDF.

## Recorrido y evidencia

1. Con controles visibles se introdujo A: 100 €, 2 %, 10 años, 50 €/mes, compuesto, inflación 1 %; B: 200 €, 3 %, 5 años, 100 €/mes, compuesto, inflación 1 %. Se pulsó Calcular A y B. El informe quedó habilitado; tabla visible: A aportado 6.100,00 €, nominal 6.751,74 €, real 6.112,26 €; B 6.200,00 €, 6.689,95 €, 6.365,26 €.
2. Se pulsó el botón real **Imprimir / guardar como PDF**. Observado `beforeprint`; el DOM preparado contenía los dos escenarios, tabla y evolución. `matchMedia('print')` era false durante el evento y a los 3 segundos; no se observó `afterprint` ni target con «print». La captura de la página quedó igual, con estado «Ambos escenarios están actualizados. El informe se captura al imprimir». La captura de página no muestra ni descarta un diálogo nativo fuera de ella; el protocolo de automatización utilizado no permitió operarlo o verificarlo. No se verificó archivo descargado o guardado.
3. Se editó A de 100 a 101: botón deshabilitado, mensaje «Escenario A tiene cambios sin calcular. Ambos deben estar actualizados.» y DOM preparado vaciado. Tras recalcular A, botón habilitado y mensaje de actualizado. En un segundo clic no se observó otro evento `beforeprint` en los 3 segundos siguientes; DOM preparado presente, `matchMedia('print')` false y mismo mensaje. No se sabe si el primer diálogo quedó pendiente o si el entorno suprimió la segunda solicitud.
4. Capturas: [tras pulsar](screenshots/01-tras-pulsar.png), [bloqueo por edición](screenshots/02-editado-bloqueado.png), [tras recálculo](screenshots/03-recalculado.png), [reintento](screenshots/04-reintento.png). Los eventos y texto del DOM están en [evidence.json](evidence.json). Se activaron Runtime y Log CDP, pero no se obtuvo un buffer histórico de consola; **ausencia de errores no comprobada**.

## Hallazgo 1 — Guardado no observable, sin orientación tras la pulsación

- **Clasificación:** observado el estado sin orientación; desenlace y causa del fallo de guardado **inconclusos**. Severidad UX **media** en este entorno; impacto en el host del usuario aún por confirmar.
- **Pasos:** completar y calcular A y B como arriba; pulsar Imprimir / guardar como PDF; esperar; reintentar tras editar y recalcular.
- **Esperado:** que el usuario pueda acceder al diálogo de impresión/guardar como PDF y completar el guardado, o reciba orientación útil cuando el host no permita abrirlo. Cancelar no debería confundirse con éxito.
- **Actual:** se preparó informe y ocurrió `beforeprint`, pero no pudimos observar ni manejar diálogo ni comprobar archivo; el estado visible no informa sobre la situación. No se pudo provocar ni verificar una cancelación real: no se afirma que la aplicación no informe tras cancelar en un navegador normal. El segundo clic no generó otro `beforeprint` observable.
- **Causa probada:** el código `static/comparison_report.js:66–72` monta el informe y llama a `root.print()`; no genera ni descarga por sí mismo un archivo PDF. `afterprint` limpia el DOM (línea 79); en esta sesión no llegó evento observable. CSS `comparison_report.css:4–9` oculta el informe en pantalla y lo presenta bajo `@media print`. Esto explica el diseño del flujo, **no prueba por qué falló el host ni si el diálogo se abrió fuera de la captura**.
- **Recomendación mínima:** comprobar manualmente en navegador completo y en el preview de Hermes con la misma acción; documentar que es impresión del navegador y dónde seleccionar «Guardar como PDF». Si el host no expone impresión, ofrecer indicación de abrir la app en un navegador compatible. No afirmar éxito de guardado basándose solo en `afterprint`, que tampoco distingue guardar de cancelar.

## Comparación con la incidencia comunicada de Hermes

El usuario comunica que no consigue guardar desde el botón ni descargar un PDF adjunto en Hermes. Esta sesión no inspeccionó ni modificó su preview ni comprobó la descarga del adjunto. Un informe DOM preparado y `beforeprint` **no prueban** apertura de diálogo, PDF guardado, ni funcionamiento del adjunto de Hermes. La descarga de un adjunto es un flujo distinto a `window.print()`; no hay evidencia para atribuir ambos síntomas a una misma causa, ni para absolver o culpar a la aplicación o al host.

## Fuera de alcance / límites

Sin pruebas automáticas existentes, Page.printToPDF, proveedor externo, perfil real, base de datos, cambios de código ni servidor nuevo. No se verificó diálogo nativo, cancelación, descarga, archivo físico ni consola completa. Datos y capturas únicamente sintéticos; el servidor compartido permanece en ejecución.
