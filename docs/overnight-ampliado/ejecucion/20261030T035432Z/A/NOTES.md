# Hito A — adapter offline, evidencia parcial

Fecha de corte del encargo: 2026-10-30T07:00:00Z. Todos los datos de proveedor, contenido y secreto son ficticios. No se ha usado Groq, red externa, modelo ni credenciales. Las pruebas HTTP solo usan loopback.

## Implementación y alcance

`structured_provider_adapter.py` acepta exclusivamente la clase exacta `FakeChatProvider`, construida con `test_only=True`, y exige `test_only=True` al adaptador. El fake devuelve un `ChatResult` programado en memoria; no tiene transporte. No se admite `GroqProvider` ni se afirma compatibilidad con su protocolo de salida. La selección es JSON completo, UTF-8 codificable, acotado a 4096 bytes y con claves únicas; campos, versiones, intents e IDs cerrados. Rechaza tool calls, negativa, truncamiento y finish distinto de stop. No retorna razonamiento ni contenido crudo. Devuelve un error fijo; servicio lo transforma en error HTTP fijo. Como máximo una llamada por turno, sin herramientas ni reintentos.

`LocalChatService` existente debe crearse con `provider=StructuredProviderAdapter(fake, test_only=True), enabled=True, test_only=True, structured_mode=True`. Su constructor actual mantiene bloqueadas herramientas, admisión, contexto e historial en esta modalidad. El backend vincula la simulación al escenario del mismo request y calcula con `domain`; el adaptador no recibe el escenario. Esto no verifica aritmética de un backend comprometido. El fake almacena mensajes en memoria para pruebas; no usarlo con datos reales.

## Adaptación de fixture de navegador para coordinación con el agente principal

No se ha modificado `tests/serve_structured_fixture.py` para evitar colisión. Se puede envolver el fixture actual en un proveedor fake que serialice su respuesta (incluida la adulterada) y pase por el adaptador, sin modificar backend ni constructor:

```python
import json
from providers import ChatResult
from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter

class AdaptedFixture:
    test_only = True
    def select_education(self, messages):
        selection = StructuredFixture().select_education(messages)
        fake = FakeChatProvider(ChatResult(json.dumps(selection), None, (), 'stop'), test_only=True)
        return StructuredProviderAdapter(fake, test_only=True).select_education(messages)

# En main: provider = AdaptedFixture() en lugar de StructuredFixture().
```

Verificar navegador con el proceso fixture propio, incluyendo respuesta válida, adulterada, cálculo del turno y ausencia de fallback; conservar evidencia y cerrar servidor. **No se ha ejecutado navegador con este adaptador en este trabajo.** Los tests HTTP sí recorren `ChatResult -> adapter -> LocalChatService -> app HTTP`.

## Resultados

Desde `prototipos/paideia-local`:

- `python -B -m unittest discover -s tests -p 'test_structured*.py' -v`: 20 tests OK (incluye integración loopback, fallo de motor, aislamiento, validaciones y turnos). Salida `structured-tests.txt`.
- `python structured_eval.py`: `synthetic-eval.json`: 4 fixtures, 3 válidos, 2 relevantes entre los 3 válidos, `winner:null`. Etiquetas manuales mínimas, sin evaluación de calidad real ni representatividad.
- Evidencia TDD `red-adapter.txt` / `green-adapter.txt`, `red-message.txt` / `green-message.txt`, `red-eval.txt` / `green-eval.txt`, `red-winner.txt` / `green-winner.txt`. Los reds iniciales de módulo ausente son errores de importación esperados; el red de mensajes es fallo de comportamiento. Algunas pruebas adicionales de regresión se añadieron tras implementar la validación, no se afirma ciclo rojo individual para cada una.
- No se ha ejecutado la suite completa desde este trabajo; coordinar con agente principal y volver a ejecutarla tras integrar cambios concurrentes.

## Activación futura no autorizada

El adaptador actual no permite proveedor real ni HTTPS. Una futura integración necesitaría diseño y autorización nueva, consentimiento explícito apropiado, admisión y ledger compartido, presupuesto/reintentos y validación del protocolo real; nada de esto está implementado ni autorizado por el fixture. El modo legacy no queda reparado por estas pruebas.
