# Diagnóstico y límites tras la prueba real

La evidencia original del benchmark no permite identificar la causa exacta: se perdió la distinción entre truncado, rechazo, parser y transporte. No se reescribe su resultado ni se adivina la causa. Tampoco se reintenta/reanuda automáticamente.

Se reprodujo offline un caso posible y concreto: HTTP200 con finish_reason=length, reasoning presente y content vacío dispara invalid_response; el callback anterior lo convertía en provider_error genérico. Esto demuestra el defecto de observabilidad, NO que fuese la causa del fallo real.

Con rojo→verde se añadieron metadatos enum/bool/count al error de parser, sin contenido/razonamiento/clave. El benchmark conserva failed_case y distingue truncado/refusal/error en nuevas ejecuciones, filtrando todo campo no permitido. Su estado ya no dice complete si se detuvo con error. Se añadió brevedad al prompt del chat por el truncado real de su cálculo, sin ampliar tokens ni usar respuestas falsas.

Estas mejoras están en disco y pasan regresión, pero el proceso real activo fue arrancado antes de ellas. NO se ha intentado leer su clave, hotpatcharlo ni reiniciarlo: conserva la sesión autorizada hasta el corte. Para comprobar las mejoras con llamadas reales hará falta otra autorización/entrada segura; hasta entonces se consideran pruebas offline.

Código/resultado de regresión en04-coordinador/regression-after-real-tests.json:185Python,20Node,19HTTP, sintaxis JS. Revisión independiente adicional solicitada, todavía no usada como aprobación.
