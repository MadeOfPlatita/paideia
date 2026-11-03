# Hitos principales verificados — 00:03+01

- A sin dependencia GUI: revisión independiente favorable (deleg_931f4ba8/tarea1), sondeo coordinador 6 tests incluida la comprobación permanente de no abrir presupuesto si falta Tk.
- B procedencia cerrada: revisión final independiente favorable (deleg_1181f200/tarea2), 55 unittest propios del revisor + sondeos adversariales; no afirmar pytest completo por ese revisor. El coordinador acaba de comprobar pytest conjunto con funciones y unittest.
- Contaminación de pruebas: patch.dict restauraba el mock de MissionBudget después del contexto; se corrigió en pruebas exclusivamente. Evidencia RED/GREEN en MISSION-ISOLATION.md.
- Regresión conjunta del coordinador: `regression-coordinator-green.json`: **398 passed**, 369 unittest +29 nodos pytest no unittest, 6 pruebas GUI exactas deseleccionadas, 0 errores de colección, exit0. No se ejecutaron ventanas. Primer parseo de stdout del coordinador falló por texto adicional; se leyó el JSON guardado y se agregaron los resultados con código. El archivo es la evidencia, no ese error de parsing.
- Runner aprobado por revisión independiente y comprobación propia de 14 tests; no sandbox de procesos hijos.

Con base en A/B verdes y revisión, se autoriza fase opcional acotada hasta 00:13 para permitir revisión y cierre: parser puro y uso directo del ChatResult en la sesión sintética contada, sin envolverlo como FakeChatProvider. Esto **no implementa el transporte HTTPS estructurado real**, no habilita Groq y no se declarará prioridad2 completa por ese avance parcial. Corte general00:32:27, reserva pruebas/cierre desde00:22:27.
