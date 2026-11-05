# C — corrección ciclo2, pendiente de dictamen independiente

## Fallo y causa
El dictamen desfavorable de esta mañana se conserva en `REVISION-INDEPENDIENTE.json`. El buscador permitía100letras y un espacio final (101caracteres visibles en el control), porque sus tres comprobaciones de longitud usaban trim antes de medir. Una solicitud con la consulta recortada se enviaba sin error. El fallo no es del servidor: el contrato exige rechazar el texto excedido sin petición y preservarlo.

## RED observado antes del cambio
Se amplió `tests/c_integration_browser.js` con valores de101caracteres: espacio al final, espacio al principio y todo espacios. La primera ejecución en navegador con API local real falló exactamente en `raw 101 characters rejected without fetch: trailing space`; capturó una petición q de100letras. Resultado completo `CICLO-2-RED.json`. No se cambió código de producción antes de este RED.

## Cambio mínimo
Solo `static/app.js`: eliminar trim en las tres comprobaciones de longitud (carga, input y reconstrucción al volver). Se conserva el recorte para construir una consulta válida, maxlength100, mensajes, requestId, demora, filtros y resto del comportamiento. El test verifica que valores excedidos conservan texto literal, filtro, error y aria-invalid, sin fetch, incluso al navegar.

No se añadió helper, dependencia, capa o nuevo cálculo. No se tocaron motor,perfil,Pai ni formato de informe.

## GREEN y regresión del coordinador
- `CICLO-2-desktop.json`:27/27, client/scroll1440/1440.
- `CICLO-2-mobile.json`:27/27, client/scroll390/390.
- Escenarios:114/114 por tamaño; anchos efectivos1425y390, sin desbordamiento de página.
- Informe:18/18 por tamaño; anchos efectivos1425y390, sin desbordamiento de página.
- Resumen agregado por código: `../REGRESION-FRONTEND.json`.
- `node --test tests/*.test.cjs`:40aprobadas,0fallos.
- `node tests/report_unit.js`:correcto (céntimos exactos, whitelist, mismatch, estados y datos inválidos).
- `node --check static/app.js` y `node --check tests/c_integration_browser.js`:correctos.
- Backend intacto: no repetir ni contar Python antiguo como ejecución posterior.

Servidor propio18872 detenido; netstat sin entradas y GET/api/status rechazado con WinError10061. Evidencia definitiva `COORDINADOR-CIERRE-VERIFICADO.json`. El primer connect_ex con timeout retornó10035; por sí solo no se aceptó como prueba definitiva y se conservó en su fichero original.

## Revisión y límite
Nueva revisión independiente despachada: `deleg_5a184ff2`, archivos exclusivos `ciclo2-revision/`. Hasta verificar ese dictamen C sigue pendiente, no aprobado. Este es el segundo y último ciclo del bloqueo; si persiste no se abre un tercero. Corte del tramo14:38:42+01:00, no se modifica.
