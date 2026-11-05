# Catálogo editorial de afirmaciones cerradas para Pai

**Versión propuesta:** `paideia-education-v2` · **Fecha:** 4 de noviembre de 2026 · **Estado:** propuesta editorial, no implementada · **Idioma:** español de España.

> En el modo estructurado, el proveedor no escribe prosa: elige identificadores de este catálogo y el servidor renderiza los textos. Ningún texto de este documento se envía al proveedor ni se genera en el turno.

## 1. Por qué este catálogo y qué cambia

La evaluación de la ejecución 4h30 deja cinco preguntas sin contenido visible (P2, P5, P7, P8 y P9) porque el filtro léxico retiene la respuesta entera cuando aparece una cifra o una palabra de atribución. En P2 el falso positivo es estructural y confirmado: cualquier ejemplo válido de TIN y TAE contiene un porcentaje. En P5 el disparador aparecería en una respuesta correcta (la TAE o la ficha); en P7, P8 y P9 el propio enunciado ya lo contiene. El problema no se arregla solo afinando el filtro: se arregla separando lo que el servidor puede afirmar de lo que el modelo puede elegir.

Este catálogo es la lista cerrada de lo que el servidor puede afirmar. Cada entrada explica un concepto; ninguna sustituye a la ficha de un producto. Los datos de producto —tasas, plazos, importes, coberturas, nombres de entidades y fechas— siguen viviendo en la capa de condiciones, con su fuente, su clase y su fecha. Esa separación es la que permite responder P2, P7 y P9 sin que el modelo invente una atribución.

El catálogo también corrige los dos puntos ciegos que la evaluación observó en respuestas que sí pasaron el filtro: «instrumentos seguros» o «riesgo mínimo» en P1 y «capital protegido en caso de insolvencia» en P4. En ambos casos la solución no es añadir un aviso genérico, sino partir la afirmación y explicar el límite: qué cubre la garantía, qué no cubre y por qué la solvencia no la sustituye.

**Fuentes leídas para redactarlo:** `docs/pai-calidad/ejecucion-4h30/EVALUACION.md` (apartados 2, 3, P2, P5, P7, P8, P9 y 8), `docs/pai-calidad/RUBRICA-DIEZ-PREGUNTAS.md`, el glosario compartido de `app/static/context_help.js` y `static/app.js`, el catálogo `app/data/condiciones.json` con `catalogue_conditions.py` y `docs/catalogo-condiciones-20261103/EVIDENCIA.md`, el precedente `app/structured_education.py` y el contrato `docs/ia-calidad-estructurada/ejecucion/20261030T032529Z/CONTRATO.md`.

## 2. Reglas de redacción

- **39 afirmaciones en 9 grupos.** Cada una tiene entre una y tres frases; el máximo observado es 3.
- **Sin cifras, porcentajes, importes ni fechas de vigencia.** Tampoco se escriben números con dígitos: las cantidades solo pueden venir del motor determinista o de la capa de condiciones.
- **Sin nombres de entidades, productos, medios, países o sistemas concretos.** Se habla de «la entidad», «el producto», «el régimen de garantía», no de un caso.
- **Sin «oficial», «vigente», «vigencia» ni «en vigor» en el texto renderizado, ni siquiera en negación.** La negación se expresa por lo que la afirmación explica, no por el token que antes disparaba el filtro. En las entradas del catálogo, esos términos solo aparecen en `never_claim`, como criterio de revisión.
- **Sin recomendación, superlativos, comparativas de mercado ni garantía absoluta.** El catálogo explica criterios; no elige por la persona.
- **`text` es propiedad del servidor.** `when` orienta al selector; `never_claim` es la lista de comprobación de la revisión. Ningún campo se interpola con datos del usuario.
- **Los datos de producto no entran aquí.** Una tasa, un plazo, un importe, una cobertura o un nombre de entidad se renderizan desde la capa de condiciones, con fuente, clase y fecha; nunca desde este catálogo.

## 3. Resumen por grupos

| Grupo | Prefijo | N.º | Para qué sirve |
|---|---|---|---|
| Alcance y límites de la respuesta | `alcance_` | 3 | Qué puede y qué no puede hacer una explicación educativa; cuándo hay que decir que faltan datos. |
| Ahorro, inversión y riesgo | `ahorro_` | 3 | Distinción conceptual y riesgos que no se ven en el saldo. |
| TIN, TAE e interés | `interes_` | 5 | Definiciones, ejemplo conceptual sin cifras y condiciones de comparabilidad. |
| Inflación y poder adquisitivo | `inflacion_` | 4 | Nominal frente a real, método de ajuste y límites del escenario. |
| Liquidez, plazo y cancelación | `liquidez_` | 4 | Disponibilidad del dinero, vencimiento, penalizaciones y costes. |
| Comparar sin recomendar | `comparar_` | 5 | Criterios, base común, datos que faltan y frontera de la recomendación. |
| Garantía de depósitos | `garantia_` | 6 | Qué protege, con qué límites, qué queda fuera y cómo comprobarlo. |
| Datos vencidos, fuentes y atribución | `fuente_` | 5 | Por qué un dato caducado no es una oferta y qué exige una atribución. |
| Simulación y cálculo | `simulacion_` | 4 | Hipótesis, supuestos, costes excluidos y convención del tipo. |

## 4. Catálogo completo

### 4.1 Alcance y límites de la respuesta (`alcance_`)

Qué puede y qué no puede hacer una explicación educativa; cuándo hay que decir que faltan datos.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `alcance_educativo_sin_asesoramiento` | Esta explicación es educativa: ayuda a entender conceptos y a leer condiciones, pero no es asesoramiento financiero, fiscal ni jurídico personalizado. Una explicación general no tiene en cuenta la situación, los objetivos ni la tolerancia al riesgo de quien la lee. | Cuando la persona pida una recomendación, pregunte qué producto elegir o pueda interpretar la respuesta como un consejo personalizado. | No afirma que la aplicación sea un asesor registrado ni que su respuesta sustituya a un profesional; no recomienda contratar ningún producto ni elegir una entidad concreta. |
| `alcance_datos_que_faltan` | Cuando faltan datos para responder, lo correcto es decir que no se puede concluir con esa información y señalar qué falta. Rellenar el hueco con un supuesto no convierte el supuesto en un dato del producto. | Cuando la respuesta dependa de una condición que no consta, como el plazo de uno de los productos, el periodo de aplicación de la condición o el tipo aplicable. | No afirma que un dato ausente sea deducible del contexto ni que un supuesto razonable equivalga a una condición documentada. |
| `alcance_no_confirma_condiciones` | Una explicación educativa no confirma las condiciones de un producto concreto. Para saber qué se aplica en el momento de decidir hay que leer la documentación del producto y comprobar a qué periodo se refiere. | Cuando la persona pregunte por una condición concreta de un producto o por lo que puede contratar ahora. | No afirma que la aplicación haya consultado la ficha, que el dato siga aplicándose ni que la explicación refleje una oferta comercial. |

### 4.2 Ahorro, inversión y riesgo (`ahorro_`)

