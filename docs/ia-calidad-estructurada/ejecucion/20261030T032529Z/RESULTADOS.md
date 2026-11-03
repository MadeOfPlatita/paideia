# Resultado del trabajo nocturno offline

**Resultado:** sección vertical estructurada de prueba completada y revisada dentro del alcance offline. El punto 1 de Paideia no está completado ni se ha validado el proveedor real.

| Criterio | Evidencia | Resultado |
|---|---|---|
| Proveedor ficticio y selección cerrada | `tests/test_structured_education.py`, `tests/test_structured_turn_scenario.py`, `selection.schema.json` | Comprobado offline; no certifica un proveedor externo |
| Texto editorial y cálculo del turno | `structured-cycle1-e2e.json`, HTTP200/200; escenario explícito 1000 EUR/3%/1 año, motor devuelve 1030.00 EUR | Comprobado en navegador contra fixture recién arrancado |
| Consentimiento y datos | Mismo recorrido: sin consentimiento no se envió; requests sin perfil/historial | Comprobado para fixture |
| Respuesta con texto falsificado | Mismo recorrido: HTTP502, mensaje seguro y sin texto arbitrario | Comprobado; sin reintento |
| Regresión | `regresion-ciclo1.json`:270 Python,32 Node,19/19 HTTP; exit0 | Aprobada. Los19HTTP corresponden al servidor normal nuevo; la modalidad estructurada se verificó aparte en8771 |
| Revisión independiente | `REVISION-1.md` falló; `REVISION-2.json` pasó tras el primer ciclo de corrección;13 Python/63 subtests/11 Node | Aprobada solo en el alcance revisado |
| Cierre de procesos | Puertos8765,8768,8769,8771 cerrados al cierre; no se utilizó un proveedor real | Verificado |

Se conserva el contraejemplo léxico y el mapa del cambio de prueba en `MIGRACION-TESTS.md`. El legacy de texto libre sigue ejecutable y no aprobado; una regresión verde de la nueva modalidad no lo corrige. El UI confía en el backend local para exactitud aritmética; `test_only` por sí solo no imposibilita red. No se ha declarado revisión profesional del texto editorial.

**Próximo paso:** el equipo puede probar el fixture con `README-PRUEBA-LOCAL.md`. La futura adaptación y prueba con Groq requiere autorización específica, entrada segura y revisión adicionales; consultar `PENDIENTE-GROQ.md`. A/B/C y contexto/historial remoto permanecen pendientes.
