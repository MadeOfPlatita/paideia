# Backend: evidencia local

Desde `prototipos/paideia-local`, sin red de proveedor ni credenciales:

- `python -B -m unittest discover -s tests -p 'test_structured_education.py' -v`: rojo inicial, exit 1, TypeError porque no existía `structured_mode` (`RED.txt`).
- El mismo comando: verde inicial, 1 test, exit 0 (`GREEN-inicial.txt`).
- Con prueba nueva de capability: rojo, 7 tests, exit 1, KeyError `structured_education` (`RED-capability.txt`); después de implementar capability y probar HTTP: `python -B -m unittest discover -s tests -p 'test_structured_education*.py' -v`, 7 tests OK, exit 0 (`GREEN-final.txt`). El HTTP real utiliza `app.create_server(port=0)`, servidor propio efímero detenido por context manager.
- `python -B -m unittest discover -s tests -p 'test_domain.py' -q`: 11 OK, exit 0.
- `python -B -m unittest discover -s tests -p 'test_backend_integration.py' -q`: 13 OK, exit 0.
- `python -B -m unittest discover -s tests -p 'test_chat_context.py' -q`: 6 tests, 1 fallo, exit 1. `test_status_advertises_disabled_capabilities` compara el dict completo antiguo y no admite el nuevo campo obligatorio `structured_education: false`. No se ha modificado el test antiguo, fuera del alcance asignado; el coordinador debe migrar explícitamente esta aserción y registrar el mapa de migración. No es una regresión verde.

Solo pruebas sintéticas; no prueba calidad de un modelo, cobertura completa ni UI; falta integración coordinada y revisión independiente.
