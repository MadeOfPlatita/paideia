# Migración v1, opt-in y borrado

## Formatos reconocidos

- Actual: `paideia.profile.v2`, envolvente `{version:2, profile, legacyAnswers}`.
- Anterior de la UI existente: `paideia.profile.v1`, envolvente `{version:1, profile:{income, expenses, knowledge, objective, horizon, risk}}`.
- Alias legado reconocido y borrado: `paideia.profile`, formato v1 envuelto o el objeto antiguo de seis campos directamente.

La carga busca v2 primero. Solo intenta migrar si encuentra y valida un snapshot persistido en una clave anterior. La UI no pasa el perfil en memoria a la migración; almacenamiento vacío produce perfil nuevo, `profileOptIn=false` y cero escrituras. Un formato v1 persistido implica el opt-in previo del flujo existente: se conserva el permiso, se escribe v2 y se elimina el origen anterior únicamente si la escritura nueva tuvo éxito. Si falla la escritura, el perfil anterior se deja intacto y se muestra aviso; no se inventa ni se envía información.

## Conversión conservadora v1 → v2

| Campo anterior | Conversión | Respuestas conocidas sin equivalencia exacta |
|---|---|---|
| `income`, `expenses` | Decimal string válido → flujo mensual puntual con el mismo string en `min_eur=max_eur`; `unknown→no_se`, `skipped→omitido`, `null→sin_preguntar`. Cero se conserva. | Ninguna si cumple el validador v1. |
| `objective` | `buffer→colchon_imprevistos`; `planned_purchase→gasto_previsto`; estados `unknown/skipped/null` conservan su estado. | `understand` queda en `legacyAnswers.objective`. |
| `horizon` | `1-3→1_3_anos`; `3-5` y `gt5→mas_3_anos` (categoría superior del schema 05); estados sin valor conservan estado. | `lt1` queda en `legacyAnswers.horizon`; no se fuerza a menos de 6 ni a 6–12 meses. |
| `knowledge` | `beginner→empezando`; `unknown/skipped/null` conservan estado. | `some` y `experienced` quedan en `legacyAnswers.knowledge`; no se afirma que se hayan usado productos. |
| `risk` | `unknown/skipped/null` conservan estado. | `low`, `moderate` y `high` quedan en `legacyAnswers.risk`: las opciones anteriores no son equivalentes a la reacción nueva. |

Los seis campos no reinterpretables en `legacyAnswers` se siguen mostrando en el resumen como legado local, con una acción para responder la pregunta actual. Responder, marcar «No lo sé» u omitir reemplaza ese legado por una respuesta v2 explícita. Todos los campos nuevos (liquidez, importe objetivo, gastos esenciales, deuda, colchón, compromisos y capacidad de pérdida, entre otros) empiezan en `sin_preguntar`.

## Confirmación de borrado

Los botones de borrar del encabezado y de Privacidad confirman la operación antes de llamar `clearStoredProfiles`. También se confirma al desactivar el toggle cuando hay una copia opt-in. Una confirmación aceptada quita la clave actual `paideia.profile.v2` y las claves anteriores `paideia.profile.v1` y `paideia.profile`; si el usuario cancela, la preferencia y la copia permanecen. El perfil actual en memoria puede seguir en la pestaña después de borrar, pero vuelve a no estar autorizado para persistirse.

La función Node pura prueba el borrado de cada clave, el camino sin opt-in y la migración solo desde un snapshot almacenado. No se usó localStorage personal del usuario para las pruebas.
