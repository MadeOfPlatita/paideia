# Paideia — especificación del mapa conversacional de Pai

**Estado:** propuesta de planificación; no implementada ni aprobada como criterio regulatorio.  
**Ámbito:** onboarding educativo en español para personas adultas en España. Respuestas en rangos, perfil local y borrable, sin registro ni identificadores. Pai adapta el orden y profundidad de las explicaciones; no selecciona instrumentos ni calcula idoneidad.

## 1. Decisiones de diseño

- El recorrido inicial tiene **4 preguntas**; cada una incluye **«No lo sé»**, **«Omitir»** y **«¿Por qué lo preguntamos?»**. Las respuestas desconocidas, omitidas y aún no preguntadas se guardan con estados distintos.
- El detalle económico y las preguntas sobre riesgo son **ramas voluntarias**. Solo se abren cuando la persona las elige. No se exige revelar ingresos, saldos, deudas ni capacidad de pérdida para aprender.
- Usar rangos en euros y periodicidad declarada. No se piden importes bancarios exactos, documentos, edad, nombre, localidad, empleo, identificadores, movimientos ni credenciales.
- Persistir localmente después de cada respuesta válida y antes de avanzar. El resumen se puede editar y borrar. El cuestionario es determinista: **no llama al LLM** ni manda el perfil a un servicio externo, analítica o registro de eventos. La personalización de Pai se implementa como un selector local de lecciones y textos revisados que usa únicamente las respuestas declaradas necesarias. Si más adelante se conecta un LLM externo al chat, el perfil no se adjunta al prompt; el chat contesta de forma general y solo el selector local adapta qué lección se ofrece. Enviar cualquier dato del perfil a un proveedor requeriría una decisión nueva del grupo, información previa y revisión de privacidad/regulatoria.
- Un estado incompleto es válido. «No lo sé» y «Omitir» permiten avanzar; nunca se convierten en ceros, promedios ni respuestas inferidas. Una cifra usada por una simulación queda separada de los datos del perfil y se etiqueta como hipotética.
- Tolerancia al riesgo y capacidad de soportar pérdidas son campos distintos. No se combinan en una puntuación, etiqueta («conservador», «agresivo») ni regla de selección.
- **No está autorizada ninguna recomendación ni ranking de producto personalizado.** Se permite adaptar lecciones y ejemplos ficticios, o comparar datos que la persona seleccione por sus propios criterios. No mostrar «mejor para ti», asignaciones, ISIN sugerido ni orden por perfil.

El límite entre información educativa y recomendación personalizada no se resuelve con una etiqueta fija: las fuentes del proyecto señalan que importan la personalización, el instrumento y el contexto, y que un aviso de «no es asesoramiento» no neutraliza por sí solo una recomendación individual. Por eso, el límite de Pai se aplica en la lógica de respuesta y en cada interacción relevante, no solo en un cartel. Véanse `../../investigacion/09-rigor-financiero.md` §§1.1–1.2, 2 y 4; la decisión de publicar una función que relacione perfil y productos requiere revisión profesional en España. La secuencia de cuatro preguntas y el resumen editable siguen `../../REQUISITOS.md` y `../../investigacion/08-ux-recursos.md` §3.

## 2. Árbol adaptativo

### Entrada y progreso

**Texto de Pai**

> Hola, soy Pai. Te haré cuatro preguntas breves para escoger qué explicar y qué ejemplos mostrar. Puedes responder con rangos, elegir «No lo sé» u «Omitir», editar el mapa o borrarlo. Esto adapta el aprendizaje; no decide qué producto te conviene. No escribas tu nombre ni datos bancarios. En este diseño, las respuestas se guardan en este navegador y no se envían al chat ni a analítica.

**Acciones:** `Empezar` · `Ver cómo se usan mis respuestas` · `Borrar mi mapa` (solo si ya existe uno). No hay avance automático.

El indicador muestra el paso recorrido, no una nota de completitud: `Pregunta 2 de 4 · 1 respuesta · 1 «No lo sé»`. Un campo contestado con «No lo sé» u «Omitir» cuenta como paso resuelto, pero no como dato declarado.

