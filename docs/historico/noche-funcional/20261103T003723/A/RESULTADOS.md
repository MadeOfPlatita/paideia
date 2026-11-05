# Hito A — implementación y evidencia

Estado: implementación funcional ejercitada; **pendiente revisión independiente de coordinación**, por lo que no se declara aceptación final. Fecha de prueba 2026-11-03. No se usaron proveedor remoto, claves ni datos personales. Dos hipótesis sintéticas se envían al servidor normal propio en loopback, no a un mock financiero.

## Delta

`#escenarios` reutiliza el formulario, motor `/api/calculate`, representación SVG y tabla anual ya existentes. Añade dos escenarios editables independientes A/B y tabla comparativa simultánea, con valores nominal, real y aportado; cada uno mantiene su gráfico y tabla. Solo se presentan cifras devueltas por el servidor. No se calcula diferencia entre escenarios: no viene del motor y no se añade otra fórmula financiera. La representación SVG convierte los valores decimales a `Number` para coordenadas aproximadas; resumen y tabla conservan los céntimos exactos de las cadenas del motor. Se muestran pérdidas, saldos negativos y aviso de tasa cero; supuestos manuales, conversión de tasas, aportación al fin del mes, exclusión de costes/impuestos y carácter no predictivo están visibles.

Cada escenario pasa por `dirty`, `pending`, `current`, `error`. Toda edición invalida cifras inmediatamente, incluso con solicitud en curso; respuesta de versión anterior se descarta. Un fallo no elimina el resultado del otro. El snapshot para B se documenta en `CONTRATO-B.md`. No se modifica perfil ni Pai. No se persisten comparaciones al recargar.

## Evidencia y comprobaciones nuevas

- `red-browser.json/png`: un formulario previo, no dos. `red-summary.json`: sin tabla comparativa. `red-precision.json`: el formato anterior perdía dígitos en importes grandes y mostraba cuatro decimales de tasa como dos. `red-zero-warning.json`: sin aviso explícito de tasa cero. `red-validation.json`: notación exponencial rechazaba el servidor con mensaje genérico. `red-mobile-overflow.json`: viewport 390, scrollWidth 1303 con cifras extremas.
- `desktop.json` y `mobile.json`: 114 aserciones cada uno, todas correctas. Ventanas configuradas 1440×900 (clientWidth 1425) y 390×844 (clientWidth 390), ambas con scrollWidth igual a clientWidth en el caso extremo. Se prueban importes no nulos, capital y tasa cero, tasa negativa, saldo negativo con interés simple, interés compuesto, avisos, series, tabla, SVG, resumen y cifras de 4 decimales. Respuesta real retenida tras fetch y soltada después de editar: se descarta; fallo de transporte sintético aislado: B permanece; se comprueba validación sin enviar solicitud y aislamiento del snapshot. Las referencias financieras se comparan con nuevas peticiones HTTP al motor real.
- Capturas propias `desktop.png`, `desktop-chart.png`, `mobile.png`. La versión móvil limita horizontalmente el desbordamiento de tablas con importes extremos mediante regla CSS acotada a escenarios.
- `node --check static/app.js` y `node --check tests/scenario_browser.js`: correctos. Con `C:/Users/aleja/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe -m pytest tests/test_domain.py -q`: 11 passed, 16 subtests passed. `... -m pytest tests/test_backend.py -q -k calculate`: 2 passed, 16 deselected, 4 subtests passed. No se ejecutó suite global.
- El `python` activo carecía de pytest; se utilizó el intérprete instalado prescrito, sin instalar nada. Primera automatización del navegador esperó una promesa más de 5 s y agotó el timeout del harness; se repitió guardando la promesa en ventana y consultando su resultado. Una primera corrección de CSS inline fue bloqueada por CSP; se sustituyó por CSS local permitido y se repitió la prueba.
- Servidor propio `python -u app.py --port 18764` terminado; `netstat` no muestra listener en `127.0.0.1:18764`. Solicitud posterior no respondió dentro de 2 s. Ningún servicio ajeno fue detenido.

## Reproducibilidad

Desde `app`, iniciar servidor de prueba loopback `python -u app.py --port 18764`; abrir `http://127.0.0.1:18764/#escenarios` en navegador aislado, inyectar el contenido de `tests/scenario_browser.js` como expresión asíncrona y esperar el objeto devuelto; detener solo el servidor propio. Las pruebas interceptan el `fetch` exclusivamente para retener una respuesta real o producir un error de transporte explícitamente sintético; no sustituyen cifras financieras. El script también puede iniciarse como promesa sin esperar en una evaluación limitada a 5 segundos y consultarse posteriormente. No necesita perfil ni IA.

## Límites

No hay diferencia calculada A−B ni informe imprimible en esta entrega; B debe consumir el contrato y rechazar estados no `current`. Las cifras extremas pueden requerir desplazamiento dentro de la tabla móvil. La captura visual y las aserciones no sustituyen revisión independiente, accesibilidad integral, datos de producto reales, asesoramiento o despliegue. Los resultados históricos de otras misiones no se han vuelto a ejecutar ni sumar.
