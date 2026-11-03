# QA de integración del chat

## Alcance y resultado

Se inspeccionaron `LocalChatService`, `ToolChatRunner`, admisión, `POST /api/chat`, `POST /api/chat-status` y el código de chat de inicio. No se modificó backend, proveedor, catálogo, cuestionario ni estilos. No se utilizaron claves ni red externa.

Se corrigieron, con pruebas RED → GREEN, dos carreras acotadas: un envío repetido mientras hay otro pendiente podía generar dos solicitudes, y un ticket de cola recibido tras editar la pregunta podía asociarse al texto nuevo. Ahora el segundo envío se bloquea y el ticket antiguo se descarta con aviso si el texto se editó. El ticket descartado no se cancela en el servidor y puede ocupar plaza hasta su caducidad; no se inventó un endpoint de cancelación.

## Comprobaciones

- Node: `node --check static/app.js` y `node --test tests/*.test.cjs`: 20 pruebas correctas, cinco nuevas de chat. Se ejercita el código real de la sección y `apiRequest` con un simulador pequeño y local de elementos y respuestas; no es un navegador completo.
- Consentimiento: sin marcar no se envía; tras marcar se envía solamente `message` y `consent` con `paideia-chat-remote-v1`, `free_chat` y `approved_fields: []`, más `ticket` solo en reenvío. No se envía el mapa de perfil. El texto libre puede contener datos que el usuario escriba; esto no prueba su ausencia.
- DTO sintético de modo `external`: no se descarta y no se etiqueta como prueba; se ejercitan también modo `test_only`, `refused`, `truncated`, herramientas, enlaces HTTPS seguros y rechazo de enlaces peligrosos. **Un DTO sintético con `provider_mode: external` no constituye respuesta real.**
- Cola HTTP 202: posición y cupo visibles, sin envío automático; el reenvío solo al pulsar. Error HTTP 429 visible sin reintento. Las carreras de edición y doble envío se reproducjeron antes del arreglo.
- Navegador real en loopback con `tests/serve_test_only_chat.py --port 0`: sin consentimiento cero solicitudes; con consentimiento una solicitud sin perfil y respuesta visible marcada inequívocamente como sintética, con herramienta `calculate_scenario (executed)`. Puerto efímero 64025, fixture detenido. Esta prueba usa backend HTTP y herramientas locales, pero proveedor ficticio: no prueba conectividad real externa.
- Backend: `test_backend_integration.py` 13, `test_chat_admission.py` 18, `test_pai_runtime.py` 14, `test_functional05_http.py` 9; todas correctas.

## Límites y contrato propuesto

- No se hizo ni se afirma una llamada real desde el frontend a Groq: el escenario de navegador fue sintético; el DTO `external` de Node fue una fixture. Un smoke real independiente no demuestra este recorrido frontend. Tampoco se inspeccionaron secretos ni se garantiza que un usuario no los escriba en el campo libre.
- `LocalChatService` marca `external_sent: true` solo en respuesta final externa, y `false` en cola; el estado `configured_not_verified` no demuestra conectividad. Un turno externo requiere admisión/presupuesto y, si usa herramientas, aprobación del uso externo de catálogo y dispatcher. El frontend no valida `external_sent` contra `provider_mode`; proponer un contrato versionado y documentar sus invariantes antes de endurecerlo.
- El endpoint de estado requiere ticket y no envía al proveedor, pero la interfaz deliberadamente no hace polling; la recuperación es manual mediante `/api/chat`. Proponer cancelación explícita e idempotente para evitar tickets abandonados al editar o navegar, y especificar caducidad/posición y qué sucede en caso de timeout ambiguo.
- Se muestran hasta 20 fuentes con URL HTTPS segura; fuentes sin URL segura se omiten y el aviso distingue identidad de condiciones. Proponer informar cantidad omitida y conservar procedencia completa en el contrato; no convertir fuentes de identidad en evidencia de rentabilidad.
- Una respuesta o rechazo real no implica calidad financiera: verificar por separado afirmaciones como «ahorrar sin riesgo» y política de seguridad del proveedor. El test de transporte no evalúa veracidad.
- No se realizó una auditoría completa de secretos, accesibilidad, móvil ni la interacción con un proveedor externo; no hay polling ni reintentos secretos en la sección inspeccionada. El navegador se probó con una sola conversación sintética, no con escenarios visuales 202/429 reales.
