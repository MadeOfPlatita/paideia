# B6 — revisión independiente de la corrección 1

**Dictamen: desfavorable.** La revisión informó que se corrigieron la pérdida de procedencia al editar importes o copiar escenarios y la omisión de la etiqueta de fuente secundaria. Persisten cuatro bloqueos: error de condiciones confundido con ausencia de tasa en biblioteca, texto contradictorio en el comparador, posible indicación de vigencia de una tasa ya vencida y fecha de condición ausente de la tarjeta. También detectó diferencias en los motivos de comparación entre servidores y validaciones mejorables para fechas y valores vacíos.

El revisor comprobó en navegador local con IA apagada la descarga de informes, la comparación de cálculos con el motor y el escapado de entradas hostiles; también informó paridad de estáticos y condiciones. Las pruebas usan viewport móvil emulado y PDF generado por Chrome sin diálogo nativo ni impresora. No se desplegó. La reproducción de vencimiento se hizo con una condición que representaba el estado conservado en una pestaña, no esperando el cambio real de fecha.

Artefactos temporales en el scratch del perfil Hermes `b6-review2/` (sujetos a limpieza). Transcripción: `deleg_ac57f676`. Procede el segundo y último ciclo de corrección del bloque, seguido de revisión independiente; si no se supera, se detiene B6 sin marcarlo como aceptado.
