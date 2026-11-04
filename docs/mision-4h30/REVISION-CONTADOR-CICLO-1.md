# LEDGER_REVIEW — revisión adversarial del contador global de intentos reales

Fecha: 2026-11-04 (UTC), entorno Windows 11, Python 3.11.15.
Objeto: `prototipos/paideia-local/mission_ledger.py` (nuevo), su gancho en
`providers.GroqHTTPSJSONTransport._post` y los mapeos `CHAT_MISSION_*` de
`backend_services.py`.
Método: pruebas propias, offline, sin clave, sin red y sin tocar el perfil real.
`LOCALAPPDATA` se apuntó a un directorio temporal por caso; `.env` no se ha leído
ni impreso; no se ha llamado a Groq. Los 13 tests del autor pasan
(`tests/test_mission_ledger.py`, 13/13), pero no cubren B1–B5.

Veredicto: **NO PASA** (`passed: false`). La propiedad básica «contar antes de
conectar y no devolver cupo» está bien implementada en el transporte ordinario,
pero hay una ruta que envía de verdad sin pasar por el contador, el corte no se
aplica en la frontera real, el contador colisiona con el manifest de la misión
nocturna preexistente, la suite del proyecto consume cupo real y el
`send_state=not_started` no llega al JSON HTTP de la app.

Scripts y salidas crudas en
`C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/cache/scratch/ledger_review/`
(`probe_core.py`, `probe_http.py`, `probe_fs.py`, `probe_multi.py`,
`probe_lock.py`, `probe_extra.py`, `evidence/`).

---

## 1. Hallazgos bloqueantes

### B1. Bypass total por la ruta de sesión contada (`secure_groq_session`)

`providers.GroqHTTPSJSONTransport` **no** es el único punto que abre la conexión
al proveedor. `secure_groq_session._CountedTransport._post` no llama a
`providers._post`: llama a `_guarded_https_post(upstream, ...)`, que abre su
propio `http.client.HTTPSConnection` y hace el POST:

- `secure_groq_session.py:373` → `return _guarded_https_post(upstream, **kwargs, send_guard=send_guard)`
- `secure_groq_session.py:416` → `connection = http.client.HTTPSConnection(GROQ_HOST, timeout=timeout)`
- `secure_groq_session.py` no importa `mission_ledger` en ningún punto
  (`rg mission_ledger secure_groq_session.py` no devuelve nada).

Esta ruta es la que construye `pai_setup._night_chat_service` cuando
`PAIDEIA_NIGHT_MISSION_ENABLED=1` (`pai_setup.py:246`, `Session(...)`), y también
la que usa el CLI `secure_groq_session.py --mission-config`. Con una misión
global activa (cap=1) y el `HTTPSConnection` sustituido por un doble offline:

```
python probe_extra.py   # evidence/probe_extra.json
"counted_session_bypass": {
  "answer": "ok",
  "connections": 1,
  "ledger_journal_exists": false,
  "ledger_used": 0
}
```

Es decir: **un POST real, respuesta válida y cero registros en el ledger**. El
`mission_ledger.py` documenta que no protege «rutas que no pasen por
`providers.GroqHTTPSJSONTransport` con el transporte real»; esta ruta *sí* usa
ese transporte como upstream, pero no su `_post`, así que la cobertura que
promete `CONTADOR-GLOBAL.md` («el único punto que abre la conexión HTTPS») es
falsa. Requisito (3) incumplido.

### B2. El corte no bloquea en la frontera real: solo deja de contar

`reserve_for_active_mission` filtra primero con `active_mission(now)`. Si
`now >= cutoff`, no hay misión activa, devuelve `None` y `_post` sigue adelante
con la conexión y sin escribir en el diario. `MISSION_CLOSED` solo se produce
llamando a `reserve()` directamente; es inalcanzable desde `_post` salvo una
carrera de microsegundos entre las dos lecturas del reloj.

