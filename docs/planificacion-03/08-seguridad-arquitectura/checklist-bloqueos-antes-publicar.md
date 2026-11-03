# Bloqueos antes de publicar — Paideia

**Uso:** lista P0 de salida. Cada casilla exige enlace/artefacto de evidencia, responsable y fecha. «Pendiente» equivale a **NO PUBLICAR** en esa capacidad. Este diseño no ha ejecutado pruebas; no marcar nada como aprobado por estar descrito aquí. Chat/ingesta pueden mantenerse apagados para publicar sólo la web estática si sus rutas/secretos no están presentes.

## P0 — bloqueos del sitio público

- [ ] **Alcance y textos:** resolver conflicto de alcance entre `docs/REQUISITOS.md` (perfil contextual, productos específicos) y `docs/investigacion/10-seguridad-calidad.md` (MVP chat externo apagado/datos ficticios). Texto visible indica simulación; no ofrece consejo/profesionalidad ni dice que el flujo contrata. Evidencia: decisión de alcance y capturas de pantallas.
- [ ] **Sin transacciones/PII:** inventario de rutas, dependencias, tablas, colas y botones confirma ausencia de pagos, contratación, cuenta, lead, solicitud, datos de identidad y operaciones; simulaciones en memoria sin endpoint de escritura. Evidencia: inventario y pruebas de recorrido en backend de test.
- [ ] **Frontend/proxy:** HTTPS, host/origin exactos, CORS no reflectivo, métodos esperados, límite de body y límite de conexión; forwarded headers confiables sólo desde proxy. Evidencia: configuración y test HTTP en staging.
- [ ] **Separación de red:** navegador no contiene DSN/clave, no llama a PostgreSQL/proveedor y sólo usa API mismo origen; reglas egress restringen destinos. Evidencia: build/source map revisados, HAR de prueba sintético y configuración del host.
- [ ] **PostgreSQL (si se publica):** rol runtime no owner/superuser/BYPASSRLS; sólo SELECT mínimo; RLS habilitada y forzada; política de filas publicadas probada con rol runtime; sin permisos de DDL/DML/TRUNCATE. Evidencia: grants/policies de staging y test negativo por operación.
- [ ] **SQL:** ninguna ruta acepta SQL libre, nombres de tablas/campos libres ni SQL del modelo; parámetros unidos al statement y orden/filtros por mapas cerrados. Evidencia: tests con `SQL-*` y revisión de repositorio de datos.
- [ ] **Tools:** por defecto ninguna tool; si se habilita lectura, inventario cerrado + JSON Schema estricto, límites de cantidad/longitud y dispatch de servidor; cero URL/fetch, SQL, shell, filesystem o writes. Evidencia: configuración del proveedor y tests `TOOL-*`.
- [ ] **SSRF/ingesta:** no aceptar URL del usuario/LLM; ingesta off si no hay registro de fuentes, validación DNS/IP en conexión, bloqueos v4/v6, redirects off y egress controlado. Evidencia: pruebas deterministas con resolver/HTTP stubs; no pruebas contra redes reales.
- [ ] **PDF:** sin upload público. Si se habilita ingesta PDF, proceso aislado sin red, tipo real, límite de tamaño/páginas/tiempo, acciones/adjuntos sin ejecución, cuarentena y revisión humana. Sin aislamiento: desactivada. Evidencia: test del parser en staging aislado.
- [ ] **Markdown/XSS:** salida y contenido de fuentes se tratan como texto no confiable; no `innerHTML` sin sanitizador auditado; raw HTML, enlaces no HTTPS, imágenes remotas, SVG e iframe bloqueados. Evidencia: casos `HTML-*` en DOM/browser.
- [ ] **CSP:** política bloqueante en header para documentos, API y errores: `default-src 'none'`, scripts/conexiones/recursos propios, `object-src 'none'`, `base-uri 'none'`, `frame-ancestors 'none'`; sin `unsafe-inline/eval` salvo excepción aprobada. Evidencia: capturas de headers de staging y prueba de bloqueo de carga externa; report-only no cuenta.
- [ ] **Secretos:** proveedor elegido con clave sólo backend; escaneo de fuentes, historial revisable y artefactos distribuidos; `.env`/secrets excluidos; ninguna clave en bundle/sourcemap/logs/respuestas. Si hay exposición: revocada/rotada y retirado historial/artefactos afectados. Evidencia: scanner + revisión manual sin copiar secretos al reporte.
- [ ] **Privacidad:** perfil no financiero sólo local y borrable; importes sólo memoria; no se envían perfil/escenarios a LLM ni logs/analytics. Aviso «no introduzcas datos personales/bancarios». Para chat externo: proveedor, uso, región, retención, condiciones/contrato y aviso revisados; no resuelto = chat off. Evidencia: inspección de red con fixtures sintéticos y texto/aviso aprobado.
- [ ] **Presupuesto global:** cifra diaria y mensual en euros aprobada para modelo/proveedor, límite interno ejecutable además del límite del proveedor, contador atómico/reserva y alertas/off-switch. Valor nulo/no definido = chat off. Evidencia: config del provider mock y lectura de contadores de staging; no gastar en proveedor real durante estas pruebas.
- [ ] **Justicia de NAT/cuotas:** límite primario por token anónimo/sesión; IP no hard limit normal; trusted proxy configura IP. Configuración candidata: 5/min y 30/día por sesión, 300 llamadas/día global, 12 concurrencias, todos sujetos a revisión. Evidencia: test de 100 sesiones sintéticas en una IP TEST-NET y prueba de exceso individual/global; ningún 429 provocado por IP compartida.
- [ ] **Timeout/retry/off-switch:** deadline total, límites de respuesta, retries 0 en SDK/proxy/cliente, circuito, budget exhaustion y `PAIDEIA_CHAT_ENABLED=false` comprobados; el off-switch impide llamadas nuevas. Evidencia: provider mock devuelve timeout/429/503; una llamada máxima, error tipado y catálogo todavía operativo.
- [ ] **Errores/logs:** contratos de `contratos-error.md` probados; payloads/logs no contienen prompt, salida completa, clave, cookies, SQL, stack ni datos personales; timeout no afirma que proveedor no recibió texto. Evidencia: snapshots de error/log con señuelos sintéticos.
- [ ] **Catálogo:** cada campo relevante tiene fuente, licencia, fecha de consulta/efectiva, moneda y estado; obsolescencia tratada conforme regla decidida; nada del flujo de ingesta publica directamente. Evidencia: registro versionado fuente → candidato → aprobación → release.

