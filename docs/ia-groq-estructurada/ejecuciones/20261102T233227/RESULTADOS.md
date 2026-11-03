# Resultado — estabilización de Paideia y avance estructurado offline

## Estado y horario

**Objetivo principal A+B completado**: código corregido, pruebas RED→GREEN, regresión y revisiones independientes favorables en el alcance descrito. **Prioridad 2 parcial**: se mejoró el recorrido sintético conectado, pero la integración HTTPS real estructurada no está implementada ni probada y sigue desactivada.

- Inicio: 2026-11-02T23:32:27+01:00.
- Corte máximo original, sin ampliación: 2026-11-03T00:32:27+01:00.
- Comprobación de cierre: 2026-11-03T00:21:05+01:00. Cierre final registrado: 2026-11-03T00:22:34+01:00. Se termina antes por hitos viables logrados y para no ampliar el alcance real sin permiso.
- Sin llamadas reales de la aplicación a proveedores, claves reales, datos personales, ventanas Tk, pagos, instalaciones, DB nueva ni despliegue. Se utilizaron datos/credenciales ficticios, HTTP loopback y conexiones instrumentadas. Las guardas del runner son del proceso Python, no un sandbox de procesos hijos; no se afirma seguridad frente a control arbitrario del proceso.

## Cambios entregados

### A — backend sin Tk obligatorio: completo

`secure_groq_session.py` ya no carga Tk al importar el backend HTTP. La GUI resuelve sus dependencias solo cuando se necesita, conserva los overrides históricos para tests y devuelve un error explícito si falta Tk antes de abrir el presupuesto de misión. Tests permanentes: `tests/test_backend_without_tk.py`; seis pruebas comprobadas por coordinación. Revisión `deleg_931f4ba8/tarea1` favorable; no se probaron visualmente controles nativos ni se abrieron ventanas.

### B — procedencia cerrada: completo dentro del contrato soportado

`backend_services.py` rechaza al construir y antes de despachar las combinaciones que intentaban etiquetar un proveedor real o arbitrario como test-only. No basta una etiqueta `test_only=True`: se admiten implementaciones ficticias cerradas y la fachada de sesión sintética validada. El despacho ficticio usa métodos fijados; se preserva el código de rechazo estructurado. No se habilitó modo real por payload ni se atribuye ausencia de red a un proveedor arbitrario. Tests: `test_service_provenance.py` y migraciones de fixtures de contexto, herramientas, admisión y calidad. Revisión final `deleg_1181f200/tarea2` favorable en ese alcance, con pruebas independientes de impostores y sondeos loopback.

Se extendió `FakeChatProvider` con secuencias y errores sintéticos tipados y acotados para recuperar cobertura sin admitir callbacks/transportes arbitrarios. Se migraron pruebas y tres servidores de fixtures sin quitar las aserciones de límites ni reemplazar fallos de transporte por respuestas HTTP500. Se recuperaron tests de misión antes omitidos; además se corrigió una contaminación de mocks en `test_mission_session.py` que restauraba `MissionBudget` como mock tras terminar un contexto. Evidencia en `B-PROVENANCE.md`, `MISSION-TESTS.md`, `MISSION-ISOLATION.md` y JSON de compatibilidad. Los informes iniciales rojos se conservan.

### Runner reproducible: completo

`scripts/run_offline_regression.py` ejecuta unittest y funciones pytest con un intérprete ya instalado, permite loopback y bloquea accesos externos ordinarios y creación de intérpretes Tk en el proceso. Excluye exactamente seis pruebas de ventanas, sin omitir módulos enteros por AST. Conserva resultados de setup/call/teardown y fallo de limpieza, clasifica xfail/xpass como no verde y escribe identificadores opacos en el informe en vez de parámetros crudos. Hashes deterministas no son cifrado: no usar secretos en tests. Mantiene categoría saneada para errores de colección. Documentación: `RUNNER.md`; aprobación final independiente `deleg_b422838b`, catorce pruebas propias verificadas también por coordinación.

### Parser y sesión estructurada: avance parcial aprobado

