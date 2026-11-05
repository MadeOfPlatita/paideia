# Contrato experimental estructurado — v1, solo prueba offline

> **Revisión del ciclo 1:** aprobada en el alcance offline; ver `REVISION-2.json`. No implica aprobación de IA real ni del modo legado.

## Frontera

El servidor se configura explícitamente con `LocalChatService(..., enabled=True, test_only=True, structured_mode=True)` y un proveedor que declare `test_only is True` e implemente `select_education`. El constructor rechaza este modo si se activan herramientas, admisión, perfil o historial, o si el proveedor no es de pruebas. El cliente no puede elegir el modo: un campo adicional se rechaza en la solicitud. La configuración normal permanece sin proveedor.

El contrato de solicitud web de chat y el consentimiento `paideia-chat-remote-v1` siguen siendo los existentes; `approved_fields` debe estar vacío. En este modo no se admite contexto ni historial. La indicación `test_only` no certifica que un objeto de Python sea incapaz de red: la garantía operativa de esta ejecución deriva además del fixture local inspeccionado y sin transporte, y no habilita modelos reales.

## Selección no confiable

`select_education(messages)` devuelve exactamente `version`, `intent` y `claim_ids`: no entrega `scenario`, texto libre ni resultados. Versión `paideia-education-v1`; intención `explain` o `calculate`; lista no vacía y sin duplicados de identificadores de `structured_education.EDITORIAL`. Para `calculate`, el usuario debe proporcionar explícitamente `scenario` en la solicitud actual, con campos y tipos estrictos; el servidor valida y ejecuta `domain.calculate_scenario`. Para `explain`, `scenario` debe estar ausente. Los parámetros no se toman de la selección del proveedor ni de otro turno. El modo legacy rechaza el campo `scenario`.

Ejemplo ficticio: `{"version":"paideia-education-v1","intent":"explain","claim_ids":["risk","inflation"]}`.

## Resultado construido en servidor

La aplicación usa el diccionario editorial local para construir `answer` y `structured_education.items`; los resultados numéricos son del motor local y van en `structured_education.calculation`, con `source:"deterministic_local"`. La interfaz de este modo muestra los ítems estructurados y no `answer` como prosa elegida por el proveedor. En el fixture del navegador la respuesta malformada produce `502 CHAT_STRUCTURED_INVALID_RESPONSE`, sin texto de proveedor ni reintento. Una salida estructurada no es una verificación universal ni revisión profesional del contenido local.

**Límite de confianza numérico:** la interfaz valida estructura y coincidencia de supuestos, pero no recalcula cada cifra. Un backend o respuesta HTTP adulterados podrían presentar cifras incorrectas con supuestos idénticos; el proveedor ficticio no puede inyectar cifras mediante el contrato backend revisado. No se afirma resistencia ante un servidor comprometido.

**Pendientes y límites:** la modalidad aún no está conectada a Groq; no hay A/B/C válido, perfil real ni historial remoto aprobados. El modo anterior con respuestas libres y guard léxico no queda aprobado por esta sección y conserva el contraejemplo documentado en MIGRACION-TESTS.md. Los textos editoriales no acreditan revisión de profesores ni reguladores. Cualquier activación real requiere un trabajo posterior y autorización nueva.