### Núcleo: cuatro preguntas

| Paso | Texto exacto de Pai | Respuestas / controles | «¿Por qué lo preguntamos?» exacto | Uso permitido |
|---|---|---|---|---|
| 1. Tema/objetivo | **¿Qué te gustaría explorar primero?** | `Entender un colchón para imprevistos` · `Preparar un gasto con fecha` · `Aprender sobre ahorro a largo plazo` · `Entender el riesgo y las posibles pérdidas` · `Comparar familias que yo elija` · `Aprender conceptos básicos` · `Solo curiosear` · `No lo sé` · `Omitir` | `Así puedo empezar por el tema que te interesa. No usaré esta respuesta para elegir productos.` | Ordenar módulos educativos y ofrecer, nunca activar, la rama de importe objetivo. |
| 2. Horizonte | **Si este ejemplo tuviera una meta, ¿cuándo crees que podrías necesitar ese dinero?** | `En menos de 6 meses` · `Entre 6 y 12 meses` · `Entre 1 y 3 años` · `En más de 3 años` · `No hay fecha; solo quiero aprender` · `No lo sé` · `Omitir` | `El plazo cambia qué conceptos conviene explicar, por ejemplo la diferencia entre una fecha prevista y una salida antes de tiempo. No predice una rentabilidad.` | Elegir ejemplos con el plazo declarado; no inferir edad, fecha real ni producto adecuado. |
| 3. Liquidez | **¿Cuánto te importa poder disponer rápidamente del dinero del ejemplo?** | `Necesitaría poder disponer de él en cualquier momento` · `Podría planificar una fecha para disponer de él` · `Solo usaré cifras ficticias; no hay dinero real` · `No lo sé` · `Omitir` | `La disponibilidad y el plazo pueden plantear compromisos distintos. Te explicaré esa diferencia; no asumiré que «líquido» significa «sin pérdidas».` | Priorizar una explicación de disponibilidad, vencimiento y posible precio de salida si la persona abre esa familia. No recomendar. |
| 4. Experiencia e interés | **¿Qué conoces y qué te gustaría aprender?** | Nivel (una opción): `Estoy empezando; no he usado estos productos` · `He leído o comparado, pero no los he tenido` · `He tenido alguno y quiero repasar` · `Prefiero no contar mi experiencia`. Temas (selección opcional): `Cuentas remuneradas` · `Depósitos` · `Letras o bonos` · `Fondos` · `ETF` · `Aún no lo sé`. También `No lo sé` y `Omitir`. | `Me ayuda a ajustar el vocabulario y empezar por lo que tú elijas. Haber usado un producto no demuestra que otro sea adecuado.` | Cambiar el nivel didáctico, no inferir conocimientos por estudios, edad, profesión ni posesión de productos. |

Los botones «No lo sé» y «Omitir» aparecen en cada pregunta. «No lo sé» registra `no_se`; «Omitir» registra `omitido`. No se muestra ninguna como «sin respuesta». La salida o cierre antes de elegir deja el campo `sin_preguntar`.

### Resumen inicial

Al acabar las cuatro preguntas, Pai dice:

> Ya está tu mapa inicial. Puedes cambiar cualquier respuesta o añadir detalles si te apetece. Lo que no has respondido sigue sin respuesta; no lo completaré por ti. Este mapa solo organiza el aprendizaje.

El resumen lista cada campo bajo `Declarado`, `No lo sé`, `Omitido` o `Aún no preguntado`, con botón `Editar`. No calcula «perfil de riesgo». Acciones: `Guardar y seguir aprendiendo` · `Añadir un rango de objetivo` (solo si hay meta concreta) · `Añadir contexto económico` · `Explorar cómo me afectan las caídas` · `Borrar mi mapa`.

### Ramas opcionales

Se abre una rama solo tras una acción afirmativa. Pai explica el motivo antes de recoger cualquier dato; puede omitirse campo por campo.

#### A. Importe objetivo

Solo si la persona eligió una meta concreta:

> **¿Tienes un rango aproximado para esa meta?** No hace falta una cifra exacta. Elige un rango en euros o pulsa «No lo sé» u «Omitir».

