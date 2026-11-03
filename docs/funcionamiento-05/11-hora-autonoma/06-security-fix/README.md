# Frontera de envío de la sesión

El transporte de sesión conecta DNS/TCP/TLS fuera del lock; después adquiere el mismo lock que `revoke`, vuelve a comprobar el reloj absoluto y monotónico y el estado, y ejecuta `HTTPSConnection.request` bajo dicho lock. El punto lógico de compromiso es la comprobación satisfactoria inmediatamente anterior a entrar en `request` bajo exclusión. Si revocar gana el lock antes, no se llama a `request`; si el envío gana, revocar espera a que retorne `request`. No se mantiene el lock durante `getresponse` ni `read`. Una solicitud comprometida puede terminar tras revocar; no se promete cancelación in-flight. Una escritura lenta puede retrasar la revocación hasta el fin/error de `request` y el timeout no es una garantía absoluta de planificación.

El límite temporal se comprueba en el punto lógico, no se garantiza físicamente que ningún bit salga por la red después de la hora: el planificador, TLS y el sistema operativo pueden retrasar ejecución o transmisión. No se hacen reintentos. El contador se incrementa antes de conectar: fallos de DNS/TLS y cancelación durante conexión siguen consumiendo intento. El intento 24 conserva su permiso individual para pasar el guard, aunque al admitirlo se borre la clave de la sesión y se marque `quota_exhausted`; revocación o vencimiento aún lo bloquean. El transporte sin guard conserva la API anterior para el flujo one-shot. Los transportes alternativos inyectados solo para tests no proporcionan por sí mismos esta garantía de frontera.

Pruebas sin proveedor real: `HTTPSConnection` falso determinista cubre revocación y vencimiento durante conexión, respuesta ya iniciada, cierre, 24º intento, fallo de conexión y API anterior. La regresión inicial observada falló porque se realizó `request` después de revocar; tras el cambio pasa. No se verificó transmisión física ni se utilizó IA real.

Desde `C:/Users/aleja/Downloads/App Financiera/prototipos/paideia-local`:

- `python -m unittest discover -s tests -p 'test_session_send_boundary.py' -v` → 6 OK, salida original `target-final.txt`.
- `python -m unittest discover -s tests -p 'test_*.py' -v` → 191 OK, salida original `python-suite-final.txt`.
- `node --test tests/*.test.cjs` → 20 OK, salida original `node-suite.txt`.

Las salidas anteriores a la última prueba adicional se conservan como `target.txt` y `python-suite.txt`.
