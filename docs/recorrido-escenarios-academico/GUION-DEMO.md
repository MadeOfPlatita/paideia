# Guion de demo · recorrido académico de escenarios

Uso previsto: enseñar en clase o en la memoria del trabajo cómo Paideia compara dos hipótesis propias y produce un justificante. Duración aproximada: 4 minutos. Todos los datos son ficticios y la aplicación corre en local (`http://127.0.0.1:8765/#escenarios`) sin IA.

## Antes de empezar

- El servidor de demo en el puerto 8765 debe estar activo. Si no lo está, arrancarlo desde `prototipos/paideia-local` como en las pruebas; no hace falta ninguna clave ni conexión externa.
- Abrir la aplicación en una ventana normal (no en el panel de vista previa de Hermes): la descarga HTML y el diálogo de impresión necesitan un navegador completo.
- Si la página ya tenía escenarios de una sesión anterior, los filtros y la selección de biblioteca se pierden al recargar: es el comportamiento actual, no un fallo de la demo. Hacer la demo en una pestaña recién abierta.

## Pasos y qué decir

1. **Situar la hipótesis.** «Estos números no son una predicción ni una oferta: son mis supuestos. El motor solo aplica la convención que se indica abajo, en bruto y sin fiscalidad.»
2. **Empezar/ajustar.** Pulsar «Cargar ejemplo ficticio en A» y leer en voz alta los campos: 1.000 € iniciales, 2 % anual, 5 años, 50 €/mes al final de cada mes, inflación 2 %, compuesto. Señalar que **no se ha calculado nada todavía**: el estado sigue «Pendiente de calcular».
3. **Calcular A.** Pulsar «Calcular escenario A». Resultado esperado: saldo final **4.255,02 €**, aportado **4.000,00 €**, saldo real **3.853,91 €**. Explicar la diferencia entre nominal y real: el real descuenta la inflación supuesta.
4. **Comparar/entender.** Pulsar «Copiar A a B para probar un cambio»; si aparece la confirmación, aceptarla. Cambiar solo la tasa de B de **2 % a 3 %** y pulsar «Calcular escenario B». Resultado esperado: **4.388,32 €** nominales y **3.974,64 €** reales. El resumen explica que la única diferencia es la tasa y avisa si los horizontes no coinciden.
5. **Interpretar.** «Mismo capital, misma aportación, mismo plazo: **133,30 €** más de saldo final (**120,73 €** más en términos reales) por un punto de tasa. La comparación no recomienda ningún producto; solo describe el efecto del supuesto que he cambiado.»
6. **Guardar.** Pulsar «Guardar» en la guía. El foco pasa al informe y el siguiente Tab llega a «Descargar informe (HTML)». Descargar el archivo y abrirlo: cinco tablas, los mismos supuestos, resultados y diferencias, la fecha y las advertencias; no incluye perfil ni datos personales.
7. **Cerrar.** «El informe es un justificante de esta comparación concreta. Si cambio un supuesto, deja de ser válido y hay que recalcular y volver a descargarlo.»

## Qué no prometer en la demo

- No hay PDF automático desde el panel de vista previa de Hermes; el botón de impresión depende del diálogo del navegador y no está verificado como guardado de archivo.
- No hay persistencia: al recargar se pierden filtros, selección y escenarios no guardados fuera del HTML descargado.
- No hay recomendación de producto, conexión con proveedores ni datos reales de ninguna entidad.

## Verificación de esta guion

Las cifras citadas se leyeron del motor local durante la comprobación del coordinador del 3 de noviembre (sesión aislada, `coordinador/foco-ciclo1.json`). El recorrido completo, incluida la descarga HTML leída desde disco, se comprobó en `implementacion/` y `revision/`. La corrección de foco posterior al dictamen se reprodujo con teclado real en 1280 y 390 px; su revisión independiente sigue pendiente.
