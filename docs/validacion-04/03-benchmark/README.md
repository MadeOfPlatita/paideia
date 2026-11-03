# Arnés local de contexto A/B/C para Pai

## Estado y alcance

Ejecutable local, solo Python estándar. Contiene **seis perfiles y escenarios exclusivamente sintéticos**; no hay catálogo comercial real, nombres, DNI, bancos, credenciales, cuenta de proveedor, API key ni modelo elegido. Los importes del perfil son enteros EUR y se conservan como aparecen. `null` significa «no declarado/desconocido», nunca 0 ni una lista vacía.

El arnés materializa requests locales; **no es un cliente Gemini/Groq** y no abre sockets, no realiza consultas de red, no simula respuestas, y no atribuye inteligencia a un stub. No se instaló ninguna dependencia. Presupuesto disponible: **0 EUR**. Los comandos `validate`, `generate` y `summary` no contactan proveedores. No se ejecutó red.

La pregunta textual y la evidencia sintética fija son iguales en A/B/C. Cambia solo la inclusión del objeto de perfil:

- **A — sin perfil:** en el prompt solo van la instrucción común, evidencia fija y pregunta. No se adjunta un marcador o resumen de perfil.
- **B — relevante:** se adjunta la proyección JSON seleccionada por `projection_fields`. Las cifras y objetos anidados elegidos se copian exactamente. `projection_exclusion_reason` se materializa como metadato de auditoría por cada campo omitido; **no** se envía al proveedor.
- **C — completo:** se adjuntan todos los `profile_fields` y sus estados, sin identificadores.

La pregunta misma puede incluir cifras que cualquier variante debe ver: A significa que no se adjunta el objeto del perfil, no que se borre información ya escrita en la pregunta. Cada request expone `base`, `base_sha256`, `profile_context`, `messages` y `rendered_prompt`; las variantes de cada caso comparten el mismo `base_sha256`. El adaptador futuro debe enviar solamente `messages`.

Los casos son: liquidez próxima; tolerancia alta frente a capacidad baja; deuda con coste conocido y reserva corta; aportaciones largas con supuestos; datos no declarados; ficha comercial ficticia contradictoria. El sexto fixture está marcado como sintético y no representa entidad ni oferta real.

## Ejecutar en modo offline

Desde este directorio:

```sh
python pai_context_benchmark.py validate
python pai_context_benchmark.py generate --out generated
python pai_context_benchmark.py summary
python -m unittest -v test_benchmark
```

`generate` no sobrescribe un directorio de salida no vacío. Los artefactos nuevos se limitan a este directorio.

### Ejecución real efectuada

- `validate`: `valid=true`, `case_count=6`, `provider_calls=0`, `result_count=0`, `winner=null`.
- `generate --out generated`: `request_count=18` (6 casos × A/B/C); verificado además por lectura de `manifest.json` y recuento de archivos: **18 JSON en 6 carpetas, 3 variantes por caso**, sin llamada externa.
- `summary`: `provider_call_count=0`, `result_count=0`, A/B/C = 0, Gemini/Groq = 0, `winner=null`.
- `python -m unittest -v test_benchmark`: **7 tests, OK**. Cubren validación/proyección sin pérdida, inmutabilidad del dataset durante generación, igualdad de la base, selección B frente a C, `null` frente a 0 y omisión, cero resultados/ganador sin proveedor, rechazo de registro sin atestación y settings requeridos.

TDD observado: las pruebas de `validate`, `generate` y `summary`/`record` se ejecutaron primero en rojo por comando/módulo aún no implementado; se añadieron las rutas mínimas y volvieron a verde. La prueba de exclusiones B falló por ausencia de `selected_fields`; se añadieron razones y metadatos y pasó. No se crearon respuestas de prueba.

## Registrar una salida real después

El arnés no llama al proveedor. Cuando exista autorización independiente y se haya hecho una llamada externa real con uno de estos requests sintéticos, guardar su salida sin modificarla en un archivo local y registrarla así (plantilla; sustituir parámetros por valores efectivamente observados):

```sh
python pai_context_benchmark.py record \
  --request generated/requests/SYN-01-LIQUIDEZ/B.json \
  --provider gemini \
  --model "IDENTIFICADOR_EXACTO_REPORTADO" \
  --settings-json '<JSON no secreto de la configuración realmente aplicada>' \
  --response-file results/RESPUESTA_REAL.txt \
  --confirmed-provider-call \
  --results results.jsonl \
  --latency-ms MILISEGUNDOS --input-tokens TOKENS_ENTRADA --output-tokens TOKENS_SALIDA
```

