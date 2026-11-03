# Backend local de Paideia

**Estado:** prototipo HTTP local de solo loopback. No es una API de producción, no crea PostgreSQL, no accede a bancos ni conecta un proveedor LLM.

## Arranque y parada

Desde `prototipos/paideia-local/`:

```sh
python app.py --port 8765
```

Abre `http://127.0.0.1:8765/`. El backend solo acepta bind en `127.0.0.1`; `--port` admite 1–65535. Para parar, usa Ctrl+C en esa terminal. No abras `static/index.html` con `file://`. El servidor de pruebas usa puerto efímero, se ejecuta en un hilo de prueba y se cierra antes de terminar.

No se instalan paquetes: app y dominio usan la biblioteca estándar de Python. El cálculo usa `Decimal`.

## API

Todas las respuestas JSON usan UTF-8. Los errores tienen esta forma cerrada y no incluyen entradas ni detalles internos:

```json
{"error":{"code":"INVALID_REQUEST","message":"...","request_id":"<hex>","retryable":false}}
```

| Método y ruta | Contrato y comportamiento |
|---|---|
| `GET /api/status` | Informa `mode=local_prototype`, `ai.connected=false`, `ai.status=not_configured`, 20 candidatos/0 publicables y `storage=local_snapshot_not_postgresql`. |
| `GET /api/catalogue` | Devuelve `{items,count,not_for_publication:true}`. Filtros opcionales `q` (hasta 100 caracteres) y `family` (`cuenta_remunerada`, `deposito`, `letra_deuda_publica`, `fondo_tradicional`, `etf_ucits`). |
| `GET /api/products/{id}` | Lookup exacto de ID del snapshot; desconocidos o rutas inválidas devuelven 404 JSON. |
| `POST /api/compare` | Solo `{product_ids:[...]}`: entre 2 y 4 IDs distintos. Devuelve metadatos, `comparison_kind=educational_metadata_only`, `quantitative_ready=false`, razones y `hypothetical=false`; no ordena ni recomienda. Si hay familias distintas, avisa que tienen naturaleza distinta. |
| `POST /api/calculate` | Solo los campos descritos abajo; devuelve una serie hipotética, nunca una predicción ni una condición de producto. |
| `POST /api/chat` | Un cuerpo válido `{message:string}` recibe siempre 503 `CHAT_NOT_CONFIGURED`; el mensaje no se guarda, registra ni envía a un proveedor. No hay respuestas prefabricadas. |
| `POST /api/context-preview` | Solo fixture sintética allowlisted, selección y consentimiento explícitos; no acepta un perfil enviado por el cliente. Usa el adaptador local y devuelve `{projection,external_sent:false}`. Si el adaptador local no está disponible, 503 `CONTEXT_ADAPTER_UNAVAILABLE`. El frontend no llama este endpoint con perfiles. |

### Cálculo

Cuerpo cerrado:

```json
{"principal":"1000.00","annual_rate_percent":"3.00","years":5,"monthly_contribution":"100.00","method":"compound","inflation_percent":"2.00"}
```

- `principal` y `monthly_contribution`: cadenas decimales de 0 a 1.000.000.000, hasta dos decimales.
- `annual_rate_percent` e `inflation_percent`: cadenas porcentuales mayores que −100 y hasta 1000, hasta cuatro decimales. `3` significa 3 %, no 0,03 como ratio.
- `years`: entero de 1 a 40; `method`: `simple` o `compound`.
- El compuesto convierte cada tasa anual efectiva a tasa mensual efectiva: `(1 + tasa/100)^(1/12) - 1`. El saldo existente acumula interés mensual y la aportación entra al final del mes.
- El método simple aplica interés lineal durante el tiempo restante a cada aportación de fin de mes.
- El saldo real divide el saldo nominal entre el factor acumulado de inflación efectiva. La serie incluye mes 0 y cierres anuales, incluido el mes final.
- Aritmética `Decimal` con 80 dígitos significativos; no hay redondeo a céntimos mensual. Los valores serializados se redondean a céntimos con `ROUND_HALF_UP`. Se muestran pérdidas; no se aplica un suelo artificial.
- Las salidas son brutas: no se inventan ni incluyen impuestos o comisiones.

