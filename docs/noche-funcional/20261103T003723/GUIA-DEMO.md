# Guion de demostración — Paideia sin depender de la IA

## Estado de este guion

Guion basado en la comprobación real del coordinador de escenarios e informe. A y B tienen revisión independiente favorable dentro del alcance documentado. La ayuda contextual y las mejoras de biblioteca siguen en integración. No presentar la IA como conectada ni el catálogo como ofertas cuantitativas aprobadas. Todos los datos de esta demostración son hipótesis ficticias.

## Preparación para Alejandro

En la carpeta `prototipos/paideia-local`, arrancar `python -B app.py --port 8765` y abrir `http://127.0.0.1:8765/#escenarios`. Solo funciona mientras ese proceso y ese ordenador estén encendidos; no es todavía un enlace público para clase. No poner claves ni datos reales. Si el puerto está ocupado, no detener procesos ajenos.

## Parte que puede explicar José Manuel

**Idea:** «Podemos comparar dos hipótesis, ver qué parte aportamos nosotros y qué efecto tienen el interés y la inflación. Los resultados no son una promesa ni una oferta bancaria».

### 1. Introducir dos alternativas

En ambos escenarios:
- Capital inicial:1000euros.
- Tasa anual hipotética:3%.
- Plazo:5años.
- Aportación mensual:50euros.
- Inflación hipotética:2%.

EnAseleccionar **compuesto** y enB **simple**. Pulsar los respectivos botones **Calcular escenario A** y **Calcular escenario B**.

### 2. Leer la comparación

Referencias calculadas con el motor local y contrastadas en el navegador del coordinador:

| Dato | A: compuesto | B: simple |
|---|---:|---:|
| Total aportado | 4.000,00€ | 4.000,00€ |
| Saldo final nominal | 4.388,32€ | 4.371,25€ |
| Intereses | 388,32€ | 371,25€ |
| Saldo final ajustado por inflación | 3.974,64€ | 3.959,18€ |

Explicación: «Las aportaciones se hacen al final de cada mes. El importe ajustado por inflación representa poder adquisitivo en la hipótesis, no dinero adicional. No se han incluido impuestos ni comisiones». La tasa compuesta se interpreta como tasa anual efectiva; el motor usa otra convención para interés simple. No sonTAEdeunproducto.

Bajar a gráficos y tablas para ver la evolución. No deducir que la diferencia se repetirá en una inversión real ni que toda rentabilidad es garantizada.

### 3. Cambiar una decisión

Cambiar la tasa deAsin volver a calcular. Sus resultados deben dejar de mostrarse como vigentes, mientrasBseconserva. Explicar: «La pantalla no mezcla cifras antiguas con supuestos nuevos». Volver a calcularAconla nueva hipótesis.

### 4. Mostrar límites de forma honesta

Caso aparte:1000euros,−5%anual,1año,sinaportaciones,métodocompuesto,inflación2%. Referencia del motor:saldo nominal950,00€,intereses−50,00€,ajustadoporinflación931,37€. Esto es un escenario matemático negativo, no una predicción ni el riesgo completo de un producto. También se admite capital/aportaciones/tasa cero con valores explícitos.

## Informe y biblioteca

Con ambos escenarios calculados y vigentes, pulsar **Imprimir / guardar como PDF**. Se prepara un documento separado con los supuestos, las convenciones, los resultados, las diferencias **B − A** y las tablas. El diálogo de impresión depende del navegador: no es una descarga PDF automática. Si se edita o falla un escenario, volver a calcularlo antes de imprimir.

Para esta demostración, la diferencia B − A es −17,07 € en saldo nominal y −15,46 € en saldo real. No implica una recomendación de producto. No se exporta el perfil completo.

Artefacto ya generado por el coordinador desde los cálculos reales de esta demostración: `B/DEMO-1000-3-5.pdf`, dos páginas A4. Se verificaron importes, diferencias y último mes mediante extracción de texto; la primera página se revisó visualmente. Se utilizó Chromium CDP para generar el PDF, no una impresora física ni la selección manual del diálogo. La revisión independiente del hito B es favorable; no certifica impresión física ni el diálogo nativo.

Las ayudas contextuales y el diagnóstico por producto aún están integrándose; no usar esos pasos como entrega cerrada hasta su comprobación.

En la biblioteca existen candidatos investigados; las condiciones que falten o estén en conflicto no se rellenan inventando valores. Si no se puede comparar cuantitativamente, explicar el motivo y no hacer ranking de rentabilidad.

## Si preguntan por Pai

«Pai tiene preparada una parte de la arquitectura y las respuestas estructuradas se han probado con datos ficticios. Su integración real y la evaluación de calidad siguen pendientes. Los cálculos de esta demostración los hace el motor de la aplicación, no la IA».

## Al terminar

Cerrar únicamente el servidor propio usado para la demostración. No confundir un prototipo local con la publicación independiente del PC, que sigue pendiente.
