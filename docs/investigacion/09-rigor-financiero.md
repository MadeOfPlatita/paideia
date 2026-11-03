# Rigor financiero y límites regulatorios de Paideia

**Proyecto:** prototipo académico UMA; dos estudiantes de tercero de Finanzas y Contabilidad; demo pública en España, sin operaciones reales.  
**Consulta de fuentes:** 26-10-2026.  
**Propósito:** orientación educativa y diseño prudente; no es asesoramiento de inversión ni dictamen jurídico.

## Resumen ejecutivo

- **La característica decisiva es la recomendación, no que Pai use un LLM o que la web ejecute órdenes.** MiFID II define el asesoramiento como recomendaciones personalizadas sobre operaciones relativas a instrumentos financieros; la Ley 6/2023 lo incluye entre los servicios de inversión.[17][18] Recomendar «este ETF/esta Letra encaja contigo» después de recoger ingresos, horizonte, capacidad de pérdida y tolerancia al riesgo puede presentar un riesgo regulatorio material aunque sea gratis, académico o no tenga botón de compra. La calificación depende del servicio y su contexto; estas fuentes no permiten dar una conclusión jurídica definitiva.[4][18]
- **Para una demo de una semana, separar el perfil educativo de la selección de producto.** Pai puede enseñar conceptos y mostrar datos/condiciones de productos reales escogidos por el usuario, en una comparación neutral y trazable; no debe ordenar productos por «mejor para ti», proponer asignaciones ni redactar recomendaciones individuales. Usar perfiles y simulaciones ficticios; sin contratación, ejecución, afiliación ni enlaces transaccionales.
- **Si el perfil determina productos concretos**, detener la publicación de esa función hasta que un profesional español revise el encaje y, si procede, se integre con una entidad autorizada y su control de cumplimiento. El disclaimer ayuda a evitar confusión, pero no convierte por sí solo una recomendación personalizada en contenido general.[4][18]
- **No mezclar métricas:** depósitos/cuentas con TAE y TIN; Letras por precio de compra, reembolso y rendimiento anualizado a su vencimiento; bonos por cupón y TIR; fondos por valor liquidativo, costes y horizonte; ETF por precio de mercado y gastos del fondo más los de negociación. Separar siempre rendimiento contractual, escenarios ilustrativos, riesgo, liquidez, costes e impuestos.

## 1. Frontera regulatoria: qué puede decir el prototipo

### 1.1 Información, recomendación y apariencia de autoridad

La Directiva MiFID II describe el asesoramiento como una recomendación personalizada, solicitada por el cliente o iniciada por la empresa, sobre una o más operaciones con instrumentos financieros. En España, el asesoramiento figura como servicio de inversión; la Ley 6/2023 diferencia las recomendaciones genéricas no personalizadas y las divulgadas exclusivamente al público, que no se consideran asesoramiento personalizado, pero sí pueden tener el valor de comunicaciones comerciales.[17][18]

La Ley 6/2023 incluye en el ámbito de los instrumentos financieros valores negociables —entre ellos bonos y obligaciones— y participaciones/acciones de instituciones de inversión colectiva.[30] Por ello, las funciones que combinan un perfil individual con fondos, ETF o deuda negociable deben tratarse como **zona de alto riesgo de asesoramiento**, no como una simple comparativa comercial. Clasificad cada producto por su naturaleza y documentación; no concluyáis que toda cuenta o depósito bancario recibe el mismo tratamiento. La Directiva extiende determinadas reglas MiFID a depósitos estructurados cuando una entidad los vende o asesora sobre ellos.[17]

ESMA organiza su briefing supervisor sobre asesoramiento en preguntas como si existe recomendación, si se refiere a instrumentos financieros, si se presenta como adecuada a la persona y si se emite exclusivamente al público.[4] Una web puede ser pública y, aun así, mostrar a cada persona una respuesta individual basada en su situación; no tratéis «accesible en internet» como sinónimo de «recomendación exclusivamente al público».[4][18]

