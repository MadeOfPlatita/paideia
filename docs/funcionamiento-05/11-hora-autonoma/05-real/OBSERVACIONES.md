# Primer recorrido real del chat web

Sesión autorizada por ventana local; leído session-status.json activo y test_only:false. Benchmark opcional se detuvo tras su primera solicitud:0resultados, stop_reason=provider_error, ganador null. No se reintentó ni reanudó. El código actual no conserva si ese resultado fue truncado, rechazado, fallo de parser u otro error: causa NO determinada. No interpretar benchmark=complete del estado como dieciocho respuestas: solo terminó el hilo.

## Pruebas diferentes desde interfaz real

- Pregunta de cálculo ficticio → calculate_scenario ejecutada → respuesta de Groq, HTTP200 y provider_mode:external. Principal1000,3%efectivo,1año,aporte0,inflación0,compuesto; respuesta muestra1030EUR. Se observó herramienta ejecutada, sin fuentes de catálogo. El texto se truncó con límite256; la UI mostró el aviso. Recorrido conectado, NO aceptación completa de calidad.
- Pregunta conceptual diferente, pedida en dos frases → HTTP200, sin truncado/rechazo, en español. Rechaza la afirmación de ahorro universalmente sin riesgo y menciona pérdida de poder adquisitivo por inflación. Se conserva íntegra en real-risk-first.json; no prueba exactitud universal.
- Ambas solicitudes enviaron message y consentimiento remoto-v1, approved_fields vacío; sin perfil/historial. No es una garantía sobre lo que cualquier usuario podría escribir en texto libre.

No se consumieron peticiones para reintentar el benchmark fallido. Estas pruebas distintas estaban dentro del cupo global autorizado y sus continuaciones cuentan. Falta diagnóstico seguro y revisión completa A/B/C; no se elige estrategia ni ganador. Se mantiene límite absoluto de sesión.