Distinción conceptual y riesgos que no se ven en el saldo.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `ahorro_frente_a_inversion` | Ahorrar es apartar dinero para usarlo más adelante; invertir es poner ese dinero a trabajar aceptando que su valor puede subir o bajar. El ahorro prioriza la disponibilidad; la inversión acepta variaciones de valor a cambio de un rendimiento esperado. | Cuando la persona pregunte por la diferencia entre ahorro e inversión o quiera situar su objetivo en uno de los dos. | No afirma que ahorrar esté exento de riesgo ni que invertir garantice un rendimiento; no califica ningún producto como seguro. |
| `ahorro_riesgo_inflacion` | El ahorro conserva el importe nominal, pero no protege por sí solo del efecto de la inflación: si los precios suben más que la remuneración, el dinero compra menos. Esa pérdida de poder adquisitivo puede no aparecer en el saldo. | Cuando se hable de ahorro, cuentas remuneradas o depósitos y la persona pregunte si su dinero está protegido. | No afirma que la inflación vaya a superar a un tipo concreto ni que el ahorro pierda valor siempre; no da cifras de inflación. |
| `ahorro_riesgos_de_invertir` | El riesgo es la posibilidad de que el resultado difiera de lo esperado, incluida la pérdida de parte o todo el capital invertido. En una inversión no viene solo de que el precio baje: también influyen la solvencia del emisor, la liquidez para vender, la custodia del activo y las condiciones del producto. Repartir el dinero entre varios activos puede reducir el impacto de un mal resultado aislado, pero no elimina el riesgo de mercado ni garantiza conservar el capital. | Cuando la persona pregunte qué riesgos tiene invertir o qué debe mirar además de la rentabilidad. | No afirma que un producto tenga una calificación de riesgo concreta, que diversificar elimine las pérdidas ni que diversificar garantice conservar el capital. |

### 4.3 TIN, TAE e interés (`interes_`)

Definiciones, ejemplo conceptual sin cifras y condiciones de comparabilidad.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `interes_tin_nominal` | El TIN es el tipo de interés nominal pactado: expresa el porcentaje de interés sobre el capital sin incorporar por sí mismo la frecuencia de los pagos ni todos los gastos. Dos productos con el mismo TIN pueden producir resultados distintos si cambia la forma de liquidar los intereses. | Cuando la persona pregunte qué es el TIN o compare dos ofertas que solo muestran ese dato. | No afirma que el TIN sea el rendimiento efectivo ni que dos TIN iguales impliquen el mismo resultado; no da tipos concretos. |
| `interes_tae_equivalente` | La TAE es la tasa anual equivalente: resume el coste o el rendimiento anual bajo unos supuestos, incorporando la frecuencia de los pagos y ciertos gastos. Sirve para comparar, pero no describe por sí sola todas las condiciones del producto. | Cuando la persona pregunte qué es la TAE o por qué se usa para comparar ofertas. | No afirma que la TAE incluya todos los costes ni que coincida con lo que la persona recibirá; no da valores ni compara entidades. |
| `interes_ejemplo_tin_tae` | Ejemplo conceptual: si los intereses se abonan varias veces al año y se reinvierten, el rendimiento efectivo del año supera al tipo nominal pactado; si se abonan una sola vez al final, ambos pueden coincidir. La TAE recoge ese efecto y el TIN no. | Cuando la persona pida un ejemplo de la diferencia entre TIN y TAE sin atribuirlo a ninguna entidad. | No afirma que la TAE sea siempre mayor que el TIN; el ejemplo no usa porcentajes ni importes ni se atribuye a un producto real. |
| `interes_misma_base_comparacion` | Dos TAE solo describen alternativas equivalentes si se refieren al mismo plazo, a la misma moneda y a condiciones parecidas de liquidación, cancelación y vinculación. Una TAE de un plazo corto y otra de un plazo largo no miden lo mismo. | Cuando la persona compare ofertas con plazos distintos o pregunte si puede ordenarlas por TAE. | No afirma que la TAE más alta sea la mejor opción ni que una TAE sea aplicable a otro plazo. |
| `interes_compuesto` | El interés compuesto se produce cuando los intereses ya generados también producen intereses en periodos posteriores. Cuanto más frecuente sea la capitalización, más se separa el resultado de aplicar el tipo una sola vez al capital inicial. | Cuando la persona pregunte cómo crece un importe con el tiempo o qué significa capitalización. | No afirma un resultado concreto ni que la capitalización frecuente compense otros costes o riesgos; no da tipos ni plazos. |

### 4.4 Inflación y poder adquisitivo (`inflacion_`)

Nominal frente a real, método de ajuste y límites del escenario.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `inflacion_que_es` | La inflación es la subida general y sostenida de los precios de bienes y servicios. Se mide sobre una cesta representativa, de modo que la inflación que percibe una persona puede diferir de la media. | Cuando la persona pregunte qué es la inflación o cómo le afecta. | No afirma una tasa de inflación concreta ni que la cesta representativa refleje el consumo de una persona determinada. |
| `inflacion_nominal_y_real` | El importe nominal es el que aparece en el saldo o en el contrato; el importe real intenta expresar cuánto se puede comprar con él tras descontar la inflación. Un saldo que no cambia puede perder poder adquisitivo si los precios suben. Ese cálculo real sigue siendo una aproximación, no una medida exacta. | Cuando la persona compare un saldo o una rentabilidad sin ajustar por inflación. | No afirma que el cálculo real sea exacto para una persona concreta ni que la inflación pasada se repita. |
| `inflacion_descontar_no_restar` | Para llevar un importe de un momento a otro en términos de poder adquisitivo se descuenta la inflación acumulada, no se resta un porcentaje suelto del importe. Restar linealmente exagera la pérdida cuando hay varios periodos. | Cuando la persona pida ajustar un importe por inflación o interprete una resta simple como un ajuste correcto. | No afirma que el ajuste por inflación sea una predicción ni que el resultado coincida con lo que la persona podrá comprar. |
| `inflacion_limites_escenario` | Un escenario de inflación es una hipótesis, no un pronóstico: si el supuesto cambia, el resultado cambia. Además, la inflación media no refleja la subida de los bienes que consume una persona en particular. | Cuando se presente un cálculo ajustado por inflación o la persona pregunte si el resultado es lo que va a pasar. | No afirma que la inflación futura vaya a coincidir con el supuesto ni que el resultado sea una previsión. |

### 4.5 Liquidez, plazo y cancelación (`liquidez_`)

Disponibilidad del dinero, vencimiento, penalizaciones y costes.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `liquidez_que_es` | La liquidez es la facilidad para disponer del dinero sin perder valor ni asumir costes relevantes. Un producto puede parecer líquido y tardar en convertirse en efectivo, o hacerlo con penalización. | Cuando la persona pregunte por liquidez, disponibilidad del dinero o qué pasa si necesita el dinero antes. | No afirma que un producto concreto sea líquido ni que la disponibilidad sea inmediata o sin coste. |
| `liquidez_plazo_y_vencimiento` | El plazo es el periodo durante el cual se mantiene la condición; el vencimiento es el momento en que termina. Que una condición tenga fecha de fin no significa que el dinero esté disponible antes ni que la oferta se pueda contratar después. | Cuando la persona confunda plazo, vencimiento y disponibilidad, o pregunte cuándo recupera el dinero. | No afirma que un producto permita cancelar antes del vencimiento ni que el vencimiento coincida con la devolución efectiva. |
| `liquidez_cancelacion_anticipada` | La cancelación anticipada puede ser libre, estar sujeta a una penalización o no estar permitida. También puede ser parcial o total, y el tratamiento de los intereses ya abonados cambia según las condiciones. | Cuando la persona pregunte si puede sacar el dinero antes del plazo o qué le cuesta hacerlo. | No afirma que la cancelación sea gratuita, posible o inmediata en un producto concreto. |
| `liquidez_comisiones_y_penalizaciones` | Comisiones, penalizaciones y gastos pueden reducir el resultado aunque el tipo de interés no cambie. Una rentabilidad anunciada sin esos costes no equivale al resultado neto que recibe la persona. | Cuando se comparen ofertas por su tipo de interés o la persona pregunte cuánto recibirá de verdad. | No afirma que un producto no tenga comisiones ni que el tipo anunciado sea el resultado neto; no da importes. |

### 4.6 Comparar sin recomendar (`comparar_`)

