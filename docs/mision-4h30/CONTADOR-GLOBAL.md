# Contador global de intentos reales — misión del 4/11/2026

## Qué se ha construido

`prototipos/paideia-local/mission_ledger.py` es un contador con cupo duro, corte y
diario append-only, situado en un directorio **canónico por perfil del sistema
operativo y fuera de cualquier copia del repositorio**:

- Windows: `%LOCALAPPDATA%\Paideia\ledger-missions\<id>\`
- POSIX: `$XDG_STATE_HOME/Paideia/ledger-missions/<id>/` (o `~/.local/state/…`)

Cualquier copia del árbol y cualquier proceso del mismo perfil resuelven al mismo
sitio. La misión existe solo si se ha provisionado a mano su `MISSION.json` con
misión, inicio, corte y cupo. Mientras haya un manifest **activo**, todo envío por el
transporte real de Groq queda contado, sin depender de variables de entorno ni de la
copia del repositorio desde la que se lance.

La reserva se hace **antes** de abrir la conexión, con `flush` + `fsync` del diario
antes de devolver el testigo. Un cierre brusco no regala intentos; un diario ilegible
o un manifest corrupto bloquean el envío (`fail closed`), nunca empiezan de cero.

## Dónde se aplica

Hay exactamente dos rutinas que abren una conexión HTTPS al proveedor y **ambas**
reservan justo antes de conectar:

1. `providers.GroqHTTPSJSONTransport._post` — ruta del chat de la app.
2. `secure_groq_session._guarded_https_post` — ruta de la sesión contada
   (`pai_setup._night_chat_service`) y del CLI de sesión segura.

La primera revisión independiente demostró que la segunda ruta enviaba sin pasar por
el contador; se cerró añadiendo la misma reserva antes de su conexión. Si la reserva
falla, el código devuelve un `ProviderError` con `send_state=not_started` y un código
propio (`mission_exhausted`, `mission_closed`, `mission_unavailable`,
`mission_corrupt`, `mission_guard_unavailable`); la capa HTTP lo traduce a
`CHAT_MISSION_*` con ese mismo `send_state` y un mensaje que dice que no se envió nada.

El estado vive en un directorio propio, `Paideia/ledger-missions`, separado de
`Paideia/missions` (mecanismo de la misión nocturna): así un manifest ajeno no bloquea
la app. Mientras exista un manifest, **antes de su inicio y desde su corte** el envío
se bloquea hasta retirarlo con `scripts/provision_mission.py --close`.

## Qué se ha verificado (offline)

`prototipos/paideia-local/tests/test_mission_ledger.py` (13) y
`tests/test_mission_ledger_boundary.py` (10): ausencia de manifest no consume ni
bloquea; manifest fuera del directorio canónico se rechaza; manifest corrupto falla
cerrado; conteo antes de enviar y persistencia al reabrir; cupo duro sin escritura
extra al agotarse; diario corrupto bloquea en vez de reiniciar; dos misiones activas se
rechazan; estado `used/remaining`; en la frontera del transporte, un envío sin misión
no escribe, una misión activa cuenta exactamente un intento antes de conectar y una
misión agotada **no construye ninguna conexión**; corte duro antes del inicio y desde
el corte; directorio propio separado del mecanismo nocturno (un manifest de la noche
no bloquea); la ruta de `secure_groq_session` también queda bloqueada sin abrir
conexión; y el JSON HTTP lleva `send_state=not_started` con un mensaje explícito.

## Límites que se mantienen

- No es un sandbox: quien controle el proceso, el reloj o el sistema de archivos puede
  borrar el diario o el manifest, o mover la hora. No hay testigo externo.
- Solo cubre rutas que pasen por el transporte real de `providers.py`; un cliente
  propio que hable con el proveedor por otra vía no queda contado.
- La cuota diaria de la app (60/día) sigue existiendo y **no se eleva** para alcanzar
  el cupo de la misión.
- El cupo autorizado por Alejandro es un máximo de 100 intentos reales desde el
  entorno local, con datos ficticios; no es una meta de consumo.

## Estado

Contador implementado y probado offline. **No se ha provisionado todavía la misión ni
se ha hecho ninguna llamada real en esta ventana.** Provisionar consiste en crear el
manifest en el directorio canónico con `cap` y corte correctos; se hará solo después de
que la revisión independiente del bloque de Pai y la suite completa estén en verde, y
quedará documentado aquí con la hora exacta y el consumo real.
