# Cuestionario: continuidad y respuestas explícitas

## Petición y cambios

El recorrido inicial terminaba tras cuatro preguntas y exigía abrir aparte las ramas económicas y de riesgo. Además, Continuar convertía una respuesta vacía en sin_preguntar y avanzaba. Ambos fallos se reprodujeron en navegador antes de corregirlos; ver los dos archivos *red.json.

Ahora hay doce preguntas consecutivas con tres bloques identificados: objetivo/conocimientos, situación económica y riesgo. No se necesita un botón intermedio para abrir cada bloque. Cada respuesta debe ser válida o una elección explícita No lo sé/Omitir. También se validan los subcampos visibles de deuda; no se convierten blancos en ceros ni se exige revelar importes. Sin_preguntar se conserva para preguntas aún no visitadas o una pausa.

Pausar lleva al resumen y Continuar donde lo dejé vuelve al primer campo pendiente. Un perfil con todas las preguntas respondidas muestra Revisar cuestionario. La edición vacía no borra una respuesta previa. La pausa solo conserva la sesión en memoria; la persistencia entre visitas sigue siendo voluntaria desde Privacidad.

## Evidencia

- Pruebas Node: 15/15, incluidas dos nuevas regresiones de continuidad explícita (valor cero, desconocido, omitido, deuda parcial).
- Python: 155 tests correctos; HTTP: 19/19. Ambos JavaScript pasan node --check.
- Navegador real: doce preguntas hasta resumen, pausa/reanudación, edición vacía, deuda parcial, ceros, No lo sé/Omitir, sin guardado automático ni cuerpos de red. Dieciséis aserciones guardadas en profile-flow-green.json; dos comprobaciones de overflow móvil a 390px incluidas, no auditoría visual global.
- regression-results.json conserva la salida real del comando de regresión.
- Dos intentos de harness con pestaña activa perdida se descartaron; la aceptación completa se repitió desde new_tab en una única llamada. No se presentan como errores de la app.

Sin rediseño, proveedor real, despliegue, datos personales ni cambios del backend. No se afirma captura visual: capture_screenshot no devolvió un archivo utilizable.