Se extrajo `parse_selection(ChatResult)` en `structured_provider_adapter.py`. Tanto el adaptador falso como la ruta de sesión contada usan el parser estricto. La ruta de sesión procesa el resultado directamente, sin envolverlo en un `FakeChatProvider`. Test HTTP demuestra una sola petición ficticia, una reserva durable, cálculo local con supuestos de ese turno y ausencia de escenario/valores distintivos en el cuerpo enviado al fixture. Se mantienen los rechazos de duplicados, IDs/texto no permitido, refusal, truncado y herramientas, sin reintento.

La primera revisión de esta parte encontró sustitución de proveedor durante claim. Se corrigió con referencia local, revalidación tras admisión y método fijado; pruebas de sustitución de proveedor, método, modalidad y misión no despachan impostor y completan el ticket. Revisión `deleg_7dfacf91` tenía un dictamen contradictorio (passed con una preocupación que era límite de modelo de amenaza); se solicitó aclaración. `deleg_ed396411` confirma booleano true, sin preocupaciones ni errores dentro del modelo soportado, y documenta que monkeypatch privilegiado concurrente del proceso queda fuera. No es una garantía de sandbox.

**No completa la prioridad 2 real:** el upstream de esta ruta sigue siendo `StructuredSessionFixture` exacta. No se ensambló ni habilitó transporte HTTPS real estructurado, ni se probó compatibilidad de Groq o calidad financiera del modelo. La selección editorial sintética no prueba relevancia, asesoramiento o aprobación profesional.

## Evidencia ejecutada por el coordinador

| Prueba | Resultado | Archivo |
|---|---|---|
| Python con pytest, unittest y funciones, sin GUI | **404 passed**, 375 unittest+29 otros nodos pytest; **6 GUI deseleccionados**, 0 errores de colección, exit0 | `regression-final.json` |
| Node y sintaxis JS | **40/40**, exit0 | `node-final-repeated.json` |
| HTTP normal con servidor nuevo loopback | **19/19**, exit0 | `http-final-repeated.json` |
| Runner auto-pruebas | **14/14** | `runner-coordinator.json` |
| Backend sin Tk | **6/6** | `A-permanent-budget-probe.json` |

No sumar subtests ni mezclar los recuentos históricos como si fueran la misma suite. Seis casos nativos excluidos no equivalen a una suite completa con GUI. Los 404 recogen también funciones pytest que el antiguo unittest no descubría. Excluidos exactos y sus motivos en `RUNNER.md`. Primera ejecución conjunta falló; `regression-first.json` y `compat-full-final.json` preservan las regresiones antes de corrección. Los 19 HTTP normales no sustituyen pruebas específicas del modo estructurado, que se ejecutaron en su integración separada.

La primera pasada HTTP pasó las 19 comprobaciones pero falló en una comprobación inmediata de cierre (`http-final.json`). No se ocultó. Se repitió tras la corrección de verificación de lifecycle del harness: último servidor propio terminado, sin listener8765, exit0 en `http-final-repeated.json`. `known-ports-final.json` comprueba sin listeners en 8765,18764,18765,18789; no es auditoría de todos los puertos de Windows ni prueba de que no exista otro proceso ajeno.

## Instrucciones y próximos pasos

Inicio local y comandos en `INICIO-LOCAL.md` y runner en `RUNNER.md`. Inicio normal mantiene IA desconectada. No hay proceso persistente que necesite seguir abierto tras esta entrega.

1. Ensamblar de forma separada y desactivada la ruta estructurada real con fachada contada, misión nueva válida, consentimiento y metadatos fiables. Probar antes con HTTPSConnection ficticia sin aflojar los guardas.
2. Solo después plantear una prueba real: autorización específica y ventana/plazo vigentes, confirmación humana de Free e introducción voluntaria de clave por ventana segura. No reutilizar misiones antiguas ni asumir que el checkbox verifica facturación.
3. Evaluar calidad/contexto del modelo con datos sintéticos; fixtures y conectividad histórica no lo acreditan.
4. Fuera de esta misión: aprobar condiciones y permisos de productos reales, alojamiento/QA integrada y diseño final. Paideia no está terminada ni desplegada.
