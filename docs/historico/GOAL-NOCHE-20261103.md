# Paideia — borrador nocturno anterior (sustituido)

> El equipo cambió la prioridad a entregas funcionales. Usar `docs/GOAL-NOCHE-FUNCIONAL-20261103.md`; este archivo se conserva como borrador anterior y no debe ejecutarse en su lugar.

## Preparación, activación y corte

Este archivo prepara un encargo nuevo; no activa por sí solo /goal ni un proceso independiente. El usuario ha elegido trabajar hasta las **2026-11-03T08:00:00+01:00**. La ejecución comienza cuando ordene ejecutar este documento o envíe el slash goal. Consulta el reloj y guarda inicio y corte en un directorio de ejecución nuevo. El corte es absoluto, no se renueva tras reinicios, notificaciones o nuevas delegaciones. Reserva desde las07:40 para pruebas finales, informe y cierre; no empezar desarrollos que no quepan. Detener antes por objetivos viables logrados, bloqueo humano, agotamiento de uso o máximo de dos ciclos de revisión fallidos por bloqueo. No trabajar para rellenar horas. Si el plazo ya ha vencido, no iniciar.

La misión anterior de una hora conserva su corte 00:32:27: este encargo no la extiende ni permite rehacer sus evidencias. Cerrar documentalmente su estado real por separado. Mantener Hermes abierto, PC despierto y conexión; la persistencia de /goal no garantiza ejecución durante suspensión/cierre ni evita límites de turnos o cuota.

## Proyecto y estado que se debe contrastar

Raíz `C:/Users/aleja/Downloads/App Financiera/`; app `app/`; exclusivamente perfil Hermes trabajos. Leer docs/GOAL-UNA-HORA-20261102.md y docs/ia-groq-estructurada/ejecuciones/20261102T233227/ (HITOS-PRINCIPALES.md, CIERRE-CHECKPOINT.md y RESULTADOS.md si ya existe). Revisar código actual, no inferirlo de informes viejos. Docs/ESTADO_Y_PLAN.md contiene tramos históricos que no prueban que haya sesiones activas.

Último resultado verificado por coordinador antes de preparar este documento:404 pruebas Python con pytest (375unittest+29nodos de otro tipo),6GUI exactas deseleccionadas,40Node,19HTTP loopback. Backend sin Tk obligatorio y procedencia test_only cerrada recibieron revisión favorable. Hay parser puro en sesión sintética contada; la primera revisión detectó cambio de proveedor durante admisión y se corrigió. El último dictamen de esa mejora era inconsistente (passed=true con una limitación de proceso Python arbitrario en security_concerns); una aclaración estaba pendiente. Aceptar solo dictamen coherente, no convertir una limitación fuera del modelo de amenaza en garantía ni aprobación general.

La vía estructurada real HTTPS/Groq **no está ensamblada ni autorizada para llamar**. No afirmar calidad real de modelo ni catálogo cuantitativo aprobado. Misiones reales antiguas caducadas: intactas.

## Objetivo de la noche

Entregar una versión local más estable y demostrable, con pasos verificables hacia Pai estructurada y sin introducir más capas ficticias aisladas como sustituto de integración. Priorizar backend y recorrido de usuario; diseño visual al final. El trabajo debe producir código integrado y ejercitado, no solo análisis o nuevos documentos.

## Hito A — consolidar y cerrar las fronteras actuales

1. Resolver el dictamen pendiente del recorrido estructurado sintético y comprobar su alcance. Si aparece un defecto dentro de las fronteras soportadas, TDD y corrección con revisión independiente. No prometer un sandbox contra código con control total del proceso Python: documentar esa exclusión y no gastar ciclos persiguiendo monkeypatch arbitrario de todo el programa.
2. Ejecutar el runner revisado `scripts/run_offline_regression.py` con el intérprete ya instalado que tenga pytest, junto a Node y HTTP local. El intérprete comprobado fue `C:/Users/aleja/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`; verificar que existe, no instalar si falta. Unittest solo no recoge las funciones pytest. Excluir exclusivamente las seis pruebas nativas GUI que enumera el runner; no ocultar fallos con exclusiones de módulos enteros. Conservar errores y cambios de recuento.
3. Mantener no-Tk startup, procedencia de éxitos y errores, consentimiento, admisión, cuota persistente, revocación, deadline, singleflight y estados not_started/unknown/completed. completed no demuestra recepción ni cobro.

Aceptación: regresión pertinente verde y revisión independiente favorable, con exclusiones/limitaciones publicadas y comandos reproducibles. No dar por terminada toda la web.

## Hito B — integración estructurada de sesión, desactivada y probada sin red

Solo tras A verde:

