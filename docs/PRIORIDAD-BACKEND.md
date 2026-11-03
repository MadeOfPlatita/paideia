# Prioridad vigente — backend y funcionamiento antes del diseño

El grupo rechaza el diseño del prototipo. Se aplaza el rediseño; la interfaz actual sirve únicamente para probar. Esto no autoriza cambios de presupuesto, instalaciones, cuentas, pagos, datos personales o despliegue.

## Trabajo iniciado

Lote `deleg_171ec57c`, dos agentes en paralelo, con archivos exclusivos bajo `prototipos/paideia-local/`:

1. `providers.py`, `tests/test_providers.py`, `PROVEEDORES.md`: adaptador de proveedor con transporte inyectable, configuración apagada por defecto y pruebas offline de requests/respuestas, errores y ausencia de reintentos/fuga de secretos. Groq es candidato técnico; ninguna llamada real ni clave leída por el agente. No cambiar el endpoint actual hasta revisión e integración del coordinador.
2. `catalogue_facts.py`, `tests/test_catalogue_facts.py`, `HECHOS-CATALOGO.md`: hechos tipados y trazables, estados/nulos, fechas, derechos y reglas versionadas de comparabilidad por uso. Positivos solo sintéticos de test; no inventar condiciones de productos reales ni activar publicación por un ISIN válido.

## Recepción e integración

- Inspeccionar módulos y reproducir tests antes de afirmarlos integrados.
- Conectar después con app.py mediante contratos explícitos y pruebas HTTP. Los agentes no modifican app.py ni frontend en paralelo.
- Mantener las pruebas existentes del prototipo. No reemplazar un chat no conectado por un stub presentado como IA.
- Configurar acceso gratuito al proveedor por vía segura solo cuando se vaya a hacer un smoke real autorizado. No pegar claves en chat ni crear facturación.
- Completar después calidad A/B/C, datos verificables/comparación y persistencia/ingesta autorizadas; UI definitiva al final.

## Estado

Módulos recibidos, inspeccionados, reproducidos e integrados en la API local mediante backend_services.py. Verificación del coordinador: 94 tests correctos, 19/19 comprobaciones HTTP y sintaxis JS correcta. Detalle y límites: ../prototipos/paideia-local/BACKEND-INTEGRACION.md y evidence/BACKEND-INTEGRACION.json. Catálogo real cuantitativo y proveedor operativo siguen pendientes: ningún hecho sintético se cargó en el inventario real, ninguna llamada LLM externa ni lectura de claves reales. Los límites económicos y de privacidad no cambian. Diseño intacto.