Evidencia (`evidence/cutoff_clock.txt`), manifest con `cutoff = now+1min` y
cap=100:

```
active_now: True
active_at_cutoff: False
transport_path before_start: None (NO BLOCK)
direct_reserve before_start: MissionBlocked MISSION_CLOSED
transport_path at_cutoff: None (NO BLOCK)
direct_reserve at_cutoff: MissionBlocked MISSION_CLOSED
transport_path after_cutoff: None (NO BLOCK)
direct_reserve after_cutoff: MissionBlocked MISSION_CLOSED
journal: 0
```

Y en el transporte completo (`probe_core.py`, caso M2, manifest caducado hace
1 minuto, cap=5): `status: 200`, `journal: 0`, `connection_constructed: true`.
El test del autor `test_cutoff_blocks_even_with_budget_left` llama a `reserve()`
directamente, por lo que prueba una rama que el transporte nunca ejecuta. Si el
corte autorizado es un tope duro, después de la hora límite la app puede seguir
enviando (hasta la cuota diaria de 60, no contada). Requisito (4) incumplido.

### B3. Colisión con el manifest de la misión nocturna preexistente

`active_manifests()` recorre **todos** los subdirectorios de
`%LOCALAPPDATA%/Paideia/missions/` y llama a `load_manifest(child/"MISSION.json")`.
El mecanismo anterior (`mission_budget.py`) guarda su manifest exactamente ahí:

```
ledger_root: ...\Paideia\missions
night_dir:   ...\Paideia\missions\paideia-night-20261104
same_parent: True
night_manifest_inside_ledger_root: True
night_schema: paideia-night-mission.v1
ledger_schema: paideia-mission-manifest.v1
```
(`evidence/roots.txt`)

En cuanto exista `paideia-night-20261104/MISSION.json`, el ledger lo lee, ve un
schema distinto y falla cerrado **para siempre y para todos los envíos**, incluso
fuera de cualquier ventana:

```
probe_core.py, caso H:
{"error": {"type": "ProviderError", "code": "mission_corrupt",
           "send_state": "not_started"},
 "events": [], "connection_constructed": false}
```

Hoy el perfil real no tiene `%LOCALAPPDATA%/Paideia` (ver §3, requisito 7), pero
los dos mecanismos están diseñados para convivir en el mismo directorio y no
pueden: o no se provisiona la misión nocturna, o la ruta ordinaria queda muerta
con `CHAT_MISSION_UNAVAILABLE`. Además, cualquier `MISSION.json` ajeno que se
deje en ese árbol bloquea la app entera. Esto no es «fail-closed ante corrupto»:
es un falso positivo estructural por compartir espacio de nombres.

### B4. La suite del proyecto consume cupo real de la misión

Cualquier test que use el transporte real cuenta, aunque `HTTPSConnection` esté
sustituido por un doble: la reserva ocurre antes de construir la conexión. Con
un perfil temporal y una misión activa cap=100:

```
tests/test_transport_send_state.py  delta=13  (12 passed)
tests/test_providers.py             delta=1   (20 passed)
tests/test_service_provenance.py    delta=1   (5 passed)
tests/test_session_send_boundary.py delta=1   (8 passed)
total_attempts=16   routes: {'groq_chat': 16}   n_values: 1..16
```
(`evidence/suite.txt`)

Ninguno abrió red (todos parchean `HTTPSConnection`), pero los 16 quemaron el
cupo real. Una o dos ejecuciones de `pytest` durante la ventana agotan los 100
intentos antes de cualquier uso real, y a partir de ahí los propios tests que
esperan un envío correcto empiezan a fallar con `mission_exhausted`. El autor
presenta «pruebas que usen el transporte real» como cobertura; operativamente
es una fuga de cupo. Requisito (1)/(3) en la práctica.

### B5. `send_state=not_started` no llega al HTTP de la app

