# Checkpoint de ejecución

Corte fijo: 2026-10-30T07:00:00Z. No cambiar deadline. Sin llamadas a proveedor de IA o API financiera.

- **A:** adaptador fake y evaluación sintética implementados; flujo en navegador con fixture 200/200/502, cálculo 1030 y sin fuga del texto alterado. Revisión1 detectó inyección arbitraria `test_only`; fix1 en curso. No se aprueba proveedor real.
- **B:** 7 pruebas de mapping/permisos con hechos sintéticos. Revisión1 detectó política explícita sin límites de frescura; fix1 en curso. Ningún hecho real fue publicado y no se infirió un TTL real.
- **C:** snapshot sintético en único proceso/escritor, validación/hash/promoción; pruebas y comparación real HTTP+browser de dos IDs sintéticos, `quantitative_ready:false`. La revisión focalizada no reportó defecto en C; no afirmar garantías distribuidas o persistencia cloud. Fixture propio cerrado.
- **D:** fallo de confirmación al volver corregido y probado por trabajador en navegador; perfil opt-in y borrado probados con fixtures. El encabezado ya no atribuye realidad al fixture. La impresión solo se emuló, no se probó impresora/PDF. Revisión pidió ampliar casos de cambio de producto.
- Última regresión conjunta previa a fixes1:293Python/32Node/19HTTP. No presentar ese resultado como actual hasta ejecutar otra suite después de las correcciones. Dos agentes trabajan en A/B con archivos exclusivos; no sondear, procesar notificación de fin. Tras su retorno reproducir regresiones, revisar independientemente y probar navegador fresco. Máximo dos ciclos de corrección/revisión.