Selector de rangos, adaptado al campo: `0 €` · `1–499 €` · `500–999 €` · `1.000–1.999 €` · `2.000–4.999 €` · `5.000–9.999 €` · `10.000–24.999 €` · `25.000–49.999 €` · `50.000–99.999 €` · `100.000 € o más` · `No lo sé` · `Omitir`.

> **¿Por qué lo preguntamos?** `Solo para que un ejemplo de aprendizaje use una escala parecida a la que has declarado. No es una meta que Pai valide ni una cantidad que deba invertirse.`

#### B. Contexto económico (opt-in)

**Puerta de entrada exacta:**

> Si quieres, puedes añadir rangos de ingresos, gastos, deudas y dinero disponible. Esto permite explicar un ejemplo de presupuesto con más contexto. No es obligatorio, no calcularé una recomendación y puedes borrar estos datos cuando quieras. ¿Quieres continuar?

Acciones: `Sí, añadir rangos` · `Ahora no`. No abrir la rama por defecto. Mostrar siempre:

> `Estos rangos son información financiera sensible aunque no lleven tu nombre. Se guardan en este navegador en este dispositivo. El almacenamiento local no es una caja fuerte: no uses un dispositivo compartido si otras personas pueden acceder a él. No se enviarán al chat ni a analítica en este diseño. Puedes borrar el mapa desde el resumen.`

Preguntas en este orden; cada pantalla tiene `No lo sé`, `Omitir` y `¿Por qué lo preguntamos?`:

1. **Ingresos:** `En un periodo habitual, ¿en qué rango están tus ingresos netos aproximados?` Elige un rango (mismas bandas que arriba, ajustadas a un flujo mensual) y una periodicidad: `Cada semana` · `Cada 14 días` · `Dos veces al mes` · `Cada mes` · `Una vez al año`. No usar la palabra ambigua «quincenal». Si varían mucho: `Elige un periodo habitual; no el mejor mes.` Motivo: `Sirve para explicar un presupuesto; no necesito nóminas ni la entidad que te paga.`
2. **Gastos esenciales:** `¿En qué rango están tus gastos esenciales habituales (por ejemplo, vivienda, alimentación y transporte)?` Mismos controles de rango y periodicidad. Motivo: `Ayuda a explicar la diferencia entre ingresos disponibles y compromisos. No asumiré que conozco todos tus gastos.`
3. **Deuda:** `¿Estás pagando alguna deuda ahora?` `Sí` · `No` · `No lo sé` · `Omitir`. Si sí: una pantalla con `Saldo total aproximado` (rango sin periodicidad), `Cuota habitual` (rango y periodicidad) y, solo si lo conoce, `Coste anual aproximado` (rango porcentual 0–100 %). Cada subcampo puede quedar `no_se` u `omitido`. Motivo: `El coste y las cuotas son compromisos distintos de la rentabilidad de una inversión. No asumiré que invertir supera el coste de tu deuda.`
4. **Reserva disponible:** `Sin contar dinero que necesitarás para gastos próximos, ¿en qué rango está el dinero que podrías usar con rapidez?` Rango en euros; sin periodicidad. Motivo: `Me permite explicar liquidez y margen de maniobra. No fijaré un colchón obligatorio ni deduciré cuánto deberías tener.`
5. **Compromisos próximos (opcional):** `¿Prevés algún gasto o compromiso importante durante los próximos 12 meses?` `No` · `Sí, indicar solo un rango total` · `No lo sé` · `Omitir`. Si sí, rango total en euros y plazo `Menos de 3 meses` · `3–6 meses` · `6–12 meses` · `Fecha no clara`. Motivo: `Un compromiso próximo puede cambiar qué ejemplo de liquidez tiene sentido explicar; no necesito saber qué vas a comprar.`

Los rangos económicos son bandas, no mediciones exactas. Los topes abiertos significan «ese importe o más», no un importe supuesto. Las opciones concretas de bandas para cada flujo se fijarán en la implementación, manteniendo límites no solapados y el mismo catálogo en interfaz, esquema y pruebas.