El transporte sí devuelve `ProviderError("mission_exhausted",
send_state=NOT_STARTED)`, pero al cruzar `backend_services._tools_chat` el estado
se descarta:

- `backend_services.py:621` → `send_state=_trusted_send_state(service._provider, error)`
- `_trusted_send_state` exige `type(provider) is _SingleFlightProvider`
  (`backend_services.py:288`); en la ruta ordinaria el provider es un
  `GroqProvider` normal, así que devuelve `None`.
- `app.py:249-251` solo añade `send_state` si es un string no nulo.

Resultado real con la app (`app.create_server`, `LocalChatService` con
`tools_enabled=True`, transporte real y clave falsa; misión ya agotada, así que
no se intenta conexión) — `evidence/app_route.txt`:

```
service: LocalChatService tools: True
service_problem: 429 CHAT_MISSION_EXHAUSTED send_state= None
json: {"error": {"code": "CHAT_MISSION_EXHAUSTED",
                 "message": "No se pudo completar la llamada al proveedor; ...",
                 "request_id": "...", "retryable": false}}
```

Y el mismo resultado por la ruta de servicio usada en `probe_http.py`:

```
attempt_1: {"status": 429, "code": "CHAT_MISSION_EXHAUSTED", "send_state": null}
attempt_2: {"status": 429, "code": "CHAT_MISSION_EXHAUSTED", "send_state": null}
app_error_json: {"error": {"code": "CHAT_MISSION_EXHAUSTED",
                "message": "No se pudo completar la llamada al proveedor; ...",
                "request_id": "...", "retryable": false}}
http_status: 429
journal_lines: 1
trusted_send_state_direct: null
```

El código y el 429 son correctos y **no se construyó ninguna conexión**, pero el
cliente no recibe `send_state: not_started`; el contrato del requisito (2) no se
cumple en el mapeo HTTP. (Nota adicional: los dos intentos bloqueados consumieron
la cuota diaria: `calls_day: 2` de 60.)

---

## 2. Requisitos, uno a uno

| # | Requisito | Resultado | Evidencia |
|---|---|---|---|
| 1 | Se cuenta antes de abrir la conexión; fallo/cierre posterior no devuelve cupo | **PASA** | `probe_core.py` B: en `HTTPSConnection.__init__` el diario ya tenía 1 línea. C1/C2/C3: tras fallo en `__init__`, en `request` y revocación del guard, el diario sigue creciendo (2, 3, 4). `probe_fs.py` crash: proceso hijo `os._exit(7)` tras la reserva; diario=1 y el siguiente envío es `n=2`. |
| 2 | Cupo agotado: ninguna conexión y error con `send_state=not_started`, incluido el HTTP | **PARCIAL** | Transporte: D1/D2, `mission_exhausted` + `not_started`, `connection_constructed: false`, diario intacto. HTTP: B5, falta `send_state` en el JSON. |
| 3 | Sin bypass por otra copia, otro proceso, reinicio, WSGI ni `_post` directo | **NO PASA** | Otra copia y otro proceso: `probe_multi.py`, 20 procesos cap=5 → 5 éxitos, 5 registros, sin `n` duplicados; copia del repo escribe en el mismo diario. Reinicio: `n=1,2`. `_post` directo: D2. WSGI (`api/index.py`): no tiene endpoint de chat ni importa `providers`, no puede enviar. **Pero** la ruta `secure_groq_session` sí envía sin contar (B1). |
| 4 | El corte bloquea aunque quede cupo; fuera de la ventana lo ordinario funciona | **NO PASA** | B2: `reserve_for_active_mission` devuelve `None` en/después del corte y el envío sale (200, diario 0). Antes de `start` también sale (M1). Sin manifest, sale (A). `MISSION_CLOSED` solo por `reserve()` directo. |
| 5 | Fail-closed ante manifest corrupto, diario corrupto, directorio no escribible y dos misiones activas | **PASA (con reservas)** | E1/E2 → `mission_corrupt`, 0 conexiones. F1/F2 → `mission_corrupt`, 0 conexiones. Diario como directorio o de solo lectura → `mission_unavailable`, 0 conexiones. G (dos activas) → `mission_corrupt`, 0 conexiones. Reserva: B3 (manifest ajeno legítimo también bloquea) y B4 (lock no-`FileExistsError` sale sin tipo, ver L2). |
| 6 | La cuota diaria existente no se eleva | **PASA** | `pai_setup.py:176` sigue `calls_per_day=60`; `git diff -U0 pai_setup.py | grep calls_per_day` solo muestra la línea nueva `+ calls_per_day=limit` de la ruta nocturna (servicio distinto, no `app.py`). `service.quota()` devuelve `calls_per_day: 60`. |
| 7 | El estado real del usuario no se ha tocado | **PASA** | `ls "$LOCALAPPDATA/Paideia"` → `No such file or directory` antes y después. Todos los probes fijan `LOCALAPPDATA` a `.../cache/scratch/ledger_review/cases/...`; ningún `attempts.jsonl` se creó en el repo (verificado con `find`). |

