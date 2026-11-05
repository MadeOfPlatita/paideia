# Corrección C · ciclo 1

- Se invalida únicamente el diagnóstico pendiente al salir de Comparar: se incrementa su identificador y se libera el estado ocupado. No se inicia ninguna petición al volver; el reintento sigue siendo manual. La selección y los resultados o errores ya completados se conservan.
- El buscador tiene ahora `maxlength=100`. La validación JavaScript de 101 caracteres inyectados programáticamente sigue rechazando la consulta antes de fetch.
- TDD con API y motor locales reales: la nueva carrera con respuesta retenida falló antes de corregir navegación; la nueva aserción nativa falló con 120 antes del cambio a 100. Después, `tests/c_integration_browser.js` pasó 24/24 tanto a 1440×900 como a 390×844; midió ancho cliente/desplazamiento 1440/1440 y 390/390 respectivamente. Incluye reintento manual, ausencia de petición automática y descarte por cambio de selección.
- `node --test tests/*.test.cjs`: 40/40; `node --check static/app.js` y `node --check tests/c_integration_browser.js`: correctos. No se repitió la suite Python.
- Servidor propio `127.0.0.1:18867` detenido; `netstat` sin entradas del puerto y conexión posterior `ECONNREFUSED`. No se usaron proveedores reales ni datos personales. Se conserva intacta la revisión independiente fallida original. Esta corrección aún requiere nueva revisión independiente por un contexto distinto; este resultado no sustituye dicha revisión.
- Incidencia de ejecución: una evaluación síncrona del navegador excedió el timeout del puente; las ejecuciones finales se recogieron de forma asíncrona en documentos nuevos.
