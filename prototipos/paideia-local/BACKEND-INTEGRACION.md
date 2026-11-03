# Backend: integración local verificada

## Resultado

Se revisaron y reprodujeron los dos módulos de `deleg_171ec57c` y se conectaron a `app.py` mediante `backend_services.py`. No se modificó el diseño ni se instalaron dependencias. Servidor local: http://127.0.0.1:8765/ mientras esté encendido el proceso.

**Pruebas del coordinador:** 94 tests OK, 19/19 comprobaciones del servidor HTTP y sintaxis JavaScript correcta. Evidencia: `evidence/BACKEND-INTEGRACION.json`, `backend-tests-final.json`, `http-backend-final.json` y `backend-javascript-final.json`. Los tests de integración usan sockets HTTP reales locales y proveedor/datos positivos exclusivamente de test; no son respuestas de Groq.

## Chat y proveedor

- `/api/chat` pasa por `LocalChatService` y puede recibir un `GroqProvider` mediante configuración del servidor; ni el navegador ni el mensaje deciden proveedor, modelo, roles, herramientas o estado habilitado.
- El arranque normal `python -B -u app.py --port 8765` no configura proveedor, no lee la clave ni habilita llamadas por encontrar variables de entorno. El servicio está apagado por defecto. No se añadió un interruptor de activación externa a la CLI en esta fase.
- Para una futura configuración autorizada se necesitan tanto habilitación explícita del servicio como opt-in del adaptador. `PAIDEIA_GROQ_ENABLED=1` por sí sola NO conecta la aplicación. Antes deben confirmarse autorización, cuenta gratuita sin coste y condiciones de uso. No se ha hecho esa configuración.
- Si un operador configura el servicio, cada envío exige `message` y un consentimiento exacto: `notice_version="paideia-chat-remote-v1"`, `accepted_chat_processing=true`, `purpose="free_chat"`, `approved_fields=[]`. Esta versión solo permite el mensaje escrito: no perfil, contexto económico ni historial. El consentimiento local del prototipo anterior no se interpreta como autorización remota.
- Solo se construyen mensajes `system` del servidor y `user`. Se rechazan perfiles, historial arbitrario, modelos y campos adicionales. El formulario actual aún no implementa este nuevo contrato remoto y, con un proveedor habilitado, no podría saltarse la validación.
- Se transforman 401, 429, timeout, 5xx y JSON inválido en errores HTTP/códigos seguros, sin reintento automático ni eco del cuerpo del proveedor. No se presenta ningún fallback como IA.
- No se devuelve razonamiento interno. La respuesta diferencia rechazo y salida truncada (`refused`, `truncated`). Un transporte de test se identifica como `provider_mode="test_only"`, `external_sent=false` y nunca aparece conectado a IA real en `/api/status`.
- El chat NO anuncia ni ejecuta tools todavía. Una llamada no solicitada del modelo se rechaza con `CHAT_TOOL_CALL_REJECTED`, sin segunda llamada ni ejecución.
- Corregido un caso de seguridad del adaptador: comprobar solo bytes no detectaba un secreto ficticio escapado en JSON. La regresión comprueba texto, razonamiento, rechazo y argumentos anidados tras decodificar. No se usó ninguna clave real.

## Hechos y comparabilidad

`POST /api/compare` mantiene el contrato anterior `{ "product_ids": ["ACC-01", "ACC-02"] }`. Continúa siendo comparación de metadatos, sin tasas ni ranking fabricados.

Se admite opcionalmente el criterio técnico cerrado:

```json
{"product_ids":["DEP-01","DEP-02"],"criterion":"deposit_tae_12m_eur"}
```

- Devuelve diagnóstico `comparability`: falta de hechos, falta de política de frescura aprobada y familia incompatible se expresan con códigos. Ausencia de política no se confunde con ausencia de una métrica ya documentada.
- En el arranque normal no se han cargado hechos cuantitativos ni aprobado políticas. El resultado sigue siendo `quantitative_ready=false`, valores null y `not_for_publication=true`.
- La correspondencia técnica `deposito` → `term_deposit`/`term_deposit_tae`/`deposit.tae`, porcentaje explícito, EUR y doce meses no certifica que ningún candidato tenga esas condiciones. Otros criterios no se improvisan ni se deducen del ISIN.
- Solo el servidor puede inyectar hechos inmutables y una política explícita de frescura. La API no permite subir hechos, imponer TTL ni activar fixtures desde el cliente.
- Con política configurada se evalúa `app_display`: permiso de transformación no acredita visualización. Siguen pendientes derechos y evidencia de ingesta/transformación para productos reales.
- La familia del repositorio también debe coincidir; un ETF no se convierte en depósito por cambiar la métrica del hecho.
- Hechos sintéticos se excluyen por defecto. El positivo end-to-end usa únicamente productos `SYN-*` en un repositorio temporal de test, bandera de test explícita y respuesta `test_only_quantitative`; no se insertaron ofertas ficticias en el inventario real.
- Se retiró el límite accidental de exactamente veinte candidatos en `SnapshotRepository`. La regresión carga y sirve veintiuno sintéticos; el inventario real conserva sus veinte candidatos. Veinte es un hito, no un techo.

## Correcciones y evidencia roja→verde

Se conservan regresiones para criterio HTTP, wiring de hechos, wiring de chat, errores del proveedor, herramientas no solicitadas, truncado/rechazo, crecimiento de catálogo, estado de política y secreto escapado. El probe del proceso antiguo falló con 400 en el criterio nuevo (`http-backend-stale-server.json`); tras reiniciar únicamente el proceso gestionado de Paideia, las 19 comprobaciones pasaron.

## Pendiente: no se declara terminado el backend de producción

1. Acceso autorizado gratuito y smoke real sintético de Groq; cero llamadas externas hasta ahora.
2. Evaluación A/B/C y estrategia de contexto, aún sin ganador; no enviar perfiles reales.
3. Dispatcher acotado de herramientas y chat contextual/multiturno, cupos y cola, y nuevo consentimiento funcional en UI (sin rediseño visual).
4. Condiciones/fuentes/derechos publicables y políticas de frescura aprobadas; de momento cero ofertas cuantitativas verificadas cargadas.
5. Perfil financiero completo, PostgreSQL, ingesta, hosting público y carga. No se han creado DB/cuentas/despliegues.
6. Diseño definitivo, expresamente al final.
