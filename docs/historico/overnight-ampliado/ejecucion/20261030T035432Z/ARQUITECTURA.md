# Arquitectura provisional y límites de la ejecución

## A. Adaptador ficticio

`ChatResult` programado → `StructuredProviderAdapter` cerrado → selección de IDs → `LocalChatService` en modo estructurado explícitamente test-only → textos editoriales del servidor. El fixture no tiene transporte real y el servicio solo admite el adaptador/tipo concretos en esta modalidad. Una clase cualquiera con `test_only=True` ya no basta. La revisión independiente aprobó este alcance (`REVISION-2.json`): no es sandbox contra quien controle el proceso Python ni integración Groq.

`scenario` solo procede de la solicitud actual con sus supuestos expresos; el servidor valida y ejecuta `domain.calculate_scenario`. La interfaz verifica esquema, IDs/textos y coincidencia de supuestos, pero confía en la aritmética del servidor. Un servidor comprometido queda fuera de la prueba. `structured_eval.py` evalúa fixtures sintéticas, no calidad del proveedor; el ganador permanece null.

## B. Hechos y comparabilidad

Catálogo real y facts sintéticos permanecen separados. El comparador exige scope, unidad, permiso de acción y dos límites de frescura explícitos; un `None` en cualquier límite causa `FRESHNESS_BOUNDS_UNCONFIGURED`, no se inventa TTL. `display` no equivale a `app_display`. El servidor normal no tiene política/facts aprobados. Las pruebas no publican ofertas ni determinan permisos reales.

## C. Snapshot aislado

`SyntheticSnapshotRepository` valida fixture versionado, campos y procedencia, política temporal de prueba, checksum y escribe temporal con flush/fsync antes de replace. Pruebas HTTP y navegador con dos candidatos ficticios solo muestran metadatos (`quantitative_ready:false`). Es un experimento en directorio propio y un solo escritor/instancia/proceso; no implementa ingesta de API real, coordinación multiproceso, autenticación criptográfica ni garantía de supervivencia a pérdida eléctrica. No crea DB.

## D. Perfil y ensayo

Perfil local opcional: datos de prueba distinguen cero/desconocido/omitido/no preguntado, guardado opt-in y revocación. Ensayo no contrata, no solicita credenciales, no envía importe y no atribuye condiciones desconocidas. Se invalida la confirmación al retroceder para editar. La impresión solo fue emulada con CSS, sin PDF/impresora real. Revisión final de la interfaz continúa pendiente: no presentar el objetivo completo hasta recibirla.

## Handoffs

La ruta legacy de prosa libre sigue ejecutable, limitada y NO aprobada; el trabajo nuevo no la convierte en segura. La activación de un proveedor real, A/B/C, perfil remoto, derechos de publicación y hosting siguen sujetos a autorización y validación separadas.
