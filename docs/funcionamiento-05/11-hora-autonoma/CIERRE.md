# Bloque autónomo de IA — resultados y límites

## Resultado real alcanzado

El chat web se conectó a Groq en la sesión temporal8768. Se comprobaron dos turnos independientes HTTP200, sin envío del perfil:

1. Pregunta → calculate_scenario ejecutada → respuesta real. El escenario ficticio de1000EUR/3%efectivo/1año/aporte0/inflación0 mostró1030EUR, coincidente con comprobación separada de la calculadora determinista. La respuesta del modelo se truncó a256tokens y la interfaz avisó.
2. Una pregunta conceptual breve sobre ahorro e inflación recibió respuesta completa en español, sin recomendar productos concretos. No se presenta como garantía universal de calidad financiera.

La sesión consumió cuatro intentos según el último estado runtime: uno del benchmark, dos del turno con herramienta y uno conceptual. Esos cuatro son de esta sesión; el smoke previo es evidencia separada. No se activó pago ni se creó cuenta, DB o despliegue. Free fue confirmado por el usuario, no técnicamente verificado contra facturación.

## Qué no se completó

A/B/C se detuvo tras su primer intento, sin resultados válidos. El registro original decía provider_error sin suficiente detalle: no se adivina la causa ni se fabrican resultados/ganador. No hubo reintento o reanudación automática. Contexto real del perfil, memoria entre turnos, datos comparables aprobados, hosting público y cupos durables siguen pendientes.

## Cambios locales

- Scope servidor calculator_only, registro de tools por subconjunto y rechazo de tools no anunciadas. No se concede permiso de catálogo.
- Bloqueo de doble envío y de asociar un ticket de cola a texto editado.
- Sesión temporal: entrada enmascarada y consentimiento, clave en memoria,24intentos máximos y corte absoluto, benchmark opcional con perfiles ficticios.
- Prompt con riesgos/inflación y brevedad; diagnóstico enum/bool/count que distingue truncado sin publicar reasoning/cuerpos brutos ni claves.
- El estado del benchmark distingue finalización con resultados de parada por error.

## Seguridad y estado actual

Una revisión independiente encontró una carrera entre admisión y envío. El coordinador detuvo la sesión y verificó cerrado el puerto8768. El fix conecta TLS primero y comprueba de nuevo estado/plazo bajo el mismo lock que revocar, justo antes del compromiso lógico de request; lectura de respuesta fuera del lock. No se promete instante físico de salida de bits ni cancelación de una petición comprometida; una escritura lenta puede retrasar la revocación.

Corrección reproducida offline con seis pruebas específicas y un probe independiente, sin red real. Regresión actual:195Python,20Node y19/19HTTP; sintaxis JS correcta. La segunda revisión independiente confirmó el TOCTOU resuelto y detectó un cierre automático prematuro del último intento reservado, corregido en el segundo y último ciclo. La GUI conserva la última reserva pendiente, pero revocar o expirar siguen bloqueándola; cuatro regresiones nuevas y suite conjunta reproducidas por el coordinador. Último veredicto independiente favorable (deleg_77165aae), sin incidencias en las rutas revisadas y con diez pruebas objetivo/probe sin red. No es una auditoría universal ni aprobación de calidad del modelo; sesión real apagada. No se reabre la sesión automáticamente ni se lee/reutiliza la clave anterior.

La aplicación normal8765 permanece separada y sin proveedor configurado. Las últimas mejoras de diagnóstico/brevedad/guard no se han probado contra Groq tras reiniciar; requieren nueva entrada y autorización segura. No es una entrega de producción.

## Evidencia

- `05-real/`: solicitudes/respuestas reales, benchmark detenido, cálculo independiente y último estado de sesión.
- `04-coordinador/regression-after-last-slot-fix.json`: salida real de regresión.
- `04-coordinador/independent-race-probe-after-fix.json`: probe del coordinador, falsoHTTPS.
- `06-security-fix/`: código de prueba, límites y salidas del agente corrector.

Bloque cerrado con veredicto independiente favorable en el alcance revisado. Siguiente paso: nueva validación de calidad/contexto solo con autorización segura, nueva entrada de clave y límites explícitos. No se amplía el corte temporal ni se reabre la IA automáticamente. No se requiere ninguna acción del equipo mientras esté ausente.
