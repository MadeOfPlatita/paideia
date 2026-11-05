# Contador global de intentos reales — misión del 4/11/2026

> **Corrección de continuidad, 4/11/2026:** la segunda revisión independiente fue **desfavorable** (`REVISION-CONTADOR-CICLO-2.md`). El manifest de la misión de 4 h 30 min fue retirado tras 15 intentos reales; no reutilizar esta misión ni su script de provisión para otra ventana. Aunque las rutas indicadas abajo se corrigieron después de aquella revisión, no hay dictamen favorable sobre esta versión. En una prueba independiente de lock obsoleto se concedieron 6 reservas para un cupo de 5: el máximo no está acreditado en ese caso. Hasta reparar y revisar la versión exacta, **no usar este mecanismo para autorizar nuevos envíos**.

## Qué se ha construido

`app/mission_ledger.py` es un contador con cupo duro, corte y
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

`app/tests/test_mission_ledger.py` (13) y
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
- Solo cubre las dos rutas enumeradas arriba: el transporte real de `providers.py`
  y `_guarded_https_post` de `secure_groq_session.py`. Un cliente propio que hable
  con el proveedor por otra vía no queda contado.
- Las pruebas del proyecto pueden reservar intentos incluso con HTTPS sustituido.
  La revisión observó **85 reservas de 100** en una suite offline con manifest activo.
  No ejecutar pruebas con un manifest real activo; usar un directorio de estado
  absoluto, independiente y comprobado para cada prueba. `LOCALAPPDATA` relativo
  no aísla, porque el módulo vuelve al perfil real.
- La recuperación del lock obsoleto no garantiza exclusión mutua si el primer
  poseedor sigue vivo. No usar el cupo en condiciones reales hasta corregir y revisar
  esa carrera y los demás límites enumerados en la segunda revisión.
- La cuota diaria de la app (60/día) sigue existiendo y **no se eleva** para alcanzar
  el cupo de la misión.
- El cupo autorizado por Alejandro es un máximo de 100 intentos reales desde el
  entorno local, con datos ficticios; no es una meta de consumo.

## Estado

En la misión histórica se contaron 15 intentos reales; se realizaron pese a que la
segunda revisión era desfavorable, un incumplimiento reconocido en el cierre de esa
misión. El manifest de aquella ventana se retiró; el diario se conserva. La misión
posterior no ha realizado llamadas reales y necesita una provisión propia, segura y
revisada: la herramienta histórica fija un corte que ya pasó. Véanse
`../CIERRE-4H30-20261104.md` y `../PAIDEIA-HASTA-BLOQUEO-SEGUIMIENTO.md`.
