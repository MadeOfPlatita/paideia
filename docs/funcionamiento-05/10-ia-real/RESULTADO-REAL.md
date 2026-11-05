# Primera llamada real a Groq — verificada

Evidencia leída directamente: `../../../app/evidence/REAL-IA-SMOKE.json`.

- Fecha UTC: 2026-10-29T16:34:20.977120+00:00.
- Modelo: openai/gpt-oss-20b.
- Una llamada, HTTP 200, test_only:false.
- Respuesta en español, no truncada y sin rechazo.
- Sin envío de perfil ni persistencia deliberada de la clave; la entrada fue por ventana local enmascarada y confirmación Free del usuario. No se verificó técnicamente el estado de facturación de la organización.

## Respuesta recibida

> Ahorrar es guardar dinero sin riesgo, mientras que invertir implica usarlo para generar rendimientos a cambio de asumir riesgo.

## Valoración

Conectividad y autenticación reales comprobadas; no es una respuesta sintética. La calidad financiera NO queda aprobada: «ahorrar ... sin riesgo» es demasiado absoluto y debe matizar riesgos como la pérdida de poder adquisitivo por inflación y las condiciones del instrumento. Una pregunta no demuestra exactitud, calidad contextual ni uso de tools.

## Límites y siguiente validación

Esta prueba autónoma no conectó el chat web ni sus herramientas, no transmitió perfil, no probó cola, concurrencia, persistencia de cupos ni alojamiento. El programa permite una sola petición por apertura; no se reutiliza la clave ni se inicia otra llamada automáticamente. Faltan pruebas reales con herramientas/cálculos y A/B/C, con autorización acotada y acceso por el mismo mecanismo seguro. El chat web continúa sin proveedor configurado.
