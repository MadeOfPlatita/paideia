# Recorrido de escenarios: implementación y comprobaciones

Implementación académica original, en el cliente existente. No se copiaron código ni activos de terceros. Se mantienen las advertencias y el cálculo local existente.

## Evidencia TDD

- `red-orden.json` → `green-orden.json`: orden y enlaces.
- `red-ejemplo.json` → `green-ejemplo.json`: ejemplo explícito y cancelación.
- `red-copia.json` → `green-copia.json`: copiar campos A a B.
- `red-diferencias.json` → `green-diferencias.json`: resumen con ambos resultados del motor local.
- `green-escritorio.json`, `green-movil.json`: integración ampliada, 33 comprobaciones por tamaño; incluyen navegación, validación, equivalencia decimal, copia y respuestas pendientes. Los tests adicionales no tienen RED individual registrado.

Los scripts se ejecutaron como IIFE asíncrona desacoplada en navegador aislado contra la API local en 127.0.0.1:8765, con datos ficticios. No se tocó la pestaña de vista previa del usuario ni se detuvo su servidor. Se deshabilitó la caché al cargar los cambios.

## Regresiones

Desde `prototipos/paideia-local`:

```sh
node --check static/app.js
node --check tests/scenario_journey_browser.js
node --test tests/*.test.cjs tests/report_unit.js
```

Resultado: 41/41 pruebas Node. Salida en `node-tests.txt`. En navegador: `scenario_browser.js`, `report_browser.js`, `qa_layout_browser.js` y `c_integration_browser.js` pasaron (detalles en `regresiones-browser.json`). La primera ejecución de `report_download_browser.js` falló por no activar el guard de la prueba; se repitió con `window.__hermesPrintGuard=true` antes de cargar la página y pasó (`descarga-browser.json`). Se verificó la solicitud de descarga, no el contenido del archivo descargado en el host.

## Tamaños y límites

`viewport.json` registra client/scroll iguales: 1265/1265 en ventana de 1280 px y 375/375 en ventana de 390 px; `escritorio.png` y `movil.png` son capturas de la página. La anchura de contenido excluye la barra vertical. No se realizó revisión independiente ni aprobación de QA. Estas pruebas no sustituyen una auditoría de accesibilidad completa ni comprueban todos los navegadores.
