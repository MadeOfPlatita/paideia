# Verificación conjunta pendiente del ciclo 1

No aceptar por separado los informes de los dos cambios. Una vez finalicen ambos trabajadores:

1. Leer las firmas y el payload real del modo estructurado, comprobar por código que el escenario pertenece a la misma solicitud y que las cifras no proceden de la selección ficticia. Un `source:deterministic_local` sin esa vinculación no cumple la aceptación.
2. Ejecutar pruebas reales sobre la nueva versión, incluidas las regresiones del backend y del selector de UI. Guardar los resultados completos y corregir únicamente incompatibilidades de integración sin inventar salidas.
3. Iniciar fixture propio en loopback con código recién cargado. Navegador: consentimiento bloqueado por defecto; explicación editorial; introducir supuestos ficticios de cálculo expresamente y comprobar 1030.00 desde el motor; intentar DTO falsificado, dato numérico de otro turno y capabilidad cambiante; comprobar error sin texto libre ni reintento.
4. Documentar que el modo legacy permanece no aprobado. Si se desactiva, probar que no puede devolver prosa peligrosa; si solo se conserva para compatibilidad, no decir que está aprobado ni usarlo en modalidad nueva.
5. Ejecutar suite Python, Node, sintaxis y HTTP. El test migrado del clasificador no prueba que haya corregido la regex anterior; preservar evidencia y tabla de migración. Asegurarse de que el servidor utilizado haya cargado la versión actual y cerrarlo al terminar.
6. Revisión independiente de la integración y de las correcciones, no mera suma de suites aisladas. Máximo dos ciclos de corrección/revisión. Conservar alcance, respuestas reales y matriz; no usar el pase como acreditación de Groq.

Todas las pruebas de proveedor deben utilizar fixtures test_only y ningún transporte externo. El corte de la misión es fijo 2026-10-30T07:00:00Z; no se renueva.
