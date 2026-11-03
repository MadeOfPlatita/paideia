# Checkpoint de integración: presentación estructurada

Corte fijo 2026-10-30T07:00:00Z. Sin llamadas a modelos ni proveedor externo. Backend a cargo de un trabajador en archivos exclusivos; revisión de su resultado y pruebas conjuntas pendientes.

El coordinador añadió `static/structured_education_ui.js` y `tests/structured_education_ui.test.cjs`. El ciclo rojo→verde del selector muestra que una respuesta esperada como estructurada que carece del DTO es rechazada, sin presentar prosa de reserva. El selector solo acepta `provider_mode:test_only` y `external_sent:false`, valida forma/version/procedencia y descarta `answer` del modelo para crear la vista estructurada. El código `app.js` etiqueta explícitamente contenido editorial, resultado determinista y prueba sintética, empleando nodos de texto; no conserva el texto de respuesta arbitrario en historial en esta ruta. `index.html` carga el módulo.

Prueba ejecutada: `node --test tests/structured_education_ui.test.cjs` → 3/3; `node --check static/app.js` y `node --check static/structured_education_ui.js` → exit0. Esto no prueba todavía contrato completo backend ni navegador. El mecanismo de modalidad se señaliza mediante `state.status.ai.capabilities.structured_education` y requiere comprobar que backend lo expone y que el navegador lo conoce antes de la petición; un status no disponible o discrepante no debe provocar fallback.

Baseline legado: test_financial_quality_known_gap.py contiene un fallo real previo. No se ha eliminado, modificado, marcado expectedFailure ni declarado suite completa verde. La migración de pruebas requerirá un mapa explícito y una sustitución que compruebe que el texto arbitrario no puede llegar a la salida estructurada; hasta entonces la regresión continúa fallida.
