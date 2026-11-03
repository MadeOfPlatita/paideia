# 06 — Admisión local de chat

Implementación aislada en `prototipos/paideia-local/chat_admission.py`; contrato ejecutable a integrar por el padre en `api-contract.json`. No toca rutas HTTP ni habilita el proveedor actual.

## Decisiones

- Política explícita por scope: concurrencia, tamaño máximo de cola, llamadas por minuto/día UTC, TTL de ticket y TTL de reclamación.
- Sin política: `disabled`. Política sin reloj/estado presupuestario válido: `state_unavailable` (fail closed).
- FIFO, reserva inicial previa al despacho y reserva explícita antes de cada llamada upstream adicional —incluidas rondas LLM con tools—. Cierre/cancelación/expiry no reembolsan reservas; EOF/timeout no se declaran éxito.
- `InMemoryBudgetState` no persiste: puede exportarse/restaurarse para pruebas. Para supervivencia a reinicios y multi-réplica hace falta un almacén compartido, duradero y atómico inyectado por la integración. No se creó DB ni infraestructura.
- Sin perfil, mensaje, credenciales ni IP; no hay cuotas por IP. El presupuesto mostrado es de llamadas configuradas por el padre, no una cuota real de Groq.

## Alcance de las pruebas

El archivo `test-results.json` conserva el resultado local; `tests/test_chat_admission.py` incluye concurrencia sintética de 100 solicitudes. No es un test de carga de chat/proveedor ni certifica 100 sesiones o 100 chats simultáneos.

Documentación de implementación e integración: `prototipos/paideia-local/ADMISION-CHAT.md`.