---

## 3. Otros agujeros buscados

| Vector | Resultado | Detalle |
|---|---|---|
| Carrera entre dos procesos (condiciones normales) | **Sin fuga** | 20 procesos, cap=5: 5 éxitos, 15 `mission_exhausted`, 5 registros con `n=1..5`, 5 pids distintos, sin duplicados. `probe_multi.py`. |
| Lock obsoleto (>60 s) | **Fuga posible** | `_Lock._break_if_stale` borra el lock ajeno y `__exit__` hace `unlink` sin comprobar propiedad. Con `LOCK_STALE_SECONDS=0.001` (equivalente a un poseedor legítimo que tarda >60 s), 3 hilos solapan dentro del lock (`max_inside: 2`); `reserve()` con cap=5 llegó a conceder **6** reservas en una ejecución y, en la repetición, 5 reservas pero con `n` duplicados (`distinct_n: 3`, duplicado el 3). Control con 60 s: 5/5, `distinct_n: 5`. `probe_lock.py`. |
| Lock como directorio / `os.open` con otro `OSError` | **Falla cerrado pero sin tipo** | `_Lock.__enter__` solo captura `FileExistsError`; un `PermissionError` (lock que es un directorio, ACL, EACCES) escapa de `_post` y de `post()`. En la app se convierte en `503 CHAT_PROVIDER_UNAVAILABLE` con `send_state: null` (no `CHAT_MISSION_UNAVAILABLE`); no se envía nada. `probe_extra.py`. |
| Symlink / junction del directorio de misión | **Aceptado** | Un junction `missions/m1 → outside_target` con `MISSION.json` válido pasa `load_manifest` (ambos lados se resuelven) y el diario se escribe fuera del árbol canónico (`journal_in_target: 1`). `probe_fs.py`. |
| `attempts.jsonl` hardlinkeado fuera | **Aceptado** | `os.link` a un fichero externo: el registro se escribe en el fichero externo (`outside_file_written: 1`) y se lee por la ruta de la misión (`journal_via_mission: 1`). |
| Manifest fuera del directorio canónico | **Rechazado** | `MISSION_UNAVAILABLE`. `probe_core.py` J1. |
| Manifest que declara otro `mission_id` que su directorio | **Rechazado** | `MISSION_UNAVAILABLE`. J2. |
| Ids raros | **Sin traversal** | Rechazados `""`, `..`, `a/b`, `a\b`, `"mission "` (espacio). Aceptados por `mission_dir` los nombres reservados Windows `CON`/`NUL`, Unicode (`mïssion`, `①`) y longitud 300; no se pueden provisionar como directorio (fallan cerrado al escribir). K. |
| Reloj movido | **Desactiva el guard** | Con manifest válido, `reserve_for_active_mission(now=start−1s)` y `now=cutoff` devuelven `None` (no bloquean, no cuentan). No hay ancla monotónica para la ventana. `evidence/cutoff_clock.txt`. |
| Doble conteo | **No observado** | Un `_post` escribe exactamente una línea (B); sin `n` duplicados en 20 procesos con el umbral real (60 s). |
| Tests existentes que consumen cupo | **Sí** | 16 intentos medidos en 4 ficheros (B4). Los tests de la ruta de sesión no consumen porque esa ruta hace bypass (B1). |
| Ruta WSGI | **No aplica** | `api/index.py` no tiene `/api/chat` ni importa `providers`: no puede enviar al proveedor. |
| `.env` / clave real | **No tocado** | No se ejecutó `app.main()`; `env_local.load_env` solo se llama ahí. No se leyó ni imprimió `.env`. |
| Guard ausente (`mission_ledger.py` no importable) | **Falla cerrado** | Copia con solo `providers.py`: `mission_guard_unavailable` + `not_started`, 0 conexiones. `probe_extra.py`. |

