# Paideia — plan integrador de una semana

> **Estado:** propuesta de trabajo relativa D1–D7. Es un plan, no una aplicación terminada, una arquitectura aprobada ni evidencia de que las integraciones funcionen. D1 significa el primer día de ejecución; la fecha de entrega exacta no consta. Responsables y criterios marcados como propuestos necesitan aceptación de Alejandro y José Manuel.

## 1. Punto de partida: aprobado, comprobado y pendiente

### Requisitos aprobados por el grupo

- Paideia es una web educativa en español para España; Pai es un triángulo.
- Perfil conversacional editable, chat con IA y personalización contextual; admitir «no lo sé» y «omitir», no inventar el perfil y no empujar siempre a invertir.
- Biblioteca de **productos reales** y comparador, priorizando cuentas remuneradas, depósitos, letras/deuda pública, fondos y ETF. Mostrar fuentes y fechas; no convertir datos hipotéticos en condiciones contractuales.
- Simuladores de interés simple y compuesto, escenarios visuales, glosario y simulación de contratación sin operación real.
- Sin registro; perfil local borrable; no pedir DNI, credenciales bancarias, pagos ni otros identificadores innecesarios.
- La web publicada debe seguir disponible con los ordenadores del grupo apagados. La entrega prevista incluye web enlazada en la Wiki del Campus, HTML/CSS/JS y diario en Moodle, GitHub y demo presencial. El límite de Moodle citado es 1 GB.
- Presupuesto objetivo: 0 €. El peor caso de afluencia se estima en 100 usuarios; su capacidad no está demostrada.

### Hallazgos verificados en los documentos del proyecto

- No se encontró una fuente gratuita que resuelva todo el catálogo de condiciones comerciales diarias. Las series estadísticas no equivalen a ofertas actuales de productos concretos. Se requiere verificar fuentes, permisos, campos y fechas por producto.
- No se ha probado una IA pública gratuita, un despliegue, una actualización diaria integral ni capacidad para 100 usuarios simultáneos. Una cuota publicada no acredita concurrencia.
- La investigación anterior propone, no aprueba, una web estática más un servicio de chat separado. La propuesta de PostgreSQL es nueva y no está autorizada como requisito ni implementada.
- Según `docs/planificacion-03/00-COORDINACION.md`, hay 16 informes adicionales despachados y pendientes de revisión. Este plan no espera, sondea ni atribuye resultados a esos trabajos; cualquier resultado posterior se incorpora solo tras leerlo y comprobarlo.

## 2. Prioridades y alcance

Las etiquetas ordenan el trabajo; **no autorizan a retirar requisitos aprobados**. Si al D7 una función aprobada no supera su DoD, se registra como pendiente y se solicita decisión/replanificación; no se cambia a datos ficticios ni a una función simulada sin autorización.

| Prioridad | Alcance | Criterio para declarar terminado |
|---|---|---|
| **Must — listo para demo** | Flujo Pai/perfil editable; chat con LLM real y contexto; biblioteca de productos reales; comparador; simuladores simple y compuesto; gráfico de escenarios; contratación simulada; glosario; privacidad y transparencia; web publicada y fuentes/diario entregables. | Cada feature pasa su DoD de la sección 5 y la aceptación manual propuesta de José Manuel. La falta de proveedor/datos no se disfraza como éxito: bloquea la aceptación de esa feature y se eleva al grupo. |
| **Should — alcance aprobado cuya profundidad sigue por concretar** | Amplitud de la biblioteca; cobertura de las cinco familias prioritarias más allá del conjunto de prueba; actualización diaria donde haya fuente, permiso y método adecuados. | En D1 se acuerdan cobertura inicial medible, campos y antigüedad admisible por tipo de dato. Publicar solo el alcance alcanzado, con fecha/fuente/limitaciones. Si no se logra, se informa y se pide aprobación antes de reducirlo. |
| **Could — opcional o ampliación** | PDF descargable (ya indicado como opcional); familias fuera de las cinco prioritarias; animaciones, automatización o funciones adicionales; PostgreSQL si la necesidad se demuestra. | Solo comenzar tras aceptar los DoD de Must y Should, y sin retrasar entregables. La omisión del PDF opcional no se presenta como retirada de un requisito obligatorio. PostgreSQL no se añade por novedad. |

No se promete «90 % de los más populares»: el universo, la popularidad y la cobertura no están definidos. La amplitud y la actualización son objetivos aprobados, pero requieren un criterio acordado y evidencia de fuente.