Criterios, base común, datos que faltan y frontera de la recomendación.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `comparar_criterios` | Para comparar alternativas conviene mirar el plazo, la TAE, la frecuencia de pago de intereses, la cancelación anticipada, las comisiones, el importe mínimo, los requisitos de vinculación y la garantía aplicable. Ninguno de esos criterios decide por sí solo: hay que leerlos juntos. | Cuando la persona pida criterios para comparar productos o no sepa qué mirar además del tipo de interés. | No afirma que un criterio sea el más importante ni que la lista sea exhaustiva para cualquier producto. |
| `comparar_misma_base` | Una comparación solo es válida si los datos se refieren al mismo plazo, a la misma moneda y al mismo momento de consulta. Mezclar un dato de hoy con otro de hace meses puede producir una conclusión falsa. | Cuando la persona compare ofertas con plazos o fechas distintas, o pida ordenar productos por una cifra. | No afirma que dos cifras sean comparables por el hecho de estar expresadas en la misma unidad. |
| `comparar_falta_plazo` | Si solo se conoce el plazo de uno de los dos productos, no se puede comparar su rendimiento: falta el plazo del otro y, con él, la base de la comparación. Tampoco se puede suponer que el plazo desconocido sea igual al conocido. | Cuando la persona pida comparar dos productos y solo aporte el plazo de uno. | No afirma que el producto sin plazo sea peor ni que su plazo pueda deducirse del otro. |
| `comparar_sin_mejor_absoluto` | No hay una opción mejor en abstracto: la elección depende del objetivo, del horizonte, de la necesidad de disponer del dinero y de la tolerancia al riesgo de cada persona. Dos productos con la misma TAE pueden ser adecuados para situaciones distintas. | Cuando la persona pregunte qué producto es mejor, cuál elegir o cuál le conviene. | No afirma que exista una opción óptima universal ni que la TAE más alta sea la mejor elección. |
| `comparar_sin_recomendar` | Se pueden explicar criterios y mostrar diferencias, pero no se puede recomendar la contratación de un producto ni de una entidad. La decisión corresponde a la persona, que debe comprobar las condiciones en la documentación aplicable. | Cuando la persona pida una recomendación de contratación o pregunte cuál debe elegir. | No afirma que un producto sea adecuado para una persona concreta ni que la aplicación haya evaluado su perfil. |

### 4.7 Garantía de depósitos (`garantia_`)

Qué protege, con qué límites, qué queda fuera y cómo comprobarlo.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `garantia_de_depositos_que_es` | La garantía de depósitos es una protección legal para depósitos que cumplen ciertos requisitos; no es una garantía general para cualquier producto financiero. Su alcance depende de la legislación aplicable, del tipo de depósito y de la entidad, el país y el titular. | Cuando la persona pregunte qué significa que un depósito esté garantizado o si su dinero está protegido. | No afirma que todos los depósitos estén cubiertos ni que la garantía alcance cualquier importe o producto. |
| `garantia_limite_por_persona` | La cobertura tiene un límite máximo por persona y entidad, y por encima de ese límite el saldo no queda protegido por el sistema de garantía. Repartir el mismo dinero en varias cuentas de la misma entidad no multiplica la cobertura por sí solo. | Cuando la persona pregunte cuánto de su dinero está cubierto o si puede superar el límite repartiendo cuentas. | No afirma una cifra de cobertura ni que el límite sea igual en todos los países o sistemas; no confirma la cobertura de un caso concreto. |
| `garantia_no_cubre_inversiones` | La garantía de depósitos no cubre fondos de inversión, ETF ni valores, aunque se contraten a través de una entidad que también capte depósitos. En esos productos, la protección frente a una caída de valor o un impago es distinta y no equivale a la de un depósito. | Cuando la persona pregunte si la garantía cubre una inversión, un fondo o un producto distinto de un depósito. | No afirma que un fondo esté garantizado por estar comercializado por una entidad de depósitos; no evalúa la solvencia de ninguna entidad. |
| `garantia_frente_a_solvencia` | La solvencia de una entidad y la garantía de depósitos son cosas distintas: la primera describe su capacidad de responder a sus obligaciones; la segunda es una protección con requisitos y límites. Una entidad solvente no sustituye a la garantía, y la garantía no elimina el riesgo de otros productos. | Cuando la persona pregunte si una entidad es segura, si la garantía cubre su dinero o si la solvencia basta. | No afirma que una entidad sea solvente ni que la garantía cubra todo el saldo; no califica de seguro ningún producto. |
| `garantia_como_comprobarla` | Para saber qué protección tiene un depósito hay que comprobar el tipo de producto, el titular, la entidad y el régimen de garantía aplicable en la documentación del producto y en la información del propio régimen. Un resumen de un tercero no permite confirmar esos extremos. | Cuando la persona pregunte por la cobertura de un depósito concreto o por dónde comprobarla. | No afirma que la cobertura esté confirmada para un caso concreto ni que la aplicación haya consultado la documentación. |
| `garantia_capital_garantizado` | Que un producto garantice la devolución del capital al vencimiento no es lo mismo que estar cubierto por un sistema de garantía de depósitos. La primera expresión describe una obligación contractual; la segunda, una protección legal con requisitos y límites. | Cuando la persona lea una expresión como capital garantizado o pregunte si eso equivale a la garantía de depósitos. | No afirma que un producto con capital garantizado esté además cubierto por la garantía de depósitos ni que ambas protecciones sean intercambiables. |

### 4.8 Datos vencidos, fuentes y atribución (`fuente_`)

Por qué un dato caducado no es una oferta y qué exige una atribución.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `fuente_dato_vencido_no_sirve` | Un dato con un periodo de aplicación terminado describe una condición pasada, no una condición que se pueda usar para decidir hoy. Aunque el dato sea correcto como registro histórico, no sirve como oferta ni como base de una comparación. | Cuando la persona aporte un dato con fecha de fin ya pasada o pregunte si puede tratarse como una oferta actual. | No afirma que el dato fuera falso cuando se publicó ni que la condición siga aplicándose; no calcula una oferta sustitutiva. |
| `fuente_vencido_no_se_renueva_solo` | Que una condición haya terminado no permite suponer que se ha prorrogado ni que se ha sustituido por otra equivalente. Para saber qué se aplica después hay que consultar la documentación del producto o preguntar a la entidad. | Cuando la persona pregunte si un dato vencido sigue siendo válido o si la oferta se ha renovado. | No afirma que la condición haya sido renovada, prorrogada ni sustituida; no atribuye una intención a la entidad. |
| `fuente_secundaria_que_es` | Una fuente secundaria es la que resume, comenta o reproduce información de otra fuente: una nota de prensa, un comparador o un blog. Puede ayudar a localizar un dato, pero no es la ficha del producto ni el documento donde la entidad fija las condiciones. | Cuando la persona aporte una noticia, un comparador o un resumen y pregunte si sirve como prueba. | No afirma que toda fuente secundaria sea incorrecta ni que sus datos sean falsos; no identifica medios ni entidades. |
| `fuente_secundaria_no_basta` | Que una fuente secundaria atribuya una tasa o una condición a una entidad no basta para tratarla como la condición aplicable. Para eso hace falta el documento de la entidad, la fecha y el punto concreto donde consta, y comprobar que ese documento no ha sido sustituido. | Cuando la persona pregunte si una fuente secundaria basta para afirmar qué condiciones ofrece una entidad. | No afirma que la fuente secundaria sea oficial ni que la condición atribuida sea la que se aplica; no valida la atribución. |
| `fuente_atribucion_con_prueba` | Atribuir un dato a una entidad exige poder señalar el documento, la fecha y el punto concreto donde aparece; sin esa cadena, la atribución es una afirmación sin respaldo. Repetir un dato citando a un tercero no crea esa cadena. | Cuando la persona pida atribuir una tasa a una entidad o pregunte de dónde sale un dato. | No afirma que una atribución sea verdadera por ser repetida ni que la aplicación haya verificado el documento; no nombra entidades. |