- Ejecutar primero un tracer mínimo de contratos actuales y asignar archivos exclusivos. Construir una ruta de ensamblaje exclusivamente del servidor, desactivada por defecto y no elegible por payload, que use el constructor json_schema best-effort, la fachada singleflight y el transporte contado existentes.
- Exigir misión y ledger verificados para esa ruta, no la ruta legacy sin cuota durable. Los tests usan manifiestos y almacenamiento sintéticos aislados, sin alterar whitelist productiva o misiones antiguas para habilitar pruebas reales.
- Probar el **transporte HTTPS real del código** con HTTPSConnection sustituida e instrumentada y sockets externos bloqueados, no una interfaz post ficticia que no prueba las guardas reales. El modelo/limitación/token/formato deben coincidir con la configuración autorizada de la instancia. Structured Outputs sin herramientas ni streaming y parser local estricto: no suponer soporte estricto del modelo por el esquema válido offline.
- Recorrido conjunto: HTTP local→consentimiento→admisión→sesión y misión→reserva durable→conexión ficticia→guarda tras conexión→un POST→parser puro→editorial y cálculo local. No envolver respuestas reales como FakeChatProvider ni heredar metadatos test_only indebidamente. Escenario de este turno solo local; sin perfil/historial remotos. No continuidad de herramientas ni reintentos silenciosos.
- Ensayar denegación previa, expiración y revocación durante conexión, último cupo, fallo durable y reinicio,429/5xx, fallos TLS/request/read, duplicados/refusal/truncamiento/toolcalls/prosa arbitraria, estado de envío incierto y liberación de admisión en finally. Rechazar antes de salida si autorización o configuración falta.
- Mantener separado el indicador de prueba del hecho de que se ejercita código de transporte real: una conexión instrumentada no demuestra tráfico externo ni compatibilidad efectiva con Groq. No devolver external_sent=false si el estado es incierto en la ruta real futura.

Aceptación: ensamblaje seguro desactivado, pruebas verticales reales del código bajo conexión sustituida, revisión independiente favorable y ninguna llamada externa. Si requiere autorización humana ausente o no se puede garantizar la unión, marcar el hito parcial/bloqueado; no fabricar una pieza fake y declararlo completo. La prueba real posterior queda fuera de la noche.

## Hito C — producto demostrable y datos sin inventar

Si B se completa o se bloquea de forma concreta y existe trabajo independiente seguro:

- Probar el recorrido local completo con navegador aislado y datos ficticios: cuestionario continuo, cero/desconocido/omitido/no preguntado, edición, permiso local renovado al recargar, autoguardado fallido, copias residuales y borrado/reintento; escenario y comparación/simulación sin confundir operación ficticia con contratación.
- Corregir defectos funcionales reproducibles, no rediseñar por estética. No borrar ni migrar silenciosamente datos del navegador del usuario; usar origen de prueba aislado.
- Reconciliar catálogo y fuentes **locales existentes**: identidad, plazo, fecha efectiva, condiciones y permiso por acción. Caso concreto Openbank/YieldMeister6frente12meses; marcar contradicción/cuarentena, no resolverla inventando oferta vigente. Candidato real investigado no equivale a dato cuantitativo autorizado. No inventar TTL ni equiparar display con app_display.
- Si se integra esa reconciliación al catálogo, debe quedar inequívoca la no comparabilidad de condiciones contradictorias o caducadas con tests del servicio y UI; no introducir nuevas tasas o aprobaciones. No investigar interminablemente fuentes sin entregar funcionalidad.
- Preparar un guion corto de demostración reproducible de lo que realmente funciona y lo que está bloqueado. Fixture siempre identificada como ficticia. Inicio normal no finge IA conectada.

Aceptación por subhito: funcionalidad integrada, pruebas locales ejercitadas y revisión; los documentos de reconciliación no significan datos actuales ni derechos de publicación concedidos.

## Hito D — entrega y cierre

- Guardar red/green, resultados, revisiones y cambios por lote en directorio de ejecución nuevo del proyecto, no solo scratch. No sobrescribir informes históricos.
- Revisión por contexto independiente de cambios actuales; sin Git, archivos explícitos y límites, no inicializar Git ni hacer commits. Máximo2ciclos de corrección por bloqueo; no resetear el límite creando otro subagente o cambiando el nombre del hito. Si persiste, mantener deshabilitado el modo y pasar solo a tarea independiente segura o cerrar.
- Ejecutar regresión final tras cambios. Contar en código: seleccionados, aprobados, fallidos, xfailed/xpassed, excluidos y errores de colección; no sumas manuales ni presentar recuentos históricos como nuevos. Mantener resultados por fase y diagnósticos sanitizados. Runner es defensa en proceso: auditar procesos hijos propios, no prometer herencia del guard ni aislamiento absoluto.
- Cerrar servidores e hilos propios en finally, comprobar sus endpoints; no detener servicios ajenos. Si un cierre excede el corte, registrar hora real y no fingir puntualidad. No dejar servidor público ni tareas pendientes indefinidas.
- Actualizar estado actual breve enlazado desde el plan general; informe final con objetivos completos/parciales/bloqueados, evidencia, fallos conservados, alcance real vs simulado, qué requiere al equipo y siguiente acción concreta. No prometer Paideia final ni IA real validada.

## Prohibiciones y permisos

Solo modificaciones del proyecto y perfil trabajos, código propio local, fixtures y ledger de prueba, servidores/navegador loopback aislados y documentación. Sin llamadas de la app a Groq u otros proveedores externos, claves reales, perfiles personales, lectura de secretos de entorno/portapapeles/memoria ajena, ventanas Tk/credenciales, cuentas, pagos, instalaciones, ejecución de código descargado, DB nuevas o despliegues. No saltar auth/WAF, ampliar misiones antiguas ni resetear ledger. Conservar presupuesto0€.

Una futura prueba real requiere permiso concreto, misión nueva vigente, confirmación humana de Free e introducción voluntaria de clave por ventana segura. El checkbox no verifica facturación. Esa interacción no puede suponerse por el encargo nocturno.

## Definición de terminado

Cerrar A y los subhitos viables de B/C con código integrado, pruebas y revisión; entregar explícitamente lo que no se alcanzó. No continuar buscando tareas por llenar la noche. Parar como máximo a las08:00+01 o antes por los límites indicados. Dar reporte corto con Siguiente paso y Qué tenéis que hacer; indicar si no requiere intervención.
