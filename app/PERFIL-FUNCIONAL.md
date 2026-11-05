# Perfil funcional local de Paideia

## Recorrido

- El recorrido presenta doce preguntas consecutivas, con tres bloques identificados: objetivo y conocimientos, situación económica y riesgo. Ya no termina tras las primeras cuatro.
- La parte económica (importe objetivo, ingresos netos, gastos, deuda, colchón y compromisos) y la de riesgo siguen automáticamente al bloque inicial. Pausar y ver el resumen conserva lo respondido; Continuar donde lo dejé retoma el primer campo pendiente. El resumen permite editar cada respuesta.
- **Continuar exige una respuesta válida**, o una elección explícita **No lo sé/Omitir**. No se avanza en blanco ni se deduce un cero. Esto incluye subcampos visibles de deuda. Sin_preguntar se reserva para preguntas pendientes o pausas. Se puede volver, pausar o salir sin completar el perfil; no es requisito para usar el resto de la web. Una edición vacía no borra la respuesta previa.
- Los campos monetarios son texto decimal, no texto libre: hasta 10 dígitos enteros y dos decimales, entre 0 y 9.999.999.999,99 EUR. Se conserva el decimal como cadena; un cero declarado no es desconocido ni omitido. Flujos económicos llevan periodicidad `mensual`. La cifra declarada se representa como rango puntual `min=max`; no es una banda estimada.
- Deuda separa `sin_deuda` de una deuda declarada y conserva estados independientes para saldo, cuota y coste anual. Compromisos y los dos campos de riesgo mantienen estructuras separadas. No se puntúa, clasifica ni relaciona el mapa con productos.

## Datos y privacidad

- El modelo local v2 sigue los paths de `docs/planificacion-03/05-perfil-conversacion/perfil.schema.json`; el cruce explícito está en `docs/funcionamiento-05/03-perfil/01-MAPPING-PERFIL05.md`.
- `static/profile_model.js` es la fuente única del frontend para preguntas, opciones, labels, mapping, validación, versión y persistencia. `static/index.html` carga ese módulo antes de `app.js`.
- El perfil se mantiene en memoria hasta que el usuario marca el opt-in y pulsa **Guardar perfil local** en Privacidad. En una visita posterior solo se carga una copia local previa que ya se había guardado voluntariamente; una preferencia guardada antes se conserva al migrar un snapshot persistido v1. Los valores antiguos sin equivalencia exacta se conservan como `legacyAnswers` y se pueden volver a responder.
- Borrar o revocar pide confirmación y elimina v2 y formatos anteriores conocidos. El backend no recibe ni consulta el perfil. La vista previa se genera en el navegador y tampoco envía datos. El chat usa consentimiento remoto separado y sigue sin proveedor real conectado; no se adjunta perfil ni historial.
- No se pregunta nombre, documento, banco, cuenta, credenciales ni texto libre confidencial. La evaluación es educativa, no asesoramiento, puntuación de idoneidad ni recomendación de producto.

## Verificación actual de continuidad

- `node --test tests/profile_model.test.cjs tests/profile_flow.test.cjs`: 15/15. Las dos nuevas pruebas cubren explicitud, cero, desconocido, omitido y deuda parcial; los perfiles parciales siguen siendo válidos para pausar.
- Suite Python: 155 correctas; HTTP: 19/19; ambos JavaScript pasan sintaxis. No se modifica el backend.
- Navegador real: doce preguntas, pausa/reanudación, bloqueo de blancos y edición sin pérdida, ceros, deuda y ausencia de guardado/envío automáticos; pregunta y resumen sin overflow a 390px. Dieciséis aserciones en `../../docs/funcionamiento-05/09-cuestionario/profile-flow-green.json`.
- Informe y salida real de regresión: `../../docs/funcionamiento-05/09-cuestionario/VERIFICACION.md`. Pausar conserva memoria de sesión; guardar entre visitas sigue exigiendo opt-in. No es aprobación visual ni prueba de IA/producción.

## Verificación histórica de la ampliación inicial

- `node --test tests/profile_model.test.cjs`: 13 pruebas Node built-in, incluyendo validación de paths contra el schema perfil05 existente, estados, ceros/decimales/límites, deuda, riesgo, migración, persistencia sin opt-in y borrado.
- `node --check static/app.js` y `node --check static/profile_model.js`.
- `python -B -m unittest discover -s tests -v`: 146/146 correctas; no modifica el backend.
- En la sesión aislada `paideia-perfil05-agent` se recorrieron campos con respuestas sintéticas, edición, vista previa, opt-in y borrado confirmado. Las llamadas de biblioteca/comparador/calculadora/ensayo se respondieron con fixtures sintéticas en navegador; no se envió un mensaje de chat ni un perfil. La captura y el registro de llamadas están en `docs/funcionamiento-05/03-perfil/evidence/`.
- Es una verificación de funcionalidad del perfil y una exploración de regresión en sesión aislada; no constituye aprobación visual, auditoría global ni integración de IA real.
