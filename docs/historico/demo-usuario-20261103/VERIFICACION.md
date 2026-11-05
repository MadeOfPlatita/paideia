# PDF de la demo del usuario

Se observó que el botón Imprimir / guardar como PDF no produjo un guardado para Alejandro dentro del panel de vista previa de Hermes. Se verificó que la implementación llama window.print(), no una descarga de archivo. No se ha establecido técnicamente si el panel bloquea el diálogo o falta otro paso; no se declara arreglado el botón ni verificada impresión nativa.

Se recrearon en un navegador aislado únicamente los supuestos mostrados en la pantalla del usuario, sin tocar su estado:
- A:100€,2%,10años,50€/mes,compuesto,inflación1%.
- B:200€,3%,5años,100€/mes,compuesto,inflación1%.

La API local real devolvió los mismos saldos mostrados:6751.74 y6689.95; reales6112.26 y6365.26. Snapshot en escenarios-demo.json. El módulo existente preparó el informe, con window.print interceptado solo en la pestaña aislada. Page.printToPDF de Chromium generó Comparacion-escenarios-A-B.pdf; esto no prueba el diálogo de guardar del panel del usuario.

Verificación mediante PyMuPDF:2páginas, importes yplazos presentes,advertenciaHipótesis ymes120 presentes,menúCuadernode ruta ausente. Se rasterizaron yexaminaron las2páginas; tablaslegibles ysincolumnasrecortadas visibles. El PDF entregado contiene tablas ysupuestos, no gráficos, deacuerdoconelformatoexistente. No proveedoresreales,claves,perfil oPII transmitidos. Nocambios deproducción.

Pendiente: probar guardado desde navegador externo y, si se autoriza, ofrecer una salida de archivo que no dependa del diálogo del panel. La entrega del PDF aquí es una alternativa operativa, no una corrección de esa interacción.
