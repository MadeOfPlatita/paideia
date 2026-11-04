# Intento descartado — atribuciones negadas en Pai

**Fecha:** 4/11/2026, 23:00–23:40 (Málaga).
**Estado:** **descartado**. El código no está en la aplicación; se conserva aquí como evidencia.

## Qué se intentó

La evaluación de diez preguntas (`docs/pai-calidad/ejecucion-4h30/EVALUACION.md`) mostró que Pai suprimía cinco de diez respuestas legítimas. Una de las causas era que la frontera léxica de `backend_services.py` trataba igual «según la fuente oficial» y «una fuente secundaria **no** es oficial»: la forma correcta de responder era justo la que disparaba la retención.

Se implementó, con TDD, una regla de negación: una atribución solo cuenta como afirmada si aparece en una cláusula sin partícula negativa previa, con excepciones para los giros que llevan negación pero afirman («no solo», «sin duda», «no cabe duda», «no deja de», «no obstante», «sin embargo», «no dudo», «no es menos cierto»).

## Dictámenes

| Revisión | Resultado | Qué encontró |
|---|---|---|
| `deleg_e4d6eb3d` | **passed: false** | Seis fugas: «**no** obstante el folleto lo publica», «**sin** embargo el folleto lo publica», «No es un banco **según la entidad**» y tres dobles negaciones afirmativas. Dos eran regresiones respecto de la versión anterior. |
| `deleg_273d4b47` | **passed: false** | 21 atribuciones afirmadas de 59 frases pasaban. Dos causas: la coordinación no es frontera de cláusula («**No** es una fuente oficial **y** el folleto lo publica») y la rama de negación hacia delante no consultaba las excepciones («El folleto **no solo** recoge la condición, también la publica»). Las 21 se retenían antes del cambio. |

Ambas revisiones confirmaron lo que sí estaba bien: hashes y alcance exactos, 660 pruebas Python y 95 Node en verde, cifras e identificadores intactos y la web pública sin empaquetar `backend_services.py`.

## Por qué se descarta en vez de seguir parcheando

La causa común de las 21 fugas es el **alcance de la negación**: un «no» que gobierna otro predicado deja de gobernar la atribución. Eso no se arregla añadiendo conectores: cada lista nueva deja fuera la siguiente coordinación, y el resultado es una regla que *parece* rigurosa pero deja pasar «no es un banco **y** el folleto lo publica». En un asesor educativo, presentar como hecho una atribución inventada es peor que no mostrar la prosa.

Se agotó el presupuesto de corrección del bloque. **No se sube código que la revisión independiente ha rechazado dos veces.**

## Qué queda en su lugar

- La frontera original, sin cambios (`_ATTRIBUTION_SURFACE.search`), que retiene cualquier atribución y es la versión revisada y desplegada.
- El aviso honesto (`chat_withheld_notice.js`), aceptado: explica el motivo real de cada retención en lugar de atribuirlo siempre a «fuente oficial».
- Las pruebas del intento se conservan aquí (`test_pai_attribution_negation.py`) para que el siguiente diseño parta de los casos que hoy fallan.

## Qué haría falta para resolverlo de verdad

1. **Extracción de afirmaciones**: pedir al modelo una salida estructurada (afirmación, tipo, valor, fuente declarada) y validar cada campo contra el catálogo, en lugar de clasificar prosa con expresiones regulares.
2. **Verificación por frase**: comprobar cada frase con cifra o atribución contra las fuentes locales y mostrar solo las que tengan respaldo, en vez de retener el turno entero.
3. **Prueba de aceptación**: las diez preguntas de la rúbrica, con el texto original del modelo guardado, para poder juzgar qué se retiene y por qué.

Es una decisión de producto y arquitectura, no un parche de expresiones regulares.

## Ficheros

- `intento.patch` — diff exacto aplicado y revertido (64 líneas añadidas, 1 modificada).
- `backend_services_intentado.py` — copia íntegra del módulo con la regla, tal como se revisó.
- `test_pai_attribution_negation.py` — 29 pruebas del intento; 11 discriminaban el cambio.
