# Spike 005 — API directa vs snapshot/cache JSON

**Pregunta:** ¿necesita el catálogo de lectura PostgreSQL o basta con un proveedor de API, normalización y una snapshot JSON persistente?  
**Tipo de dato usado:** exclusivamente `synthetic_test`; tres filas genéricas ficticias, sin productos financieros ni perfiles.  
**Entorno:** Python stdlib; no API/red, chat, credencial, instalación ni base de datos (PostgreSQL, SQLite u otra).  
**Decisión completa:** [docs/funcionamiento-05/01-almacenamiento/DECISION.md](../../../docs/funcionamiento-05/01-almacenamiento/DECISION.md).

## Hipótesis y variantes

1. **Lectura directa:** cada llamada de aplicación ejecuta un `fetch` del proveedor fake y no guarda snapshot.
2. **Snapshot JSON persistente:** fallo en frío hace un único `fetch`; normaliza/valida, guarda `snapshot.v1` con fecha y SHA-256; lecturas posteriores consultan el snapshot y un cache de proceso. Un refresco explícito crea un temporal en la misma carpeta y lo sustituye mediante `os.replace`.
3. **PostgreSQL:** se compara sólo como diseño opcional. No se escribió adaptador ni se creó DB. Sus ventajas aplican cuando hay consultas relacionales, coordinación de escritores o actualizaciones multi-registro transaccionales, no por ser la fuente de información.

`CatalogQueryService` usa el contrato `CatalogReader.read() -> ReadResult`; por ello cambia el adaptador (directo/JSON) sin incluir detalles de almacenamiento en la lógica de consulta. La vía PostgreSQL queda sólo como posible adaptador futuro al mismo contrato, no como código de producción.

## Política de cache incluida

- `CachePolicy()` por defecto: `ttl_seconds=None` (sin expiración automática) y `serve_stale_on_error=False`.
- Caducidad no se infiere de la fecha de descarga. Si se configura TTL, debe ser explícito y además se conserva `retrieved_at_epoch` para comunicar antigüedad.
- El test de respaldo usa TTL=10 segundos y `serve_stale_on_error=True`; sólo entonces devuelve el último snapshot con `status=stale_fallback` y `is_stale=true`. Si la política no permite ese fallback, el error se propaga, sin borrar el último archivo bueno.
- La producción debe definir máximo de antigüedad por fuente/campo, aviso y exclusión de comparaciones. Este spike no asigna TTL ni política productiva.

## Ejecución y resultados

Desde la raíz del proyecto:

```text
python3 -m unittest discover -s spikes/005-api-cache-vs-direct -p 'test_storage_spike.py' -v
exit 0 — Ran 11 tests — OK

python3 spikes/005-api-cache-vs-direct/storage_spike.py --run
exit 0 — 6/6 checks true; results.json y results.csv escritos
```

El comando de benchmark ejecuta **100 lecturas concurrentes por variante, no conversaciones**, con 100 hilos locales y una espera artificial de 3 ms en el fake. Cada lectura devuelve las mismas tres filas sintéticas.

| Variante | Requests fake | Hits | Resultados / filas | p50 / p95 / p99 local (ms) |
|---|---:|---:|---:|---:|
| Directa | 100 | 0 | 100 / 300 | 3,603 / 4,101 / 4,256 |
| Snapshot JSON fría | 1 | 99 | 100 / 300 | 3,993 / 5,627 / 5,641 |

Los valores de latencia sólo describen este proceso Python, sistema de archivos local y delay sintético. No estiman latencia API, hosting, proveedor, free-tier, cuota, capacidad real para 100 usuarios, ni rendimiento de una arquitectura desplegada. El dato observable del experimento es el recuento: el snapshot coalesció 100 lecturas en 1 llamada al fake y 99 hits locales.

Resultados reproducibles: [`results.json`](results.json) y [`results.csv`](results.csv). El JSON registra comando, `exit_code`, clasificación, latencia orientativa, integridad/reinicio y comprobaciones. El CSV conserva los dos agregados de ráfaga.

## Comprobaciones realizadas

