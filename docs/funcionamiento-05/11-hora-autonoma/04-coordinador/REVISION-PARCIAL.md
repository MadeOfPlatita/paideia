# Revisión intermedia del bloque autónomo

- Recibidas las tres entregas deleg_ad9612c6. La primera estaba bloqueada y no produjo lanzador: no se ha presentado como completada funcionalmente.
- El coordinador resolvió con rojo→verde el bloqueo: runner admite subconjuntos registrados no vacíos y rechaza herramientas no anunciadas ANTES de dispatch; LocalChatService ofrece tools_scope=calculator_only, filtrado exclusivamente en servidor, sin aprobar uso del catálogo. Se probaron HTTP positivo, tool de catálogo rechazada y scope de cliente rechazado. También se endureció error de configuración inválida.
- Se delegó de nuevo el lanzador (deleg_17d8f235) con las interfaces corregidas; aún no se abre nueva ventana ni se usa ninguna clave o llamada real durante esta revisión.
- Benchmark recibido/revisado:18 solicitudes sintéticas A/B/C, callback sin red propia, error/429 detiene sin retries, ganador null. Constructor nativo Groq verificado aparte con modelo canónico. Formato de fixtures no equivale a transmisión de perfil real del navegador ni a mapping remoto aprobado.
- Chat recibido/revisado: bloqueo de doble submit y ticket ligado a texto original; veinte pruebas Node correctas. El ticket abandonado todavía caduca, no se cancela explícitamente. Navegador del agente solo test-only, no evidencia de chat externo.
- Se añadió instrucción educativa al prompt real sobre inflación y evitar afirmar que ahorrar siempre carece de riesgo. Prueba verifica presencia de instrucción, NO obediencia ni calidad del LLM. Los datos y tasas siguen sin aprobación de publicación.
- Resultados intermedios de scopes/prompt/HTTP en JSON; la regresión final conjunta se hará tras recibir/revisar el lanzador. No se consideran producción, persistencia global ni nueva llamada real.
