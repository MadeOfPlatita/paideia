# Alcance de la integración opcional tras B

Análisis independiente `deleg_138ba986`, sin cambios ni pruebas, propone extraer un parser puro de selección y usarlo directamente en el recorrido de sesión contada ya existente, en vez de envolver ChatResult en FakeChatProvider. El tracer del coordinador ya mostró esa incompatibilidad. No iniciar mientras B esté editándose o sin aprobación y regresión.

Archivos propuestos si hay tiempo y aceptación: structured_provider_adapter.py (parseo puro), backend_services.py (consumo directo), tests/test_session_structured_integration.py y tests/test_structured_provider_adapter.py. No debilitar restricciones de proveedores, misión ni procedencia. La sesión seguiría usando StructuredSessionFixture exacta, no el transporte HTTPS real. Por tanto ese saneamiento, aun conectado y probado, sería un avance parcial, **no completa prioridad 2** de la misión ni integra Groq real.

Una ruta HTTPS real estructurada con conexión ficticia requiere un ensamblaje separado y revisión adicional. No extender el corte por este objetivo opcional. Priorizar B verde y revisión independiente de la regresión, con cierre desde 00:22:27 y corte 00:32:27+01.