## P0 — chat/ingesta: puertas adicionales de activación

- [ ] Proveedor y modelo nominados; límites/retención/entrenamiento/región/condiciones y aviso revisados; responsable de secretos y revocación asignado.
- [ ] Host permite secreto backend y límites/circuito; CDN/proxy no expone secreto ni elude quota/timeout; versión/configuración del SDK verificada con retries desactivados.
- [ ] Herramientas de lectura probadas bajo cuenta read-only/RLS; el LLM no ve perfil ni importes; salida inválida produce rechazo/fallback.
- [ ] Fuentes externas permitidas y licencia registradas; DNS/redirect/egress y parser PDF aislado verificados. Si no se cumplen, ingesta desactivada y catálogo versionado manualmente.

## P1 — antes de afirmar «100 usuarios concurrentes»

- [ ] Existe staging propio y autorización del titular; recorrido y volumen (concurrencia, think-time, duración) acordados.
- [ ] Prueba futura con provider mock y 100 VUs; mide p95/errores, límites, memoria y disponibilidad de catálogo/calculadora. La cifra objetivo de latencia/errores se acuerda y registra antes de ejecutar; no inventar mediciones ni cargar proveedor comercial.
- [ ] Confirmar que shared NAT no provoca 429 de sesión a usuarios distintos; documentar cuáles respuestas resultan del techo global, proveedor o presupuesto.
- [ ] Revisar carga/picos, cuota gratuita real del proveedor, coste máximo y comportamiento al superar presupuesto; sin cifra/cupo comprobado, chat off.

## Evidencia y cierre

| Control | Responsable | Evidencia/enlace | Resultado (aprobado/bloqueado) | Fecha |
|---|---|---|---|---|
| C01–C16 | | | | |

Publicar sólo capacidad verificada. La publicación de la SPA no habilita automáticamente chat, ingesta ni fuente real. No se garantiza eliminar prompt injection; se aprueba únicamente contención: sin permisos/escrituras/secretos/datos privados y con salidas tratadas como no confiables. Referencias técnicas y límites de este diseño: [`threatmodel.md`](./threatmodel.md).