# Guardado real desde Hermes — verificación del coordinador

## Recorrido ejecutado
1. Se abrió la aplicación de prueba en el panel real de Hermes, en http://127.0.0.1:18881/#escenarios (servidor propio separado del servicio de demo8765).
2. Con los controles de esa página se introdujeron A:100€,2%,10años,50€/mes,compuesto,inflación1%; B:200€,3%,5años,100€/mes,compuesto,inflación1%. Se pulsaron ambos cálculos.
3. La lectura real del panel mostró ambos escenarios actualizados, horizonte10/5años y aviso de que los saldos corresponden a momentos distintos. Mostró asimismo «La impresión está desactivada en este panel. Descarga HTML y ábrelo en tu navegador para imprimir/guardar PDF». El inventario confirmó impresión deshabilitada y descarga habilitada.
4. Se pulsó el botón real Descargar informe(HTML) mediante drive_preview, sin sustituir window.print ni invocar Page.printToPDF.
5. computer_use capturó un diálogo nativo Guardar como de Windows, con origen blob:http://127.0.0.1:18881/ y nombre informe-comparacion.html. No era una captura simulada de un diálogo.
6. En el campo Nombre se estableció por UIA ValuePattern el archivo de prueba dentro del proyecto. Se invocó el botón Guardar. No hubo acceso a otras carpetas/documentos del usuario.
7. Se leyó del disco el archivo escrito por esa descarga y se comprobó su contenido. Ninguna herramienta write_file ni script de generación escribió ese HTML: procede del botón y del diálogo nativo.

## Archivo y contenido verificados
`informe-guardado-desde-Hermes.html`,5203bytes.
SHA256:11ff1ae2888af4047c8395a176a7ebc9d27eae654c6899de0e08a61c767ef907.

Texto y estructura:doctypeHTML, importes6751,74/6689,95 y reales6112,26/6365,26, plazos10/5años y advertenciaHipótesis presentes. Se abrió además el archivo real mediante file:// en navegador aislado:5tablas,0scripts,0recursos externos. `host-file-open.json` contiene la lectura, y `host-informe-abierto.png` una captura del archivo abierto.

## Límites y fallos de automatización conservados
Las primeras pulsaciones de Calcular con campos vacíos no calcularon; se rellenaron después los campos reales. Un Ctrl+A de computer_use por entrega Win32 no seleccionó el nombre y añadió una letra: se detectó en captura y no se guardó con ese nombre. Se usó UIA ValuePattern para sustituir el contenido íntegro; la captura confirmó la ruta correcta antes de guardar. No se repitió un Guardar ya confirmado.

El flujo nuevo guarda **HTML**, no un PDF automático. Abrirlo e imprimirlo como PDF en un navegador normal es un paso posterior; no se ha probado aún ese diálogo nativo de PDF. Tampoco se considera reparada la descarga del adjunto PDF del chat, que es una función de Hermes separada de la web.

La API desktop_preview.open reutilizó el identificador del navegador de preview al cambiar de8765a18881; por ello no se afirma que se creara una segunda pestaña web ni que la navegación conservara una comparación de sesión. Antes de cambiar, el panel leído mostraba ambos escenarios pendientes. No se modificó ni borró perfil persistente alguno; el archivo y los valores probados son ficticios. Mantener el servidor de demo8765 y cerrar el servidor de pruebas18881 al terminar.

La revisión independiente de los cambios sigue separada de esta prueba de host. La presencia del archivo demuestra esta descarga concreta, no seguridad universal ni éxito de cualquier diálogo.