### 4.9 Simulación y cálculo (`simulacion_`)

Hipótesis, supuestos, costes excluidos y convención del tipo.

| ID | Afirmación (`text`) | Cuándo elegirla (`when`) | Qué no afirma (`never_claim`) |
|---|---|---|---|
| `simulacion_es_hipotetica` | Una simulación es un ejercicio hipotético: aplica unos supuestos para mostrar cómo evolucionaría un importe si se cumplieran. No es una predicción, no es una oferta y no garantiza el resultado que se obtendría. | Cuando se muestre un cálculo o la persona pregunte si el resultado es lo que va a ocurrir. | No afirma que el resultado vaya a realizarse ni que la simulación refleje una condición contratable. |
| `simulacion_supuestos` | El resultado de una simulación depende de sus supuestos: el importe inicial, las aportaciones, el plazo, el tipo, la capitalización y la inflación. Cambiar uno de ellos cambia el resultado, y el cálculo no justifica por sí solo el valor elegido. | Cuando se presente un cálculo o la persona pregunte por qué sale una cifra y no otra. | No afirma que los supuestos sean los adecuados para la persona ni que procedan de una oferta real. |
| `simulacion_sin_costes_ni_impuestos` | Una simulación sencilla suele dejar fuera impuestos, comisiones y otros gastos, y no recoge penalizaciones por cancelación. Por eso el resultado bruto no coincide necesariamente con lo que la persona recibiría. | Cuando la persona interprete un resultado simulado como dinero disponible o pregunte si incluye impuestos y comisiones. | No afirma que el resultado incluya todos los costes ni que sea un importe neto; no calcula impuestos. |
| `simulacion_convencion_del_tipo` | La forma de convertir un tipo anual en un tipo por periodo cambia el resultado: no es lo mismo dividir el tipo entre los periodos que aplicar la equivalencia compuesta. Una simulación debe declarar qué convención usa para que el número se pueda interpretar. | Cuando la persona pregunte cómo se ha convertido el tipo anual o compare dos cálculos con resultados distintos. | No afirma que una convención sea la correcta para todos los productos ni que el resultado sea el que aplicaría la entidad. |

## 5. Cobertura de las diez preguntas

La columna «Cómo evita la prosa libre» señala qué parte de la respuesta queda cerrada y qué parte, si la hay, debe venir del motor o de la capa de condiciones.

| Pregunta | Qué pide | Afirmaciones que la cubren | Cómo evita la prosa libre |
|---|---|---|---|
| P1 | Ahorro e inversión: diferencia y riesgos de cada uno. | `ahorro_frente_a_inversion`<br>`ahorro_riesgo_inflacion`<br>`ahorro_riesgos_de_invertir`<br>`inflacion_nominal_y_real` | Define ambos términos y separa riesgos; no nombra productos ni promete rentabilidad. |
| P2 | TIN y TAE: diferencia y ejemplo hipotético sin atribución. | `interes_tin_nominal`<br>`interes_tae_equivalente`<br>`interes_ejemplo_tin_tae`<br>`interes_misma_base_comparacion`<br>`interes_compuesto` | Dos definiciones y un ejemplo conceptual con palabras; si se quiere un ejemplo numérico, tendría que venir del motor como simulación etiquetada, no del catálogo. |
| P3 | Inflación y poder adquisitivo en un escenario ficticio. | `inflacion_que_es`<br>`inflacion_nominal_y_real`<br>`inflacion_descontar_no_restar`<br>`inflacion_limites_escenario`<br>`simulacion_supuestos` | Explica el método de ajuste y sus límites; el número sale del motor con sus supuestos visibles. |
| P4 | Liquidez y cancelación antes de elegir un depósito. | `liquidez_que_es`<br>`liquidez_plazo_y_vencimiento`<br>`liquidez_cancelacion_anticipada`<br>`liquidez_comisiones_y_penalizaciones`<br>`garantia_de_depositos_que_es`<br>`garantia_frente_a_solvencia` | Cubre disponibilidad, vencimiento, cancelación, costes y la diferencia entre garantía y solvencia. |
| P5 | Comparar alternativas sin recomendar contratación. | `comparar_criterios`<br>`comparar_misma_base`<br>`comparar_sin_mejor_absoluto`<br>`comparar_sin_recomendar`<br>`interes_misma_base_comparacion`<br>`liquidez_comisiones_y_penalizaciones` | Da criterios, exige base común y cierra la frontera de la recomendación sin ordenar productos. |
| P6 | Datos que faltan para comparar dos depósitos. | `comparar_falta_plazo`<br>`alcance_datos_que_faltan`<br>`comparar_criterios`<br>`comparar_misma_base`<br>`liquidez_plazo_y_vencimiento` | Declara que sin el plazo del segundo no hay comparación y pide el dato en vez de suponerlo. |
| P7 | Garantía de depósitos y comprobación en la documentación. | `garantia_de_depositos_que_es`<br>`garantia_limite_por_persona`<br>`garantia_no_cubre_inversiones`<br>`garantia_frente_a_solvencia`<br>`garantia_como_comprobarla`<br>`garantia_capital_garantizado` | Explica qué protege la garantía, sus límites y dónde comprobarla; no afirma cobertura de un caso. |
| P8 | Dato vencido presentado como oferta actual. | `fuente_dato_vencido_no_sirve`<br>`fuente_vencido_no_se_renueva_solo`<br>`alcance_datos_que_faltan`<br>`comparar_misma_base` | Trata el dato caducado como registro histórico y bloquea la inferencia de renovación. |
| P9 | Fuente secundaria y atribución. | `fuente_secundaria_que_es`<br>`fuente_secundaria_no_basta`<br>`fuente_atribucion_con_prueba`<br>`garantia_como_comprobarla`<br>`comparar_misma_base` | Define fuente secundaria, niega que baste y exige documento, fecha y localización. |
| P10 | Escenario compuesto a dos años: supuestos y límites. | `simulacion_es_hipotetica`<br>`simulacion_supuestos`<br>`simulacion_sin_costes_ni_impuestos`<br>`simulacion_convencion_del_tipo`<br>`interes_compuesto` | Declara hipótesis, supuestos, costes excluidos y convención del tipo; el resultado es del motor. |

## 6. Casos límite: afirmaciones que NO deben existir

Esta sección es la lista negra del catálogo. Ninguna de estas formulaciones puede convertirse en una entrada editorial, aunque sea tentadora o aunque el usuario la pida. Si el dato existe, se renderiza desde la capa de condiciones con su fuente, su clase y su fecha; si no existe, la respuesta correcta es decir que falta.

