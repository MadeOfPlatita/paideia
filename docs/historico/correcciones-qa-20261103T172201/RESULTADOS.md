# Cierre de las correcciones QA autorizadas

Cierre documentado:3/11/2026, tras recibir y contrastar el dictamen independiente a las17:48+01:00. **Alcance local aprobado**, no aprobación global de Paideia ni de Pai.

## Resultado utilizable
- **Conservar el informe:** botón Descargar informe(HTML) desde dos escenarios actualizados. Archivo autónomo con supuestos, saldos, diferencias, tablas y advertencias; sin perfil, scripts ni recursos externos. Edición, pendiente, error y navegación bloquean la exportación obsoleta. Los fallos transitorios permiten reintentar.
- **Host real:** clic de descarga en Hermes → diálogo Guardar como nativo → archivo real en disco → lectura y apertura file://. `informe-guardado-desde-Hermes.html`,5203bytes,SHA25611ff1ae2888af4047c8395a176a7ebc9d27eae654c6899de0e08a61c767ef907. El revisor leyó independientemente ese mismo archivo y confirmó hash/importes; no repitió la interacción nativa. Evidencia detallada:`HOST-GUARDADO.md`,`.json`, `host-file-open.json`, `host-informe-abierto.png`.
- **Inicio móvil:** las cadenas largas se ajustan sin ocultarse.390px de ancho y390px de contenido, frente a448px antes.
- **Comparación:** muestra horizontes A/B y avisa cuando los saldos corresponden a momentos diferentes. Editar A conserva B y retira los importes obsoletos de A.
- **Biblioteca:** explica que selección y filtros son temporales y se pierden al recargar; no añade persistencia.

## Verificación y dictamen
`revision/REVISION-INDEPENDIENTE.json`:passed=true; listas security_concerns,logic_errors,verification_blockers vacías. Fuentes no editadas por el revisor. `revision/evidence.json` conserva los resultados por comprobación; el coordinador volvió a contarlos y contrastarlos con el dictamen y el hash real, sin errores.

| Ejecución independiente | Comprobaciones correctas |
|---|---:|
| qa_layout_browser.js |5|
| c_integration_browser.js |27|
| scenario_browser.js |114|
| report_browser.js |18|
| report_download_browser.js |14|
| Probes propios de exportación |5|

Los cinco scripts suman178comprobaciones, separadas de5probes propios. Node:`node --test tests/*.test.cjs tests/report_unit.js`,41/41 sin fallos; Node cuenta report_unit como archivo con aserciones internas, no41casos nuevos de informe. No se repitió Python no modificado. Las evidencias RED/GREEN originales se conservan en layout/ y exportacion/.

El revisor descargó además un HTML real en su navegador aislado, `revision/informe-comparacion.html`; tras sucesivas pruebas quedó la última versión de ese archivo, no una copia inmutable de cada descarga. La prueba de revocación ejecutó manualmente el callback previsto para60000ms; no acredita una espera de60segundos reales.

## Runtime y límites
Servidor propio18881 detenido y puerto sin listener; demo8765 responde con IA desconectada. Pestaña de prueba18881 cerrada; informe real abierto en preview. No hubo nuevas llamadas a proveedores, instalaciones, pagos, bases de datos, despliegue ni commits. No se cambiaron fórmulas ni se añadió persistencia.

Se guardó **HTML**, no PDF automático. No se verificó impresión nativa ni creación de PDF mediante su diálogo. La descarga del adjunto del chat sigue siendo un recorrido distinto y no se declara arreglada. La API preview.open reutilizó la pestaña web al abrir la prueba: no se afirma que se conservaran estados de navegación entre8765y18881; antes del cambio se habían observado ambos escenarios pendientes. Valores ficticios y límites detallados en HOST-GUARDADO.md.

## Guion de uso y siguiente paso
1. Entrar en la demo http://127.0.0.1:8765/#escenarios; introducir dos escenarios ficticios y calcular ambos.
2. Leer los horizontes y el aviso si difieren; editar uno para comprobar que requiere recalcular sin borrar el otro.
3. Pulsar Descargar informe(HTML), elegir ubicación en Guardar como y comprobar el archivo. La aplicación dice descarga solicitada, no promete guardado antes de confirmarlo.
4. Abrir el HTML guardado en un navegador normal. Si se necesita PDF, intentar allí Imprimir/Guardar como PDF: paso todavía no certificado en este cierre.

No continúa automáticamente el backlog de producto. Próximo paso propuesto:priorizar una mejora pequeña del recorrido a partir de `docs/comparativa-producto-20261103/COMPARATIVA.md`, en un encargo separado. Pai conserva su plan y permanece desconectado. El equipo no tiene que intervenir para cerrar estas correcciones; sí elegir/autorizar el siguiente bloque antes de construirlo.