#### C. Riesgo: tolerancia y capacidad, por separado (opt-in)

**Puerta de entrada exacta:**

> Puedo mostrarte dos preguntas distintas: cómo te sentirías ante una caída ficticia y qué efecto tendría una pérdida en una necesidad o meta. No es un test, no calcularé una etiqueta ni una recomendación. ¿Quieres verlas?

Acciones: `Sí, verlas` · `Ahora no`.

1. **Tolerancia (reacción/preferencia):** `Imagina solo este ejemplo: 1.000 € pasan temporalmente a valer 900 €. ¿Qué crees que harías?` Opciones: `Me inquietaría y probablemente querría salir` · `Me inquietaría, pero esperaría a entender qué ha pasado` · `Podría esperar, sabiendo que el valor puede caer más` · `No lo sé` · `Omitir`. Motivo: `La respuesta describe cómo dices que te sentirías ante este ejemplo; no mide tu capacidad económica ni predice tu conducta.`
2. **Capacidad de soportar pérdidas (impacto):** `En ese mismo ejemplo ficticio, si faltaran 100 €, ¿qué efecto tendría en una necesidad o meta importante?` Opciones: `No cambiaría una necesidad ni una meta importante` · `Me obligaría a retrasar o reducir una meta` · `Afectaría un gasto esencial o un compromiso` · `No lo sé` · `Omitir`. Motivo: `Esto pregunta por el impacto económico, no por cuánto riesgo te gusta. No lo deduciré de tus ingresos.`

Ninguna respuesta se convierte en puntuación, «perfil» o permiso para asumir más riesgo. El ejemplo 1.000/900/100 es un escenario didáctico visible y editable; no describe el dinero de la persona.

## 3. Validación, periodicidad y contradicciones

### Validación de rangos

- La moneda de los rangos es EUR. No aceptar valores negativos, `NaN`, infinito, campos extra ni rangos sin unidad. `máximo` debe ser mayor o igual que `mínimo`; `máximo = null` significa banda abierta superior, nunca dato desconocido.
- Los rangos seleccionados deben coincidir con una banda del catálogo de interfaz. No aceptar límites solapados entre bandas, límite inferior fuera de banda ni un rango de un campo usado como otro campo.
- Costes/tipos declarados como porcentaje anual: 0–100 %, mínimo ≤ máximo. No convertir «no conozco el coste» en 0 %.
- Los flujos siempre llevan una periodicidad explícita; saldos, deuda total, reserva y meta no llevan periodicidad. No comparar un ingreso semanal con gasto mensual como si compartieran unidad.
- Factores deterministas para alertas internas, no para valorar la persona: semanal × 52/12; cada 14 días × 26/12; dos veces al mes × 2; mensual × 1; anual × 1/12. El resultado solo puede etiquetarse «equivalente mensual aproximado» y no se almacena como un dato declarado nuevo.
- Texto de error exacto para un rango inválido: `Ese rango no es válido. El límite superior debe ser igual o mayor que el inferior. No he guardado este cambio.` Para campo vacío: `Elige un rango, «No lo sé» u «Omitir». No completaré este dato por ti.`

### Contradicciones y tensiones

Las alertas son explicaciones para revisar, no veredictos sobre la persona. No sobrescriben los valores originales ni cambian su estado de `declarado`.

