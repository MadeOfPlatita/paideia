# Revisión independiente 1 — hallazgos y acciones

`deleg_f2f50aec`: revisión A no aprobada. El adaptador aceptaba solo `FakeChatProvider` pero `LocalChatService` aceptaba cualquier objeto con `test_only=True` y `select_education`; el objeto podría hacer red y se reportaría `external_sent:false`. No se realizó ninguna conexión. Corrección ciclo1 encargada: frontera cerrada y fixture sin wrapper arbitrario; no considerar `test_only` una garantía general de red.

Revisión B/C/D no aprobada en conjunto: una política explícita con ambos límites `None` permite comparar observaciones antiguas. Default sin política ya fallaba cerrado; no atribuir el problema al default. Ciclo1 debe exigir límites explícitos sin inventar TTL, preservar pruebas y mapear migración. C focalizado 9 pruebas verdes, una instancia/un escritor; sin garantía multiproceso o energía. D inspeccionado; el retroceso borra confirmación, faltan regresiones navegador adicionales y se detectó que el encabezado decía «candidato real» incluso en fixture ficticio.

El coordinador reprodujo ese encabezado con `tests/simulation_fixture_label.test.cjs` en rojo y lo corrigió a «candidato del catálogo»; el mismo test y sintaxis JS pasaron en verde. No significa que todos los candidatos sean reales ni publicados.

No declarar ninguno de los hitos afectados aprobado antes de recibir las correcciones, repetir integración/navegador y revisión independiente. Presupuesto de revisión: máximo dos ciclos.
