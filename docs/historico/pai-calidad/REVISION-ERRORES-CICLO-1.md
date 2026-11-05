# B1 — revisión independiente de avisos de error, ciclo 1

**Dictamen desfavorable** `deleg_11496335`, 4/11/2026. Solo el delta de presentación de errores, sin proveedor real y sin aprobar la calidad de B1.

La espera de más de 12 s mostró un aviso de estado incierto con un solo POST, pregunta conservada si no se edita y sin reenvío automático; 429 y 504 se distinguieron y el modo `not_configured` no envió. La revisión detectó, sin embargo:

1. Al editar una pregunta después de un timeout queda un aviso obsoleto que puede hablar de un ticket ya descartado o presentar la pregunta nueva como reenvío.
2. Si se cambia la pregunta mientras la anterior está en vuelo, el aviso asegura que se conserva aunque el campo contiene la nueva.
3. El mensaje promete reutilizar el ticket de cola, pero el backend puede haberlo reclamado y consumido, por lo que el reenvío puede ser rechazado.
4. `send_state` describe un intento de transporte: si el turno tiene varias rondas de herramientas, `not_started` de la última ronda no demuestra que el proveedor no recibiera rondas anteriores. `completed` describe escritura, no aceptación o procesamiento.
5. El foco puede caer en `BODY` al deshabilitar el botón. La alerta sí se anuncia.

El revisor no probó Groq ni leyó `.env`; las afirmaciones de backend se derivan del código, no de una prueba con proveedor real. Segundo y último ciclo de corrección en curso; no aceptar hasta disponer de revisión independiente sobre los archivos resultantes.
