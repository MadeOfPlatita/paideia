# Paideia — coordinación de cierre de planificación

## Estado

Se recibieron dieciséis frentes de planificación y las dos auditorías cruzadas 17/18; se han revisado sus archivos y JSON. La ronda de diez áreas de APIs está revisada estructuralmente y contrastada en casos decisivos; el frente de fondos fallido se recuperó directamente. Leer `../ESTADO_Y_PLAN.md`, `../investigacion-apis-02/00-SINTESIS.md` y `19-integracion/CRITERIO-INTEGRACION.md` como estado vigente. Las revisiones parciales anteriores son históricas. Está consolidado el criterio documental, no cerrada la implementación de contratos ni la integración de aplicación/DB/LLM. Los pendientes y decisiones permanecen visibles.

No se han autorizado ni realizado instalaciones, alta de servicios, pagos, despliegues o creación de una base PostgreSQL por esta ampliación. Se permiten especificaciones, recursos originales y pequeños verificadores propios aislados; los resultados de estos últimos se deben reproducir antes de declarar un componente validado.

## Frentes adicionales y entregables esperados

| ID | Directorio exclusivo | Problema que debe concretar | Verificación pendiente |
|---|---|---|---|
| 01 | `01-pai-tools/` | Pai, backend y consultas controladas a PostgreSQL | Contratos, schemas, fuentes y estados de fallo |
| 02 | `02-ia-alternativas/` | Proveedores adicionales de IA y condiciones de uso | Evidencia de cuotas, región, herramientas y carácter gratuito |
| 03 | `03-capacidad-ia/` | Consumo con instrucciones, herramientas, historial y cien usuarios | Reejecutar cálculos; no confundir con carga real |
| 04 | `04-motor-financiero/` | Fórmulas y casos de referencia | Reejecutar verificador y comprobar límites documentados |
| 05 | `05-perfil-conversacion/` | Árbol adaptativo, omitir, editar y contradicciones | Coherencia con requisitos, privacidad y límites de orientación |
| 06 | `06-escenarios-visuales/` | Supuestos, visualización y accesibilidad | Separar flujos contractuales de hipótesis de mercado |
| 07 | `07-comparador-reglas/` | Comparaciones, filtros, orden y datos incompletos | Trazabilidad, elegibilidad y ausencia de métricas engañosas |
| 08 | `08-seguridad-arquitectura/` | Amenazas, permisos y control de abuso | Controles verificables y NAT compartida en clase |
| 09 | `09-privacidad-datos/` | Flujo de datos locales, chat, logs y exportación | No inferir anonimato por ausencia de DNI |
| 10 | `10-diseno-pai/` | Diseño responsive y mascota original | Estado de propuesta, contraste y recursos sin copiar marcas |
| 11 | `11-simulacion-pdf/` | Contratación ficticia y justificante | Sin transacciones, identificación real ni apariencia de contrato válido |
| 12 | `12-qa-aceptacion/` | Matriz de pruebas y definición de terminado | Separar pruebas propuestas, ejecutadas y pendientes |
| 13 | `13-despliegue-operacion/` | Alojamiento, DB, secretos, tareas y recuperación | Coste, PC apagado y pasos que exigen cuentas del usuario |
| 14 | `14-ingesta-calidad/` | Adaptadores, versiones, fuentes y caducidad | Idempotencia, discrepancias y publicación del último dato validado |
| 15 | `15-licencias-limites/` | Código, datos, reutilización y límites del servicio | Evidencia primaria; sin garantía jurídica ni cambios unilaterales |
| 16 | `16-plan-semana/` | Ruta crítica, reparto y demo/entrega | Dependencias, decisiones del grupo y fechas relativas |

## Reglas de integración

1. Conservar `../REQUISITOS.md` como registro de lo aprobado. Las propuestas de los subagentes no lo sustituyen.
2. PostgreSQL es una propuesta nueva para el catálogo; distinguir desarrollo local de alojamiento accesible sin el ordenador del grupo. No almacenar perfiles personales centralmente por defecto.
3. Los agentes de APIs buscan datos reales complementarios. No sustituir esos requisitos por un catálogo inventado para presentar la planificación como resuelta.
4. La IA debe consultar herramientas limitadas: nada de SQL arbitrario, secretos, operaciones reales o escritura decidida por el modelo.
5. Registrar por campo origen, fecha efectiva y fecha de comprobación. Verificar permisos de acceso, almacenamiento y presentación por separado.
6. El perfil puede adaptar la experiencia educativa; no dar por resuelto el encaje de recomendaciones personales sobre instrumentos concretos.
7. Las cuotas no certifican cien inferencias simultáneas. La NAT compartida de clase impide tratar una IP como una sola persona.
8. Antes de consolidar: comprobar archivos y JSON de todos los frentes, leer resultados, reproducir scripts propios seguros y resolver incompatibilidades entre schemas, cálculos, datos y política de privacidad.
9. Una verificación en un script aislado no equivale a una integración ni a una aplicación desplegada.
10. Actualizar índice, diario y registro de decisiones únicamente con resultados recibidos y comprobados. Lo pendiente debe seguir visible.

## Dependencias entre lotes

- Ronda APIs → catálogo inicial y permisos → adaptadores/ingesta → PostgreSQL y herramientas de consulta.
- Proveedor y cuotas IA → modelo de consumo → límites de chat y prueba operativa.
- Fórmulas + perfil + comparador → escenarios y textos → aceptación end-to-end.
- Seguridad + privacidad + licencias → configuración y criterios de publicación.
- Todo lo anterior → plan de una semana, demo y entrega.

Las dependencias anteriores son hipótesis de coordinación; los conflictos y las decisiones que requieran aprobación se resolverán tras recibir los informes, no esperando entre subagentes.