| # | Formulación que no debe existir | Por qué | Dónde viviría, si es un dato |
|---|---|---|---|
| 1 | Este depósito es la mejor opción para ti. | Recomendación personalizada: la puerta no compensable. Exige perfil, idoneidad y responsabilidad que el catálogo no tiene. | En ningún sitio. |
| 2 | Te recomiendo contratar el producto de esta entidad. | Recomendación de contratación y nombre de entidad en la misma frase. | En ningún sitio. |
| 3 | El capital está protegido en caso de insolvencia. | Es la casi-puerta de P4: protección sin límite de cobertura. La solvencia no sustituye a la garantía. | Se parte en garantia_de_depositos_que_es y garantia_frente_a_solvencia. |
| 4 | El capital está garantizado al cien por cien. | Garantía absoluta y cifra; la cobertura depende del producto, el titular y el límite. | Capa de condiciones, solo si la ficha lo dice y con su fecha. |
| 5 | Los depósitos están cubiertos hasta una cifra concreta. | Importe y jurisdicción; no es una explicación general. | Capa de condiciones, con fuente y fecha. |
| 6 | Este producto no tiene riesgo / es seguro. | Garantía absoluta o ausencia de riesgo sin fundamento. Ningún producto la sostiene. | En ningún sitio. |
| 7 | La oferta sigue vigente / la fuente es oficial. | Atribución y vigencia: solo un documento fechado puede sostenerlo, y el catálogo no lo consulta. | Capa de condiciones, con clase de fuente, fecha y periodo. |
| 8 | La TAE de este producto es la más alta del mercado. | Superlativo comparativo que exige un universo completo y una fecha; además empuja a recomendar. | En ningún sitio. |
| 9 | El TIN siempre es menor que la TAE. | Generalización falsa: pueden coincidir si el pago es anual y no hay gastos que la TAE incorpore. | Se sustituye por interes_ejemplo_tin_tae. |
| 10 | Si el plazo venció, la oferta se renueva. | Inferencia sin documento; la entidad no ha dicho que renueve. | En ningún sitio; como mucho, fuente_vencido_no_se_renueva_solo. |
| 11 | El dato vencido del ejemplo sigue siendo la referencia. | Repite una cifra y trata un dato caducado como base de decisión. | En ningún sitio; la respuesta usa fuente_dato_vencido_no_sirve sin repetir la cifra. |
| 12 | Una fuente secundaria es fiable si el medio es conocido. | Heurística de credibilidad que no es una cadena de atribución. | En ningún sitio; se usa fuente_atribucion_con_prueba. |
| 13 | La garantía de depósitos cubre fondos de inversión y ETF. | Alcance falso: la garantía no es general para productos de inversión. | En ningún sitio. |
| 14 | La solvencia de la entidad garantiza el capital. | Sustituye la garantía legal por solvencia; es el defecto de fondo que la evaluación señala en P4. | Se parte en garantia_de_depositos_que_es y garantia_frente_a_solvencia. |
| 15 | Esta simulación muestra lo que ganarás. | Predicción encubierta; la simulación es hipotética y depende de supuestos. | En ningún sitio; se usa simulacion_es_hipotetica. |
| 16 | El resultado ya incluye impuestos y comisiones. | El motor no los calcula; afirmarlo convierte una omisión en un dato. | En ningún sitio; se usa simulacion_sin_costes_ni_impuestos. |
| 17 | La aplicación ha revisado la ficha y confirma las condiciones. | Afirmación falsa sobre el proceso: no hay revisión de la ficha ni verificación humana. | En ningún sitio. |
| 18 | Este depósito no tiene comisiones / puedes cancelar cuando quieras. | Dato de producto concreto; comisiones y cancelación cambian por ficha. | Capa de condiciones, con la cláusula exacta. |
| 19 | Los depósitos son la opción más segura para ahorrar. | Recomendación y superlativo de seguridad; no hay una opción universal. | En ningún sitio. |
| 20 | La TAE incluye todos los gastos. | Falso: incorpora ciertos gastos bajo supuestos, no todos. | Se sustituye por interes_tae_equivalente y liquidez_comisiones_y_penalizaciones. |
| 21 | El dato del ejemplo no es una oferta vigente. | La conclusión es correcta, pero el texto usa el token de vigencia y repite la formulación del enunciado. El catálogo dice lo mismo sin ese token. | Se sustituye por fuente_dato_vencido_no_sirve. |
| 22 | Una fuente secundaria no es oficial. | La conclusión es correcta, pero el token «oficial» vuelve a disparar la revisión léxica y no explica la cadena de atribución. | Se sustituye por fuente_secundaria_no_basta y fuente_atribucion_con_prueba. |
| 23 | La TAE más alta es siempre la mejor opción. | Confunde un criterio con una decisión: ignora plazo, liquidez, riesgo, garantía y necesidades de la persona. | Se sustituye por comparar_sin_mejor_absoluto y comparar_criterios. |
| 24 | Se pueden comparar dos depósitos aunque solo se conozca el plazo de uno. | Falta la base de la comparación; el resultado sería una falsa equivalencia entre plazos distintos. | Se sustituye por comparar_falta_plazo y alcance_datos_que_faltan. |
| 25 | A la inflación se le resta el porcentaje al importe. | Método lineal que exagera la pérdida cuando hay varios periodos; el ajuste correcto descuenta la inflación acumulada. | Se sustituye por inflacion_descontar_no_restar. |

### 6.1 Regla de división

Una formulación insegura no se arregla añadiendo un «pero»: se parte en dos afirmaciones que el servidor pueda sostener por separado.

- «El capital está protegido en caso de insolvencia» → `garantia_de_depositos_que_es` (qué es la protección) + `garantia_frente_a_solvencia` (solvencia no es garantía).
- «La TAE es lo que recibirás» → `interes_tae_equivalente` (qué resume) + `liquidez_comisiones_y_penalizaciones` (costes que pueden reducir el neto).
- «El dato del ejemplo no es una oferta vigente» → `fuente_dato_vencido_no_sirve`, sin repetir la cifra ni el token de vigencia: la afirmación dice que un periodo terminado no sirve para decidir hoy.
- «Este producto es seguro» → `ahorro_frente_a_inversion` (qué significa ahorrar) + `ahorro_riesgos_de_invertir` (qué riesgos existen); no se califica el producto.

### 6.2 Lo que el catálogo no puede hacer

- No verifica la ficha de un producto ni la fecha de una condición. Eso es la capa de condiciones.
- No convierte una explicación general en asesoramiento personalizado. La puerta de recomendación sigue siendo no compensable.
- No acredita revisión de profesores, reguladores ni profesionales. Los textos son edición local de esta misión, como ya advierte el contrato del modo estructurado.
- No sustituye la revisión humana de las respuestas: da una lista cerrada y comprobable, no una verdad financiera.

## 7. Verificación mecánica

El documento se genera desde un único diccionario: la tabla y el JSON no pueden divergir. Estas son las comprobaciones ejecutadas sobre los campos `text` (no sobre el resto del documento, que contiene cifras de conteo y referencias).

| Comprobación | Resultado |
|---|---|
| Entradas en el catálogo | 39 (rango exigido: 25-40) |
| Grupos temáticos | 9 |
| IDs únicos y en snake_case | 39 únicos; 39/39 cumplen el patrón |
| `text` con dígitos | 0 casos |
| `text` con `%`, `€`, `$` o `£` | 0 casos |
| `text` con términos de atribución o vigencia | 0 casos |
| `text` con nombres de entidades o países del catálogo de condiciones | 0 casos |
| Frases por `text` | mínimo 2, máximo 3 (límite: 1-3) |
| `when` presente y con disparador «Cuando» | 39/39 |
| `never_claim` presente y con «No afirma» | 39/39 |
| Textos duplicados | 0 |
| Cobertura de P1-P10 | 10/10 preguntas; mínimo 4 afirmaciones por pregunta |
| JSON válido y round-trip | sí; `json.loads(json.dumps(payload)) == payload` |

## 8. Notas de integración

**Versión.** El diccionario actual es `paideia-education-v1` con cinco IDs. Este catálogo no es compatible hacia atrás: los cinco IDs antiguos desaparecen y una selección `v1` válida dejaría de serlo. Se propone `paideia-education-v2` y rechazar cualquier selección con la versión anterior antes de resolver IDs. Si se necesita compatibilidad temporal, mantener un mapa explícito y validarlo, no reutilizar `v1` con otro diccionario.

| ID antiguo (`v1`) | Cobertura en `v2` |
|---|---|
| `saving_investing` | `ahorro_frente_a_inversion` |
| `risk` | `ahorro_riesgos_de_invertir` |
| `inflation` | `inflacion_que_es` + `inflacion_nominal_y_real` |
| `guarantees` | `garantia_de_depositos_que_es` + `garantia_limite_por_persona` |
| `simulation` | `simulacion_es_hipotetica` + `simulacion_supuestos` |

