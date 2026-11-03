# Criterios de la siguiente prueba con Groq — NO AUTORIZADA por este documento

La petición vigente autoriza únicamente corrección y pruebas offline. No abrir ventana de credenciales ni llamar al proveedor por tener cupo restante. La sesión anterior está cerrada y su intento consumido se conserva.

## Qué prueban las regresiones

El guard debe rechazar la respuesta observada antes de mostrarla, preservar respuestas correctas, liberar admisión y no reintentar. Los proveedores ficticios prueban esta barrera y la integración, NO que un modelo siga el prompt. El conjunto del coordinador fue independiente al redactarse; una vez comunicados sus fallos al corrector, sus resultados posteriores son regresión conocida, no evaluación ciega ni precisión generalizable.

La detección es léxica y parcial. Las variantes exploratorias no cubiertas deben mantenerse visibles en el informe, no eliminarse ni convertirse retroactivamente en pruebas aprobadas. No se da por verificada una respuesta solo por no tener flags.

## Cuándo hace falta Groq

Solo después de revisión independiente y prueba web local con el código nuevo cargado. Habrá que pedir permiso expreso y entrada nueva en ventana segura, sin recuperar la clave anterior. Comprobar corte y presupuesto persistente antes de abrir; no extender ni reiniciar una misión vencida.

1. Repetir una única vez la pregunta conceptual del incidente con el prompt corregido. Examinar el contenido real: ahorrar como reserva de recursos; inversión y posible pérdida; separación entre riesgo nominal/custodia/entidad e inflación/poder adquisitivo; sin promesas universales. Una salida bloqueada demuestra acción del guard, no mejora del modelo. Truncado, error o rechazo de calidad detienen esta evaluación sin reintento.
2. Solo si el texto real es correcto y completo, probar cálculo ficticio por herramienta y contrastarlo con motor determinista. Son esperables dos llamadas upstream (tool y respuesta); medir llamadas realmente consumidas, no equiparar un turno web con un intento.
3. No activar A/B/C hasta calidad mínima comprobada y autorización separada. No cambiar modelo, salida de256tokens ni límites de consumo para mejorar resultados sin autorización.

No existe aún ganador A/B/C ni aprobación de perfil/historial remoto. La nueva prueba distinguirá transporte correcto, guard correcto y calidad real del modelo; son tres resultados diferentes.