La salida identifica el resultado como `hypothetical=true` y `not_prediction=true`; `summary` contiene `contributions`, `final_balance`, `interest` e `inflation_adjusted`. Cada punto de `series` contiene `month`, `contributions`, `balance` y `real_balance` como cadenas decimales con dos posiciones.

### Vista previa sintética

`fixture_id` permitido actualmente: `synthetic-full-profile-01`. El request requiere `synthetic_fixture:true`, propósito conocido, lista de campos permitidos para ese propósito y consentimiento que coincida exactamente con la selección. Se rechazan extras —incluido `profile`—, IDs desconocidos, flag falso, consentimiento rechazado y campos no seleccionados. El adaptador carga localmente la fixture conocida; no confía en un objeto de perfil recibido y no abre conexiones externas.

**Desviación deliberada del contrato de entrada inicial:** el contrato describía un campo `profile` en el request. Se omite/rechaza para que un flag o ID no convierta un perfil aportado por el cliente en “sintético”; la única fuente es la fixture local allowlisted. Esto no habilita una ruta de perfil real.

## Snapshot de catálogo

`SnapshotRepository` lee, desde una ruta relativa a la raíz del proyecto, `docs/validacion-04/05-catalogo/candidatos.json`. No lo escribe ni expone su objeto completo: proyecta una lista blanca de identidad, marca, ISIN, URL primaria, fecha inequívoca, estado de identidad, conflictos y campos desconocidos. Devuelve copias para impedir que un consumidor mutile el snapshot en memoria.

Las tasas, NAV y campos cuantitativos con permisos de copia/display pendientes no salen por la API. Los textos de conflictos se reducen a un aviso genérico para no reproducir cotizaciones; las fechas asociadas a NAV se omiten. `publication_ready` siempre es `false`, `conditions_state` es `pending`, y no se infiere tasa, riesgo, garantía ni disponibilidad. Los enlaces HTTPS se entregan como metadatos, pero el servidor no los consulta.

El adaptador de repositorio es temporal y de solo lectura; PostgreSQL no existe ni se crea en este prototipo. Los 20 candidatos no son ofertas listas para publicar.

## Seguridad y alcance

- El cuerpo POST tiene límite de 16 KiB, `Content-Type: application/json` UTF-8 y `Content-Length` único obligatorio. Se rechazan claves JSON duplicadas, `NaN`/`Infinity`, JSON inválido, campos extra, cifras fuera de rango y tipos distintos de los contratos cerrados.
- Las acciones POST exigen `Host` loopback y `Origin` HTTP del mismo host/puerto. No hay cabeceras CORS `Access-Control-Allow-*`; `OPTIONS` no habilita preflight.
- No se registran bodies ni perfiles. El handler suprime logs HTTP; los errores son seguros y no reflejan el body.
- La superficie estática solo sirve archivos bajo `static/` con extensiones HTML/CSS/JS/SVG e imágenes/fuentes locales permitidas, hasta 2 MiB. `/` sirve `static/index.html`; las rutas relativas de assets y `/static/...` usan el mismo directorio. Se resuelven rutas y symlinks bajo la raíz estática, con bloqueo de `..`, separadores codificados, NUL y extensiones no permitidas; no hay listado de directorios.
- Respuestas con `Content-Security-Policy` compatible con scripts/estilos externos propios y SVG local, sin `unsafe-inline` ni conexiones fuera de `'self'`; también `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` y `X-Frame-Options: DENY`.
- No hay SQL libre, URL-fetch, compras, llamadas de red salientes, credenciales, perfiles guardados, despliegue ni servicio persistente iniciado por las pruebas.

## Verificación

Desde esta carpeta:

```sh
python -B -m unittest discover -s tests -v
node --check static/app.js
```

Las pruebas HTTP crean servidores efímeros en `127.0.0.1`, verifican API, validación, traversal, logs y cierre limpio. Las pruebas del adaptador comprueban aparte la proyección sintética y selección/consentimiento; ninguna prueba llama un LLM.
