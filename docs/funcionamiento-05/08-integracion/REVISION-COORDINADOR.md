# Funcionamiento 05 — recepción e integración verificadas

## Resultado del coordinador

Las siete entregas de `deleg_09c6c535` se recibieron y revisaron. Se reprodujeron pruebas, se conectaron herramientas/orquestación/admisión a la frontera HTTP y se probó el perfil contra el servidor real. No se ha configurado ni llamado un proveedor LLM real, no se ha creado DB ni desplegado nada. Diseño/CSS sin cambios.

| Verificación final | Resultado | Evidencia |
|---|---|---|
| Suite Python de la aplicación | 155 tests OK, incluidos 9 tests nuevos de integración HTTP con subcasos | python-tests-final.json |
| Perfil frontend | 13 tests Node OK | node-profile-final.json |
| Sintaxis de ambos JS | OK | javascript-syntax-final.json |
| Probe del servidor normal | 19/19 HTTP | http-final.json |
| Navegación navegador real | 8 rutas × escritorio/móvil: 16 combinaciones sin overflow ni errores capturados | browser/f05-routes-summary.json |
| Perfil y privacidad | Núcleo, ramas económicas/riesgo, cero/no saber/omitir/sin preguntar, edición decimal, opt-in y borrado de copia y memoria; sin body de perfil | browser/f05-profile*.json |
| Modelo → tools → respuesta | HTTP y navegador con upstream TEST ONLY, motor y dispatcher reales locales; nunca IA real | test_functional05_http.py, browser/f05-chat-display-green.json |
| Cola | 202 + posición visible, reanudación manual, ticket cerrado no se repite; sin autoenvío | test_functional05_http.py, browser/f05-queue-browser-green.json |
| Estabilidad admisión | 20 ejecuciones de sus 18 tests, todas OK | admission-repeat.json |
| Spike almacenamiento | 11 tests reproducidos y experimento vuelto a ejecutar: 6/6 checks | spike-reproduced-results.json |

No sumar suites de referencia/spike a la suite de aplicación para anunciar un único total. Cien lecturas o solicitudes sintéticas no prueban cien chats ni capacidad de producción.

## Cambios integrados

- `backend_services.LocalChatService` conserva el chat apagado por defecto. Puede usar `ToolChatRunner` + `ToolDispatcher` con configuración confiable del servidor, consentimiento previo y admisión explícita.
- Las cinco herramientas son búsqueda, detalle, comparación, cálculo y fuentes. No hay SQL libre, URLs arbitrarias ni operaciones de compra/escritura. El motor determinista hace los cálculos.
- El turno inicial y cada llamada posterior al modelo consumen reserva antes de despachar. Agotamiento impide la continuación; errores no reembolsan reservas y `finally` libera el slot. La ejecución local de una tool no es otra llamada upstream.
- El chat externo sin presupuesto conocido falla cerrado. Además, habilitar tools externas exige aprobación separada del uso de datos del catálogo: tener un adaptador o una clave no convierte el inventario de investigación en datos publicables.
- `POST /api/chat-status` acepta solo un ticket opaco y devuelve estado/posición sin almacenar mensajes/perfiles ni llamar al proveedor. `/api/chat` admite reanudar con ticket, no un historial/rol/modelo suministrado por el cliente. Un turno ya reclamado/cerrado devuelve conflicto, no se vuelve a ejecutar.
- La UI ahora envía el consentimiento exacto, puede mostrar una respuesta válida con sus herramientas/fuentes y distingue explícitamente `test_only` de `external`. Muestra truncado/rechazo y cola manual; no incluye el perfil en el chat ni reintenta automáticamente.
- El perfil completo vive en el navegador con ramas voluntarias. El formato local v2 mantiene decimales como strings y mapping de paths a perfil05. **No valida directamente como el schema remoto 05 original**, que usa JSON number para importes. Esto está documentado por el agente y sigue siendo una frontera de conversión/evaluación pendiente, no permiso para enviar datos reales.

## Defectos reproducidos y corregidos al integrar

1. El formulario aún enviaba solo `message`; faltaba el consentimiento que exige el backend preparado. Regresión de navegador antes/después.
2. La UI descartaba un HTTP 200 válido aunque estuviera marcado como prueba. Ahora lo muestra como **PRUEBA SINTÉTICA — NO ES UNA IA REAL**, nunca como conexión demostrada.
3. Una búsqueda de los veinte candidatos producía 18.210 bytes de resultado de herramienta, superando por sí sola el límite de 16 KiB de request al modelo. Se compacta la vista enviada al modelo a resumen de identidad, conservando los veinte registros y las citas completas en el DTO del servicio. Los máximos de request no se ampliaron y la fuente de identidad no se convierte en evidencia de rentabilidad.
4. En el nuevo camino con admisión se perdía la distinción de errores 429/timeout. Se mantienen los códigos específicos, sin reintentos y conservando el consumo reservado.

