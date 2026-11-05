# Encargo preparado: cerrar el punto 1 — IA de Paideia

ESTADO: PREPARADO, NO ACTIVADO. Este archivo no crea un goal activo, cron ni trabajo independiente. El usuario lo ejecutará más adelante mediante /goal. No consumir API ni arrancar ventanas/servidores durante la preparación.

## Raíz, prioridades y lectura mínima

Proyecto: C:/Users/aleja/Downloads/App Financiera. Perfil Hermes: trabajos; no modificar otros perfiles. Backend/funcionamiento primero, diseño al final. Reutilizar investigación y código existente; evitar releer todo el historial, nuevas rondas generales y delegaciones masivas. Leer:

1. docs/funcionamiento-05/11-hora-autonoma/CIERRE.md.
2. docs/funcionamiento-05/11-hora-autonoma/04-coordinador/FINAL-REVIEW.json y regresión más reciente.
3. app/secure_groq_session.py, providers.py, backend_services.py, pai_runtime.py y context_quality_benchmark.py.
4. Tests específicos según el cambio. Perfil: static/profile_model.js y PERFIL-FUNCIONAL.md solo al conectar contexto.

## Hechos de partida, no trabajo por repetir

- Última regresión verificada:195 Python,20 Node,19/19HTTP. Revisiones de guard de envío y último intento cerradas favorablemente en alcance, no auditoría universal.
- Hubo dos turnos WEB reales con Groq: cálculo con herramienta y respuesta truncada; concepto ahorro/inflación completo. Cuatro intentos en aquella sesión. No confundir con resultados de la próxima sesión.
- A/B/C se detuvo tras un intento, cero resultados válidos, ganador null. Su causa original es desconocida: no la reescribir como truncado probado. Diagnóstico posterior y brevedad solo se verificaron offline.
- IA temporal detenida, clave no conservada. Puerto8768 se cerró; no suponer que ningún proceso siga vivo.
- HARD_DEADLINE está fijado al bloque anterior (2026-10-29T17:40:20Z). No ejecutar a ciegas ni usar aquel corte como plazo de la nueva misión.
- Catálogo: sin condiciones cuantitativas aprobadas. Tools externas solo calculate_scenario; no aprobar catálogo por habilitar IA.

## Activación posterior y límites

Al recibir la orden de ejecución, comprobar hora real y fijar UNA ventana de trabajo de hasta60min desde activación, sin prolongarla silenciosamente por reinicios. Registrar inicio/corte e ID de misión en docs/ia-real-siguiente/ejecucion/. Adaptar el corte antiguo de forma explícita y probada antes de pedir la clave. No activar esta misión al leer su preparación.

Coste permitido0EUR: sin pagos, upgrades, tarjetas, altas, instalaciones de código descargado, DB ni despliegues. No modificar configuración de Hermes salvo necesidad expresamente autorizada. Código propio local y pruebas autorizados. Mantener ordenador y Hermes activos; no prometer supervivencia al cierre.

Máximo24 intentos externos en TODO el nuevo bloque: chat, herramientas/continuaciones, benchmark y diagnósticos incluidos. Mantener un registro seguro de consumo para no restaurar24 al reiniciar. No mezclar el cupo de este bloque con el anterior. Ningún reintento automático tras error/429; guardar parcial y parar esa evaluación. No elevar salida, modelo o consumo a escondidas. No rellenar la hora ni gastar el cupo porque quede disponible.

Antes de cada fase real, clave introducida voluntariamente en ventana LOCAL ENMASCARADA, confirmación Free sin facturación y consentimiento de sesión. No pedir claves por chat, leerlas del historial/clipboard/entorno ni archivos de credenciales, capturarlas o guardarlas en proyecto/logs. No reutilizar clave de proceso viejo. El checkbox no verifica técnicamente la cuenta ni garantiza coste si el usuario está en un plan distinto. Sin esta entrada, completar lo offline y detener la parte autenticada con dependencia clara.

Datos exclusivamente sintéticos en las pruebas. No transmitir un perfil real ni activar envío automático al conectar chat. Contexto e historial son fronteras de consentimiento distintas del guardado local. No conceder publicación de catálogo ni derechos de fuentes.

## Orden ejecutable

### A. Preflight barato y continuidad segura

- Cargar skills pertinentes (Hermes si se usa /goal; TDD/debugging/dogfood según trabajo).
- Verificar archivos/cambios, procesos y puertos. No matar procesos ajenos ni suponer Git disponible.
- Leer docs/ia-real-siguiente/PREPARACION.json: es una comprobación offline previa, no prueba futura ni cuotas reales.
- Reproducir primero guard/revocación, última reserva, diagnóstico y constructor de solicitudes; ejecutar la suite completa una vez tras cambios relevantes, no repetidamente sin motivo.
- Preparar nuevo corte configurable y probado: revocar/expirar bloquea ANTES del compromiso lógico de envío tras TLS; no prometer cancelación in-flight ni instante físico de bits. Conservar último slot admitido hasta fin/error sin autorizar el siguiente.

