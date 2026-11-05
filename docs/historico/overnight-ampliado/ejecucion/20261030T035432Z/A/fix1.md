# A cycle 1: cierre del límite del proveedor estructurado

## Cambio y alcance

`LocalChatService` solo admite en modo estructurado el tipo exacto `StructuredProviderAdapter` con `FakeChatProvider` exacto, además de las restricciones de aislamiento existentes. La ejecución usa referencias fijadas a los métodos implementados localmente, no despacha métodos suministrados por la instancia; los slots impiden sustituir métodos por instancia. Se vuelve a comprobar el estado antes de cada llamada; un estado inválido devuelve `CHAT_STRUCTURED_INVALID_PROVIDER` (503), distinto de un JSON/respuesta inválidos (502), sin texto crudo ni reintento. El flag `test_only` no es una garantía de seguridad por sí solo.

El fake acepta datos sintéticos `ChatResult` o el guion fijo local de la fixture de navegador. No hay transporte, lectura de credenciales ni selección de callbacks en ese camino. El adaptador exige JSON completo, sin claves duplicadas, constantes no JSON, campos extra, IDs desconocidos o repetidos, ni respuesta truncada, rechazos o herramientas. Calcula en servidor solo con el escenario de ese turno.

## Migración de pruebas

- Antes `FakeEducationProvider.select_education` devolvía objetos arbitrarios; ahora el helper del mismo nombre serializa los mismos casos a `ChatResult` sintético, procesado por el adaptador real. Los casos adversarios y sus aserciones de 502, no divulgación, número de llamadas, consentimiento, escenario y HTTP se conservan.
- `StructuredFixture`/`AdaptedFixture` del servidor de navegador se sustituyen por `StructuredProviderAdapter(FakeChatProvider(..., scripted=True))`. El guion incorporado conserva las ramas explain, calculate, forged y entrada no sintética; `test_scripted_browser_fixture_over_http` las comprueba sobre loopback.
- Las pruebas originales del adaptador para JSON hostil, herramientas, secretos ficticios, error de cálculo, una llamada y ausencia de red siguen ejecutándose. La nueva prueba reproduce el objeto arbitrario `test_only=True`, con `socket.connect` parcheado, y exige rechazo en construcción. Otra prueba comprueba subclases, parcheo de métodos, ausencia de conexiones, y estado mutado.

## Evidencia

RED: `python -m unittest discover -s tests -p test_structured_provider_adapter.py -k arbitrary -v` falló porque no se lanzó `ValueError`. GREEN: el mismo comando pasó. Suite estructurada: 23 pruebas correctas. Suite completa: 301 pruebas correctas, incluida la nueva prueba HTTP. Ejecución completa con guardia en `socket.socket.connect` que solo permite loopback.

## Límites

Esto es aislamiento de código local para fixtures, no sandbox ante un propietario malicioso del proceso Python, que puede reemplazar módulos, globals, builtins o memoria. El camino legado no estructurado conserva su comportamiento y no queda endurecido por esta corrección. Las pruebas son sintéticas y no demuestran calidad de un modelo real ni conectividad externa. No se usaron credenciales ni proveedores reales.