**Límite de selección.** El esquema actual permite cinco IDs por turno. El catálogo no cambia el esquema, pero algunas preguntas (P4 y P7) tienen seis afirmaciones pertinentes. Hay que decidir explícitamente: mantener cinco y priorizar, o subir el límite con una prueba nueva. Lo que no conviene es dejar que el máximo sea `len(EDITORIAL)`: al crecer el diccionario, ese número deja de expresar la intención de producto. Mejor un `MAX_CLAIMS` separado.

**Renderizado.** Unir los `text` seleccionados con un separador de párrafo, en el orden devuelto, sin interpolar nombres, cifras ni datos del usuario. Rechazar IDs desconocidos, listas vacías y duplicados. El servidor sigue siendo el único que compone la respuesta; el proveedor solo elige.

**Datos de producto.** Las tasas, plazos, importes, coberturas, clases de fuente y fechas se muestran desde `condiciones.json` y `catalogue_conditions.py`, con su estado (`known`, `unknown`, `conflict`, `stale`) y su clase de fuente. Este catálogo no duplica esa capa ni la sustituye.

**Pruebas sugeridas.** (a) Ningún `text` contiene dígitos, `%`, `€`, «oficial», «vigente», «vigencia», «en vigor» ni nombres de entidades o productos. (b) Todo ID seleccionado existe en la versión declarada. (c) Cada pregunta de la rúbrica tiene al menos tres afirmaciones disponibles. (d) Un `never_claim` se convierte en una comprobación de revisión, no en una frase renderizable. (e) El renderizador no acepta texto del proveedor, solo IDs.

## 9. Bloque JSON

Copia directa a código. La forma es exactamente `{id: {text, when, never_claim}}`; no hay campos adicionales. El orden de las claves es el orden de renderizado propuesto. La versión no va dentro del bloque: se mantiene como constante del módulo, igual que ahora, y se valida antes de resolver IDs.