---

## 4. Límites que quedan (documentados o residuales)

1. **No es un sandbox**: borrar `attempts.jsonl` (o el directorio de la misión)
   reinicia el contador sin error; no hay testigo externo. Ya está declarado.
2. **Reloj**: la ventana se evalúa con reloj de pared; moverlo antes de `start`
   o después del `cutoff` desactiva el guard (y, por B2, permite enviar sin
   contar). No hay ancla monotónica.
3. **Lock obsoleto**: un poseedor que tarde más de 60 s (proceso suspendido,
   `fsync` colgado, depurador) permite superar el cupo; `__exit__` borra el lock
   aunque ya no sea suyo. Demostrado con umbral artificial; con 60 s reales hace
   falta un estancamiento de ese orden.
4. **`OSError` no tipado en el lock**: lock que es directorio, ACL denegada,
   `EMFILE`, etc. → 503 `CHAT_PROVIDER_UNAVAILABLE` en vez de
   `CHAT_MISSION_UNAVAILABLE`; sin `send_state` y sin envío.
5. **Junction/symlink/hardlink**: el estado puede acabar físicamente fuera del
   directorio canónico; la comprobación de «manifest fuera del directorio» no
   cubre el directorio enlazado ni el diario enlazado.
6. **`LOCALAPPDATA` es la raíz**: un proceso lanzado con otro `LOCALAPPDATA`
   tiene un ledger independiente. Es consustancial al diseño por perfil, pero
   conviene saberlo.
7. **Cuota diaria**: no se eleva (60), pero cada intento bloqueado por la misión
   consume una llamada de las 60 (`calls_day: 2` tras dos bloqueos). 60 intentos
   bloqueados agotan la cuota sin haber enviado nada.
8. **Import fail-closed**: cualquier copia/despliegue sin `mission_ledger.py`
   deja el chat muerto con `mission_guard_unavailable`. En Vercel/WSGI no hay
   chat, así que hoy no afecta a esa ruta.
9. **Escaneo del árbol**: `active_manifests` lee todos los subdirectorios en cada
   envío; un `MISSION.json` ajeno (B3) bloquea todo. El coste O(n) es irrelevante
   con cap=100.
10. **Ids**: `mission_dir` acepta nombres reservados de Windows y longitud
    ilimitada; no permiten traversal y fallan cerrado al intentar provisionar,
    pero el validador no es el mismo que el de `mission_budget`
    (`[A-Za-z0-9][A-Za-z0-9._-]{0,63}`).
11. **Corte de energía a mitad de append**: una línea partida deja el diario
    «corrupto» y bloquea todos los envíos hasta repararlo a mano (fail-closed,
    sin undercount, pero es una parada total).
12. **Lock tras un crash**: el proceso muerto deja el `lock`; durante hasta 60 s
    los envíos fallan con `mission_unavailable` (el `_Lock` no lo rompe hasta
    superar `LOCK_STALE_SECONDS`).

---