| Situación detectada | Tratamiento | Texto exacto de Pai |
|---|---|---|
| Tras normalizar periodicidades, el mínimo de gastos esenciales + cuotas declaradas supera el máximo de ingresos netos declarados. | `PRESUPUESTO_NO_CUADRA`; posible diferencia de perímetro, periodo, ingresos no incluidos o rango. Pedir revisión; no inferir déficit ni ajustar importes. Puede continuar en modo educativo, sin usar esa parte para personalizar un escenario financiero. | `Con los rangos y periodos que has indicado, los gastos esenciales y las cuotas podrían superar los ingresos netos. Puede que los rangos no cubran el mismo periodo o que falte información. ¿Quieres revisar ingresos o gastos? No cambiaré ninguna respuesta sin que la edites.` Acciones: `Revisar ingresos` · `Revisar gastos/cuotas` · `Seguir sin usar este cálculo`.
| Meta a más de 3 años y preferencia por disponer del dinero en cualquier momento. | **Tensión, no contradicción.** Conservar ambas declaraciones; explicar el compromiso entre fecha y disponibilidad, sin elegir una. | `Has indicado una meta de más de 3 años y también que quieres acceso en cualquier momento. Ambas preferencias pueden coexistir; cambian el ejemplo que te conviene explorar, no determinan un producto. ¿Quieres revisar alguna o mantener las dos?` Acciones: `Revisar fecha` · `Revisar disponibilidad` · `Mantener ambas`.
| Alta disposición declarada a tolerar caídas, pero respuesta de capacidad indica que una pérdida afectaría gastos esenciales o un compromiso. | **No es contradicción:** preferencia y capacidad son dimensiones distintas. No producir una etiqueta «agresiva» ni dejar que la tolerancia anule la capacidad declarada. | `Has dicho que podrías esperar ante una caída, y también que una pérdida de este ejemplo afectaría un gasto esencial o un compromiso. Una cosa es cómo te sientes ante el riesgo y otra el impacto que podrías asumir. No las convertiré en una puntuación ni elegiré productos. ¿Quieres revisar una respuesta o ver una explicación sobre riesgo y liquidez?` Acciones: `Revisar tolerancia` · `Revisar impacto` · `Ver explicación`.
| El estado declarado indica que no hay deuda, pero el esquema trae saldo o cuota de deuda. | Rechazo estructural; no guardar ese envío. Pedir que se revise el estado o los campos. | `La respuesta «no tengo deuda» no puede llevar un saldo o una cuota de deuda. Revisa ese paso; no he guardado el cambio.`
| Ingreso declarado como 0 y gastos positivos. | No etiquetar contradicción: puede haber otras fuentes o ahorros que no se preguntan. No inferir solvencia ni imposibilidad. | `Has declarado ingresos de 0 € en este periodo y gastos positivos. No sé si hay otras fuentes o ahorros, así que no sacaré conclusiones. Puedes revisar los rangos o seguir sin usar este cálculo.`
| Falta un dato o hay un «No lo sé»/«Omitir» relevante para la explicación solicitada. | No completar con edad, profesión, estudio, familia, texto de chat, otros campos ni valores típicos. Identificar exactamente el campo. | `Para explicar [tema] con tu mapa me falta [campo]. No voy a suponer una respuesta. Puedes dar un rango, ver una explicación general o dejarlo para más tarde.` Acciones: `Añadir un rango` · `Ver explicación general` · `Ahora no`.

Si la persona deja sin resolver una tensión, las respuestas se conservan como fueron declaradas, junto al código de aviso calculado. Al editar una respuesta, recalcular avisos localmente. El LLM no crea, resuelve ni explica contradicciones financieras como si conociera la respuesta correcta.

## 4. Progreso, persistencia y borrado

- El paso de progreso cuenta preguntas visitadas, no respuestas «correctas». Un flujo parcial es válido; el botón `Guardar y salir` está siempre disponible.
- Persistir cada respuesta terminal (`declarado`, `no_se` u `omitido`) antes de mostrar la siguiente pregunta. Si se cierra antes de contestar, conservarla como `sin_preguntar`. No esperar al final ni enviar datos a servidor.
- Límite operativo: hasta 18 acciones de respuesta en el onboarding completo, incluidas las ramas elegidas; recorrido normal de 4 preguntas y máximo 15 pantallas de pregunta si se abren todas las ramas (4 núcleo + 11 opcionales). Si hay reintentos de validación, cuentan dentro del máximo de 18. Al llegar al límite, guardar el estado parcial y mostrar el resumen, sin forzar respuesta. Las validaciones son deterministas y no abren turnos de LLM.
- Resumen editable antes de pasar al chat. El chat libre no modifica el mapa: una frase del usuario no actualiza ningún campo automáticamente. Pai dice: `No he cambiado tu mapa con lo que has escrito en el chat. Si quieres actualizarlo, elige «Editar mi mapa» y confirma el campo y el rango.`
- Acción de borrado: botón `Borrar mi mapa` y confirmación exacta `¿Borrar de este navegador todas las respuestas, avisos y supuestos de escenario de Pai? No se podrá deshacer.` Botones `Borrar ahora` · `Cancelar`. Tras borrar: `Mapa borrado de este navegador. Puedes empezar de nuevo cuando quieras.` El borrado incluye respuestas, progreso, avisos y supuestos; no borrar configuraciones generales de la web.
- No guardar textos libres ni identificadores. Aun así, el perfil económico es sensible: el informe de seguridad advierte que el almacenamiento del navegador no es una caja fuerte frente a XSS. Antes de implementar, el grupo debe resolver la persistencia técnica, amenazas locales, retención y pruebas de borrado; no afirmar «anónimo», «cifrado» o «seguro» sin verificarlo. Véase `../../investigacion/10-seguridad-calidad.md` §§1 y 5.

