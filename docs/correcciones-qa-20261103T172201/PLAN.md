# Correcciones autorizadas tras QA de usuarios

Inicio:03/11/2026 17:22:01+01:00. Alejandro autoriza corregir los puntos de INFORME-QA.md, sin rediseño general. Solo proyecto App Financiera y perfil trabajos. No se instala ni despliega nada, no se usan proveedores reales de la app, claves, datos personales, Tk, pagos, DB o commits.

## Causa descubierta y alcance de exportación
Lectura de la fuente instalada de Hermes (sin modificarla): apps/desktop/src/app/chat/right-rail/preview-pane.tsx:216–219 define __hermesPrintGuard y reemplaza window.print por una advertencia de impresión desactivada en el panel. No desactivar la protección ni arreglar Hermes fuera de ámbito. La captura exacta del flag en el panel del usuario y la interacción de descarga quedan pendientes de prueba.

Solución mínima: descargar un informe HTML autónomo con el contenido validado existente; mantener impresión/PDF nativo por separado y explicar la limitación del panel. No llamar PDF a un HTML ni afirmar descarga/guardado por haber generado un Blob. Verificar un archivo real desde el entorno del usuario o declarar el paso pendiente; los adjuntos de Hermes son otro flujo. No añadir backend que guarde entradas arbitrarias ni dependencias PDF.

## Propiedad de archivos
Delegación deleg_cbff4867, dos workers:
- Layout/claridad: static/app.js, static/styles.css y nuevo tests/qa_layout_browser.js; evidencia layout/. Ajuste acotado de cadenas largas en Inicio, horizonte/aviso en resumen, aclaración temporal de filtros/selección sin persistencia nueva.
- Exportación: static/comparison_report.js y su CSS si es necesario, tests/report_unit.js y nuevo tests/report_download_browser.js; evidencia exportacion/. Descarga HTML, mensajes para impresión bloqueada, versiones/whitelist y reintento seguros. No tocar app.js ni styles.css.

Ambos deben observar RED antes de modificar producción, luego GREEN. Preservar datos y resultados del otro escenario, límites de búsqueda, diagnóstico y privacidad. No arreglar ESC-02, convención Intl es-ES estándar descartada como defecto.

## Coordinación y aceptación
El coordinador verificará los archivos, probará la descarga real y solicitará revisión independiente después de la integración. La salida del implementador no aprueba su propia corrección. Máximo dos ciclos de corrección por bloqueo en este encargo autorizado nuevo, sin reabrir presupuestos de misiones antiguas. Detener si se requiere intervención o persiste bloqueo; no llenar horas sin un plazo nuevo acordado.

No recargar el panel del usuario mientras conserva escenarios sin guardarlos. Registrar el estado ficticio actual antes de cualquier recarga consentida: A100€,2%,10años,50€/mes,inflación1%,compuesto;B200€,3%,5años,100€/mes,inflación1%,compuesto. No asumir que esos valores no cambiaron: volver a leer antes de actuar.

Servidor de demo8765 es del coordinador y debe seguir disponible para el usuario. Workers usan sesiones aisladas; cerrar solo servidores propios adicionales. No repetir suites Python intactas; correr regresión frontend/Node y consumidores de informe según delta. Mantener dictámenes y QA históricos, añadir resultado nuevo y actualizar estado/demo solo al verificar.