## 3. Ruta crítica y dependencias

```text
D1: G0 alcance/aceptación + G1 datos + G2 IA + G3 almacenamiento/DB
                      │ decisiones y contratos aprobados
                      ▼
D2: modelo de datos, privacidad, contratos UI/API y plan de pruebas
          ┌───────────┴───────────┐
          ▼                       ▼
D3: catálogo real + perfil     D4: cálculos deterministas
          │                       │
          └───────► comparador ◄──┘
                        │
               gráficos + contratación simulada
                        │
          G2 IA + perfil + datos verificados
                        ▼
D5: integración de chat real, límites y estados de error
                        │
D6: QA de extremo a extremo, seguridad, publicación y paquete
                        │
D7: aceptación, ensayo Demo Day y entrega Wiki/GitHub/Moodle
```

**Ruta crítica:** resolver gates de D1 → congelar contratos de D2 → disponer de datos reales y cálculos deterministas → integrar el comparador/escenarios → integrar el chat únicamente con un proveedor aceptable → QA/publicación → ensayo y entrega. Datos, proveedor, permisos, política de datos obsoletos y decisión de almacenamiento pueden bloquear la integración; no son detalles que se puedan inventar al final.

### Gates obligatorios de D1

Los umbrales siguientes son **criterios propuestos para acordar**, no decisiones ya aprobadas. Alejandro y José Manuel anotan evidencia, resultado (pasa / falla / no comprobado) y decisión. No se crea cuenta, clave, base de datos, despliegue ni gasto por este plan.

| Gate | Comprobación y evidencia que debe quedar | Si falla o queda sin probar |
|---|---|---|
| **G0 — alcance y aceptación** | Confirmar Must/Should/Could; acordar qué significa biblioteca «amplia», cobertura inicial y qué campos hacen comparable un producto. Registrar decisiones pendientes. | No afirmar completa la biblioteca ni reemplazar cobertura por ejemplos inventados. Escalar la decisión; seguir solo en tareas no dependientes. |
| **G1 — datos** | Para las cinco familias prioritarias: listar fuentes primarias candidatas; producto real de prueba; campos respaldados y faltantes; fecha efectiva y de comprobación; permisos de consulta, almacenamiento y publicación; caducidad por tipo de dato. Propuesta de prueba vertical: al menos un registro real verificable por familia, sin que eso limite el catálogo final. | Familia/campo sin evidencia queda fuera de comparación hasta validación; no se rellena con datos ficticios. La biblioteca aprobada sigue pendiente y se pide al grupo aceptar cualquier cambio de cobertura. |
| **G2 — IA** | Verificar términos aplicables a una web pública en España/EEE, gratuidad sin tarjeta no aprobada, cuota/límites, privacidad, protección de clave y posibilidad de llamar desde un backend protegido. Prueba manual acotada en español: pregunta basada en dato real, fuente visible, desconocidos admitidos y no inventar condiciones. | No usar proveedor que no supere términos/privacidad/coste; no poner claves en JS ni simular un LLM con respuestas fijas. El chat sigue Must y queda bloqueado hasta decisión del grupo, aunque el resto pueda avanzar. |
| **G3 — almacenamiento/DB** | Decidir si el catálogo requiere escrituras, búsquedas/joins o concurrencia que no cubra un archivo versionado. Comprobar coste, acceso remoto con PC apagado, secretos, copias y recuperación antes de escoger servicio. Mantener los perfiles solo en el navegador. | **Default recomendado, aún por aprobar:** catálogo curado en JSON/versionado en Git, sin DB central. PostgreSQL solo tras demostrar necesidad y alojamiento gratuito viable, y aprobación explícita. No almacenar perfiles ni ejecutar SQL arbitrario desde IA. |

G1–G3 se cierran con una tabla de evidencia y decisión, no con «parece viable». La investigación previa advierte que el acceso a una API o un cálculo de cuotas no prueba un producto completo ni 100 usuarios concurrentes.

### Plan por día (relativo)

