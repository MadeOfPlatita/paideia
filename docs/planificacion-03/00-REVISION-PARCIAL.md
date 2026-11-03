# Revisión parcial del coordinador — lote 11–16

## Estado

Se han recibido y revisado los seis frentes 11–16. El coordinador comprobó sus archivos obligatorios y parseó sus JSON. Los demás frentes de planificación y la ronda de APIs no se dan por recibidos ni verificados por este documento.

## Comprobaciones realizadas

| Frente | Revisión | Alcance real |
|---|---|---|
| 11 Simulación/PDF | Leída especificación y comprobados archivos | Diseño documental; no hay flujo implementado ni PDF generado |
| 12 QA | Leída matriz y revisados conflictos con requisitos | Casos propuestos, todos sin ejecución de app |
| 13 Despliegue | Leído runbook y parseado checklist | No hay cuentas, despliegue o DB creados |
| 14 Ingesta | Leídos especificación y script; reejecutado verificador por el coordinador | `OK: 7 casos JSON; 10 registros; JSON Schema Draft 2020-12 válido; 1 rechazo(s) estructural(es) esperado(s); ninguna fixture publicable.` |
| 15 Licencias/límites | Leídas decisiones y comprobados entregables | Propuestas operativas y revisión documental, no autorización de datos o dictamen vinculante |
| 16 Plan de semana | Leídos plan y lista de decisiones | Ruta D1–D7 propuesta; no ejecución ni aprobación automática del grupo |

El verificador de ingesta contrasta fixtures y algunas invariantes, no implementa un publicador PostgreSQL ni demuestra ingesta real, idempotencia transaccional o resolución automática de conflictos.

## Correcciones aplicadas tras revisión

1. QA describía la IA como opcional, en contradicción con el chat con LLM y perfil contextual solicitado. Se ha restituido el requisito y separado de la decisión pendiente sobre datos transmitidos.
2. La prueba de inyección prohibía toda llamada a herramientas. Se ha distinguido SQL/URLs/acciones arbitrarias de herramientas aprobadas de lectura y cálculo con validación y mínimo privilegio.
3. El plan de carga confundía presupuesto de cero euros con prohibición absoluta de un smoke gratuito. Se permite únicamente con autorización, cuota gratuita comprobada y sin facturación; de lo contrario sigue bloqueado.
4. El plan de semana decía que todos los datos de la contratación simulada serían ficticios. Se ha aclarado: operación e inputs de ejemplo ficticios; los hechos del producto real siguen siendo reales, con fuente, sin rellenar huecos.

## Puntos de integración todavía abiertos

- Alinear el contrato de herramientas de Pai con el adaptador de ingesta y el esquema físico de PostgreSQL cuando se reciban sus propuestas.
- Integrar datos mínimos contextuales autorizables con el mapa de privacidad, sin eliminar el perfil solicitado ni enviarlo completo automáticamente.
- Consolidar frescura por campo: los valores 24 h, 7 y 90 días son propuestas, no SLA ni valores aprobados.
- Actualizar las frases sobre ausencia de fuentes o permisos después de revisar los hallazgos de la segunda ronda; una carencia de la primera ronda no prueba que no haya alternativas.
- No elevar preferencias arquitectónicas como snapshot JSON frente a PostgreSQL a decisión del grupo sin explicar el resultado de la comparación.
- Un smoke de IA y una prueba de frontend con stub no demuestran cien inferencias concurrentes reales.
- Las decisiones técnicas recuperables por investigación no se devolverán al grupo como un nuevo cuestionario exhaustivo; las elecciones de alcance, cuentas y tratamiento de datos sí requerirán aprobación cuando corresponda.

## Límite de cierre

Este lote puede servir de base para integrar la planificación. No demuestra que los problemas operativos estén resueltos, que la aplicación exista o que esté lista para publicar. El cierre global sigue pendiente de los lotes restantes y de la revisión cruzada.