## 5. Adaptación educativa por familia

La persona abre la biblioteca o selecciona qué comparar; el mapa solo decide qué explicación aparece primero o con qué profundidad. Ninguna condición del perfil muestra, oculta, clasifica, ordena o sugiere por sí sola un producto concreto.

| Familia didáctica | Cuándo se enseña | Contenido mínimo antes de comparar datos | Nunca concluir |
|---|---|---|---|
| Cuentas remuneradas | Cuando la persona elija `Cuentas remuneradas` o pregunte por disponibilidad/ahorro líquido. Si declaró necesidad de acceso inmediato, abrir primero la lección de disponibilidad. | Diferencia entre tipo, condiciones, saldo remunerado, variabilidad, comisiones y acceso. Distinguir garantía de depósitos de riesgo de mercado. | «Es la mejor para tu colchón» o equivalencia entre liquidez y ausencia de todo riesgo. |
| Depósitos | Cuando elija `Depósitos` o solicite aprender sobre plazos/condiciones. Si declaró un gasto próximo, explicar cancelación y penalización antes del ejemplo. | TIN/TAE, duración, renovaciones, vinculaciones, comisiones/penalización y condiciones que pueden cambiar el resultado. | Que el plazo encaja con su necesidad o que deba inmovilizar dinero. |
| Letras/bonos del Estado | Cuando la persona elija `Letras o bonos` o pregunte por deuda pública. | Letra: diferencia precio/reembolso y vencimiento. Bono: cupón separado de TIR. En ambos: precio posible de venta antes del vencimiento y supuestos del cálculo. | «TAE garantizada», retorno seguro al vender antes o que el plazo declarado convierta el instrumento en apropiado. |
| Fondos | Cuando la persona elija `Fondos` o abra esa ficha. Si declara un horizonte largo, se puede usar un ejemplo largo, rotulado como supuesto, sin inferir que sea adecuado. | Valor liquidativo, clase, pérdidas posibles, costes, ventanas de reembolso, documento oficial y horizonte recomendado del producto como dato descriptivo. | Asignación, clase o fondo recomendado por objetivo, horizonte o conocimientos. |
| ETF | Cuando la persona elija `ETF` o abra esa ficha. Si declara necesidad de liquidez, explicar que cotización no equivale a precio estable ni salida sin pérdida. | Precio de mercado, diferencial, costes del fondo y del intermediario, divisa, liquidez y riesgo de pérdida. | ETF «adecuado» por experiencia, horizonte o respuesta de tolerancia. |

Los detalles concretos deben seguir hechos y documentos oficiales fechados de la clase/producto que el usuario elija; si faltan datos o la fuente está caducada, no rellenarlos con memoria del modelo. La base metodológica está en `../../investigacion/09-rigor-financiero.md` §§3–4.

## 6. Límites conversacionales contextuales (no solo un cartel)

En la cabecera de Pai basta una frase discreta: `Tutor de aprendizaje · tú eliges qué explorar`. Los límites sustantivos se explican en la pregunta, resultado o solicitud que los activa.

**Si la persona pregunta «¿Qué producto me conviene?» / «¿Cuál compro?»**

