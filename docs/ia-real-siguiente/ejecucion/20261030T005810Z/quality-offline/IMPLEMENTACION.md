# Calidad financiera offline: implementación y límites

**Ámbito:** cero llamadas a modelos/proveedores; pruebas con transportes y proveedores `test_only`, salvo que el texto reproducido proviene de una respuesta real anterior y se usa como fixture offline. El HTTP a 8765 es loopback local, no un modelo. No se corrigió ni reinterpretó el benchmark histórico.

## Comportamiento

`assess_financial_text(text)` devuelve una tupla de identificadores estables; `()` significa solamente que no se encontró el patrón, **no** que el texto sea correcto. El guard léxico estrecho busca sujeto explícito ahorro/ahorrar/capital/invertir/inversión seguido de «sin riesgo» dentro de una cláusula corta. Omite citas, negaciones y condicionales para priorizar precisión. No es un verificador semántico: puede pasar paráfrasis, afirmaciones indirectas, citas no refutadas y afirmaciones en cláusulas con una negación o condicional no relacionados; tampoco verifica garantías, productos, cifras ni fuentes. Puede producir otros falsos positivos y negativos. La mejora del prompt no demuestra que el modelo obedezca.

La respuesta visible (incluida refusal) se comprueba en el chat simple y en el admitido/runner. Si se detecta patrón se devuelve 502 `CHAT_FINANCIAL_QUALITY_REJECTED`, sin texto del proveedor ni reintento; la plaza admitida se libera en `finally`. En benchmark un HTTP 200 con flag detiene el ensayo, registra solo identificadores y metadatos del caso, sin añadir respuesta ni elegir ganador. El prompt financiero compartido distingue ahorro, inversión, riesgo nominal según instrumento y erosión por inflación. Se mantienen 256 tokens, low e include_reasoning=False.

## Evidencia TDD y regresión

Desde `app`:

- RED `python -m unittest discover -s tests -p test_financial_quality_integration.py -v`: 1 test con tres subcasos falló: HTTP 200 en vez de 502 para el texto real reproducido en simple, admitido y herramientas. Tras implementar: verde.
- RED `python -m unittest discover -s tests -p test_financial_quality_benchmark.py -v`: 1 fallo `complete` frente a `financial_quality_rejected`. Tras implementar: verde.
- `python -B -m unittest discover -s tests -p 'test_financial_quality*.py' -v`: 8 tests OK, con subcasos de negación, citas, condicionales, refusal, respuesta segura y seguimiento de herramienta; el caso de seguimiento usa dos llamadas simuladas necesarias para la herramienta y ninguna adicional.
- `python -B -m unittest discover -s tests -q`: 246 tests OK. Las pruebas de GUI existentes usan fixtures y credenciales ficticias, no una sesión de usuario real. No se alteraron fixtures heredadas.
- `node --test tests/*.test.cjs`: 24 tests OK.
- `python -B verify_http.py --base-url http://127.0.0.1:8765 --out '../../docs/ia-real-siguiente/ejecucion/20261030T005810Z/quality-offline/http.json'`: 19/19 OK. Ese servidor normal ya estaba iniciado y no acredita haber cargado los cambios nuevos; el guard nuevo se comprueba mediante servidores HTTP efímeros de pruebas.

Los tests de integración y benchmark se añadieron antes de sus respectivos cambios y se observaron fallar; las ampliaciones de cobertura se ejecutaron después. No se han generado puntuaciones de modelo ni evaluado calidad real con el nuevo prompt. Una futura prueba Groq requiere autorización nueva y credencial por vía segura; no se realizó aquí.
