# Admisión acotada para chat

Esta pieza implementa una **interfaz local de admisión**, no un endpoint HTTP ni un chat conectado. No se importa desde `app.py`, no habilita el servicio actual, no llama a proveedores y no crea workers ni trabajos en segundo plano. La integración HTTP queda a cargo del coordinador.

## Límites y estado por defecto

- `InterfazChatAdmission(policy=None, clock=...)` devuelve `disabled` y no acepta solicitudes.
- Una política explícita sin `budget_state` válido, con reloj desconocido o con el scope de presupuesto incorrecto devuelve `state_unavailable` (fallo cerrado).
- `AdmissionPolicy` recibe límites agregados por scope: concurrencia, cola, llamadas reservables por minuto/día UTC, TTL del ticket y TTL de la reclamación. No hay cuotas implícitas ni valores de proveedor asumidos.
- Los números de los tests son sintéticos. No representan cuotas de Groq ni de otra cuenta. El contador cuenta **llamadas upstream**, no tokens, Neurons, coste o éxito.
- No recibe ni guarda perfil, mensaje, credenciales o IP. No hay limitación por IP. Las cuotas de este módulo son globales al scope configurado; no implementa cuotas individuales por sesión.

## Contrato mínimo

```python
from chat_admission import AdmissionPolicy, InterfazChatAdmission

policy = AdmissionPolicy(
    max_concurrent=..., calls_per_minute=..., calls_per_day=...,
    max_queue=..., ticket_ttl_seconds=..., claim_ttl_seconds=...,
    scope="provider/model-version",
)
admission = InterfazChatAdmission(policy, clock, budget_state=budget_store)
```

Los `...` son configuración obligatoria del operador, no defaults recomendados. La política debe expresar el presupuesto agregado aprobado para un scope identificable; no copiar límites públicos de Free como si fueran límites de la cuenta real.

`budget_store` debe estar explícitamente inyectado y listo (`ready is True`, `scope`, `reserve(policy, now)` y `status(now)`). `reserve` debe incrementar de forma atómica y, para uso real, durable **antes de devolver `reserved`**. Sin estado conocido no se despacha.

## Secuencia de adaptación futura

1. `submit(idempotency_key=...)`: acepta un ticket. Si hay slot y presupuesto, devuelve `admitted`; si no, devuelve `queued` con posición 1-based. El primer cupo de llamada se reserva al admitir, antes de cualquier despacho. Si el presupuesto está agotado, muestra `quota_exhausted`; si la cola acotada no admite más, `queue_full`.
2. `claim(ticket)`: es no bloqueante. Solo la cabeza FIFO puede pasar de cola a admisión; un ticket admitido pasa a `claimed` una vez. No despachar si devuelve `queued`, `quota_exhausted`, `ticket_invalid`, `expired`, `duplicate` o `state_unavailable`.
3. El padre puede hacer **un** primer despacho solo tras `claimed`. Antes de cada llamada upstream adicional (por ejemplo, una ronda LLM después de ejecutar una tool) debe llamar `reserve_provider_call(ticket)`. Cada llamada upstream que implemente o ejecute una tool también debe reservarse. La ejecución local de una tool sin llamada a proveedor no es una llamada upstream.
4. En `finally`, llamar `complete(ticket)` o `cancel(ticket)` para soltar concurrencia. `completed` describe solo el cierre del ticket; **no afirma que el proveedor tuvo éxito**.
5. `status(ticket)` permite adaptar posición/estado. No hace espera ni polling interno; no implementar loops de reintento apretados o infinitos. El ticket caduca.

Códigos visibles: `disabled`, `state_unavailable`, `admitted`, `claimed`, `queued`, `quota_exhausted`, `queue_full`, `reserved`, `completed`, `cancelled`, `expired`, `ticket_invalid`, `duplicate`, `invalid_request`.

## Presupuesto: sin reembolsos

La admisión reserva una llamada antes del despacho; cada ronda upstream adicional requiere otra reserva. `complete`, `cancel`, timeout, rechazo, truncamiento o respuesta EOF no restan contadores. Una llamada puede haber llegado al proveedor aunque el cliente observe EOF/timeout, por lo que el módulo no la convierte en éxito ni reembolsa gasto incierto. No hay SDK ni lógica de retry aquí; todo retry manual cuenta como una llamada nueva y debe reservarse de nuevo.

Una admisión admitida que nunca se despache también consume conservadoramente la reserva inicial. La expiración de un ticket o el cierre de una conversación libera **solo concurrencia**, nunca presupuesto.

## Caducidad y capacidad

La cola FIFO está limitada por `max_queue`; las admisiones simultáneas por `max_concurrent`. Un ticket expira tras `ticket_ttl_seconds` si sigue esperando o no se reclama. Una reclamación expira tras `claim_ttl_seconds`; operaciones posteriores recuperan el slot y notifican `expired`. La recuperación es perezosa: se ejecuta al recibir una operación, no hay scheduler.

El consumidor debe cancelar el transporte y fijar un deadline total menor que `claim_ttl_seconds`; de otro modo una llamada upstream que siga viva después de que venza su lease podría solaparse con otro slot. Los tests de expiración usan un reloj sintético y no verifican cancelación real de transporte.

## Reinicios, persistencia y réplicas (límite importante)

`InMemoryBudgetState` es solo memoria de un proceso. **Por sí sola no impide reiniciar para resetear el contador diario.** `new_empty()` crea explícitamente una época nueva y no debe usarse al reiniciar un proceso con presupuesto previo.

`export_state()` y `restore(snapshot, expected_scope=...)` ofrecen un formato versionado y validado para probar export/import. El test de reinicio restaura un snapshot y conserva el agotamiento diario. La biblioteca no escribe ese snapshot en disco/DB y el round-trip de test no es persistencia. Para proteger de reinicios, el padre debe persistir cada reserva de forma durable y atómica antes del despacho, y restaurar ese estado antes de aceptar tráfico. Si el estado falta, está corrupto, tiene scope incorrecto o el reloj retrocede, fallar cerrado. La validación de esquema no autentica el snapshot: protegerlo contra alteración es responsabilidad del almacén externo.

Una instancia de `InterfazChatAdmission` coordina su cola y concurrencia solo dentro del proceso. El adaptador inyectable puede proporcionar un contador de presupuesto compartido/atómico, pero **esta clase no coordina concurrencia, FIFO ni reclamaciones entre réplicas**. Varias réplicas requieren almacenamiento compartido transaccional para presupuesto, cola, leases y concurrencia. No se creó ni eligió DB/hosting en este trabajo.

No se usa IP como identidad o cuota; una clase puede compartir NAT. Si el padre añade cuotas de sesión, debe utilizar una identidad de cuenta/sesión opaca y estable, verificada por el servidor, no la IP como única clave.

## Verificación

```sh
python -B -m unittest discover -s tests -p 'test_chat_admission.py' -v
```

Hay pruebas unitarias sintéticas del flujo FIFO, expiración, cancelación, cuotas UTC, export/import y 100 solicitudes con `ThreadPoolExecutor(max_workers=100)`. Estas prueban solo el coordinador local de admisión. **No prueban 100 chats simultáneos, latencia, throughput, proveedor real, límites de Free ni coste 0 € real.**
