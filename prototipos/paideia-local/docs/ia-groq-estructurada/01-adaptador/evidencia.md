# Evidencia offline

Desde `prototipos/paideia-local`, fixtures sintéticos, sin HTTPS ni API Groq:

- RED: `python -m unittest tests.test_groq_structured_adapter.OfflineGroqContractTests.test_builds_existing_request_and_selects_once -v` → fallo esperado, `ImportError: cannot import name 'build_structured_request'`.
- GREEN: el mismo comando → `Ran 1 test in 0.042s`, `OK`.
- `python -m unittest discover -s tests -p 'test_groq_structured_adapter.py' -v` → `Ran 7 tests in 0.046s`, `OK`.
- `python -m unittest discover -s tests -p 'test_structured_provider_adapter.py' -v` → `Ran 9 tests in 1.629s`, `OK`; dos tests usan servidor HTTP loopback local, no HTTPS ni Groq.

La captura comprueba el cuerpo candidato serializado antes de descartarlo; no es una captura de transporte saliente integrado. El servicio rechaza el adaptador y la ruta de proveedor real no incorpora este cuerpo. No existe prueba real: requiere autorización explícita del usuario, además de una integración y revisión de seguridad independientes.
