# Revisión del coordinador — lote 01–10

## Estado

Los diez directorios entregados existen y sus JSON se parsearon. Los schemas declarados se comprobaron estructuralmente. Las auditorías cruzadas de contratos y coherencia están en marcha por separado: esta revisión no declara resuelta la integración ni la ronda de APIs.

## Resultados reproducidos por el coordinador

- Motor financiero: 29 tests de referencia y límites pasan con la biblioteca estándar. No es validación para todas las condiciones de productos reales ni producción.
- Capacidad de IA: se detectó y reprodujo un error en la primera oleada con herramientas; una regresión falló y después pasó con la corrección. El conjunto tiene ahora seis tests correctos y se regeneraron 432 escenarios y cuatro casos límite. Latencia y concurrencia real continúan sin medir.
- Escenarios: `reproducir_escenarios.py --check` reproduce tres escenarios y sus invariantes. Es un demostrador independiente; su uso de floats no se adopta como contrato monetario de producción.
- Contratos Pai: schema Draft 2020-12 válido con 38 definiciones. El archivo no contiene ejemplos embebidos; no se atribuye al coordinador una prueba de ejemplos inexistentes. Falta el ensayo de extremo a extremo con backend y PostgreSQL.
- Perfil: schema válido y tres perfiles ficticios de ejemplo validados. Las pruebas de aceptación descritas no se confunden con una UI ejecutada.
- Comparador: los schemas declarados son válidos; comportamiento aún no implementado.
- Pai: tres SVG bien formados y sin enlaces de recursos externos ni contenido activo; el namespace XML estándar no se trata como descarga externa. Se resolvieron 21 referencias de tokens y se recalcularon diez parejas de contraste; esto no equivale a auditar una interfaz.

Detalle numérico en `00-VALIDACION-PARCIAL.json`.

## Correcciones relevantes

### Citas del modelo de capacidad

El ledger había sido sobrescrito y mezclaba URLs financieras con extractos de proveedores de IA; la bibliografía generada también estaba mal. Se archivó la copia dañada con un nombre inequívoco, se recuperaron de nuevo las ocho páginas oficiales correctas, se reconstruyó un ledger exclusivo con evidencia vinculada a cada URL y se regeneró el informe. `verify --strict --evidence` volvió a terminar correctamente. Evidencias y explicación en `03-capacidad-ia/restauracion/`.

### Capacidad de IA

La primera oleada no puede incluir resultados de herramientas todavía no ejecutadas. La prueba detectó `145000 != 111000`; el cálculo inicial ahora incluye solo instrucciones/contexto, pregunta actual y salida inicial. Los consumos diarios no se presentan como throughput ni permiten prometer cien conversaciones simultáneas.

Se aclaró además que una ruta acotada de IA no convierte el chat aprobado en una feature opcional ni autoriza sustituirlo definitivamente por FAQ.

### Mistral

El contraste HTTP directo de las URLs oficiales obtuvo redirecciones y contenido diferente del usado por el subagente. La página actual describe Free con consumo mensual incluido y límites en el panel; no justifica por sí sola descartarlo por exclusividad de prototipado. La página de privacidad describe opt-out específico de Studio/API; no se afirma exclusión de entrenamiento por defecto.

Se corrigió la matriz y se añadió `02-ia-alternativas/CONTRASTE-COORDINADOR.md`, con citas y evidencias comprobadas. Mistral queda como candidato abierto, no aprobado: faltan cuota/modelo, condiciones, configuración de datos y prueba real.

### Diseño y contratación simulada

Se retiró del diseño la indicación de inventar el producto y se alineó el ensayo con cinco pasos: producto real documentado, condiciones, importe ficticio, comprensión de riesgos y cierre simulado. Se mantiene la dirección visual como propuesta no aprobada.

## Compatibilidades aún por cerrar

1. Unidades/escala de porcentajes, IDs, códigos y fechas entre ingesta, DB, API de comparador y herramientas.
2. Herramientas desactivadas de forma provisional en seguridad frente al contrato de lectura/cálculo necesario para Pai.
3. Perfil local con guardado opcional y contexto seleccionado al LLM, sin adjuntar el perfil completo automáticamente.
4. Límites de contexto de Pai frente a los escenarios gratuitos calculados; no seleccionar un modelo sin comprobar herramientas y calidad.
5. Retención, rate limiting y sesiones de prueba en una NAT de clase sin convertir IP en identidad de usuario.
6. PostgreSQL como propuesta del usuario frente a snapshot estático como resiliencia: pueden coexistir; no rechazar la DB por una preferencia de un subagente.
7. Las decisiones sobre datos, permisos y frescura deben incorporar las nuevas fuentes de la ronda de APIs antes de dar la planificación por cerrada.

## Qué no se ha hecho

No hay aplicación construida, base PostgreSQL creada, consulta SQL real ejecutada, proveedor LLM probado, cuentas abiertas ni despliegue. Las pruebas anteriores son verificadores de referencia y comprobaciones documentales; no se presentan como funcionalidades de Paideia ya terminadas.
