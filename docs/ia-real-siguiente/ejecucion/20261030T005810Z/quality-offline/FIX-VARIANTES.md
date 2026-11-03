# Corrección offline de variantes

- TDD: el nuevo test reprodujo seis fallos antes del cambio: H02, H03, H08, H20 y dos evasiones adicionales (negación posterior ajena y cita afirmada). Después pasan los seis ejemplos.
- Pruebas offline: 11 tests `test_financial_quality*.py` y 249 tests de `unittest discover -s tests`, ambos OK. No se modificaron las pruebas preexistentes. El informe heldout original permanece intacto; no se ha reejecutado el corpus completo (el informe disponible solo contiene resultados, no textos).
- Se conservan la bandera `ABSOLUTE_NO_RISK` y el texto original: NFKC y eliminación de caracteres Unicode Cf se aplican solo al análisis. La detección reconoce formas léxicas delimitadas; la negación y la refutación usan contexto limitado. Se detectan citas afirmadas; antes todas las citas se excluían. Las citas refutadas explícitamente de los tests siguen excluidas.
- Limitaciones: no es un verificador semántico ni garantiza ausencia de falsos positivos o negativos. No cubre necesariamente H04, H05 ni H06; son exploratorios fuera del alcance. Los marcadores contextuales no resuelven todas las negaciones, hipótesis, citas o cláusulas en español. Ninguna bandera no equivale a aprobación de calidad.
- Sin cambios de prompt, transporte, registro, modelo o respuesta; no se realizaron llamadas reales a proveedores ni se registraron respuestas crudas.
