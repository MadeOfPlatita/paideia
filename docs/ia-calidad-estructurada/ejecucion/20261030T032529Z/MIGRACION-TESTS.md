# Migración de pruebas y baseline

El modo heredado de prosa con `assess_financial_text` sigue siendo léxico y NO está aprobado como verificador universal. Su falso negativo `No es posible tener deudas, ahorrar es sin riesgo.` fue reproducido antes del cambio; evidencia original: `docs/ia-real-siguiente/ejecucion/20261030T005810Z/quality-offline/EXPLICIT-FOLLOWUP-BLOCKER.json`. Sigue siendo una limitación del modo legado, que esta tarea no declara aprobado para producción.

| Prueba anterior | Prueba sustitutiva y motivo |
|---|---|
| `test_unrelated_prefix_denial_does_not_hide_comma_separated_assertion`: pedía que la regex clasificara correctamente el texto adversarial | `test_untrusted_comma_separated_assertion_never_enters_structured_content` conserva literalmente el contraejemplo, prueba que el campo `answer` no permitido provoca error y que el contenido editorial se genera solo desde un ID conocido. Esta prueba valida una frontera diferente: no demuestra que la regex antigua detecte la frase. |

No se suprimió ni debilitó el caso para encubrirlo: se reemplazó la autoridad léxica por un contrato cerrado específicamente en el modo estructurado. La otra prueba de negación continúa intacta. Los tests de regresión del modo legado siguen vigentes y el fallo histórico se conserva en los artefactos citados. La capacidad en modo heredado NO está aprobada ni se equipara con esta prueba.

`test_chat_context.test_status_advertises_disabled_capabilities` conserva sus tres aserciones previas y añade `structured_education:false` por el nuevo campo explícito. La igualdad exacta sigue comprobando que no se habilita ni contexto ni historial. Este cambio no implica consentimiento ni envío real.