```json
{
  "alcance_educativo_sin_asesoramiento": {
    "text": "Esta explicación es educativa: ayuda a entender conceptos y a leer condiciones, pero no es asesoramiento financiero, fiscal ni jurídico personalizado. Una explicación general no tiene en cuenta la situación, los objetivos ni la tolerancia al riesgo de quien la lee.",
    "when": "Cuando la persona pida una recomendación, pregunte qué producto elegir o pueda interpretar la respuesta como un consejo personalizado.",
    "never_claim": "No afirma que la aplicación sea un asesor registrado ni que su respuesta sustituya a un profesional; no recomienda contratar ningún producto ni elegir una entidad concreta."
  },
  "alcance_datos_que_faltan": {
    "text": "Cuando faltan datos para responder, lo correcto es decir que no se puede concluir con esa información y señalar qué falta. Rellenar el hueco con un supuesto no convierte el supuesto en un dato del producto.",
    "when": "Cuando la respuesta dependa de una condición que no consta, como el plazo de uno de los productos, el periodo de aplicación de la condición o el tipo aplicable.",
    "never_claim": "No afirma que un dato ausente sea deducible del contexto ni que un supuesto razonable equivalga a una condición documentada."
  },
  "alcance_no_confirma_condiciones": {
    "text": "Una explicación educativa no confirma las condiciones de un producto concreto. Para saber qué se aplica en el momento de decidir hay que leer la documentación del producto y comprobar a qué periodo se refiere.",
    "when": "Cuando la persona pregunte por una condición concreta de un producto o por lo que puede contratar ahora.",
    "never_claim": "No afirma que la aplicación haya consultado la ficha, que el dato siga aplicándose ni que la explicación refleje una oferta comercial."
  },
  "ahorro_frente_a_inversion": {
    "text": "Ahorrar es apartar dinero para usarlo más adelante; invertir es poner ese dinero a trabajar aceptando que su valor puede subir o bajar. El ahorro prioriza la disponibilidad; la inversión acepta variaciones de valor a cambio de un rendimiento esperado.",
    "when": "Cuando la persona pregunte por la diferencia entre ahorro e inversión o quiera situar su objetivo en uno de los dos.",
    "never_claim": "No afirma que ahorrar esté exento de riesgo ni que invertir garantice un rendimiento; no califica ningún producto como seguro."
  },
  "ahorro_riesgo_inflacion": {
    "text": "El ahorro conserva el importe nominal, pero no protege por sí solo del efecto de la inflación: si los precios suben más que la remuneración, el dinero compra menos. Esa pérdida de poder adquisitivo puede no aparecer en el saldo.",
    "when": "Cuando se hable de ahorro, cuentas remuneradas o depósitos y la persona pregunte si su dinero está protegido.",
    "never_claim": "No afirma que la inflación vaya a superar a un tipo concreto ni que el ahorro pierda valor siempre; no da cifras de inflación."
  },
  "ahorro_riesgos_de_invertir": {
    "text": "El riesgo es la posibilidad de que el resultado difiera de lo esperado, incluida la pérdida de parte o todo el capital invertido. En una inversión no viene solo de que el precio baje: también influyen la solvencia del emisor, la liquidez para vender, la custodia del activo y las condiciones del producto. Repartir el dinero entre varios activos puede reducir el impacto de un mal resultado aislado, pero no elimina el riesgo de mercado ni garantiza conservar el capital.",
    "when": "Cuando la persona pregunte qué riesgos tiene invertir o qué debe mirar además de la rentabilidad.",
    "never_claim": "No afirma que un producto tenga una calificación de riesgo concreta, que diversificar elimine las pérdidas ni que diversificar garantice conservar el capital."
  },
  "interes_tin_nominal": {
    "text": "El TIN es el tipo de interés nominal pactado: expresa el porcentaje de interés sobre el capital sin incorporar por sí mismo la frecuencia de los pagos ni todos los gastos. Dos productos con el mismo TIN pueden producir resultados distintos si cambia la forma de liquidar los intereses.",
    "when": "Cuando la persona pregunte qué es el TIN o compare dos ofertas que solo muestran ese dato.",
    "never_claim": "No afirma que el TIN sea el rendimiento efectivo ni que dos TIN iguales impliquen el mismo resultado; no da tipos concretos."
  },
  "interes_tae_equivalente": {
    "text": "La TAE es la tasa anual equivalente: resume el coste o el rendimiento anual bajo unos supuestos, incorporando la frecuencia de los pagos y ciertos gastos. Sirve para comparar, pero no describe por sí sola todas las condiciones del producto.",
    "when": "Cuando la persona pregunte qué es la TAE o por qué se usa para comparar ofertas.",
    "never_claim": "No afirma que la TAE incluya todos los costes ni que coincida con lo que la persona recibirá; no da valores ni compara entidades."
  },
  "interes_ejemplo_tin_tae": {
    "text": "Ejemplo conceptual: si los intereses se abonan varias veces al año y se reinvierten, el rendimiento efectivo del año supera al tipo nominal pactado; si se abonan una sola vez al final, ambos pueden coincidir. La TAE recoge ese efecto y el TIN no.",
    "when": "Cuando la persona pida un ejemplo de la diferencia entre TIN y TAE sin atribuirlo a ninguna entidad.",
    "never_claim": "No afirma que la TAE sea siempre mayor que el TIN; el ejemplo no usa porcentajes ni importes ni se atribuye a un producto real."
  },
  "interes_misma_base_comparacion": {
    "text": "Dos TAE solo describen alternativas equivalentes si se refieren al mismo plazo, a la misma moneda y a condiciones parecidas de liquidación, cancelación y vinculación. Una TAE de un plazo corto y otra de un plazo largo no miden lo mismo.",
    "when": "Cuando la persona compare ofertas con plazos distintos o pregunte si puede ordenarlas por TAE.",
    "never_claim": "No afirma que la TAE más alta sea la mejor opción ni que una TAE sea aplicable a otro plazo."
  },
  "interes_compuesto": {
    "text": "El interés compuesto se produce cuando los intereses ya generados también producen intereses en periodos posteriores. Cuanto más frecuente sea la capitalización, más se separa el resultado de aplicar el tipo una sola vez al capital inicial.",
    "when": "Cuando la persona pregunte cómo crece un importe con el tiempo o qué significa capitalización.",
    "never_claim": "No afirma un resultado concreto ni que la capitalización frecuente compense otros costes o riesgos; no da tipos ni plazos."
  },
  "inflacion_que_es": {
    "text": "La inflación es la subida general y sostenida de los precios de bienes y servicios. Se mide sobre una cesta representativa, de modo que la inflación que percibe una persona puede diferir de la media.",
    "when": "Cuando la persona pregunte qué es la inflación o cómo le afecta.",
    "never_claim": "No afirma una tasa de inflación concreta ni que la cesta representativa refleje el consumo de una persona determinada."
  },
  "inflacion_nominal_y_real": {
    "text": "El importe nominal es el que aparece en el saldo o en el contrato; el importe real intenta expresar cuánto se puede comprar con él tras descontar la inflación. Un saldo que no cambia puede perder poder adquisitivo si los precios suben. Ese cálculo real sigue siendo una aproximación, no una medida exacta.",
    "when": "Cuando la persona compare un saldo o una rentabilidad sin ajustar por inflación.",
    "never_claim": "No afirma que el cálculo real sea exacto para una persona concreta ni que la inflación pasada se repita."
  },
  "inflacion_descontar_no_restar": {
    "text": "Para llevar un importe de un momento a otro en términos de poder adquisitivo se descuenta la inflación acumulada, no se resta un porcentaje suelto del importe. Restar linealmente exagera la pérdida cuando hay varios periodos.",
    "when": "Cuando la persona pida ajustar un importe por inflación o interprete una resta simple como un ajuste correcto.",
    "never_claim": "No afirma que el ajuste por inflación sea una predicción ni que el resultado coincida con lo que la persona podrá comprar."
  },
  "inflacion_limites_escenario": {
    "text": "Un escenario de inflación es una hipótesis, no un pronóstico: si el supuesto cambia, el resultado cambia. Además, la inflación media no refleja la subida de los bienes que consume una persona en particular.",
    "when": "Cuando se presente un cálculo ajustado por inflación o la persona pregunte si el resultado es lo que va a pasar.",
    "never_claim": "No afirma que la inflación futura vaya a coincidir con el supuesto ni que el resultado sea una previsión."
  },
  "liquidez_que_es": {
    "text": "La liquidez es la facilidad para disponer del dinero sin perder valor ni asumir costes relevantes. Un producto puede parecer líquido y tardar en convertirse en efectivo, o hacerlo con penalización.",
    "when": "Cuando la persona pregunte por liquidez, disponibilidad del dinero o qué pasa si necesita el dinero antes.",
    "never_claim": "No afirma que un producto concreto sea líquido ni que la disponibilidad sea inmediata o sin coste."
  },
  "liquidez_plazo_y_vencimiento": {
    "text": "El plazo es el periodo durante el cual se mantiene la condición; el vencimiento es el momento en que termina. Que una condición tenga fecha de fin no significa que el dinero esté disponible antes ni que la oferta se pueda contratar después.",
    "when": "Cuando la persona confunda plazo, vencimiento y disponibilidad, o pregunte cuándo recupera el dinero.",
    "never_claim": "No afirma que un producto permita cancelar antes del vencimiento ni que el vencimiento coincida con la devolución efectiva."
  },
  "liquidez_cancelacion_anticipada": {
    "text": "La cancelación anticipada puede ser libre, estar sujeta a una penalización o no estar permitida. También puede ser parcial o total, y el tratamiento de los intereses ya abonados cambia según las condiciones.",
    "when": "Cuando la persona pregunte si puede sacar el dinero antes del plazo o qué le cuesta hacerlo.",
    "never_claim": "No afirma que la cancelación sea gratuita, posible o inmediata en un producto concreto."
  },
  "liquidez_comisiones_y_penalizaciones": {
    "text": "Comisiones, penalizaciones y gastos pueden reducir el resultado aunque el tipo de interés no cambie. Una rentabilidad anunciada sin esos costes no equivale al resultado neto que recibe la persona.",
    "when": "Cuando se comparen ofertas por su tipo de interés o la persona pregunte cuánto recibirá de verdad.",
    "never_claim": "No afirma que un producto no tenga comisiones ni que el tipo anunciado sea el resultado neto; no da importes."
  },
  "comparar_criterios": {
    "text": "Para comparar alternativas conviene mirar el plazo, la TAE, la frecuencia de pago de intereses, la cancelación anticipada, las comisiones, el importe mínimo, los requisitos de vinculación y la garantía aplicable. Ninguno de esos criterios decide por sí solo: hay que leerlos juntos.",
    "when": "Cuando la persona pida criterios para comparar productos o no sepa qué mirar además del tipo de interés.",
    "never_claim": "No afirma que un criterio sea el más importante ni que la lista sea exhaustiva para cualquier producto."
  },
  "comparar_misma_base": {
    "text": "Una comparación solo es válida si los datos se refieren al mismo plazo, a la misma moneda y al mismo momento de consulta. Mezclar un dato de hoy con otro de hace meses puede producir una conclusión falsa.",
    "when": "Cuando la persona compare ofertas con plazos o fechas distintas, o pida ordenar productos por una cifra.",
    "never_claim": "No afirma que dos cifras sean comparables por el hecho de estar expresadas en la misma unidad."
  },
  "comparar_falta_plazo": {
    "text": "Si solo se conoce el plazo de uno de los dos productos, no se puede comparar su rendimiento: falta el plazo del otro y, con él, la base de la comparación. Tampoco se puede suponer que el plazo desconocido sea igual al conocido.",
    "when": "Cuando la persona pida comparar dos productos y solo aporte el plazo de uno.",
    "never_claim": "No afirma que el producto sin plazo sea peor ni que su plazo pueda deducirse del otro."
  },
  "comparar_sin_mejor_absoluto": {
    "text": "No hay una opción mejor en abstracto: la elección depende del objetivo, del horizonte, de la necesidad de disponer del dinero y de la tolerancia al riesgo de cada persona. Dos productos con la misma TAE pueden ser adecuados para situaciones distintas.",
    "when": "Cuando la persona pregunte qué producto es mejor, cuál elegir o cuál le conviene.",
    "never_claim": "No afirma que exista una opción óptima universal ni que la TAE más alta sea la mejor elección."
  },
  "comparar_sin_recomendar": {
    "text": "Se pueden explicar criterios y mostrar diferencias, pero no se puede recomendar la contratación de un producto ni de una entidad. La decisión corresponde a la persona, que debe comprobar las condiciones en la documentación aplicable.",
    "when": "Cuando la persona pida una recomendación de contratación o pregunte cuál debe elegir.",
    "never_claim": "No afirma que un producto sea adecuado para una persona concreta ni que la aplicación haya evaluado su perfil."
  },
  "garantia_de_depositos_que_es": {
    "text": "La garantía de depósitos es una protección legal para depósitos que cumplen ciertos requisitos; no es una garantía general para cualquier producto financiero. Su alcance depende de la legislación aplicable, del tipo de depósito y de la entidad, el país y el titular.",
    "when": "Cuando la persona pregunte qué significa que un depósito esté garantizado o si su dinero está protegido.",
    "never_claim": "No afirma que todos los depósitos estén cubiertos ni que la garantía alcance cualquier importe o producto."
  },
  "garantia_limite_por_persona": {
    "text": "La cobertura tiene un límite máximo por persona y entidad, y por encima de ese límite el saldo no queda protegido por el sistema de garantía. Repartir el mismo dinero en varias cuentas de la misma entidad no multiplica la cobertura por sí solo.",
    "when": "Cuando la persona pregunte cuánto de su dinero está cubierto o si puede superar el límite repartiendo cuentas.",
    "never_claim": "No afirma una cifra de cobertura ni que el límite sea igual en todos los países o sistemas; no confirma la cobertura de un caso concreto."
  },
  "garantia_no_cubre_inversiones": {
    "text": "La garantía de depósitos no cubre fondos de inversión, ETF ni valores, aunque se contraten a través de una entidad que también capte depósitos. En esos productos, la protección frente a una caída de valor o un impago es distinta y no equivale a la de un depósito.",
    "when": "Cuando la persona pregunte si la garantía cubre una inversión, un fondo o un producto distinto de un depósito.",
    "never_claim": "No afirma que un fondo esté garantizado por estar comercializado por una entidad de depósitos; no evalúa la solvencia de ninguna entidad."
  },
  "garantia_frente_a_solvencia": {
    "text": "La solvencia de una entidad y la garantía de depósitos son cosas distintas: la primera describe su capacidad de responder a sus obligaciones; la segunda es una protección con requisitos y límites. Una entidad solvente no sustituye a la garantía, y la garantía no elimina el riesgo de otros productos.",
    "when": "Cuando la persona pregunte si una entidad es segura, si la garantía cubre su dinero o si la solvencia basta.",
    "never_claim": "No afirma que una entidad sea solvente ni que la garantía cubra todo el saldo; no califica de seguro ningún producto."
  },
  "garantia_como_comprobarla": {
    "text": "Para saber qué protección tiene un depósito hay que comprobar el tipo de producto, el titular, la entidad y el régimen de garantía aplicable en la documentación del producto y en la información del propio régimen. Un resumen de un tercero no permite confirmar esos extremos.",
    "when": "Cuando la persona pregunte por la cobertura de un depósito concreto o por dónde comprobarla.",
    "never_claim": "No afirma que la cobertura esté confirmada para un caso concreto ni que la aplicación haya consultado la documentación."
  },
  "garantia_capital_garantizado": {
    "text": "Que un producto garantice la devolución del capital al vencimiento no es lo mismo que estar cubierto por un sistema de garantía de depósitos. La primera expresión describe una obligación contractual; la segunda, una protección legal con requisitos y límites.",
    "when": "Cuando la persona lea una expresión como capital garantizado o pregunte si eso equivale a la garantía de depósitos.",
    "never_claim": "No afirma que un producto con capital garantizado esté además cubierto por la garantía de depósitos ni que ambas protecciones sean intercambiables."
  },
  "fuente_dato_vencido_no_sirve": {
    "text": "Un dato con un periodo de aplicación terminado describe una condición pasada, no una condición que se pueda usar para decidir hoy. Aunque el dato sea correcto como registro histórico, no sirve como oferta ni como base de una comparación.",
    "when": "Cuando la persona aporte un dato con fecha de fin ya pasada o pregunte si puede tratarse como una oferta actual.",
    "never_claim": "No afirma que el dato fuera falso cuando se publicó ni que la condición siga aplicándose; no calcula una oferta sustitutiva."
  },
  "fuente_vencido_no_se_renueva_solo": {
    "text": "Que una condición haya terminado no permite suponer que se ha prorrogado ni que se ha sustituido por otra equivalente. Para saber qué se aplica después hay que consultar la documentación del producto o preguntar a la entidad.",
    "when": "Cuando la persona pregunte si un dato vencido sigue siendo válido o si la oferta se ha renovado.",
    "never_claim": "No afirma que la condición haya sido renovada, prorrogada ni sustituida; no atribuye una intención a la entidad."
  },
  "fuente_secundaria_que_es": {
    "text": "Una fuente secundaria es la que resume, comenta o reproduce información de otra fuente: una nota de prensa, un comparador o un blog. Puede ayudar a localizar un dato, pero no es la ficha del producto ni el documento donde la entidad fija las condiciones.",
    "when": "Cuando la persona aporte una noticia, un comparador o un resumen y pregunte si sirve como prueba.",
    "never_claim": "No afirma que toda fuente secundaria sea incorrecta ni que sus datos sean falsos; no identifica medios ni entidades."
  },
  "fuente_secundaria_no_basta": {
    "text": "Que una fuente secundaria atribuya una tasa o una condición a una entidad no basta para tratarla como la condición aplicable. Para eso hace falta el documento de la entidad, la fecha y el punto concreto donde consta, y comprobar que ese documento no ha sido sustituido.",
    "when": "Cuando la persona pregunte si una fuente secundaria basta para afirmar qué condiciones ofrece una entidad.",
    "never_claim": "No afirma que la fuente secundaria sea oficial ni que la condición atribuida sea la que se aplica; no valida la atribución."
  },
  "fuente_atribucion_con_prueba": {
    "text": "Atribuir un dato a una entidad exige poder señalar el documento, la fecha y el punto concreto donde aparece; sin esa cadena, la atribución es una afirmación sin respaldo. Repetir un dato citando a un tercero no crea esa cadena.",
    "when": "Cuando la persona pida atribuir una tasa a una entidad o pregunte de dónde sale un dato.",
    "never_claim": "No afirma que una atribución sea verdadera por ser repetida ni que la aplicación haya verificado el documento; no nombra entidades."
  },
  "simulacion_es_hipotetica": {
    "text": "Una simulación es un ejercicio hipotético: aplica unos supuestos para mostrar cómo evolucionaría un importe si se cumplieran. No es una predicción, no es una oferta y no garantiza el resultado que se obtendría.",
    "when": "Cuando se muestre un cálculo o la persona pregunte si el resultado es lo que va a ocurrir.",
    "never_claim": "No afirma que el resultado vaya a realizarse ni que la simulación refleje una condición contratable."
  },
  "simulacion_supuestos": {
    "text": "El resultado de una simulación depende de sus supuestos: el importe inicial, las aportaciones, el plazo, el tipo, la capitalización y la inflación. Cambiar uno de ellos cambia el resultado, y el cálculo no justifica por sí solo el valor elegido.",
    "when": "Cuando se presente un cálculo o la persona pregunte por qué sale una cifra y no otra.",
    "never_claim": "No afirma que los supuestos sean los adecuados para la persona ni que procedan de una oferta real."
  },
  "simulacion_sin_costes_ni_impuestos": {
    "text": "Una simulación sencilla suele dejar fuera impuestos, comisiones y otros gastos, y no recoge penalizaciones por cancelación. Por eso el resultado bruto no coincide necesariamente con lo que la persona recibiría.",
    "when": "Cuando la persona interprete un resultado simulado como dinero disponible o pregunte si incluye impuestos y comisiones.",
    "never_claim": "No afirma que el resultado incluya todos los costes ni que sea un importe neto; no calcula impuestos."
  },
  "simulacion_convencion_del_tipo": {
    "text": "La forma de convertir un tipo anual en un tipo por periodo cambia el resultado: no es lo mismo dividir el tipo entre los periodos que aplicar la equivalencia compuesta. Una simulación debe declarar qué convención usa para que el número se pueda interpretar.",
    "when": "Cuando la persona pregunte cómo se ha convertido el tipo anual o compare dos cálculos con resultados distintos.",
    "never_claim": "No afirma que una convención sea la correcta para todos los productos ni que el resultado sea el que aplicaría la entidad."
  }
}
```
