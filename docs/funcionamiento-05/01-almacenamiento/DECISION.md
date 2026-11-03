# Almacenamiento 01 — decisión provisional API, snapshot y PostgreSQL

**Fecha:** 2026-10-28  
**Estado:** evaluación aislada; no cambia la arquitectura de producción ni aprueba proveedor.  
**Presupuesto y permisos:** 0 EUR; sin instalaciones, cuentas, claves, API real, base de datos (incluida SQLite), despliegue ni datos personales/reales.

## Dictamen

**Para el alcance actual no necesitamos PostgreSQL para servir el catálogo de lectura.** La recomendación provisional es mantener una API autorizada como **fuente**, normalizar sus respuestas mediante un proceso controlado y servir una **snapshot JSON persistente y versionada**. La consulta de cada visitante lee la snapshot; no hace una llamada a la API de origen por defecto. No se elimina la opción PostgreSQL ni se modifica la app: se deja detrás de un contrato de repositorio que permita sustituir el adaptador JSON más adelante.

Una API no es la persistencia propia de Paideia ni una base de datos de Paideia: da acceso a información que mantiene el proveedor, pero no garantiza para la aplicación una copia normalizada, trazabilidad multi-fuente, último dato bueno, consulta histórica ni transacciones. La snapshot aporta persistencia sencilla; **tampoco** ofrece por sí sola transacciones relacionales, historial auditable completo o coordinación de varios escritores. PostgreSQL organiza y consulta datos; no es la fuente de los hechos, no los actualiza por sí mismo y no resuelve licencias/cobertura.

La decisión es provisional porque el estado actual sigue teniendo **20 candidatos de investigación y 0 ofertas cuantitativas publicables**, sin API de aplicación conectada, sin PostgreSQL ni despliegue. La base del prototipo es Python stdlib y se registran 94 tests y 19 checks HTTP en el estado vigente. Consultar [contrato de esta ronda](../00-CONTRATO.md), [estado actual](../../ESTADO_Y_PLAN.md), [investigación previa de PostgreSQL/ingesta](../../investigacion-apis-02/09-postgresql-ingesta-consulta.md) y [propuesta de despliegue/operación](../../planificacion-03/13-despliegue-operacion/ESPECIFICACION.md). La propuesta de despliegue ya favorece un snapshot revisado para la primera demo y deja la base gestionada como opcional/bloqueada; esta evaluación añade el experimento local, no la convierte en una decisión de hosting.

## Tres opciones

| Opción | Qué se persiste y quién consulta | Ventajas | Límites / falla | Encaje provisional |
|---|---|---|---|---|
| **1. Lectura directa de API por usuario** | Cada lectura llama al proveedor; no queda copia de la respuesta en la app. | Puede reflejar la respuesta del proveedor en ese momento; evita mantener un snapshot local. | Una ráfaga de visitantes produce una ráfaga equivalente de llamadas al proveedor. Si falla, limita o cambia la API, falla cada lectura; no hay último bueno ni recuperación propia tras reiniciar. No normaliza ni une fuentes. | Útil para una comprobación puntual o una ingesta controlada; no elegir como lectura de cada visitante sin verificar cuotas, semántica y disponibilidad de esa fuente. El test no prueba ninguna API real. |
| **2. Cache/snapshot JSON normalizada y persistente** | Un proceso de ingesta trae, valida, normaliza y publica un archivo versionado; la app consulta ese artefacto. | Separa visitas de actualizaciones; conserva la última copia íntegra al reiniciar; fácil de revisar/diff/respaldar y servir estáticamente. Puede mantener fuente, fecha efectiva/recuperación, versión y hash junto a los campos. | La frescura depende de política explícita y de una ingesta autorizada; sin ella, la copia envejece. No ofrece consultas relacionales generales, historial append-only, aislamiento multiusuario ni commits multi-registro. El spike sólo coordina hilos/instancias dentro de un proceso; no acredita varios procesos o hosting. | **Recomendada ahora para catálogo de lectura**, con promoción controlada, último bueno y avisos/exclusión por antigüedad. La política de frescura real debe definirse por fuente/campo antes de publicar datos; no se asigna un TTL de producción genérico aquí. |
| **3. PostgreSQL opcional, por responsabilidades** | Repositorio relacional compartido con adaptador de ingesta y consultas acotadas. | Constraints, joins y consultas estructuradas; transacciones cuando varias escrituras deben confirmarse o revertirse juntas. PostgreSQL describe la transacción como una operación “all-or-nothing” entre pasos concurrentes.[2] | Añade servicio operativo, migraciones, permisos, backup/restore, conexión y coste/riesgo de proveedor. No trae hechos, licencias, ingesta, API ni frescura por sí solo. No se ha creado ni probado DB alguna. | Añadir sólo al activarse un requisito relacional/transaccional real, no por tener API, chat o un número de visitantes sin una medición representativa. |