## 5. Lo que sí está bien

- La reserva ocurre estrictamente antes de `HTTPSConnection(...)` y con
  `flush` + `fsync`; el crash test lo confirma (`n=1` persistido, siguiente `n=2`).
- No hay devolución de cupo en fallos posteriores (init, request, guard).
- Con el cupo agotado no se construye ninguna conexión, ni por `post()` ni por
  `_post()` directo.
- Manifest corrupto, diario corrupto, diario no escribible y dos misiones
  activas fallan cerrado con códigos `mission_*` y `not_started`.
- La concurrencia normal (20 procesos, umbral real) respeta el cupo exactamente.
- La cuota diaria de la app sigue en 60 y el estado real del perfil no se ha
  tocado.

---

## 6. JSON de veredicto

```json
{
  "passed": false,
  "blocking_defects": [
    {
      "id": "B1",
      "title": "La ruta secure_groq_session envía sin pasar por el ledger",
      "requirement": 3,
      "evidence": "probe_extra.py counted_session_bypass: connections=1, ledger_used=0; secure_groq_session.py:373,416; sin import de mission_ledger"
    },
    {
      "id": "B2",
      "title": "El cutoff no bloquea en la frontera real; solo deja de contar",
      "requirement": 4,
      "evidence": "evidence/cutoff_clock.txt: transport_path at_cutoff=None (NO BLOCK); probe_core.py M2 status=200 journal=0"
    },
    {
      "id": "B3",
      "title": "Colisión con el MISSION.json de la misión nocturna en el mismo directorio canónico",
      "requirement": 5,
      "evidence": "evidence/roots.txt (same_parent=True); probe_core.py H: mission_corrupt, 0 conexiones"
    },
    {
      "id": "B4",
      "title": "La suite del proyecto consume cupo real (16 intentos en 4 ficheros)",
      "requirement": 1,
      "evidence": "evidence/suite.txt: deltas 13/1/1/1, total 16, rutas groq_chat"
    },
    {
      "id": "B5",
      "title": "send_state=not_started no llega al JSON HTTP de la app",
      "requirement": 2,
      "evidence": "probe_http.py: 429 CHAT_MISSION_EXHAUSTED, send_state=null; backend_services.py:288,621; app.py:249-251"
    }
  ],
  "limits": [
    "Sin testigo externo: borrar attempts.jsonl o el directorio reinicia el contador",
    "Reloj de pared sin ancla monotónica: moverlo desactiva el guard (y permite enviar sin contar tras el cutoff)",
    "Lock obsoleto >60 s y unlink sin comprobar propiedad: mutual exclusion rota; una ejecución concedió 6 reservas para cap=5 y otra dejó n duplicados",
    "OSError distinto de FileExistsError en el lock sale sin tipo: 503 CHAT_PROVIDER_UNAVAILABLE, sin send_state",
    "Junction/symlink del directorio de misión y hardlink de attempts.jsonl aceptados: estado fuera del árbol canónico",
    "LOCALAPPDATA override: ledger independiente por entorno",
    "Cada intento bloqueado consume 1 de las 60 llamadas diarias",
    "Copia sin mission_ledger.py: chat muerto con mission_guard_unavailable",
    "mission_dir acepta CON/NUL y longitud ilimitada (sin traversal; falla cerrado al provisionar)",
    "Dos misiones activas: mission_corrupt correcto, pero cualquier MISSION.json ajeno también bloquea",
    "Un corte de energía a mitad de append puede dejar una línea partida: diario corrupto y bloqueo total hasta reparación manual",
    "Un crash deja el lock: hasta 60 s de mission_unavailable para todos los envíos"
  ]
}
```

Nota final: no se ha modificado código ni documentación del repo. El único
artefacto del repo tocado por las pruebas es
`prototipos/paideia-local/evidence/session-status.json`, reescrito con el mismo
contenido que ya tenía (`git status` no muestra cambios); su mtime cambió.
