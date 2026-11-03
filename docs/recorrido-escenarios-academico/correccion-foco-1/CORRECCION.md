# Corrección de foco · ciclo 1

Cambio acotado al handler común de los tres enlaces: el destino recibe `tabindex=-1`, foco con `preventScroll` y el desplazamiento existente. Se conserva `#escenarios`. No se modificaron cálculos, datos, versión, validación, confirmaciones, estilos ni informe.

## Evidencia

- `RED.json`: prueba nueva ejecutada antes del parche; fallaron exactamente los tres focos, mientras ruta, snapshot y solicitudes se conservaron.
- `GREEN-browser-retry.json`: cinco IIFEs de navegador, en documentos nuevos y con anchos solicitados 1280 y 390: foco, recorrido, informe, descarga con guard y layout; 10/10 ejecuciones correctas. El guard se instaló antes de cada documento mediante `Page.addScriptToEvaluateOnNewDocument`.
- `GREEN-teclado.json`: 24 combinaciones de ancho, estado y enlace con Enter y Tab reales por CDP. Se verificó destino, hash, snapshot y cero solicitudes tras preparar el estado. Tab desde Empezar llega a capital A; desde Comparar o Guardar llega a imprimir (current), descargar (guard), o al glosario cuando los controles de informe están deshabilitados (pending/error). La comprobación programática dio 24/24.
- `GREEN-node.txt`: 40 pruebas Node `.test.cjs` y `report_unit.js` correcto (41 en total); `node --check` correcto para los dos archivos modificados.

## Intentos conservados y límites

`GREEN-browser.json` recoge una ejecución con documentos reutilizados accidentalmente, y `GREEN-browser-fresh.json` un intento con parámetros que el servidor responde como NOT_FOUND. Ambos son fallos de preparación de automatización; no se borraron. Se repitió con navegación a `about:blank` y luego a la URL original, documentos nuevos y sin cambiar la aplicación.

Se intentó por error ejecutar `context_help_test.js` en Node y falló por ausencia de `document`; es una prueba de navegador, no parte de la suite Node. No se modificó esa prueba. No se ejecutaron pruebas Python ni se manipuló el servidor o la vista del usuario. Los diálogos PDF nativos y una auditoría global de accesibilidad están fuera de alcance. Queda pendiente la revisión independiente selectiva; este documento no la sustituye ni constituye aprobación.