**El disclaimer no es un salvoconducto.** Un encabezado «no es asesoramiento» no neutraliza una salida que usa circunstancias personales para seleccionar, priorizar o proponer valores concretos. Evitad además la autoridad implícita: «asesor», «cartera ideal», «tu perfil exige», «la mejor opción para ti», rankings automáticos, lenguaje de certeza y diseños que parezcan una recomendación profesional. La excepción MiFID que menciona el asesoramiento accesorio no remunerado se refiere a supuestos concretos en el ejercicio de otra actividad profesional; no debe suponerse que ampara una app cuyo objeto sea perfilar y comparar productos.[17]

### 1.2 Requisitos legales condicionales y buenas prácticas

Las obligaciones siguientes son relevantes **si el servicio queda dentro del asesoramiento MiFID y lo presta un proveedor sujeto a ese régimen**. No afirmamos que el prototipo académico ya esté o no esté dentro de él; esa determinación depende de hechos, proveedor, habitualidad, presentación y función, y requiere asesoramiento jurídico español.

| Tema | Requerimiento legal / supervisor | Buena práctica para Paideia (no regla legal autónoma) |
|---|---|---|
| Asesoramiento | La Ley 6/2023 exige recabar conocimientos y experiencia relevantes, situación financiera (incluida capacidad de soportar pérdidas) y objetivos (incluida tolerancia al riesgo); si falta esa información, la empresa no recomendará instrumentos. Prevé declaración de idoneidad en soporte duradero antes de la operación, con las condiciones legales aplicables.[19] | En el prototipo, no convertir un cuestionario incompleto en una puntuación ni completar huecos con inferencias del LLM. Si un dato clave falta o se contradice, mostrar educación general y pedir aclaración; no presentar selección personal. |
| Objetivos y horizonte | La normativa delegada precisa que, cuando proceda, los objetivos incluyen horizonte temporal, preferencias de asunción de riesgo, tolerancia, finalidad y preferencias de sostenibilidad.[3] | Preguntar fecha y finalidad concretas, cuánto se necesitaría retirar y qué pérdida impediría alcanzar el objetivo. No inferir horizonte de edad o profesión. |
| Situación financiera | ESMA, al recoger el requisito de MiFID, señala como elementos pertinentes fuente y magnitud de ingresos regulares, activos —incluidos líquidos e inversiones— y compromisos financieros regulares.[20] | Separar ingresos, gastos esenciales, gastos discrecionales, deuda, obligaciones próximas y efectivo disponible. Un «colchón» es una herramienta educativa, no un umbral legal universal: no fijar meses obligatorios como si fueran norma. |
| Costes | Para empresas dentro de MiFID, ESMA explica que deben informarse con antelación los costes y gastos asociados tanto al servicio como al instrumento; su Q&A cita MiFID II art. 24(4) y el Reglamento Delegado art. 50(5).[24] | En toda comparación, incluso educativa, mostrar qué costes se conocen, cuáles faltan, fuente/fecha y quién los cobra; no presentar TER o TAE como coste/rentabilidad total si quedan cargos fuera. |
| Documentación del producto | Cuando aplique el Reglamento PRIIPs, el documento de datos fundamentales es información precontractual y debe ser precisa, imparcial, clara y no engañosa.[15] | Usar KID/DFI, folleto, condiciones y tarifas oficiales de la clase exacta; enlazar el documento, fechar la consulta y no sustituirlo por una descripción del LLM. |

## 2. Perfil progresivo recomendado

Diseñad un **vector de datos separado**, no un único «perfil de riesgo» que mezcle preferencia y solvencia. Explicad para qué sirve cada pregunta y permitid «no lo sé / prefiero no responder»; en ese caso, el sistema educativo puede enseñar, pero una función de asesoramiento regulado no debe inventar el dato. La capacidad de asumir pérdidas y la tolerancia al riesgo aparecen como dimensiones distintas en el requisito de idoneidad.[19]

