# QA de escenarios — sesión local

Fecha de cierre: 2026-11-03 17:01:11 +0100. URL: http://127.0.0.1:8765/#escenarios. Navegador aislado; cifras ficticias, IA desconectada, sin perfil guardado ni proveedor real. Sin modificar aplicación, pruebas o motor. No se probó imprimir (otro equipo).

## Hallazgos priorizados

### Medio — comparación de horizontes diferentes sin contexto en la tabla
**Pasos:** calcular A con 10.000 €, 4 %, 5 años, 100 €/mes, inflación 2 %, compuesto; calcular B con 10.000 €, −1 %, 10 años, 100 €/mes, inflación 2 %, compuesto. Observar la comparación superior.
**Actual:** A y B aparecen como actualizados en filas contiguas con aportado, saldo nominal y saldo real; no hay columna de horizonte ni aviso de que difieren. A muestra 16.000 €, 18.784,43 € y 17.013,64 €; B 22.000 €, 20.465,29 € y 16.788,66 €. Los horizontes sí figuran en cada resultado más abajo. Una persona puede interpretar como directamente comparables saldos acumulados durante períodos distintos. **Esperado:** que el propio resumen indique horizontes o advierta que difieren. Evidencia: `screenshots/comparacion-horizontes.png`. Consola: no capturada; no se afirma ausencia de errores.

### Bajo — formato incoherente de miles en la diferencia
En A, «Saldo final hipotético» aparece como 18.784,43 €, pero «Diferencia del escenario» como 2784,43 €; en B aparece −1534,71 €. El símbolo € está presente, pero falta el separador de miles empleado en los otros importes. Evidencia textual: recorrido y cifras observadas; captura del resultado detallado no conservada. Esperado: formato monetario coherente. Consola no capturada.

## Recorrido y observaciones
- La comparación mostró los importes anteriores; el calendario por filas era de mes 0 a 60 en A y 0 a 120 en B, en cierres anuales. «Aportado» incluye capital inicial y aportaciones; saldo nominal y ajustado se identifican, y la diferencia no se etiqueta como interés. Con tasa −1 %, B avisó que el saldo final queda por debajo de lo aportado. No se auditó la fórmula.
- Al editar A de 4 % a 7 % sin calcular, se retiró su resultado detallado, se reemplazaron sus valores por guiones y se indicó «Pendiente de calcular»; B permaneció actualizado. Captura `screenshots/edicion-pendiente.png`. Esto evita confundir el resultado antiguo con el editor actual.
- Con supuestos iguales en A y B (10.000 €, 4 %, 5 años, 100 €/mes, 2 %, compuesto), ambos mostraron 16.000 €, 18.784,43 € y 17.013,64 €. Al navegar por historial desde Escenarios a Inicio y de vuelta a Escenarios, permanecieron ambos resultados en esta sesión. No implica persistencia tras cerrar navegador.
- Campo capital vacío: validación nativa «Completa este campo». Cero aceptado y calculado. Horizonte 1,5: navegador exige entero y sugiere 1 o 2; 41: navegador indica máximo 40. Tasa −1 % aceptada y calculada. Al introducir `1,5` con la herramienta de escritura, el input numérico quedó en `1.5` y válido: no se verificó un envío completo ni otros navegadores/teclados.
- Tasa `1e2`: el navegador la consideró válida, pero al pulsar calcular apareció mensaje de la aplicación «Tasa e inflación: escribe valores mayores que −100 y hasta 1000 %, con hasta cuatro decimales y sin exponentes». Un capital de 100000000000000000000 pasó la restricción nativa y produjo mensaje de aplicación de límite 1.000.000.000 €; en ese momento la tasa seguía en `1e2`, por lo que no se aisló el recorrido de backend. Son validaciones visibles de la aplicación, no prueba de rechazo de backend.
- Móvil emulado 375 × 812 CSS px: en Escenarios documentElement.clientWidth y scrollWidth fueron ambos 375; formulario desplazable y captura `screenshots/movil-formulario.png`. Con foco en capital, Tab pasó a tasa, horizonte y aportación. No se recorrieron todos los controles ni se probó dispositivo físico.
- No se provocó estado pendiente/error de red: no se interceptó ni falsificó API, y no se observó error real. No se dispone de registro de consola retroactivo; fallo de un comando de automatización al intentar atajo Atrás y buscar el formulario en Inicio fue del arnés, no un crash de la app. La navegación real se comprobó luego con el historial del navegador.

## Evidencia
Capturas guardadas antes de navegar: comparación 27.867 bytes; edición 26.716 bytes; formulario móvil 30.612 bytes. Los tamaños se midieron en disco. Cronología: cálculos diferentes → edición → validaciones → igualación → navegación atrás; hora exacta por paso no registrada. No se afirma prueba de backend, red lenta, errores de consola o otros navegadores.