| Día | Objetivo y tareas | Responsable propuesto | Salida / gate |
|---|---|---|---|
| **D1 — descubrir y decidir** | G0–G3. Revisar la evidencia ya disponible; validar manualmente candidatos reales; comprobar términos y límites de IA; decidir si hace falta DB; acordar los criterios de frescura/comparación y el primer conjunto de prueba. Abrir el diario con prompts reales y decisiones. | Alejandro: síntesis técnica, pruebas pequeñas y contratos candidatos. José Manuel: revisión manual de datos/fuentes, recorrido UX y registro diario. Ambos: aceptar o dejar pendientes decisiones de alcance. | Registro firmado de pasa/falla/no comprobado. Sin un gate, no se presenta su parte como lista ni se oculta el bloqueo. |
| **D2 — contratos y arquitectura propuesta** | Convertir decisiones en esquema de producto y metadatos por campo, flujo de perfil, límites del chat, política de privacidad, estados de error y matriz de pruebas. Elegir arquitectura solo a partir de G1–G3. | Alejandro: esquemas y módulos. José Manuel: revisión de lenguaje, preguntas y claridad desde usuario no técnico. | Contratos versionados; decisiones abiertas asignadas. No implementar PostgreSQL ni proveedor no validado. |
| **D3 — primer recorrido** | Construir la carcasa responsive, Pai, onboarding con «no lo sé»/«omitir», resumen editable y borrado de perfil local. Cargar el primer subconjunto de productos reales con procedencia; mantener faltantes explícitos. | Alejandro: implementación y pruebas. José Manuel: validar el flujo, mensajes y datos fuente contra documentos oficiales; anotar observaciones en el diario. | Prueba manual desde inicio hasta perfil y biblioteca; ningún campo sin trazabilidad se marca como verificado. |
| **D4 — lógica financiera visible** | Implementar calculadoras deterministas simple/compuesta, supuestos explícitos, comparador con campos comparables, gráfico que refleje esos resultados y flujo de contratación inequívocamente simulado. Añadir el glosario. | Alejandro: cálculos, comparador y gráfico con pruebas. José Manuel: casos de usuario, lectura de resultados y control de que el flujo simulado no parezca una operación real. | Casos de referencia reproducibles; datos obsoletos/desconocidos tratados según política aprobada. |
| **D5 — chat e integración** | Integrar el proveedor aprobado detrás del servicio que protege la clave; enviar solo el contexto informado/consentido; limitar abuso/coste; probar respuestas sobre fuentes, incertidumbre y fallos. Completar el recorrido entero. | Alejandro: integración, límites, errores y pruebas. José Manuel: prueba conversacional y revisión de afirmaciones, tono y explicaciones. | Aceptación de chat real si pasó G2. Si no, registrar bloqueo y pedir decisión; no publicar un bot estático como IA. |
| **D6 — calidad y paquete** | Ejecutar matriz Must/Should, accesibilidad/teclado y tamaños móvil/escritorio, privacidad y borrado local, errores de red, revisión de fuentes/licencias, comprobación de capacidad con límites autorizados, despliegue público sin depender de los PCs del equipo. Preparar README, licencia y entrega reproducible. | Alejandro: QA técnica, publicación y secretos fuera del cliente. José Manuel: validación de datos/UX, diario y checklist del paquete. Ambos: lectura de vuelta de URL y aceptación. | Solo declarar verificado lo probado. Si no se demuestra capacidad para 100, anotarlo y elevarlo; no prometerla por cuota teórica. |
| **D7 — congelar y presentar** | No agregar extras. Corregir bloqueos críticos, repetir smoke tests desde enlace público, revisar Wiki/GitHub/Moodle, ensayar demo 6–10 min y plan de contingencia. Congelar un ZIP bajo 1 GB. | Alejandro: estado técnico, URL, código y fallos. José Manuel: explicación, demo, diario y validación final. Ambos: declarar honestamente lo que funciona y lo que falta. | Aceptación final de features probadas; entrega o bloqueos explícitos. La fecha exacta y los pasos de Moodle/Wiki se confirman con las instrucciones de la profesora. |

**Capacidad y bloqueo:** el plazo es una semana, pero no se conoce la fecha de inicio/entrega ni la disponibilidad horaria. Si G1 o G2 bloquea una feature Must, ejecutar en paralelo las partes independientes; no reducir el alcance en silencio ni contar la alternativa como aceptada. El cierre D7 puede ser «no listo» para una feature bloqueada.

## 4. Reparto propuesto