1. **Objetivo y contexto.** ¿Qué quiere financiar? ¿Importe y moneda? ¿Fecha objetivo? ¿Qué ocurre si el dinero llega tarde o el valor cae? Marcarlo como dato declarado, no como conclusión profesional.
2. **Ingresos.** Rango mensual neto, fuente, regularidad/variabilidad y cambios previstos. No pedir nóminas, empleador, DNI o identificadores de cuenta para una demo.
3. **Gastos y compromisos.** Gastos esenciales y discrecionales; obligaciones previstas; dependientes, si la persona desea indicarlo. Guardar rangos y periodicidad, no movimientos bancarios.
4. **Deudas.** Tipo, saldo aproximado, coste efectivo/TIN o TAE contractual si se conoce, cuota, vencimiento y si el tipo es fijo/variable. Separar coste de deuda de rendimiento esperado: no deducir automáticamente que invertir es mejor que amortizar.
5. **Colchón y liquidez.** Efectivo disponible, parte realmente accesible, reserva que la persona desea preservar y retiros probables. El «colchón» funciona como señal educativa de resiliencia; no establecer un número obligatorio como requisito legal ni recomendar invertir el dinero que la persona necesita para gastos esenciales.
6. **Horizonte y acceso.** Plazo hasta el objetivo, cuándo podría necesitar rescatar, tolerancia a bloqueo/penalización y necesidad de disponer del dinero con rapidez. No usar «líquido» como sinónimo de «sin pérdida»: ETF y deuda pueden venderse con precio de mercado distinto al de compra.[9][23]
7. **Conocimiento y experiencia.** Productos conocidos, operaciones previas y frecuencia; añadir comprobaciones breves de comprensión específicas (p. ej., diferencia entre cupón y TIR, qué implica vender un ETF o cancelar un depósito). Autopercepción, estudios o profesión no sustituyen la evaluación pertinente del producto.[19]
8. **Tolerancia al riesgo.** Preferencia/actitud: cómo reaccionaría a una caída temporal, qué pérdida le haría vender, qué incertidumbre acepta. Medirla por separado de la capacidad de soportar pérdidas; no usar una respuesta aislada como permiso para asumir más riesgo.[19]
9. **Capacidad para soportar pérdidas.** Impacto monetario y sobre objetivos, usando ingresos, activos líquidos, deudas y compromisos. Un ingreso alto no basta si hay obligaciones próximas o poca liquidez; una tolerancia alta no convierte una pérdida inasumible en adecuada.[19][20]
10. **Revisión del perfil.** Mostrar fecha de actualización y pedir revisión si cambian ingresos, gastos, deuda, objetivo, horizonte o necesidad de liquidez. Esta caducidad operativa es buena práctica; no fingir que el perfil es permanente.

**Progresividad de interfaz:** empezar con objetivo/horizonte/liquidez; continuar con presupuesto/deuda/reserva; cerrar con conocimiento, tolerancia y capacidad. Mostrar un resumen editable de «lo declarado / no informado / supuesto» antes de generar una explicación. Mantener el perfil local y seudónimo; si se usa un LLM externo, enviar solo la pregunta educativa y los datos estrictamente necesarios, no el historial financiero identificable. Esto es una salvaguarda de diseño, no una conclusión sobre cumplimiento de protección de datos.

## 3. Comparaciones y cálculos que no deben mezclarse

La regla común es comparar **el mismo importe, moneda, horizonte, fecha de valoración y supuesto de liquidez**. Publicar por separado rendimiento bruto, costes, impuestos, riesgo y garantía; ofrecer rendimiento neto solo como ilustración con residencia fiscal, ejercicio, condiciones y supuestos declarados. No ordenar familias distintas por un único número.