> No puedo elegir un producto para ti ni ordenarlos según tu mapa. Sí puedo explicar las diferencias entre las familias o comparar datos de las opciones que tú elijas con los criterios que tú marques. ¿Qué quieres entender primero: liquidez, plazo, costes o posibilidad de pérdida?

**Si faltan datos para el ejemplo:**

> Para explicar [tema] con tu mapa me falta [dato]. No voy a completarlo con una media ni a inferirlo de otra respuesta. Puedes elegir un rango, ver una explicación general sin personalizar o seguir más tarde.

**Si se compara un producto elegido por la persona:**

> Esta ficha describe datos y condiciones del producto que has abierto; no dice si te conviene. Revisa la fuente, la fecha, costes, liquidez y posibilidad de pérdida. ¿Quieres que te explique alguno de esos puntos?

**Si el usuario interpreta la adaptación como recomendación:**

> He usado [respuesta declarada] solo para escoger esta explicación. No significa que Pai haya evaluado si un producto es adecuado para ti.

Estos guiones no sustituyen revisión jurídica ni autorizan selección individual. No incluir nombres/ISIN como salida de una recomendación, ni un «disclaimer» como excepción a esa regla. En v1, si se pide que Pai elija por la persona, responder con educación general y filtros elegidos por el usuario, nunca con un ranking personal.

## 7. Criterios de aceptación

1. Se puede terminar el núcleo respondiendo, eligiendo «No lo sé» o «Omitir» sin bloqueos ni puntuación.
2. Cada respuesta válida queda persistida antes del siguiente paso; cerrar el navegador y volver no convierte campos ausentes en datos.
3. Editar una respuesta actualiza solo el campo confirmado por la persona y recalcula avisos; no se reescriben otras respuestas.
4. No existe ruta que derive una compra, familia ganadora, puntuación de idoneidad o recomendación de instrumento a partir del perfil.
5. Una contradicción no produce respuesta inventada, borrado silencioso ni corrección automática. Los tres casos ficticios y las pruebas de `casos.json` deben pasar como pruebas de diseño antes de cualquier implementación.
6. El perfil y sus datos financieros no viajan en ninguna llamada de chat, evento analítico, URL, registro ni mensaje de error; verificarlo en red cuando exista prototipo.
7. Borrar el mapa elimina respuestas, avisos y progreso locales y muestra confirmación visible.

## 8. Decisiones pendientes del grupo antes de implementar/publicar

- **Privacidad técnica:** el requisito aprobado mantiene personalización económica local, mientras `10-seguridad-calidad.md` recomienda evitar saldos/deudas reales y advierte sobre almacenamiento del navegador. Resolver almacenamiento, amenaza XSS, uso en dispositivos compartidos, retención y prueba de borrado sin eliminar silenciosamente los campos. La propuesta conserva esos campos en rangos y no los transmite.
- **Catálogo de bandas y cortes:** aprobar bandas por campo y equivalencias de cada periodo; estas determinan si una alerta numérica es reproducible. Las bandas no se deben presentar como umbrales normativos o financieros universales.
- **Criterio de acceso a lecciones:** confirmar qué temas/familias se ofrecen desde la primera pantalla; la regla segura es selección explícita del usuario.
- **Revisión profesional española** antes de habilitar filtros o resultados que conecten datos personales y valores concretos. Este documento no es dictamen jurídico.

## Base documental interna

- `../../REQUISITOS.md`: público, preguntas de una en una, «no lo sé»/«omitir», resumen editable, perfil local borrable y diferenciación entre tolerancia/capacidad.
- `../../investigacion/09-rigor-financiero.md`: fuentes normativas/educativas citadas por el informe; frontera entre contenido general y recomendaciones personalizadas, campos de idoneidad, reglas de bloqueo y familias.
- `../../investigacion/08-ux-recursos.md`: recorrido de cuatro preguntas, motivos de pregunta, lenguaje adulto y resumen.
- `../../investigacion/10-seguridad-calidad.md`: minimización, almacenamiento local, borrado y separación del LLM.

**No se consultaron nuevas fuentes externas para esta especificación.** Las referencias normativas y de producto se remiten a la investigación ya guardada en el repositorio; deben volver a revisarse antes de publicar.