Los 200 de prueba proceden de servidores temporales 8766/8767 con upstream fake explícito, no de Groq. Fueron detenidos y se comprobó que ambos puertos quedaron cerrados. Solo queda el servidor normal 8765, con IA no conectada. No se entrega un servidor fake como aplicación real.

## Decisión de almacenamiento

**No imponer PostgreSQL para el catálogo de lectura.** Propuesta mínima: fuente autorizada → normalización/revisión → JSON versionado y persistente → repositorio de lectura → aplicación. El spike local reprodujo 100 requests a un proveedor fake por acceso directo frente a 1 request y 99 hits por snapshot, con resultados equivalentes. Probó fallo, reinicio, reemplazo íntegro y política de fallback explícita. No prueba hosting, licencia, actualización diaria ni una API real.

Separar esa decisión de **presupuesto/cola**. El contador entregado en memoria no protege ante reinicios; export/import validado tampoco es persistencia. Para producción hacen falta persistencia antes de cada reserva y, si hay réplicas, coordinación coherente de cola/leases/concurrencia. La cancelación/deadline real del transporte antes de expirar la lease sigue pendiente: no prometer límite global de llamadas vivas por estos tests.

Cloudflare KV tiene consistencia eventual, de modo que no debe asumirse suficiente por sí solo para un contador global atómico de cupo ni para leases/FIFO.[1] Puede evaluarse para catálogo de lectura, pero no seleccionar el mismo almacén para todo por comodidad. Esto **no obliga a PostgreSQL**: obliga a validar la semántica del almacén elegido.

La recomendación Cloudflare Workers del agente es condicional. No está validada la adaptación del servidor local/transport HTTP al runtime Worker, alta sin tarjeta, región/privacidad, AUP, frontend, Cron ni coste de la cuenta. No desplegar `ThreadingHTTPServer` tal cual ni relajar Host/Origin para sortear incompatibilidades. Se corrige la formulación de Render Free como una advertencia/recomendación documental de no producción, no como una prohibición contractual acreditada.

## Datos reales: progreso y límites

Recuento propio: veinte candidatos, cuatro por familia; 62 observaciones numéricas (45 `known` del borrador y 17 `conflict`), 43 pares candidato/campo en 16 candidatos, 17 observaciones previas con recuperación solo por fecha. **Cero candidatos listos para comparación cuantitativa.** `known` no significa oferta vigente/apta: 53 hechos carecen de fecha efectiva y los permisos revisados permanecen `pending`.

Los 62 se construyen como `Fact`, pero eso solo acredita forma. Familias/scopes y permisos `display` del borrador aún necesitan mapping explícito al criterio del servicio/acción `app_display`; no se normalizaron ni aprobaron silenciosamente. El borrador no se cargó en el catálogo y el inventario original no se modificó. Se conservan conflictos de fechas, plazos y NAV.

Se reejecutaron los verificadores de citas/evidencias de los tres informes: storage, datos y alojamiento. El archivo Cloudflare Python cuyo patch falló existe y conserva sus extractos; la verificación pasó sin afirmar que ese patch se hubiese aplicado. Validar citas no acredita permisos, uso público, cuota efectiva o legalidad.

## Pendientes de producto

1. Confirmar acceso gratuito y autorizar/configurar de forma segura una prueba LLM real con datos sintéticos. Cero llamadas hasta ahora.
2. Comparación A/B/C antes de elegir contexto, conversión de perfil local y conversación contextual/multiturno. El nuevo perfil no se envía ni alimenta a Pai todavía.
3. Fuentes/condiciones/fechas/usos y mappings aprobados; ingesta real y políticas por campo sin TTL inventado.
4. Estado durable/coordinado y deadline/cancelación de transporte para las cuotas de producción, además de antiabuso. Cuotas reales de cuenta sin verificar.
5. Validar alojamiento 0 EUR, adaptación runtime, frontend y actualización programada; ninguna web pública creada.
6. Rediseño al final, no aprobado por haber pasado QA funcional.

## Notas de evidencia

La captura adicional del coordinador agotó el tiempo de la herramienta después de guardar las aserciones DOM/red. No se presenta ese fallo de captura como un defecto de app; se conservaron resultados JSON, las capturas del agente se mantienen como pruebas de su entorno sintético. Los fallos de selectores/alias del harness se separan de las regresiones funcionales rojas→verdes.

## Sources

[1] https://developers.cloudflare.com/kv/concepts/how-kv-works — How KV works
    > "KV achieves high performance by being eventually-consistent."