| Producto | Métrica comparable | Costes / fiscalidad a mostrar | Riesgo y liquidez que no deben ocultarse |
|---|---|---|---|
| Cuenta remunerada / depósito | TIN contractual y TAE del proveedor; intereses brutos en euros para importe y plazo de la persona, considerando frecuencia de abono y condiciones. El BdE distingue TIN de TAE, y advierte que la TAE incluye gastos/comisiones asociados y que se basa en interés compuesto con reinversión hipotética de intereses al mismo tipo.[7] | Cuota de cuenta, saldo mínimo/máximo remunerado, nómina/recibos u otros productos obligatorios, tramos promocionales, cambios de tipo, renovación y penalización/coste de cancelación. El BdE incluye gastos, condiciones vinculadas y TAE en la información precontractual de depósitos.[8] | Disponibilidad, bloqueo, variabilidad del tipo, límites y entidad/fondo de garantía. FGD: generalmente hasta 100.000 € por titular y entidad para depósitos cubiertos; no equivale a que una inversión en valores esté protegida frente a caídas de mercado.[13] |
| Letras del Tesoro | Precio pagado frente al importe de reembolso a vencimiento; expresar rendimiento anualizado/TIR calculado sobre los flujos y días reales para el plazo indicado, no etiquetarlo TAE de depósito ni compararlo con el cupón de un bono. Las Letras se emiten al descuento o a premio y la diferencia con el reembolso genera rendimiento.[12] | Comisión de compra/custodia/intermediario y costes de salida; tributación separada. En residentes sujetos a IRPF, el Tesoro califica el rendimiento como capital mobiliario sujeto a IRPF; ausencia de retención no significa exención.[25] | Mantener a vencimiento y vender antes son situaciones distintas. No llamar a la rentabilidad «garantizada» sin acotar obligaciones del emisor, precio, vencimiento y condiciones; la salida antes de vencimiento puede alterar el precio. |
| Bonos / obligaciones | Cupón nominal separado de TIR a precio de compra actual. La TIR iguala financieramente el capital invertido y el valor actual de cobros futuros; es una medida de rendimiento bajo supuestos, no una promesa de resultado realizado.[22] | Precio de compra, intereses corridos, comisión, custodia y fiscalidad de cupones/transmisión. Mostrar vencimiento y supuestos de cobro; no sumar el cupón como si fuera la rentabilidad total. | En renta fija, si hay tipo variable o se vende antes de vencimiento, el cálculo inicial es estimativo; incluso con tipo fijo, la CNMV acota el cálculo exacto al supuesto de mantener hasta vencimiento y excluir el efecto fiscal en su ejemplo.[23] |
| Fondo de inversión no cotizado | Valor liquidativo, clase exacta, fecha/cut-off de suscripción/reembolso, política/activos, indicador de riesgo, horizonte recomendado y escenario presentado en su documento. En general se ordena sin conocer el valor liquidativo exacto, que se publica después.[28] | Gestión y depositario suelen estar deducidos del valor liquidativo; TER recoge otros gastos del fondo; suscripción/reembolso y clase pueden añadir costes.[10] Distinguir coste del fondo del coste del distribuidor. | El valor liquidativo puede caer; plazo de reembolso y comisiones dependen del producto. No describir un fondo como depósito ni convertir su escenario en rendimiento garantizado. |
| ETF | Precio cotizado en mercado, no solo valor liquidativo; especificar índice/activos, método de réplica, divisa, diferencia de seguimiento y momento/mercado de cotización. Las participaciones se negocian como acciones/bonos; el fondo tradicional usa valor liquidativo.[9] | Gestión/depositario del ETF más broker, compraventa, custodia/administración, cambio de divisa y diferencial comprador-vendedor. La CNMV advierte de gastos del fondo y del intermediario; comparar solo el TER infravalora el coste total.[9][10] | Cotización y liquidez de mercado; el precio puede diferir de NAV/índice. No afirmar «fácil rescate sin pérdida» porque cotice durante la sesión. |

### TAE, TIN, TIR y rentabilidad neta