### B. Calidad real mínima antes del benchmark

- Abrir entrada segura solo cuando lo offline pase; explicar cupo/corte y autorización separada de A/B/C.
- Una pregunta conceptual breve y un recorrido web pregunta→calculate_scenario→respuesta, con importes ficticios. Comprobar consentimiento, cuerpo sin perfil/historial, campos de herramienta válidos y resultado frente a motor determinista, aviso de rechazo/truncado y ausencia de respuestas falsas.
- Guardar salidas reales y distinguirlas de test_only. Registrar también respuesta incompleta, no convertirHTTP200 en aprobación de calidad.
- Si vuelve a fallar, usar metadatos sanitizados para identificar capa. No publicar reasoning ni cuerpos brutos. Un caso sintético que imita el fallo no demuestra la causa del incidente real. No reintentar automáticamente ni aumentar256tokens por intuición: medir y justificar cualquier propuesta contra el presupuesto antes de autorizar más consumo.

### C. Evaluación A/B/C controlada

- Reutilizar seis casos y sus18solicitudes. Mismo modelo, pregunta, evidencia, instrucciones/herramientas y límites entre variantes; solo cambia el contexto. Usar el mismo transporte con presupuesto global.
- Sin perfil / relevante / completo, todos ficticios. No equiparar fixtures antiguas al perfil frontend v2 sin mapping de valores/tipos explícito: strings decimales, cero, no_se, omitido y sin_preguntar.
- Detener ante error/429/corte/cupo y conservar parcial/caso/código seguro. Uso/tokens/coste no suministrados son desconocidos; bytes no son tokens facturados.
- Revisar exactitud y fuentes, utilidad contextual, claridad, consumo/latencia y minimización. No elegir ganador por formato ni autovaloración del propio LLM. Si falta evidencia, winner:null y estrategia no aprobada. No autorizar por esto perfiles reales completos.

### D. Contexto e historial, sin romper privacidad

- Preparar e integrar en backend/frontend solo lo que permita la evidencia. Si C es inconcluyente, mantener chat sin perfil por defecto y funciones nuevas desactivadas o limitadas a pruebas sintéticas.
- Proyección versionada con lista exacta de campos, vista previa local y selección expresa. No convertir desconocido/omitido/sin preguntar en cero ni enviar campos no aprobados.
- Memoria de conversación acotada en la pestaña, con consentimiento remoto explícito para reenviar mensajes anteriores, borrado y límites de turnos/tamaño/presupuesto. Sin registro ni persistencia automática de chat/perfil.
- Actualizar contratos y prompt de forma coherente: no decir que no se recibe contexto si se adjunta. Nunca reenviar reasoning ni instrucciones de tools como autoridad.
- Validar nuevos DTOs completos y compatibilidad con petición antigua; no desplegar frontend incompatible sobre servidor vivo anterior. Reiniciar solo con nueva entrada segura si hace falta; consumo/corte no se reinician.

### E. Verificar, revisar y cerrar

- TDD por cambio, no lista de tests imaginados. Probar UI real y backend juntos, además de helpers.
- Ejecutar Python unittest, Node tests, sintaxis JS y HTTP con servidor real local; fixtures claramente separadas de proveedor externo. Probar cierre/cupo, consentimiento, error/cola y respuestas reales breves.
- Revisión independiente si hay cambios de credenciales/concurrencia. Máximo dos ciclos de corrección; si sigue fallando, parar y reportar sin declarar aprobado.
- Leer el destino exacto tras cada operación externa antes de declarar éxito. Conservar evidencia real sanitizada, matrices de aceptación y límites en docs/ia-real-siguiente/ejecucion/.
- Detener/revocar la sesión al cerrar el bloque y verificar puerto/cupo; mantener claves fuera de archivos. No ampliar corte ni activar cron/goal permanente.
- Informe final corto: cambios, pruebas reales, incidencias, pendientes y pasos del equipo. No afirmar punto1 completado si falta calidad, A/B/C o contexto/historial; entregar parcial honesto si existe bloqueo.

## Comandos offline de referencia

Desde app:

    python -B -m unittest discover -s tests -p 'test_session_*.py' -v
    python -B -m unittest discover -s tests -p 'test_*diagnostics.py' -v
    python -B -m unittest discover -s tests -p 'test_*.py' -q
    node --test tests/*.test.cjs
    node --check static/app.js
    node --check static/profile_model.js
    python -B verify_http.py

verify_http.py necesita servidor normal activo; si está parado es un problema de infraestructura, no inventar pasadas. No usar todos los comandos en bucle.

## Paradas

Cierre anticipado por objetivos logrados, corte60min, falta de entrada segura/confirmación Free, cuota/429/error sin diagnóstico, permisos insuficientes o dos ciclos de seguridad fallidos. Guardar punto de reanudación y decir qué falta. No buscar indefinidamente, ni gastar tokens en rehacer investigación/planificación terminada.