### Qué significa “DB opcional”

- **Consulta/cache de catálogo:** una base podría conservar identidad, observaciones, vigencias, procedencia e historial; una snapshot JSON sigue siendo una buena interfaz de publicación/último bueno. No confundir el cache de consulta con el origen de los hechos.
- **Transacciones de negocio:** el prototipo no ejecuta operaciones financieras reales; los ensayos son ficticios. Si en el futuro hay escritura de varios registros que deba confirmarse completa o revertirse completa, ése sí es un motivo transaccional para una DB. La propuesta actual no introduce tal flujo.
- **Auditoría:** si se exige una pista append-only consultable, con retención y permisos, tratarla como almacenamiento/auditoría separado del snapshot público. No guardar prompts/perfiles por defecto.
- **Perfil:** el contrato vigente mantiene el perfil en el navegador, opt-in/borrable y fuera del body de chat no autorizado. No moverlo a PostgreSQL como consecuencia automática de añadir un catálogo compartido.

## Spike ejecutado

Código y evidencia reproducible: [`spikes/005-api-cache-vs-direct/README.md`](../../../spikes/005-api-cache-vs-direct/README.md), [JSON](../../../spikes/005-api-cache-vs-direct/results.json), [CSV](../../../spikes/005-api-cache-vs-direct/results.csv). El proveedor es `synthetic_test`; se generaron tres filas genéricas sintéticas, no productos/ofertas financieras. No se enviaron requests de red ni chats, no se usaron credenciales y no se creó ninguna DB.

| Variante, ráfaga de 100 lecturas concurrentes (no chats) | Requests al proveedor fake | Cache hits | Resultados correctos / filas | Latencia local p50 / p95 / p99 |
|---|---:|---:|---:|---:|
| Directa | 100 | 0 | 100 / 300 | 3,603 / 4,101 / 4,256 ms |
| Snapshot JSON persistente, fría al inicio | 1 | 99 | 100 / 300 | 3,993 / 5,627 / 5,641 ms |

Las cifras proceden de Python local con 3 ms de espera artificial por llamada; son orientativas de este harness, no latencia de red, cuota Free, rendimiento de proveedor/hosting ni capacidad para 100 usuarios reales. El cache redujo requests **del proveedor fake** de 100 a 1 y entregó el mismo conjunto de resultados; el p95 local del cache fue algo mayor por coordinación/copia local. No se extrapola una ventaja de latencia.

También se verificó: (a) nuevo proceso reabre snapshot con hash válido y 0 llamadas al proveedor; (b) fallo directo hace 1 request y propaga error sin reintento; (c) refresco fallido o `os.replace` inyectadamente fallido conserva el último archivo bueno y limpia el temporal; (d) el reemplazo actualizado pasa validación de integridad; (e) con TTL=10 s y `serve_stale_on_error=True` explícitos, un snapshot vencido se devuelve con `status=stale_fallback`/`is_stale=true`; sin esa opción, falla cerrado; (f) el valor por defecto es `ttl_seconds=None` y stale fallback `false`. Python documenta la atomicidad del rename exitoso como requisito POSIX y advierte que el reemplazo puede fallar entre sistemas de archivos; el código crea el temporal junto al destino. Esto no acredita durabilidad ante pérdida de energía ni de filesystem de hosting.[1]

La primera prueba de lectura/escritura desde dos instancias en Windows detectó un `PermissionError` al reemplazar mientras otra instancia leía. Se reprodujo en el caso concurrente; compartir un lock/cache de proceso por ruta resolvió la carrera dentro de este proceso y pasó la regresión de lectores concurrentes más 20 refrescos. **No** se añadió lock entre procesos: ése sigue fuera del alcance. La limitación está reflejada en el README/resultados.

### Comandos y salida real

Desde la raíz `C:/Users/aleja/Downloads/App Financiera`:

```text
python3 -m unittest discover -s spikes/005-api-cache-vs-direct -p 'test_storage_spike.py' -v
exit 0 — Ran 11 tests — OK

python3 spikes/005-api-cache-vs-direct/storage_spike.py --run
exit 0 — JSON/CSV escritos — 6/6 checks true
```

La generación y consistencia de JSON/CSV se comprobó programáticamente: dos variantes, 100 lecturas cada una, directa=100 requests, snapshot=1 request/99 hits; conteos y estado de salida coinciden.