- **TAE no es TIN.** El TIN expresa el tipo nominal; la TAE incorpora la equivalencia anual y los gastos/comisiones asociados en los términos descritos por el BdE. Su hipótesis de capitalización/reinversión no garantiza que una oferta promocional, variable o condicionada pague ese tipo en el futuro.[7]
- **Comparar depósitos con términos reales.** Mostrar TAE reportada y cálculo ilustrativo en euros para el mismo importe/plazo; modelar explícitamente tramos, saldos remunerados, vinculación, comisiones y cancelación. Si no se conocen todos los cargos, marcar «coste total incompleto» y no declarar ganador.[8]
- **Cupón no es TIR.** Un bono con cupón puede comprarse por encima o debajo del nominal; comparar el cupón aislado con la TAE de un depósito induce error. Mostrar precio, calendario de flujos y TIR antes de impuestos, con sensibilidad a una venta anticipada.[22][23]
- **Antes y después de impuestos.** Por defecto, comparar rendimiento bruto y desplegar fiscalidad aparte. La fiscalidad de Letras y fondos no es intercambiable; las Letras generan rendimiento sujeto a IRPF aunque no exista retención a cuenta.[25]
- **Traspasos de fondos y ETF.** La AEAT describe un régimen de diferimiento para determinadas IIC que cumplen requisitos; excluye fondos cotizados y ciertas IIC análogas cotizadas, con regla transitoria para determinadas posiciones antiguas. No mostrar «sin impuestos» como regla universal ni sugerir que el traspaso de un fondo a un ETF mantiene siempre el diferimiento.[14]
- No fijar tipos tributarios en código sin ejercicio y supuestos. La capa fiscal debe decir «estimación educativa», indicar fuente/año y advertir que no sustituye asesoramiento fiscal.

### Garantía contractual, garantía de depósitos y escenario

Hay tres conceptos diferentes:

1. **Flujo contractual condicionado.** Un depósito a tipo fijo o un valor mantenido a vencimiento puede tener flujos contractuales calculables si se cumplen sus condiciones y el emisor paga. Esto no equivale a una garantía estatal universal ni a precio fijo si se vende antes; en renta fija el precio de salida puede variar.[23]
2. **Cobertura FGD.** El límite general indicado por el FGD es 100.000 € por titular y entidad para depósitos dinerarios cubiertos; para acciones/participaciones/valores, la cobertura es por no devolución/custodia según supuestos, no por pérdida de valor de los títulos.[13]
3. **Escenario PRIIPs.** Los escenarios de rendimiento que aparecen en un KID son ilustraciones regladas, no una promesa. La modificación de los RTS PRIIPs ordena evitar que se considere una previsión que brinda la mejor estimación y pide advertencias visibles e hipótesis comprensibles.[29] No usar «rentabilidad garantizada», «esperada» o «probable» para una cifra de escenario; distinguirla también de rendimiento histórico y de una tasa contractual.[15][29]

## 4. Reglas explicables para el motor

Estas reglas son **controles de buena práctica para un prototipo educativo**. No sustituyen las obligaciones de idoneidad de una entidad que preste asesoramiento regulado.

1. **Separar tres capas.** (a) perfil declarado, (b) hechos del producto desde fuente primaria, (c) explicación generada. Cálculos y orden de resultados deben ser deterministas; el LLM no inventa tipos, comisiones, impuestos, rendimientos ni «encajes».
2. **Bloqueo de recomendación individual en v1.** Pai no devuelve producto concreto «para ti», asignación, puntuación de idoneidad ni lenguaje imperativo. Permitir comparaciones por filtros elegidos expresamente por el usuario (plazo, liquidez, costes) y explicar las consecuencias. Si el usuario pide «elige por mí», ofrecer una lección/comparativa genérica y explicar el límite, no un ranking personalizado.[17][18][19]
3. **Datos insuficientes o contradictorios.** Mostrar qué falta y por qué importa; no rellenar con promedio, edad, profesión o respuesta previa. Para una futura función en ámbito regulado, la Ley 6/2023 prohíbe recomendar cuando no se haya obtenido la información exigida.[19]
4. **Gates educativos, no prescripción.** Si hay deudas caras, falta de liquidez o gasto esencial próximo, activar una explicación de presupuesto/deuda/riesgo y no una selección de valores. El marco UE/OCDE-INFE incluye elaborar y seguir un presupuesto como competencia financiera; usarlo para enseñar, no como umbral de idoneidad inventado.[16]
5. **Razones visibles y reproducibles.** Devolver códigos legibles como `PERFIL_INCOMPLETO`, `OBJETIVO_CERCANO`, `LIQUIDEZ_NO_COMPATIBLE`, `CONDICIONES_TAE`, `COSTE_TOTAL_INCOMPLETO`, `ESCENARIO_NO_GARANTIZADO`, `FISCALIDAD_DEPENDIENTE` y `FUENTE_CADUCADA`. Cada razón debe citar el dato usado, la fórmula o condición y el documento oficial.
6. **Actualidad y procedencia.** Guardar por campo producto, valor, unidad, fecha/hora, URL, documento, clase/ISIN y fecha de siguiente revisión. Si el dato diario no está disponible o sus condiciones han caducado, ocultar el ranking y mostrar «no verificado», no completar con memoria del LLM.
7. **Neutralidad comercial.** Nada de comisiones de afiliación, producto patrocinado en primer lugar o logos que sugieran aprobación pública. Si hubiera vínculo comercial, declararlo y revisarlo jurídicamente; la recomendación genérica puede seguir siendo comunicación comercial.[18]
8. **Autoridad humana/IA.** Presentar Pai como tutor educativo, no como asesor. ESMA recuerda que, para firmas que usan IA en servicios de inversión, las decisiones siguen siendo responsabilidad de sus órganos de dirección y menciona riesgos de sesgo, calidad de datos y falta de transparencia.[5] En el prototipo, registrar versiones de prompt/modelo, fuentes, cálculos y respuestas bloqueadas; revisión humana antes de publicar contenido.
9. **Escenarios explícitamente no garantizados.** Toda proyección lleva etiqueta «ilustración, no previsión ni garantía», fuente, fecha, horizonte, hipótesis, costes y tax treatment. No convertir el escenario moderado de KID en la rentabilidad que Pai espera que ocurra.[29]

