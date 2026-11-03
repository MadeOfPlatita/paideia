# Funcionamiento 05 — contrato y permisos compartidos

## Decisión del grupo

Aprobado avanzar en el recorrido funcional completo antes del diseño. PostgreSQL se cuestiona, no se aprueba eliminarlo ni crearlo: las APIs son fuentes, la persistencia/cache/normalización es una decisión independiente que debe validarse. Comparar la solución mínima sin DB con alternativas antes de elegir.

## Base y límites

Raíz: C:/Users/aleja/Downloads/App Financiera. App: prototipos/paideia-local/. Python stdlib, Node disponibles. Última verificación: 94 tests, 19 HTTP, JS válido. Backend app.py/backend_services.py; proveedores.py se llama literalmente providers.py. El catálogo real es inventario de 20 candidatos, 0 ofertas cuantitativas publicables cargadas. No confundir con hechos sintéticos.

Presupuesto 0 EUR. No cuentas, credenciales, lectura de claves reales, llamadas autenticadas, instalaciones, DB real (ni PostgreSQL ni SQLite), despliegue, pagos, ejecución de código descargado ni perfiles reales. Solo código propio local y red pública de lectura donde se autorice en la tarea. Sin bypass auth/WAF/TLS. Diseño/CSS/mascota fuera de esta fase. Tests positivos sintéticos aislados, no ofertas inventadas en catálogo. No modificar otras sesiones/perfiles Hermes.

## Integración: propiedad y contrato local-tools.v1

El coordinador conserva app.py, backend_services.py, providers.py, context_adapter.py, verify_http.py e integración HTTP. Ningún agente los modifica. Solo el agente de perfil modifica static/app.js e index.html, para funcionamiento, nunca estilos. Otros agentes escriben exclusivamente archivos asignados.

Las cinco herramientas mantienen los nombres del plan, pero el contrato **local-tools.v1** usa IDs literales del SnapshotRepository (DEP-01, etc.), NO finge cumplir el contrato UUID propuesto. ToolDispatcher(repository, comparison_service) expone definitions() -> lista OpenAI tool definitions y dispatch(name, arguments) -> dict con schema_version='local-tools.v1', tool, status, data, sources, error. Códigos estables y errores seguros. Toda entrada tiene campos cerrados:

- search_products: {query: string <=100, family: familia local|null, limit: integer 1..20}. Las familias son cuenta_remunerada, deposito, letra_deuda_publica, fondo_tradicional, etf_ucits. El límite es por respuesta, no techo de catálogo. No filtrar tasas que no existen.
- get_product_detail: {product_id: ID local literal}.
- compare_products: {product_ids: 2..4 IDs únicos, criterion: 'deposit_tae_12m_eur'|null}. Con null, solo metadatos; con criterio, usar comparison_service.compare(products, criterion). No crear condiciones.
- calculate_scenario: las SEIS propiedades exactas del calculate_scenario actual en domain.py: principal, annual_rate_percent, years, monthly_contribution, method, inflation_percent. Unidades y convención del motor actual; no convertir silenciosamente el contrato de meses del plan.
- get_sources: {product_ids: 1..20 IDs únicos}. Fuentes de identidad obtenidas del repositorio, etiquetadas como tales; no probar condiciones por enlazar la página. No URL arbitraria.

ToolChatRunner(provider, dispatcher, max_tool_rounds=2) recibe mensajes ya autorizados y validados por el servicio, no decide consentimiento. El proveedor implementa chat(messages, tools=None) -> ChatResult de providers.py. Usa definitions()/dispatch(), devuelve DTO sin razonamiento con answer, refusal, finish_reason, tool_events y sources derivados de resultados reales. Sin red durante pruebas: provider/transport fake marcado test_only. Rechazar tools desconocidas y llamadas repetidas/ciclos; máximo acotado y cero reintentos. Este contrato no permite al cliente enviar tools, system, SQL o URLs arbitrarias.

Los datos de perfil siguen en el navegador. La ampliación funcional preserva omitir/no saber/0, guardado opt-in/borrado y no añade perfil al body del chat. No se elige contexto completo/reducido hasta A/B/C con IA real. La ampliación frontend debe documentar su esquema local y mapping al perfil05; el coordinador revisará antes de darlo por integrado.

## Criterios de recepción

Cada agente: pruebas rojo→verde cuando implemente, evidencia con comando/exit code y alcance, cambios/rutas exactos, pendientes claros. Sin afirmar integración global, IA real, 100 chats, publicación o despliegue por pasar tests aislados. El coordinador inspeccionará y reproducirá antes de integrar y probar el recorrido real en navegador.