## Umbral provisional para decidir

**No hay un umbral de “N visitantes = PostgreSQL”.** Cien lecturas sólo demuestran ahorro de requests a un fake en un proceso, no capacidad pública; la capa de chat/modelo es otra carga. Para el catálogo, **seguir sin PostgreSQL mientras** se cumpla todo lo siguiente:

1. datos de catálogo de sólo lectura para visitantes y publicados como snapshot completo, validado y acotado;
2. un único publicador/ingestor controlado, con una promoción ordenada; sin dos escritores independientes que deban actualizar el mismo conjunto a la vez;
3. sin necesidad de commit atómico entre entidades, cuentas de usuario compartidas, transacciones reales ni consultas históricas/auditoría relacional;
4. la app puede mostrar fuente/fecha/antigüedad y excluir campos que no cumplan la política explícita de frescura;
5. el snapshot se puede servir bajo el SLO que acuerde el equipo, y el último bueno se puede revertir.

**Reevaluar PostgreSQL (o una DB relacional equivalente) al primer requisito duro** de cualquiera de estos tipos: (a) **2 o más escritores independientes/concurrentes** necesitan coordinar cambios y commits atómicos entre varios registros; (b) cualquier flujo exige una transacción multi-entidad con “todo o nada”; (c) aparece estado persistente por usuario que deba compartirse entre dispositivos/servidores; (d) se necesita auditoría/historial consultable con permisos/retención; o (e) consultas relacionales/históricas ya no caben en el repositorio JSON bajo un SLO que el equipo haya definido y medido con datos/carga representativos. El número “2 escritores” es un umbral de requisito, no una afirmación de que las APIs actuales lo necesiten. No se propone un límite arbitrario de bytes/QPS: faltan fuente real, snapshot real y SLO aprobado.

Antes de cualquier opción cloud habría que revisar condiciones/precio, región, copias, conectividad y autorización según el contrato. Este informe no aprueba Supabase, Neon ni otro proveedor.

## Protocolo de repositorio para migrar sin rehacer negocio

Propuesta de interfaz, **no implementada en la app ni aprobada como cambio unilateral**:

1. La lógica de dominio/tooling pide resultados por una interfaz estable, por ejemplo `CatalogReader.read(query) -> CatalogReadResult`; nunca importa SQL, conexión, SDK ni URL de proveedor.
2. El DTO conserva IDs locales ya acordados, familia, unidades, `schema_version`, estado de frescura, `source_id`, fecha efectiva (`as_of`), fecha de recuperación (`retrieved_at`) y versión/hash. No sustituir una fecha efectiva desconocida por hora de descarga ni actualizar una oferta por ausencia en una respuesta parcial.
3. `ApiSourceAdapter` sólo recupera; el pipeline valida cuerpo/esquema, normaliza y crea `SnapshotCandidate`. Promoción controlada publica `JsonSnapshotRepository`; error deja el último bueno y no crea una fila publicable.
4. `PostgresCatalogRepository`, si y sólo si se aprueba, implementa el mismo contrato de lectura/DTO. Escritura limitada al job de ingesta; consultas parametrizadas/allowlist, ningún SQL arbitrario al LLM. Migraciones versionadas y pruebas de conformidad repo→herramientas; comparar respuestas con snapshot antes de cambiar configuración.
5. Mantener la snapshot JSON versionada como exportación/fallback/revisión aunque exista PostgreSQL. El dispatcher/contrato `local-tools.v1` sigue operando sobre IDs locales; migrar storage no debe cambiar reglas, cálculos ni respuestas de negocio.

## Conclusión

**La hipótesis “API + snapshot/cache JSON normalizada basta por ahora” queda parcialmente validada para un catálogo de lectura, bajo las condiciones descritas.** El experimento demuestra persistencia entre procesos, integridad, último bueno y reducción de llamadas en un fake local; no demuestra integración con proveedor, permisos, frescura, capacidad web ni servicio online. PostgreSQL permanece como opción futura para necesidades transaccionales/relacionales concretas; no como sustituto de fuentes ni como una necesidad probada por 100 visitantes.

**Siguiente paso:** seleccionar y autorizar fuentes/campos y definir frescura por familia antes de publicar un snapshot real; esta ronda no ejecuta esa ingesta.  
**Qué tenéis que hacer:** ninguna acción para validar el spike; antes de producción, el equipo debe aprobar esos usos/frecuencias y reabrir la decisión de DB si aparece alguno de los umbrales anteriores.

## Sources

[1] https://docs.python.org/3/library/os.html
[2] https://www.postgresql.org/docs/current/tutorial-transactions.html
