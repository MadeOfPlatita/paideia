# Sesión local acotada — preparación, no ejecución real

El lanzador `app/secure_groq_session.py` no se ha abierto aquí con una clave real ni se ha llamado a Groq. No pega claves en el chat, argumentos, entorno, ficheros, informes ni registros. El usuario introduce personalmente la clave en el campo enmascarado y confirma de nuevo que ha comprobado el plan Free sin facturación. La casilla no verifica el plan ni garantiza coste cero. No crear cuentas, activar pagos ni usar datos personales.

## Uso por el operador, únicamente tras autorización

Desde `app`:

```text
python secure_groq_session.py --deadline-utc 2026-10-29T17:40:20Z
```

Puede elegirse una fecha UTC anterior, nunca posterior al límite absoluto. La ventana se limita también a 3600 segundos desde el inicio mediante reloj monotónico y UTC. Al iniciar tras confirmación, escucha solo `127.0.0.1:8768`; abrir esa dirección local manualmente. La aplicación normal en 8765 no se inicia ni se modifica. Es una sesión temporal en un solo proceso: reiniciar el programa crea otro contador; no constituye un límite compartido entre procesos o reinicios. No iniciar otra sesión para ampliar la autorización.

La entrada se borra antes de iniciar el servidor. El proveedor usa un diccionario privado en memoria, no `os.environ`; revocar o expirar vacía ese diccionario y bloquea futuras llamadas. Python no garantiza borrado físico de cadenas de memoria, y una petición ya en curso puede terminar después de revocar; cierre no la cancela. El contador protegido incluye cada intento de transporte, errores y continuaciones de herramienta; máximo 24, sin reintentos. La admisión limita a un turno concurrente y el proveedor usa una única llamada en vuelo también durante el benchmark. El modelo recibe únicamente la herramienta de cálculo; el catálogo no está autorizado para el modelo.

El chat requiere su propio consentimiento de envío y puede enviar lo que escriba el usuario: usar exclusivamente consultas y datos ficticios. Ni el inicio del servidor ni abrir la ventana generan peticiones externas. `READY test_only=False` indica servidor configurado, **no** conectividad comprobada ni garantía del plan.

## Benchmark opcional

La segunda casilla está desmarcada y requiere autorización independiente. Si se marca antes de iniciar, ejecuta como máximo 18 peticiones A/B/C sintéticas, separadas 21 segundos, con el mismo proveedor, límite compartido de 24 y fecha límite. Un 429 u otro fallo detiene la evaluación, sin reintentos. Revocar interrumpe la espera e impide siguientes llamadas. No hay ganador automático ni evaluación de calidad: los resultados requieren revisión humana y la procedencia de proveedor real se marca `provider_unverified`.

El estado sin claves ni contenidos se escribe en `app/evidence/session-status.json`. Su campo `benchmark` indica `not_started`, `running`, `complete` (informe escrito, no necesariamente 18 éxitos) o `error`. Si se autoriza el benchmark, su informe con respuestas sintéticas se escribe en `app/evidence/session-benchmark.json`; se sustituye al finalizar, por lo que un archivo antiguo no prueba que la ejecución actual haya acabado. Cerrar el proceso mientras hay una petición en curso puede impedir la escritura del informe final. No se guardan datos de conversación ni perfiles reales en esos archivos. Los directorios y archivos deben protegerse con los permisos locales adecuados.

## Verificación offline

```text
python -m unittest discover -s tests -p test_secure_groq_session.py -v
python -m unittest discover -s tests -q
```

Las pruebas usan transportes `test_only` ficticios y servidor de pruebas loopback con puerto efímero. El flujo HTTP pregunta → llamada a calculadora → respuesta se prueba sintéticamente, no demuestra una llamada real ni la calidad de un modelo. La prueba de GUI sustituye widgets por dobles sin abrir una ventana real. No se han usado claves reales.