- **Alejandro:** propietario técnico propuesto: integración, modelo de datos, código HTML/CSS/JS, pruebas automatizadas/manuales, protección de claves, publicación, estructura GitHub y reproducibilidad. No es una decisión de titularidad del repositorio.
- **José Manuel:** responsable propuesto de tareas no técnicas: validación manual de datos y fuentes (contrastar producto, condiciones, fecha y faltantes), pruebas UX desde perspectiva de usuario, mantenimiento del diario/prompts, preparación y conducción de demo y explicación de límites/decisiones. No se le asigna código como prerrequisito.
- **Ambos:** aprobar alcance, tolerancia de datos antiguos, proveedor/privacidad, decisión de DB, criterios de comparación, propiedad/licencia y aceptación final. José Manuel puede bloquear una ficha con datos dudosos; Alejandro no la publica como verificada hasta resolverlo.

## 5. Definition of Done por feature Must

| Feature | DoD propuesto (todos los puntos aplicables deben pasar) |
|---|---|
| **Pai, onboarding y perfil** | Preguntas de una en una, «no lo sé» y «omitir»; resumen editable; distingue conocimientos/experiencia, tolerancia al riesgo y capacidad de asumir pérdidas; no inventa respuestas; marca información faltante y límites; perfil guardado localmente y botón de borrado comprobado; usable en móvil y ordenador. |
| **Chat con IA** | Llamada real a un LLM aprobado, no guion fijo; clave solo en servidor; contexto y datos transmitidos explicados antes de enviar; límite/fallo visible; identifica fuentes y fechas para afirmaciones de producto; reconoce desconocidos; no inventa condiciones ni presenta la app como asesor profesional. Prueba real registrada en el diario. |
| **Biblioteca real** | Incluye las cinco familias prioritarias y productos específicos reales según cobertura acordada en D1; cada dato relevante muestra fuente, fecha efectiva y comprobación; campos desconocidos quedan explícitos; permisos de publicación revisados; distingue condiciones contractuales de escenarios; no afirma «90 %» sin universo medido. |
| **Comparador** | Solo compara campos equivalentes y datos que cumplen la regla aprobada de actualidad; muestra condiciones, fuente/fecha y faltantes; excluye valores cuya antigüedad pueda engañar; permite explorar sin afirmar «mejor para ti» ni inferir adecuación solo por tolerancia al riesgo. |
| **Interés simple y compuesto** | Cálculo ejecutado por código determinista, no por texto generado; entradas, tasa, período y frecuencia/supuestos visibles; resultados reproducibles contra casos de referencia acordados; límites de entrada y redondeo documentados. |
| **Escenarios/gráfico** | Representa las mismas entradas/salidas del cálculo; diferencia supuestos hipotéticos de datos actuales; ejes, unidad, período y advertencias legibles; actualización al cambiar los supuestos; acceso a los valores sin depender solo del color. |
| **Contratación simulada** | Rótulo persistente «SIMULACIÓN — no contrata»; importes, identidad y operación del ejercicio son ficticios, mientras que los datos del producto real conservan su fuente y no se inventan; sin API transaccional de entidad, envío de operación, pago, DNI, credenciales ni documentos personales; confirmación final sigue siendo simulada y no parece justificante contractual válido. |
| **Glosario** | Términos de las pantallas explicados en español sencillo, coherentes con las familias cubiertas y sin prometer resultados; fuente/revisión cuando corresponda; enlaces desde resultados o detalle. |
| **Privacidad y seguridad** | Sin cuenta por defecto; perfil local borrable; no guardar PII en logs; explicar proveedor/datos antes de llamada externa; verificar que la clave no aparece en bundle, repositorio ni consola. Pruebas de borrado y de no envío de perfil no consentido registradas. |
| **Web y operación** | URL pública probada con equipos del grupo apagados; vistas esenciales responsive; carga/error de red visibles; información estática separada del chat; límites/capacidad declarados solo según prueba. No anunciar garantía de 100 simultáneos sin test. |
| **Entrega reproducible** | Repositorio GitHub con HTML/CSS/JS, README, licencia elegida y avisos de terceros/datos; diario con prompts reales, herramienta/modelo si se conoce, cambios y resultados reales; instrucciones de ejecutar/probar, fuentes/fechas, variables sin secretos, limitaciones y pasos de publicación. Copia Moodle bajo 1 GB y enlace para Wiki según instrucciones confirmadas. |

**Regla de aceptación antes de extras:** cerrar y registrar el DoD de cada feature antes de añadir una mejora a esa feature. No empezar ningún Could hasta que Must pase aceptación end-to-end y Should esté completado o el grupo apruebe explícitamente una excepción. Nada de mejoras visuales, familias nuevas, PDF o DB nueva debe desplazar verificaciones, datos reales, privacidad, diario o demo.

