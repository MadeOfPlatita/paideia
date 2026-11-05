# Corrección parcial: frontera de transporte de sesión

Inicio de trabajo comprobado: 2026-10-30T12:05:00+01:00. Misión exclusivamente offline; no se abrió Tk ni se usaron credenciales reales, proveedores, redes externas, instalaciones ni bases de datos.

## Resultado y TDD

- Reproducción falsificadora `tests.test_session_transport_boundary_regression`: ROJO, `Liar.test_only=True` reutilizó `GroqHTTPSJSONTransport.post` y una conexión parcheada registró `['sent']`. VERDE tras exigir tipo exacto `StructuredSessionFixture` en construcción y despacho, llamar a `fixture_post` fijado y eliminar fallback arbitrario. Sustitución del método `post` de la clase fixture tampoco se despacha. La guarda de misión/cuota sigue aplicándose; la rama real legacy mantiene transporte y guarda.
- Segundo ROJO: `test_cannot_relabel_test_session_as_real` evidenció atributo `test_only` reasignable. VERDE: propiedad de solo lectura. Esto no es aislamiento contra código Python malicioso en el mismo proceso, que puede alterar atributos privados o módulos.
- `python -B -m unittest tests.test_session_transport_boundary_regression tests.test_session_structured_integration tests.test_session_structured_security tests.test_structured_counted_provider tests.test_mission_journal_integrity tests.test_session_send_boundary.BoundaryTests.test_legacy_unguarded_transport_api -q`: 26 OK. Incluye transporte legacy directamente con HTTPSConnection sustituida, no llamada exterior.
- `python -B -m unittest tests.test_providers tests.test_provider_secrets tests.test_provider_diagnostics -q`: 22 OK.
- `python -B -m unittest tests.test_session_send_boundary -q`: 6 tests, 5 errores porque usaban subclase de transporte HTTPS disfrazada de fake; el test directo legacy pasa. No se han adaptado estos tests antiguos ni otros que inyectan clases arbitrarias. No presentar como regresión legacy completa. Deben migrarse a fixture cerrada, preservando pruebas específicas de guarda real con una arquitectura de prueba que no abra una ruta de bypass. Las pruebas estructuradas existentes cubren parte, no toda, esa regresión.

## Estado de envío no implementado

`GroqHTTPSJSONTransport.post` llama a `request` que puede fallar tras una transmisión parcial, y `GroqProvider` convierte excepciones en códigos genéricos; la ruta estructurada captura además errores de transporte y validación conjuntamente. No existe metadato que preserve de forma fiable la transición a través de esas fronteras. La fixture cerrada nunca realiza envío externo, por tanto no se debe etiquetar su POST sintético como `sent` externo, ni inventar `unknown` externo. Un contrato de tres estados necesitaría instrumentación en el límite de envío real, propagación explícita y pruebas de trazas con locales y sanitización de causas/contextos antes de exponerse. Se mantiene bloqueada la modalidad estructurada real, sin cambio de claves, y sin reintentos.

## Pendiente

Migración de tests legacy sin Tk y revisión independiente. No se ha verificado una sesión real, la conectividad ni calidad de modelo. No se afirma el éxito global de la misión ni la cancelación física de bytes ya enviados.
