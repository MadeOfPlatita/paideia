# QA exploratoria con testers — Paideia

Inicio: 03/11/2026 16:55:36+01:00. Petición de Alejandro: no consigue guardar desde la aplicación ni descargar el adjunto; enviar varios subagentes a usar la web como testers. No se modifica código en esta fase.

## Entorno y conservación
Servidor de demo del coordinador: http://127.0.0.1:8765/; estado comprobado local_prototype, IA not_configured y connected:false. Mantener ese servidor y la sesión de vista previa del usuario intactos. Cada tester tiene navegador aislado propio; no tocar perfiles reales ni limpiar almacenamiento del usuario. Sin proveedores reales de la app, claves, datos personales, Tk, pagos, instalaciones, bases de datos, despliegue o commits. Solo datos ficticios.

## Reparto en paralelo
Delegación: deleg_74dfbb28, tres testers.

1. Exportación: sesión qa-user-export-165536, archivos exclusivos exportacion/. Pulsar el botón real sin sustituir window.print ni aceptar Page.printToPDF como prueba del guardado. Observar diálogo, descarga y errores; documentar limitaciones de automatización y del host sin atribuir causas no probadas.
2. Escenarios: sesión qa-user-scenarios-165536, archivos exclusivos escenarios/. Formularios normales y errores, edición, navegación, plazos diferentes, explicaciones y móvil. Uso de controles visibles, no repetir la suite aprobada como sustituto de explorar.
3. Biblioteca/navegación: sesión qa-user-library-mobile-165536, archivos exclusivos biblioteca-navegacion/. Filtros, ficha, comparador, motivos y ayudas; uso sin perfil/IA, navegación y reflow en móvil, incluido desbordamiento inicial de Inicio si se reproduce.

## Evidencia y aceptación de la QA
Cada agente entrega report.md y evidence.json con URL, pasos, resultado esperado/real, severidad, estado confirmado/inconcluso, capturas reales y errores de consola disponibles. Guardar intentos fallidos separados. Un bloqueo de automatización no es automáticamente defecto de app; un fichero PDF creado por CDP no demuestra que el usuario pueda descargarlo. No declarar aprobado el recorrido de guardar sin realizarlo.

El coordinador leerá los artefactos, verificará casos decisivos seguros y agregará/deduplicará en código los hallazgos antes de indicar totales. Separar fallos del producto, integración con el panel Hermes y límites de prueba. No iniciar correcciones automáticas ni una reconstrucción general. El problema del adjunto Hermes no se considera resuelto por repetir el mismo enlace.

## Cierre
Conservar los dictámenes previos como históricos de su alcance; esta QA cubre uso real más amplio y puede detectar huecos. Entregar informe priorizado y siguiente arreglo mínimo recomendado. Mantener el servidor de demo del usuario funcionando. No hay plazo nuevo acordado ni obligación de consumir horas o cuota.