- 100 lecturas directas: 100 llamadas al fake; el camino directo propaga fallo del proveedor con una sola llamada, sin reintento.
- 100 lecturas concurrentes a snapshot fría: una llamada, 99 hits y 100/100 resultados; tres filas por lectura, conjunto consistente.
- Reinicio real del proceso Python: el hijo abre snapshot íntegra con el proveedor fake configurado para fallar; devuelve tres filas, checksum válido y 0 llamadas al proveedor.
- Integridad: checksum SHA-256 del payload normalizado; alteración del archivo se rechaza en una lectura fría y se repara desde el fake en otro proceso. No se sirve un archivo con checksum incorrecto.
- Actualización: reemplazo de versión completa valida; una excepción inyectada en `os.replace` conserva exactamente los bytes anteriores y limpia el temporal.
- Concurrencia: lectores y escritor en un mismo proceso, con instancias distintas sobre la misma ruta, completan 320 lecturas y 20 refrescos sin respuesta parcial/corrupta. La coordinación usa lock y cache en memoria por ruta dentro del proceso.
- Expiración/fallback: casos explícitos de stale permitido y fail-closed; por defecto no hay TTL automático ni stale fallback.

## Límites y hallazgos

- `FakeProvider` nunca accede a red; la fixture no es un catálogo ni una oferta. Sin fuente real no se midió cobertura, frescura, semántica, derechos, cuotas ni latencia.
- El lock sólo cubre instancias del **mismo proceso**; no hay coordinación entre procesos/hosts que escriban la misma ruta. Ese escenario no queda validado.
- La escritura hace `flush`/`fsync` del temporal y reemplazo dentro del mismo directorio. No es backup ni garantía de durabilidad ante caída eléctrica/host/filesystem. Python documenta la atomicidad del rename exitoso como requisito POSIX; la evidencia aquí no sustituye una prueba en el filesystem de producción.[1]
- La primera prueba en Windows con locks separados por instancia falló con `PermissionError` al reemplazar mientras había lectores. El control compartiendo el mismo repositorio pasó; luego se implementó lock/cache compartido por ruta, y la prueba concurrente pasó. La solución no se presenta como lock multiproceso.
- PostgreSQL relacional/transactional no se ejercitó: ninguna DB fue creada o simulada con SQLite.

## Verdict: PARTIAL

### What worked

- Una snapshot JSON normalizada persiste entre procesos, comprueba integridad y puede conservar el último bueno ante errores de actualización.
- Para esta ráfaga sintética, el acceso por snapshot redujo las llamadas al fake de 100 a 1; el resultado no mide capacidad pública.
- Caducidad y stale fallback son elecciones explícitas, con `None`/`false` como defaults y un comportamiento degradado verificable.
- La interfaz de lectura separa consumidor de almacenamiento y permite proponer migración por adaptador.

### What didn't

- No se probó un proveedor/API real, licencia, respuesta cambiante, hosting, actualización programada ni uso de 100 personas reales.
- No se probó escritura coordinada entre procesos/hosts, recuperación ante fallo de máquina ni política productiva de frescura.
- No hay evidencia que justifique elegir o descartar PostgreSQL para futuras transacciones/auditoría; la prueba sólo responde al catálogo actual de lectura.

### Recommendation for the real build

Usar API autorizada como fuente y snapshot versionada como almacenamiento/publicación de catálogo sólo si el responsable confirma el uso de esos datos, su vigencia y atribución. El motivo para añadir PostgreSQL no es guardar los hechos: sus transacciones son pertinentes cuando un flujo necesita que varios pasos se confirmen o reviertan como una unidad, que es precisamente el comportamiento descrito en la documentación oficial.[2] Mantener una ruta de lectura de repositorio, publicar el último bueno y medir el modo de fallo con fuentes reales autorizadas antes de producción. No crear PostgreSQL ahora para resolver un problema de lecturas del catálogo que la snapshot cubre; reevaluarlo cuando aparezca el primer requisito relacional duro: **2+ escritores independientes que necesitan commits atómicos**, estado persistente compartido por usuario, auditoría consultable con retención o consultas relacionales que no cumplan un SLO acordado desde JSON. El número de visitantes por sí solo no es umbral demostrado.

**Siguiente paso:** validar fuente/campos/uso permitido y acordar frescura por campo antes de ingestar información real.  
**Qué tenéis que hacer:** ninguna acción para repetir este spike; para el servicio real, el equipo debe autorizar el uso de datos y definir el SLO/política de antigüedad.

## Sources

[1] https://docs.python.org/3/library/os.html
[2] https://www.postgresql.org/docs/current/tutorial-transactions.html
