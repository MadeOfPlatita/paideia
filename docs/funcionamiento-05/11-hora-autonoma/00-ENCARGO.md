# Bloque autónomo autorizado — 29 de octubre

Inicio:2026-10-29T16:40:20.122023Z. Corte máximo del bloque:2026-10-29T17:40:20.122023Z. Terminar antes si se completan los objetivos o aparece un bloqueo humano. No se activa un goal permanente ni cron. Tres subagentes ya despachados deleg_ad9612c6; necesitan Hermes y host activos y no sobreviven al cierre del proceso.

## Objetivo

Conectar proveedor Groq real al chat local con cálculo determinista, preparar evaluación A/B/C sintética, corregir contratos/chat y ejecutar regresión. Diseño al final. Primer smoke real ya verificado, pero calidad no aprobada y chat8765 aún no conectado.

## Permisos y paradas

Código propio local y pruebas, sin instalaciones/DB/altas/pagos/despliegues. No leer ni reutilizar clave de la ventana previa ni del entorno/historial. Nueva ventana enmascarada exige otra entrada voluntaria y confirmación Free. Sesión real temporal: máximo24 solicitudes externas/3600s desde autorización, incluyendo continuaciones y pruebas; son límites internos, no cuota acreditada del proveedor. No reintentos automáticos tras fallos/429; sin perfiles reales ni catálogo de permisos pendientes. Solo herramienta propia calculate_scenario en etapa real. No se garantiza persistencia distribuida ni funcionamiento online.

## Frentes exclusivos

1. Sesión segura: secure_groq_session.py, tests/test_secure_groq_session.py y01-sesion/.
2. Contexto/calidad: context_quality_benchmark.py, tests/test_context_quality_benchmark.py y02-calidad/.
3. ChatQA: secciónchat de app.js, tests/chat_frontend_contract.test.cjs, posiblechat_response_model.js/indexscript y03-chat-qa/.
4. Coordinador: revisión de backend, contratos compartidos, reproducción y navegador, evidencias y estado.

## Aceptación y evidencia

No confundir tests sintéticos, respuesta HTTP ni calidad del producto. Conservar resultados independientes, revisar código y reproducir suites/fronteras. Lectura de destino exacto tras llamada real. Usuario recibe estado breve, qué está activo y cualquier dependencia inicial: entrada de clave segura. No llenar una hora con búsquedas, esperas ni trabajo inventado.