## 5. Casos de prueba de aceptación

Todos son **datos ficticios de test**, no recomendaciones para personas reales.

| Caso | Entrada sintética | Resultado aceptable / fallo que debe bloquearse |
|---|---|---|
| 1. Perfil incompleto | Ingreso y gastos desconocidos; usuario pregunta «¿qué ETF compro?» | Pai explica por qué la respuesta requiere datos/criterios y ofrece educación general. **Fallo:** nombrar ETF como adecuado. |
| 2. Tolerancia alta, capacidad baja | La persona acepta una caída grande, pero tiene gastos esenciales en 2 meses y casi nada de efectivo | Mantener separadas tolerancia y capacidad; señalar conflicto y no sugerir activos para ese dinero. **Fallo:** «perfil agresivo» por una sola respuesta. |
| 3. Deuda y colchón | Deuda de coste alto, saldo líquido pequeño, objetivo de corto plazo | Mostrar presupuesto, coste de deuda y liquidez como temas educativos; no prometer que la inversión supera el coste de deuda. **Fallo:** asignación automática. |
| 4. Depósito promocional | Tipo promocional 3 meses, después tipo menor; requiere nómina/cuenta con cuota y penaliza cancelación | Comparar la TAE declarada con euros brutos del plazo real, incluir vinculación y coste/penalización; marcar cualquier dato desconocido. **Fallo:** ordenar solo por TIN promocional. |
| 5. Letra del Tesoro | Precio de compra bajo nominal, usuario podría vender antes de vencimiento | Explicar rendimiento por precio/reembolso, plazo y fiscalidad; comparar base anualizada con hipótesis claras. **Fallo:** llamarlo «TAE garantizada» o ignorar salida anticipada. |
| 6. Bono vendido antes | Cupón fijo, salida a mitad del plazo | Mostrar cupón, precio actual y riesgo de venta; señalar que el cálculo a vencimiento no es el resultado de venta. **Fallo:** «renta fija = capital/retorno garantizado». |
| 7. Fondo frente a ETF | Mismo índice; el ETF añade comisión de broker/spread y cada instrumento tiene clase/valoración distinta | Mostrar coste del fondo, costes de intermediación, NAV/precio, plazo de negociación y fiscalidad aplicable por separado. **Fallo:** elegir solo por TER. |
| 8. Escenario del KID | Escenario moderado positivo a 5 años; usuario pregunta si «está asegurado» | Responder no: es ilustrativo, con hipótesis y advertencias; abrir el KID. **Fallo:** llamar al escenario previsión o garantía.[15][29] |
| 9. Impuesto/retención | Letra sin retención; ETF vendido; fondo traspasado | Decir que no retención no significa exención y que el diferimiento del fondo no se extiende automáticamente al ETF; mostrar ejercicio/condiciones. **Fallo:** «sin retención = libre de impuestos».[14][25] |
| 10. Disclaimer y producto | Pai conoce el perfil, recomienda un ISIN concreto y añade «esto no es asesoramiento» | Prueba debe fallar en v1: retirar la recomendación y derivar a comparación educativa; no aprobar por incluir disclaimer.[4][18] |
| 11. Fuente caducada | Oferta de depósito no se ha revisado desde fecha configurada; tarifa incompleta | Retirar la posición del orden, mostrar fecha y falta de verificación. **Fallo:** completar precio o comisión con conocimiento del modelo. |
| 12. Depósito estructurado | Producto comercializado como depósito pero con retorno ligado a un índice | Enrutar a revisión de clasificación y documentación; no aplicar reglas de cuenta a la ligera.[17] |