`--provider` admite `gemini` o `groq`; `--model` es obligatorio y **no tiene valor por defecto**. `--settings-json` también es obligatorio para que una futura comparación recoja parámetros efectivamente aplicados, sin presuponerlos. El parser rechaza nombres de campos típicos de credenciales/tokens. No pongas claves en argumentos, settings, requests, dataset ni resultados. La respuesta se almacena en `results.jsonl`; stdout solo devuelve metadatos, no imprime prompt ni respuesta.

`--confirmed-provider-call` es una atestación manual, no una prueba criptográfica de origen. No se debe usar con mocks, stubs, texto fabricado ni respuestas de otro modelo. `record` todavía no se ha ejecutado con una salida real porque no existen proveedor, claves autorizadas ni llamada permitida; su ruta positiva queda pendiente de una prueba real autorizada. `rubric-template.csv` tiene 18 filas vacías para evaluación humana posterior.

Después de registrar resultados, `summary` los cuenta, pero mantiene `winner=null`: no hay ranking automático. Completar una fila humana por salida, revisar los errores críticos del caso y verificar cada puerta no compensable antes de cualquier recomendación. Usar 0–4 por dimensión; marcar `N/A` (no 0) cuando no haya evidencia, en especial coste/latencia/tokens sin llamada. No calcular promedios con dimensiones sin medir ni usar al modelo como único juez.

## Rúbrica

Está en `dataset.json` bajo `human_rubric` y la plantilla de captura en `rubric-template.csv`:

| Dimensión | Peso |
|---|---:|
| Exactitud y trazabilidad | 40 % |
| Utilidad contextual | 30 % |
| Claridad didáctica | 10 % |
| Consumo y operación observados | 10 % |
| Minimización de contexto | 10 % |

Escala 0–4 con anclas escritas en el dataset. Puertas no compensables: términos/privacidad aceptables; coste real ≤ 0 EUR; elección/consentimiento y vista previa antes de transmitir un perfil real; herramientas acotadas; sin condición financiera inventada que afecte la decisión. Un error crítico por caso implica rechazo/revisión, no se compensa con puntos.

## Contrato futuro de adaptadores (sin cliente implementado)

Interfaz canónica prevista, independiente del proveedor:

- **Entrada:** `case_id`, `variant`, `base_sha256`, y `messages: [{role, content}]` con roles `system`/`user`; modelo exacto y settings explícitos se configuran fuera del request. No transmitir `profile_context` de auditoría, rutas locales ni `excluded_fields`.
- **Salida normalizada:** texto bruto, motivo de finalización si el proveedor lo da, identificador de request opaco y métricas devueltas por proveedor (tokens de entrada/salida); la latencia se mide alrededor de la llamada. Si una métrica no está disponible, se registra `null`, no se inventa.
- **Gemini:** adaptador debe traducir roles/contenido al contrato vigente de Gemini y mantener separado el contenido de instrucciones del sistema. Lee `GEMINI_API_KEY` del entorno local del proceso autorizado; no la serializa ni registra.
- **Groq:** adaptador debe traducir `messages` al contrato vigente de la API de Groq. Lee `GROQ_API_KEY` del entorno local del proceso autorizado; no la serializa ni registra.
- Los nombres de modelos, endpoints, autenticación, límites, términos, residencia y tratamiento de datos quedan **sin decidir** hasta los informes/documentación vigentes del proveedor. No copiar modelos de memoria ni inferir gratuidad por existir cuota.

Cualquier cliente futuro requiere, antes de implementarse, opt-in online explícito, allowlist exacta de hosts, secreto solo desde entorno local, límite duro pequeño de requests por ejecución, reintentos `0`, y logs técnicos sin prompts, perfiles, respuestas ni claves. En este artefacto no hay cliente, opción online, allowlist ni acceso a entorno de claves; por tanto, no hubo red.

## Referencias de alcance

Leídos como protocolo/referencia, sin modificar:

- `../../planificacion-03/19-integracion/EVALUACION-CONTEXTO.md` — diseño A/B/C, seis casos, rúbrica y puertas.
- `../../planificacion-03/01-pai-tools/ESPECIFICACION.md` — límites propuestos, perfil/consentimiento y estado no probado.
- `../../planificacion-03/09-privacidad-datos/INFORME.md` — minimizar campos, no confundir dato local o sin identificador con anonimato.

Este arnés no prueba capacidad, calidad, seguridad, cumplimiento jurídico, términos, cuota o latencia de Gemini/Groq. **No hay respuestas de modelo, puntuaciones, ganador ni recomendación de contexto**. El paso siguiente depende de informes y autorización, no de esta ejecución offline.
