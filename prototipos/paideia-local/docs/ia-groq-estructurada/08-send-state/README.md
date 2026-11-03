# Primera rebanada: estado local de envío

`GroqHTTPSJSONTransport.post` mantiene un estado por llamada: `not_started` antes de entrar a `request`, `unknown` inmediatamente antes de invocarlo dentro del guard, y `completed` cuando retorna. `completed` solo indica que la llamada local retornó; no prueba recepción, procesamiento ni respuesta del proveedor. La conexión previa bajo guard conserva su orden; no hay reintentos añadidos. Si no hay guard, una conexión implícita dentro de `request` produce estado conservador `unknown` ante fallo.

Las excepciones de transporte operacional son `ProviderError` con código fijo y `send_state`; el error original no se encadena. La validación previa conserva `ValueError` por compatibilidad. Los límites de transporte y proveedor reconstruyen errores y limpian sus propios frames de salida. No se garantiza sanitización de frames del llamador ni objetos retenidos independientemente; no capturar locales en producción.

El proveedor propaga el estado con transporte directo exacto `GroqHTTPSJSONTransport` o el wrapper exacto `_CountedTransport` vinculado al transporte HTTPS exacto no sintético; otros wrappers se mantienen en `unknown`. Una respuesta HTTP 429 o error de parseo después de un `post` completado lleva `completed`. La reserva y el guard no cambian; errores antes de envío son `not_started`. La propagación termina en la excepción Python: no se ha modificado ni verificado el DTO HTTP. No debe interpretarse `unknown` como `external_sent=false` ni afirmar recepción remota.

Verificación sin red: `tests/test_transport_send_state.py` usa el transporte productivo, `HTTPSConnection` sustituido y `socket.create_connection` bloqueado; comprueba fases, un solo request, errores sanitizados, 429 y parseo. No se ha ejecutado llamada real ni GUI.