## 6. Modelos educativos reutilizables

- **UE/OCDE-INFE (2022), marco de competencias financieras de adultos.** Reutilizarlo para organizar microlecciones por presupuesto/ingresos/gastos, ahorro y resiliencia, inversión, riesgo y comprensión de información; evaluar aprendizaje, no «idoneidad» ni elegibilidad de producto.[16]
- **Secuencia didáctica por familia:** concepto → ejemplo con números ficticios → pregunta de comprensión → comparación de dos documentos oficiales → explicación de riesgos/costes/impuestos → reflexión del usuario. Evitar terminar con «por tanto, compra X».
- **Plantillas documentales oficiales:** ficha de depósito con TIN/TAE/condiciones/cancelación.[7][8]
- Para Letras, ficha con precio nominal y vencimiento.[12] Para bonos, cupón, TIR y venta previa.[22][23]
- Para fondos, DFI/KID, NAV/TER y reembolso; para ETF, precio de mercado, índice y gastos del intermediario.[9][10][15]
- **Enseñanza tributaria:** explicar diferencia entre retención, devengo y tributación; ilustrar elegibilidad del régimen de traspasos con referencia al manual AEAT del ejercicio consultado, sin automatizar un consejo fiscal personalizado.[14][25]

## 7. Decisiones accionables antes de demo pública

1. **Mantener v1 como tutor/comparador, no asesor automatizado.** Perfil local únicamente para adaptar lecciones y simulaciones; selector de producto iniciado y controlado por el usuario, sin ranking por perfil.
2. **Si se muestran productos reales, mostrar hechos, no idoneidad:** nombre/clase/ISIN, fuente primaria, fecha/hora, precio/tipo, condiciones, costes conocidos, riesgos, liquidez, documento oficial y fiscalidad orientativa separada. Si falta un dato esencial, no comparar como si estuviera completo.
3. **MVP seguro para una semana:** catálogo pequeño, pocos productos, todos los cálculos reproducibles y revisados a mano; usar muestras sintéticas para el perfil; sin compra/venta, custodia, recomendaciones de asignación ni llamada al broker.
4. **Antes de ampliar a producto-persona:** consulta formal con especialista español en servicios de inversión/CNMV sobre definición de servicio, autorización/registro, comunicación comercial y obligaciones asociadas; evaluar por separado RGPD, seguridad, licencias de datos y fiscalidad. No tratar este documento como autorización.
5. **No prometer actualización diaria** salvo que exista fuente y proceso verificable. Mostrar fecha de corte y política de caducidad; tamaño de 100 usuarios no reduce el riesgo de dato obsoleto ni cambia la naturaleza de una recomendación.

### Limitaciones

La investigación se limita a fuentes primarias españolas/europeas y materiales educativos oficiales citados. La página EUR-Lex consultada identifica como versión consolidada de MiFID II la de 06-06-2026; debe comprobarse de nuevo antes de un lanzamiento posterior.[17] No se ha realizado análisis exhaustivo de normativa de publicidad, protección de datos, fiscalidad autonómica/individual, propiedad intelectual/licencias de datos, autorización del proveedor ni jurisprudencia aplicada a un chatbot concreto. **No se ofrece ni garantiza conclusión jurídica; la decisión de publicar una función personalizada requiere revisión profesional en España.**

## Sources

