# Continuidad y presupuesto de esta noche

El usuario comunica 76% de cuota restante y reset en4h42; es estimación humana no verificada por API. Reloj observado00:44:25+01, reset estimado05:26:25+01. No ampliar corte08:00ni esperar artificialmente a esa hora si las entregas ya terminan.

Se configuró mediante CLI en perfiltrabajos `goals.max_turns=300` y se leyó de vuelta300. La meta activa todavía conservaba20: se localizó solo la fila activa cuyo objetivo contiene GOAL-NOCHE-FUNCIONAL-20261103.md y se actualizó con las funciones canónicas load_goal/save_goal de Hermes. Readback:300máximo,5usados,active; resto de campos intactos, sin resetear contador ni contrato ni plazo.

Fallback configurado medianteCLI y leído de vuelta:custom/qwen3.6-35b-a3b,http://127.0.0.1:1234/v1. Antes no había fallback. EndpointLMStudio respondió a /v1/models e incluyó eseID; no se ejecutó inferencia ni se verificó su calidad o soporte de herramientas. Ollama11434norespondió. No nuevas credenciales ni instalaciones ni cambio del modelo principal; no garantía de recuperación automática si el servicio local falla, falta contexto/herramientas o el runtime se detiene. La documentación oficial indica cadena actualizada desde siguiente turno y primario elegible otra vez tras reset, no recuperación garantizada.

Agrupar trabajo y comunicar entregas/hallazgos, no consumir continuaciones en relojes sueltos/checkpoints duplicados mientras se espera a agentes. Reusar evidencia pertinente, solo regresión completa tras cambios relevantes y final. Continuar prioridades funcionales del encargo. Estos ajustes de Hermes no autorizan a la aplicaciónPaideia a llamar proveedores reales.
