# LEDGER_REVIEW (segunda pasada) — contador global de intentos reales

Fecha: 2026-11-04 (UTC), Windows 11, Python 3.11.15.
Objeto: `app/mission_ledger.py` (sha256 `0235eccb…`),
ganchos en `providers.GroqHTTPSJSONTransport._post` y
`secure_groq_session._guarded_https_post`, mapeos `CHAT_MISSION_*` de
`backend_services.py` y documentación `docs/mision-4h30/CONTADOR-GLOBAL.md`.
Método: pruebas propias, offline, sin leer `.env`, sin clave real y sin llamadas
externas. Cada caso fija `LOCALAPPDATA` a un directorio temporal; el HTTP de la
app se prueba en `127.0.0.1` con `HTTPSConnection` sustituido por un doble que
registra construcción, `connect` y `request`. El perfil real
`C:\Users\aleja\AppData\Local\Paideia` no existe antes ni después.
Los ficheros revisados no cambiaron durante la revisión (mismo sha256 antes y
después; `mission_ledger.py` sí cambió a las 12:49:49, antes de empezar las
pruebas, y se releyó de disco: 14 521 bytes, sha256 `0235eccb…`).

Scripts y salidas crudas en
`C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/cache/scratch/ledger_review2/`
(`probe_b1.py`, `probe_b1b.py`, `probe_b2.py`, `probe_b3.py`, `probe_b5*.py`,
`probe_b4*.py`, `probe_b6*.py`, `probe_b7_doc.py`, `probe_quota.py`,
`probe_preflight.py`, `evidence/`).

Veredicto: **NO PASA** (`passed: false`). Los cinco defectos de código de la
primera revisión están cerrados y verificados en la frontera real. Queda un
defecto **bloqueante de documentación**: la ruta canónica que publica la guía
del operador sigue siendo `Paideia\missions`, que el contador ya **no** lee; un
manifest creado ahí se ignora y el envío sale sin contar. Además, B4 sigue
siendo un límite operativo real (una pasada completa de la suite consume 85 de
100 intentos) que el docstring del módulo declara pero la guía del operador
omite.

---

## 1. Lo que queda bloqueante

### B6. La ruta canónica documentada es la antigua y produce un bypass silencioso

El código se movió a un directorio propio (`mission_ledger.py:63`,
`SUBDIR = "ledger-missions"`), pero tres documentos siguen publicando la ruta
antigua:

- `docs/mision-4h30/CONTADOR-GLOBAL.md:9-10`:
  `%LOCALAPPDATA%\Paideia\missions\<id>\` y
  `$XDG_STATE_HOME/Paideia/missions/<id>/`.
- `app/mission_ledger.py:13-14` (primer bullet del
  docstring; la línea 35 sí dice `ledger-missions`).
- `app/scripts/provision_mission.py:9` (el script escribe
  en `ledger-missions`; su docstring dice `missions`).

Prueba (`probe_b7_doc.py`, `evidence/b7_doc.json`): manifest válido
(`paideia-mission-manifest.v1`, ventana activa, cap=1, un intento ya escrito)
creado exactamente en `Paideia\missions\m-doc`:

```
active_manifests_doc_path: []
reserve_doc_path: null
transport_status: 200
doc_path_journal_lines: 1          (el diario viejo, intacto)
ledger_root_exists: false           (Paideia/ledger-missions ni se creó)
canonical_journal: false
```

Es decir: el transporte construye la conexión y responde 200 **sin reservar**.
No es un fallo de código —el código ignora correctamente el árbol nocturno—,
pero la guía del operador y el docstring del módulo indican la ruta que
desactiva el contador. Si se provisiona a mano siguiendo la guía, el cupo deja
de existir en silencio, que es exactamente lo que el mecanismo debía impedir.
Debe corregirse la ruta en los tres sitios antes de provisionar la misión real.

La misma guía tiene otra incoherencia menor: la línea 59 dice que el contador
«solo cubre rutas que pasen por el transporte real de `providers.py`», cuando
las líneas 24-29 documentan correctamente las dos rutinas (también
`secure_groq_session._guarded_https_post`). No es un bypass, pero la sección de
límites no describe la cobertura real.

---

## 2. Los cinco defectos anteriores, uno a uno

| # | Corrección esperada | Resultado | Evidencia |
|---|---|---|---|
| B1 | La ruta `secure_groq_session` reserva antes de conectar; agotado el cupo no construye conexión | **CERRADO** | `probe_b1.py`: `mission_exhausted`, `not_started`, `connections: false`, diario 1; `active`: 1 conexión y diario ya en 1 al entrar en `HTTPSConnection.__init__`; sin manifest: 200 y sin diario. `probe_b1b.py`: la ruta completa `_CountedTransport.post` con sesión falsa: agotado → 0 conexiones; activo → 1 conexión y diario 1; revocado → `disabled` antes de construir. `secure_groq_session.py:373` llama a `_guarded_https_post`, que reserva en 414-420 y conecta en 426. |
| B2 | Con manifest: antes de `start` y desde el corte exacto, el transporte real bloquea con `MISSION_CLOSED` y no escribe intentos; retirar el manifest restaura lo ordinario | **CERRADO** | `probe_b2.py`: antes de start, en el corte exacto (`reserve_for_active_mission(now=cutoff)` → `MISSION_CLOSED`) y en el transporte poco después → `mission_closed`, `not_started`, 0 conexiones, diario 0; dentro de ventana → 200, 1 conexión, diario 1 escrito antes de `__init__`; manifest retirado → 200 y diario 0; sin manifest → 200; `now=cutoff-1µs` → permitido. `mission_ledger.py:341-344`. |
| B3 | Un manifest del mecanismo nocturno en `Paideia/missions` no bloquea ni se cuenta | **CERRADO** | `probe_b3.py` (`evidence/b3.json`): `night_dir` y `ledger_root` con `same_parent: false`; `active_manifests: []`; con solo el manifest nocturno el transporte responde 200, diario del ledger 0 y el `mission-ledger.json` nocturno sigue con `used: 7`; un `MISSION.json` nocturno corrupto tampoco bloquea; con manifest del ledger y nocturno a la vez, 200 y diario 1. |
| B5 | El JSON HTTP lleva `send_state=not_started` y un mensaje que dice que no se envió nada, sin herramientas y con herramientas | **CERRADO** | `probe_b5.py`: servicio sin herramientas → 429 `CHAT_MISSION_EXHAUSTED`, `send_state: "not_started"`, mensaje «No se envió nada al proveedor…»; servicio con herramientas (dispatcher con definición válida) → idéntico; HTTP real en `127.0.0.1` → idéntico. `probe_b5b.py`: con herramientas, agotado → 429; cerrado → 503 `CHAT_MISSION_CLOSED`; diario corrupto → 503 `CHAT_MISSION_UNAVAILABLE`; todos con `not_started` y mensaje. `probe_b5d.py`: ruta de producción `pai_setup.build_chat_service` (`tools_enabled: true`) por HTTP real → 429 con `send_state`. `backend_services.py:282-301, 536-545, 639-650`; `app.py:328-338`. |
| B4 | Sigue siendo un límite operativo documentado, no un bypass silencioso | **LÍMITE (no bypass)** | `probe_b4.py`: cuatro ficheros legacy → 48 intentos (antes 16). `probe_b4_full.py`: suite completa 613 passed, **85 intentos** (16 `groq_chat`, 69 `groq_session`) sobre cap 100. Segunda pasada de los cuatro ficheros en el mismo perfil → **7 failed**, diario 100/100 (`evidence/b4_second_run.txt`). El docstring de `mission_ledger.py:41-45` lo dice con honestidad; `CONTADOR-GLOBAL.md:55-64` **no** lo menciona. |

---

## 3. B4 en detalle (límite operativo, no bypass)

- La suite no envía nada a la red en estas pruebas (todas sustituyen
  `HTTPSConnection`), pero **sí reserva** porque la reserva ocurre antes de
  construir la conexión. Es el comportamiento declarado, no un bypass: si el
  cupo se agota, los envíos fallan cerrado con `mission_exhausted`.
- Una pasada completa de los 613 tests consume **85/100**; deja 15 intentos.
  Una segunda pasada de solo cuatro ficheros agota el cupo y hace fallar 7
  tests con `mission_exhausted` (evidencia `b4_second_run.txt`, diario 100).
- El docstring del módulo (`mission_ledger.py:41-45`) dice: «Ejecutar la suite
  del proyecto con la misión provisionada **consume cupo real**… la mitigación
  es no ejecutar pruebas dentro de la ventana y retirar el manifest al
  terminar». Es honesto.
- La guía del operador (`docs/mision-4h30/CONTADOR-GLOBAL.md:55-64`) enumera
  otros límites pero **omite** este, que es el de mayor impacto operativo. No
  es un bypass silencioso del contador, pero sí una omisión de documentación
  que puede dejar al usuario sin cupo antes de empezar. Debe añadirse a
  «Límites que se mantienen», con la cifra observada (85/100) y la instrucción
  de no ejecutar `pytest` durante la ventana.

---

## 4. Otros vectores comprobados (sin agujero nuevo)

| Vector | Resultado | Evidencia |
|---|---|---|
| Doble conteo | **No**: un `post` = una línea; tres envíos = `n` 1,2,3 | `probe_b6.py` |
| Carrera entre 20 procesos, cap=5 | **Correcta**: 5 éxitos, 15 bloqueados, 5 registros, `n` distintos, 5 pids | `probe_b6.py` |
| Lock obsoleto (>60 s, umbral artificial) | **Fuga conocida**: 8 hilos, cap=5 → 6 concesiones y `n` duplicados (1,1,3,3,5,5); `distinct_n: 3`. No es nuevo; `__exit__` sigue borrando el lock sin comprobar propiedad | `probe_b6.py` |
| Lock que es un directorio | **Falla cerrado pero sin tipo**: `PermissionError` escapa de `MissionBlocked`; en la app → 503 `CHAT_PROVIDER_UNAVAILABLE`, sin `send_state`; no se envía | `probe_b6.py`, `probe_b6b.py` |
| `attempts.jsonl` que es un directorio | **Tipado**: `mission_unavailable`, `not_started`, sin conexión | `probe_b6.py` |
| Diario corrupto (línea partida, schema ajeno, `n` booleano) | **Tipado**: `MISSION_CORRUPT`, sin conexión | `probe_b6.py` |
| Raíz de estado que es un fichero | **Tipado**: `MISSION_UNAVAILABLE`, sin conexión | `probe_b6b.py` |
| Diario de solo lectura | **Tipado**: `MISSION_UNAVAILABLE: journal not writable`, sin conexión | `probe_b6b.py` |
| Dos manifests activos | **Tipado**: `MISSION_CORRUPT`; uno caducado + uno activo → `MISSION_CLOSED` | `probe_b6.py` |
| Junction del directorio de misión | **Aceptado**: el diario se escribe físicamente fuera del árbol canónico | `probe_b6.py` |
| Hardlink de `attempts.jsonl` | **Aceptado**: el registro se escribe en el fichero externo y se lee por la ruta de la misión | `probe_b6.py` |
| Ids raros | Sin traversal: `""`, `..`, `../x`, `a/b`, `a\b`, `a b`, `-`, `_` rechazados; `CON`, `NUL`, Unicode y 300 caracteres aceptados por `mission_dir` (fallan cerrado al provisionar) | `probe_b6.py` |
| `LOCALAPPDATA` relativo | **Cae al perfil real** (`C:\Users\aleja\AppData\Local\Paideia\ledger-missions`); un entorno con ruta relativa no aísla | `probe_b6.py` |
| Reloj de pared | Sin ancla monotónica: moverlo dentro de la ventana permite enviar; antes de `start` o después del corte bloquea | `probe_b6.py`, revisión anterior |
| Cada intento bloqueado consume 1 de las 60 llamadas diarias | **Sí**: dos intentos bloqueados → `calls_day: 2` | `probe_quota.py` |
| Fallo de preflight de sesión tras la reserva global | **Consume 1 intento** aunque no se construya conexión (`transport_error`, diario 1) | `probe_preflight.py` |
| Herramienta de provisión con `--start` posterior al corte o `--cap 0` | **Crea un manifest que `load_manifest` rechaza** (`MISSION_CORRUPT`) y deja el chat bloqueado hasta `--close`; el script no valida ni explica | `evidence/b7_badprovision.txt` |
| Perfil real del usuario | **Intacto**: `C:\Users\aleja\AppData\Local\Paideia` no existe antes ni después; no hay `attempts.jsonl` en el repo | comprobación final |

---

## 5. Requisitos, uno a uno

| # | Requisito | Resultado |
|---|---|---|
| 1 | Contar antes de abrir la conexión; fallo/cierre posterior no devuelve cupo | **PASA** (B1 y B2; diario escrito antes de `HTTPSConnection.__init__`) |
| 2 | Cupo agotado: ninguna conexión y error con `send_state=not_started`, incluido el HTTP | **PASA** (transporte, servicio sin/con herramientas y HTTP de producción) |
| 3 | Sin bypass por otra copia, otro proceso, reinicio, WSGI ni `_post` directo | **PASA en código**; **NO PASA en la guía**: B6 (ruta documentada antigua) |
| 4 | El corte bloquea aunque quede cupo; fuera de la ventana lo ordinario funciona | **PASA** (B2: antes/después del corte, `MISSION_CLOSED`; manifest retirado, 200) |
| 5 | Fail-closed ante manifest corrupto, diario corrupto, directorio no escribible y dos misiones activas | **PASA** (B3/B6; todos con código `mission_*` y sin conexión) |
| 6 | La cuota diaria existente no se eleva | **PASA** (`pai_setup.py:176` sigue `calls_per_day=60`; la ruta nocturna usa `limit` de su propio servicio) |
| 7 | El estado real del usuario no se ha tocado | **PASA** (`Paideia` real ausente; todo bajo `ledger_review2/cases`) |

---

## 6. Límites que quedan (además de B4)

1. **B4 operativo**: 85/100 por suite completa; segunda pasada agota y rompe 7
   tests. Documentado en el módulo, omitido en la guía del operador.
2. **Lock obsoleto**: un poseedor que tarde más de 60 s permite superar el cupo
   y duplicar `n`; `__exit__` borra el lock ajeno.
3. **Lock con `OSError` distinto de `FileExistsError`**: `PermissionError`
   escapa sin tipo; 503 `CHAT_PROVIDER_UNAVAILABLE`, sin `send_state`; no envía.
4. **Junction/symlink/hardlink**: el estado puede quedar físicamente fuera del
   árbol canónico; la comprobación de manifest fuera del directorio no cubre
   el directorio enlazado ni el diario enlazado.
5. **`LOCALAPPDATA` relativo**: cae al perfil real; no aísla.
6. **Reloj de pared**: sin ancla monotónica; moverlo dentro de la ventana
   permite enviar sin relación con el corte real.
7. **Cuota diaria**: cada intento bloqueado consume 1 de las 60 llamadas.
8. **Preflight de sesión**: un fallo tras la reserva global consume un intento
   aunque no haya conexión.
9. **Provisionamiento**: `scripts/provision_mission.py` acepta `--start`
   posterior al corte y `--cap 0`; crea un manifest que el ledger rechaza y
   bloquea el chat hasta `--close`.
10. **TOCTOU**: un manifest creado entre `active_manifests()` y el envío deja
    esa petición sin contar (ventana de milisegundos).
11. **Sin testigo externo**: borrar `attempts.jsonl` o el manifest reinicia el
    contador; no es un sandbox.
12. **Sin fsync del directorio**: no probado; un corte de energía justo tras
    crear `attempts.jsonl` podría perder la entrada (no demostrado).

---

## 7. JSON de veredicto

```json
{
  "passed": false,
  "blocking_defects": [
    {
      "id": "B6",
      "title": "La ruta canónica documentada sigue siendo Paideia/missions; un manifest allí se ignora y el envío sale sin contar",
      "requirement": "3 (sin bypass) / B3",
      "evidence": "probe_b7_doc.py: active_manifests=[], reserve=None, transport_status=200, ledger_root_exists=false; docs/mision-4h30/CONTADOR-GLOBAL.md:9-10; mission_ledger.py:13-14; scripts/provision_mission.py:9; la línea 35 del módulo y la 38 de la guía sí dicen ledger-missions"
    }
  ],
  "limits": [
    {
      "id": "B4",
      "title": "La suite consume cupo real; una pasada completa consume 85/100 y una segunda agota el cupo",
      "documented_in": "mission_ledger.py:41-45",
      "missing_in": "docs/mision-4h30/CONTADOR-GLOBAL.md:55-64",
      "evidence": "b4_full.json: 613 passed, 85 intentos (16 groq_chat, 69 groq_session); b4_second_run.txt: 7 failed, diario 100/100"
    },
    {
      "title": "Lock obsoleto >60 s: 6 concesiones para cap=5 y n duplicados",
      "evidence": "probe_b6.py: ok=6, records=6, distinct_n=3, n_values=[1,1,3,3,5,5]"
    },
    {
      "title": "Lock que es directorio: PermissionError sin tipo; 503 CHAT_PROVIDER_UNAVAILABLE sin send_state, sin envío",
      "evidence": "probe_b6.py, probe_b6b.py"
    },
    {
      "title": "Junction/symlink/hardlink aceptados: diario fuera del árbol canónico",
      "evidence": "probe_b6.py: junction journal_outside=1; hardlink outside_lines=2"
    },
    {
      "title": "LOCALAPPDATA relativo cae al perfil real",
      "evidence": "probe_b6.py: relative root = C:\\Users\\aleja\\AppData\\Local\\Paideia\\ledger-missions"
    },
    {
      "title": "Reloj de pared sin ancla monotónica",
      "evidence": "revisión anterior evidence/cutoff_clock.txt; código sin cambios"
    },
    {
      "title": "Cada intento bloqueado consume 1 de las 60 llamadas diarias",
      "evidence": "probe_quota.py: calls_day 0 → 1 → 2"
    },
    {
      "title": "Fallo de preflight de sesión tras la reserva global consume un intento sin conexión",
      "evidence": "probe_preflight.py: transport_error, journal=1, connections=0"
    },
    {
      "title": "provision_mission.py acepta --start posterior al corte y --cap 0; crea un manifest que load_manifest rechaza y bloquea hasta --close",
      "evidence": "evidence/b7_badprovision.txt: MISSION_CORRUPT: cutoff before start / cap invalid"
    },
    {
      "title": "TOCTOU de milisegundos entre el escaneo de manifests y el envío",
      "evidence": "mission_ledger.py:300-344; no se reprodujo, ventana teórica"
    },
    {
      "title": "Sin testigo externo: borrar el diario o el manifest reinicia el contador",
      "evidence": "diseño; no es un sandbox"
    },
    {
      "title": "Sin fsync del directorio; corte de energía no probado",
      "evidence": "mission_ledger.py:261-268 solo fsync del fichero"
    }
  ],
  "evidence": {
    "B1": "evidence/b1.json, evidence/b1b.json",
    "B2": "evidence/b2.json",
    "B3": "evidence/b3.json",
    "B4": "evidence/b4.json, evidence/b4_full.json, evidence/b4_second_run.txt",
    "B5": "evidence/b5.json, evidence/b5b.json, evidence/b5d.json",
    "B6": "evidence/b7_doc.json",
    "otros": "evidence/b6.json, evidence/b6b.json, evidence/quota.json, evidence/preflight.json, evidence/b7_script.txt, evidence/b7_badprovision.txt"
  }
}
```

---

## 8. Nota sobre el estado del repo

No se ha modificado código ni documentación. Las pruebas escribieron solo bajo
`ledger_review2/cases` y `ledger_review2/evidence`; `LOCALAPPDATA` se fijó a
esos directorios en cada caso. `C:\Users\aleja\AppData\Local\Paideia` sigue sin
existir. Los tests del autor (38 en los tres ficheros de misión) pasan; la suite
completa pasa con el cupo disponible (613 passed) pero consume 85/100.