## 6. Demo Day — guion de 8 minutos

Un recorrido de 8:00 minutos queda dentro de los 6–10 min pedidos. Usar un perfil/personaje ficticio sin datos personales; seleccionar una ficha real con fuente y fecha que haya pasado la validación. No prometer que la IA o los datos están «en vivo» si no se verificó en ese momento.

| Tiempo | Qué mostrar y decir |
|---|---|
| **0:00–0:40** | Presentar Paideia, objetivo educativo y Pai. Aclarar: no es asesor autorizado ni contrata productos. |
| **0:40–1:35** | Responder dos/tres preguntas del perfil; usar «no lo sé»/«omitir» y editar el resumen. Señalar capacidad de asumir pérdidas separada de apetito de riesgo. |
| **1:35–2:25** | Abrir biblioteca y una ficha real; enseñar fuente, fecha, campos ausentes y actualización/frescura. |
| **2:25–3:40** | Hacer una pregunta al chat real, mostrar explicación contextualizada y fuente. Si falla, mostrar el mensaje de indisponibilidad sin representar una respuesta preparada como generada por IA. |
| **3:40–5:10** | Comparar alternativas reales en campos equivalentes; explicar límites y por qué datos incompletos/antiguos no sostienen una recomendación. |
| **5:10–6:00** | Cambiar importe/plazo/supuestos en interés simple y compuesto; observar el gráfico, indicando que es escenario hipotético. |
| **6:00–6:55** | Recorrer contratación simulada y el aviso persistente de que no se ejecuta ninguna operación. |
| **6:55–7:35** | Mostrar borrado del perfil local, privacidad y límites de uso/concurrencia conocidos. |
| **7:35–8:00** | Mostrar README, diario y entrega GitHub/Wiki/Moodle; cerrar con una limitación pendiente en vez de exagerar cobertura. |

## 7. Contingencias sin engañar

- **Datos antiguos o fuente caída:** mostrar solo último dato verificado con fuente y fechas; advertir antigüedad; excluir del comparador cualquier valor que supere la regla acordada. Si esa regla no está decidida, no tratar un dato dudoso como comparable. No sustituir el producto por uno ficticio.
- **Límite o caída del chat:** mostrar «chat temporalmente no disponible» y, si es seguro, el límite/reintento; mantener biblioteca, comparador y simuladores si funcionan; ofrecer glosario/explicación estática identificados como contenido, nunca como respuesta del LLM. El estado de la feature chat queda visible.
- **Caída de red o web:** probar antes un paquete local de emergencia de la vista estática/datos permitidos y capturas rotuladas «captura, no interacción en vivo». Si el enlace público no funciona, decirlo; el respaldo no reemplaza la web publicada ni permite afirmar que 100 compañeros pueden acceder.
- **Demo con alta carga/NAT compartida:** no ampliar límites ni quitar controles para «hacerla funcionar»; mostrar el estado, limitar solicitudes de forma honesta y preservar las funciones estáticas. Registrar el resultado y no prometer capacidad no probada.
- **Fallo en perfil o comparador:** usar únicamente una secuencia local previamente verificada con datos de prueba claramente identificados; no rellenar en directo con datos inventados como si fueran productos. Explicar qué paso no funciona y anotar el fallo.

## 8. Fuentes internas de estado

- [`IDEA.md`](../../../IDEA.md): entregables pedidos por la profesora, Wiki, fuente/diario, demo y tamaño máximo.
- [`docs/REQUISITOS.md`](../../REQUISITOS.md): decisiones aprobadas, aspiraciones y preguntas pendientes.
- [`docs/DIARIO_DESARROLLO.md`](../../DIARIO_DESARROLLO.md): estado inicial, advertencias y formato de registro real.
- [`docs/investigacion/00-SINTESIS.md`](../../investigacion/00-SINTESIS.md): hallazgos de fuentes/API/IA/arquitectura; propuestas no aprobadas.
- [`docs/planificacion-03/00-COORDINACION.md`](../00-COORDINACION.md): 16 frentes adicionales pendientes de revisión y reglas de integración.
- [`riesgos.json`](riesgos.json) y [`LISTA_DECISIONES.md`](LISTA_DECISIONES.md): registro operativo adjunto.