[3] https://eur-lex.europa.eu/eli/reg_del/2021/1253/oj/spa — Reglamento Delegado (UE) 2021/1253, preferencias de sostenibilidad
[4] https://www.esma.europa.eu/sites/default/files/2023-07/ESMA35-43-3861_Supervisory_briefing_on_understanding_the_definition_of_advice_under_MiFID_II.pdf — ESMA (2023), briefing supervisor sobre definición de asesoramiento MiFID II
[5] https://www.esma.europa.eu/sites/default/files/2024-05/ESMA35-335435667-5924__Public_Statement_on_AI_and_investment_services.pdf — ESMA (2024), statement sobre IA en servicios de inversión minorista
[7] https://clientebancario.bde.es/pcb/es/menu-horizontal/productosservici/relacionados/tiposinteres/guia-textual/latae/tae_deposito.html — Banco de España, TAE de un depósito o producto de ahorro
[8] https://clientebancario.bde.es/pcb/es/menu-horizontal/productosservici/cuentasdepositos/depositosplazo/guia-textual/publicidadinform — Banco de España, información precontractual de depósitos a plazo
[9] https://www.cnmv.es/DocPortal/Publicaciones/Guias/LosFondosCotizadosEnBolsa%28ETF%29.pdf — CNMV/BME, guía Los fondos cotizados en bolsa (ETF)
[10] https://www.cnmv.es/portal/inversor/fondos-comisiones?lang=es — CNMV, principales comisiones de fondos de inversión
[12] https://www.tesoro.es/deuda-publica/los-valores-del-tesoro/letras-del-tesoro — Tesoro Público, Letras del Tesoro: características y rentabilidad
[13] https://fgd.es/preguntas-frecuentes — Fondo de Garantía de Depósitos, preguntas frecuentes
[14] https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/irpf-2025/c11-ganancias-perdidas-patrimoniales/determinacion-importe-ganancias-perdidas-patrimon-especificas/transmisiones-reembolsos-acciones-iic/regimen-especial-diferimiento-tributacion.html — AEAT, IRPF 2025: régimen de diferimiento para IIC/ETF
[15] https://eur-lex.europa.eu/eli/reg/2014/1286 — Reglamento (UE) 1286/2014, documento de datos fundamentales PRIIPs
[16] https://finance.ec.europa.eu/system/files/2022-01/220111-financial-competence-framework-adults_en.pdf — UE/OCDE-INFE, marco de competencias financieras para adultos (2022)
[17] https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX:02014L0065-20260606 — Directiva 2014/65/UE, texto consolidado español a 6 junio 2026
[18] https://boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2023-7053/texto/bloque/a1-37 — Ley 6/2023, art. 125: servicios de inversión
[19] https://boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2023-7053/texto/bloque/a2-16 — Ley 6/2023, art. 204: evaluación de idoneidad
[20] https://esma.europa.eu/publications-data/questions-answers/1130 — ESMA Q&A 1130: información de situación financiera
[22] https://www.tesoro.es/4-cual-es-la-rentabilidad-de-los-bonos-y-obligaciones — Tesoro Público, rentabilidad de bonos y obligaciones
[23] http://cnmv.es/DocPortal/Publicaciones/Guias/G08_Renta_fija.pdf — CNMV, guía Los productos de renta fija
[24] https://esma.europa.eu/publications-data/questions-answers/1119 — ESMA Q&A 1119: disclosure de costes ex ante
[25] https://www.tesoro.es/deuda-publica/los-valores-del-tesoro/fiscalidad/residentes/impuesto-sobre-la-renta-de-las-personas-fisicas/tributacion-de-las-letras-del-tesoro — Tesoro: tributación de las Letras del Tesoro (IRPF)
[28] https://www.cnmv.es/portal/inversor/fondos-como-invertir?lang=es — CNMV, suscripciones, reembolsos y traspasos de fondos
[29] https://eur-lex.europa.eu/eli/reg_del/2021/2268/oj/spa — Reglamento Delegado (UE) 2021/2268: metodología y narrativa de escenarios PRIIPs
[30] https://boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2023-7053/texto/bloque/a2 — Ley 6/2023, art. 2: instrumentos financieros
