# Medición local acotada de capacidad — 4/11/2026

Prueba sin proveedor, credenciales ni red externa: servidor WSGI `api/index.py` en `127.0.0.1`, un único proceso con hilos, API servida desde el árbol local (no Vercel). La ejecución terminó y cerró el servidor.

Se lanzaron por separado 40 consultas GET por ruta, con hasta 8 hilos de cliente, sin carga sostenida ni datos personales:

| Ruta | HTTP 200 / consultas | Objetos JSON | Mediana | Máximo |
|---|---:|---:|---:|---:|
| `/api/status` | 40/40 | 40/40 | 3,965 ms | 515,01 ms |
| `/api/catalogue` | 40/40 | 40/40 | 4,965 ms | 512,71 ms |

Script reproducible de la sesión: `paideia_local_load_probe.py` en el scratch del perfil (sujeto a limpieza automática). No se midió la IA ni el chat, sesiones simultáneas, capacidad sostenida, memoria, otros equipos o servicios de terceros. Ocho hilos de cliente no equivalen a ocho usuarios simultáneos; estos resultados no predicen la capacidad de producción.
