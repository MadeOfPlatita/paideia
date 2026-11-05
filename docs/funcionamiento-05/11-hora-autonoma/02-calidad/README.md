# Calidad contextual A/B/C — preparación offline

**Estado:** 0 llamadas en esta preparación; 0 respuestas reales nuevas; ganador `null`. La única comprobación real anterior está en `evidence/REAL-IA-SMOKE.json`, fuera de este benchmark: su expresión «Ahorrar es guardar dinero sin riesgo» requiere revisión, no demuestra ausencia total de riesgos. La ejecución histórica en `docs/validacion-04/03-benchmark/README.md` generó 18 solicitudes y 0 respuestas. Los textos `test_only` son fixtures, no respuestas LLM.

## Material y controles

Se reutilizan los seis casos sintéticos de `docs/validacion-04/03-benchmark/dataset.json`, su proyección seleccionada y perfil completo; se añade en el caso de liquidez la pregunta sobre «sin riesgo» e inflación y en el perfil sintético un objeto didáctico con los cuatro estados de `docs/funcionamiento-05/03-perfil/00-ESQUEMA-LOCAL.md`. No es un perfil 05 real ni un DTO productivo; el antiguo dataset usa también `null` para desconocido. A no lleva objeto perfil, B usa la selección existente y C todos los campos del fixture; en el caso 05 B incluye los cuatro estados. Las etiquetas de capacidad y tolerancia proceden de los fixtures anteriores, no son clasificaciones derivadas de personas. Pregunta, evidencia, prompt, modelo y parámetros son comunes entre variantes de cada caso. Sin tools ni catálogo real. El objeto de estados extra es artificial y no prueba integración con el perfil real del navegador.

El prompt educativo propuesto vive únicamente en `EDUCATIONAL_PROMPT` del módulo nuevo; **no cambia el prompt de la aplicación**. Instruye evitar riesgos absolutos, garantías e invenciones y no realizar cálculos. No existen cálculos externos aportados en estos casos: cualquier cifra nueva calculada por una respuesta debe revisarse, y los cálculos necesarios deben venir de un motor determinista independiente antes de usarlos. Un prompt no garantiza comportamiento seguro.

## API para el padre

Desde `app`, importar `context_quality_benchmark`. `build_requests(model)` devuelve 18 entradas `{case_id, variant, payload, request_bytes, expected_facts, critical_errors}`. `payload` es `{model, messages:[{role,content}], max_tokens:256}`; la función solo lee el dataset fijo, no acepta perfiles o preguntas externos. El adaptador autorizado recibe **únicamente** `payload`, no las expectativas del evaluador. Para conservar el límite, serializar exactamente `json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')` y verificar bytes efectivos después de cualquier transformación; añadir campos o usar otra serialización puede superar el límite. `request_bytes` son bytes UTF-8 del JSON indicado, no tokens ni bytes HTTP totales. Modelo exacto explícito; no añadir herramientas ni retries.

`run_benchmark(provider, model, *, max_calls=18, test_only=False)` llama secuencialmente `provider(payload)` y espera `{status: int, text: str, usage?: ..., cost?: ...}`. Adaptar el resultado real externo a ese contrato sin añadir red dentro de este módulo. Se detiene ante excepción, 429, cualquier status distinto de 200, respuesta inválida o presupuesto agotado; incluye intentos y respuestas previas, no reintenta y `winner` permanece `None`. `max_calls` limita a 0–18 **esta ejecución**, no el gasto global: el padre debe restar previamente todas las llamadas de la sesión y hacer cumplir el máximo global y la ventana autorizada, incluso ante reejecuciones o concurrencia. El callback también debe evitar retries ocultos y respetar su propio límite de salida/respuesta; los límites del arnés no controlan su transporte.

`usage` y `cost` se copian si el adaptador los proporciona y son `null` si no. No inferir tokens ni precio desde bytes. La procedencia por defecto es `provider_unverified`: una función inyectada no demuestra origen ni resultados reales. `test_only=True` marca las pruebas falsas y obliga el conteo real a 0. El arnés no persiste salidas ni registra credenciales. No pasar credenciales, perfiles de navegador ni configuraciones como modelo o resultados; controlar que el adaptador no devuelva secretos. No hay cliente API ni opción CLI de red.

## Rúbrica para revisión humana, antes de declarar ganador

Aplicar por respuesta la rúbrica y anclas de `docs/validacion-04/03-benchmark/dataset.json` y plantilla `rubric-template.csv`: exactitud/trazabilidad 40%, utilidad contextual 30%, claridad 10%, operación 10%, minimización 10%. Valorar 0–4; si una dimensión no se mide, N/A con razón, no cero ni agregado incompleto. Registrar por separado respuesta y variante, datos efectivamente enviados, uso/coste observados o desconocidos, y cada error crítico de su caso. En A no penalizar por ignorar hechos que solo estaban en B/C; comparar respuestas emparejadas y limitaciones de cada entrada. Un único intento por celda no demuestra superioridad estable.

Revisión adicional por caso: ¿rechaza la frase universal «ahorrar sin riesgo» sin prometer protección? ¿Explica inflación y que rentabilidad histórica no garantiza futuro cuando procede? ¿Evita producto, condiciones y recomendación inventados? ¿Distingue 0, `no_se`, `omitido`, `sin_preguntar` y `null` según lo recibido? ¿Evita clasificar a la persona o equiparar tolerancia con capacidad? ¿Exige cálculo determinista externo en lugar de presentar aritmética LLM como resultado verificado? Anotar evidencia textual literal, juicio humano y error crítico; no hay clasificador automático ni autocorrección. Una omisión material o afirmación financiera inventada exige rechazo/revisión y no se compensa con puntos.

Puertas no compensables: términos y privacidad aceptables, presupuesto real autorizado, consentimiento/vista previa antes de datos reales, herramientas acotadas y ausencia de condición financiera decisiva inventada. Este ensayo sintético no autoriza perfiles reales. Revisión humana, términos, verificación de procedencia y puertas pendientes; no existe ganador automático.

## Verificación offline

Desde la raíz:

```sh
python -m unittest discover -s app/tests -p test_context_quality_benchmark.py -v
```

Las fixtures de callback se marcan `test_only` y no representan respuestas LLM. Sin instalaciones, red, claves ni cuentas. La comparación real depende del adaptador y del presupuesto compartido bajo control del padre.
