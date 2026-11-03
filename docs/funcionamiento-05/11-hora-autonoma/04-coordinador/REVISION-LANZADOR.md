# Lanzador revisado y abierto

Se recibió deleg_17d8f235 y se leyeron sus archivos/casos de prueba completos. El coordinador añadió una regresión y corrección: al consumirse el intento24 se cierra el acceso futuro y se elimina inmediatamente la referencia de clave, sin esperar al vencimiento. La última solicitud ya enviada puede finalizar.

## Verificado

- 182 tests Python y20Node correctos, sintaxis app.js correcta. HTTP19/19 tras arrancar de nuevo el servidor normal8765, que estaba parado: el primer fallo de infraestructura se conserva, no se presenta como defecto ni como pasada.
- GUI nativa comprobada sin claves/envío: campo oculto, ambas autorizaciones inicialmente desmarcadas; altura solicitada450 frentea520 disponible. Ventana real posterior visible, sin leer su campo ni hacer capturas.
- Proceso normal: proc_7665a0f18374,8765 sin proveedor.
- Ventana temporal real: proc_e8c2431e5524; servidor8768 se crea SOLO tras entrada voluntaria y confirmación Free. Cuenta/plan no verificables técnicamente por checkbox.
- Herramienta real habilitable exclusivamente calculate_scenario; no se conceden permisos de catálogo. Cálculo fuera del modelo, proveedor único con contador previo a cadaPOST, singleflight y24intentos globales por proceso, sin reintentos. Clave no se guarda deliberadamente en disco.
- Vencimiento absoluto17:40:20UTC2026-10-29 (además máximo3600s desde inicio): no se inicia ni envía después. Relanzar no da presupuesto global persistente; esta es una sesión temporal, no producción.
- A/B/C opcional18solicitudes sintéticas, casilla separada por defectoFALSE; presupuesto compartido, intervalo21s, errores/429 paran el benchmark. Se conserva parcial y ganador null; terminar hilo no equivale a18respuestas buenas. No guarda razonamiento ni claves.

## Pendiente de confirmación y evaluación real

No se declara nuevo chat real por pruebas offline. Esperar estado autorizado, probar vía frontend pregunta→calculate_scenario→respuesta real, leer resultados seguros del benchmark y revisar calidad financiera. No usar perfil real ni inferir ganador automático. Un HTTP200 no demuestra fuentes, razonamiento financiero ni disponibilidad/carga. El smoke previo es evidencia independiente, no este recorrido.
