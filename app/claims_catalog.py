"""Catálogo cerrado de afirmaciones editoriales de Pai (versión v2).

Copia literal del bloque JSON de ``docs/pai-afirmaciones/CATALOGO.md`` §9.
No contiene lógica ni efectos: solo datos inmutables. ``text`` es lo único
renderizable; ``when`` y ``never_claim`` son material de revisión editorial.
"""
from types import MappingProxyType

VERSION = "paideia-education-v2"
MAX_CLAIMS = 6

_EDITORIAL = {
    "alcance_educativo_sin_asesoramiento": {
        "text": "Esta explicación es educativa: ayuda a entender conceptos y a leer condiciones, pero no es asesoramiento financiero, fiscal ni jurídico personalizado. Una explicación general no tiene en cuenta la situación, los objetivos ni la tolerancia al riesgo de quien la lee.",
        "when": "Cuando la persona pida una recomendación, pregunte qué producto elegir o pueda interpretar la respuesta como un consejo personalizado.",
        "never_claim": "No afirma que la aplicación sea un asesor registrado ni que su respuesta sustituya a un profesional; no recomienda contratar ningún producto ni elegir una entidad concreta.",
    },
    "alcance_datos_que_faltan": {
        "text": "Cuando faltan datos para responder, lo correcto es decir que no se puede concluir con esa información y señalar qué falta. Rellenar el hueco con un supuesto no convierte el supuesto en un dato del producto.",
        "when": "Cuando la respuesta dependa de una condición que no consta, como el plazo de uno de los productos, el periodo de aplicación de la condición o el tipo aplicable.",
        "never_claim": "No afirma que un dato ausente sea deducible del contexto ni que un supuesto razonable equivalga a una condición documentada.",
    },
    "alcance_no_confirma_condiciones": {
        "text": "Una explicación educativa no confirma las condiciones de un producto concreto. Para saber qué se aplica en el momento de decidir hay que leer la documentación del producto y comprobar a qué periodo se refiere.",
        "when": "Cuando la persona pregunte por una condición concreta de un producto o por lo que puede contratar ahora.",
        "never_claim": "No afirma que la aplicación haya consultado la ficha, que el dato siga aplicándose ni que la explicación refleje una oferta comercial.",
    },
    "ahorro_frente_a_inversion": {
        "text": "Ahorrar es apartar dinero para usarlo más adelante; invertir es poner ese dinero a trabajar aceptando que su valor puede subir o bajar. El ahorro prioriza la disponibilidad; la inversión acepta variaciones de valor a cambio de un rendimiento esperado.",
        "when": "Cuando la persona pregunte por la diferencia entre ahorro e inversión o quiera situar su objetivo en uno de los dos.",
        "never_claim": "No afirma que ahorrar esté exento de riesgo ni que invertir garantice un rendimiento; no califica ningún producto como seguro.",
    },
    "ahorro_riesgo_inflacion": {
        "text": "El ahorro conserva el importe nominal, pero no protege por sí solo del efecto de la inflación: si los precios suben más que la remuneración, el dinero compra menos. Esa pérdida de poder adquisitivo puede no aparecer en el saldo.",
        "when": "Cuando se hable de ahorro, cuentas remuneradas o depósitos y la persona pregunte si su dinero está protegido.",
        "never_claim": "No afirma que la inflación vaya a superar a un tipo concreto ni que el ahorro pierda valor siempre; no da cifras de inflación.",
    },
    "ahorro_riesgos_de_invertir": {
        "text": "El riesgo es la posibilidad de que el resultado difiera de lo esperado, incluida la pérdida de parte o todo el capital invertido. En una inversión no viene solo de que el precio baje: también influyen la solvencia del emisor, la liquidez para vender, la custodia del activo y las condiciones del producto. Repartir el dinero entre varios activos puede reducir el impacto de un mal resultado aislado, pero no elimina el riesgo de mercado ni garantiza conservar el capital.",
        "when": "Cuando la persona pregunte qué riesgos tiene invertir o qué debe mirar además de la rentabilidad.",
        "never_claim": "No afirma que un producto tenga una calificación de riesgo concreta, que diversificar elimine las pérdidas ni que diversificar garantice conservar el capital.",
    },
    "interes_tin_nominal": {
        "text": "El TIN es el tipo de interés nominal pactado: expresa el porcentaje de interés sobre el capital sin incorporar por sí mismo la frecuencia de los pagos ni todos los gastos. Dos productos con el mismo TIN pueden producir resultados distintos si cambia la forma de liquidar los intereses.",
        "when": "Cuando la persona pregunte qué es el TIN o compare dos ofertas que solo muestran ese dato.",
        "never_claim": "No afirma que el TIN sea el rendimiento efectivo ni que dos TIN iguales impliquen el mismo resultado; no da tipos concretos.",
    },
    "interes_tae_equivalente": {
        "text": "La TAE es la tasa anual equivalente: resume el coste o el rendimiento anual bajo unos supuestos, incorporando la frecuencia de los pagos y ciertos gastos. Sirve para comparar, pero no describe por sí sola todas las condiciones del producto.",
        "when": "Cuando la persona pregunte qué es la TAE o por qué se usa para comparar ofertas.",
        "never_claim": "No afirma que la TAE incluya todos los costes ni que coincida con lo que la persona recibirá; no da valores ni compara entidades.",
    },
    "interes_ejemplo_tin_tae": {
        "text": "Ejemplo conceptual: si los intereses se abonan varias veces al año y se reinvierten, el rendimiento efectivo del año supera al tipo nominal pactado; si se abonan una sola vez al final, ambos pueden coincidir. La TAE recoge ese efecto y el TIN no.",
        "when": "Cuando la persona pida un ejemplo de la diferencia entre TIN y TAE sin atribuirlo a ninguna entidad.",
        "never_claim": "No afirma que la TAE sea siempre mayor que el TIN; el ejemplo no usa porcentajes ni importes ni se atribuye a un producto real.",
    },
    "interes_misma_base_comparacion": {
        "text": "Dos TAE solo describen alternativas equivalentes si se refieren al mismo plazo, a la misma moneda y a condiciones parecidas de liquidación, cancelación y vinculación. Una TAE de un plazo corto y otra de un plazo largo no miden lo mismo.",
        "when": "Cuando la persona compare ofertas con plazos distintos o pregunte si puede ordenarlas por TAE.",
        "never_claim": "No afirma que la TAE más alta sea la mejor opción ni que una TAE sea aplicable a otro plazo.",
    },
    "interes_compuesto": {
        "text": "El interés compuesto se produce cuando los intereses ya generados también producen intereses en periodos posteriores. Cuanto más frecuente sea la capitalización, más se separa el resultado de aplicar el tipo una sola vez al capital inicial.",
        "when": "Cuando la persona pregunte cómo crece un importe con el tiempo o qué significa capitalización.",
        "never_claim": "No afirma un resultado concreto ni que la capitalización frecuente compense otros costes o riesgos; no da tipos ni plazos.",
    },
    "inflacion_que_es": {
        "text": "La inflación es la subida general y sostenida de los precios de bienes y servicios. Se mide sobre una cesta representativa, de modo que la inflación que percibe una persona puede diferir de la media.",
        "when": "Cuando la persona pregunte qué es la inflación o cómo le afecta.",
        "never_claim": "No afirma una tasa de inflación concreta ni que la cesta representativa refleje el consumo de una persona determinada.",
    },
    "inflacion_nominal_y_real": {
        "text": "El importe nominal es el que aparece en el saldo o en el contrato; el importe real intenta expresar cuánto se puede comprar con él tras descontar la inflación. Un saldo que no cambia puede perder poder adquisitivo si los precios suben. Ese cálculo real sigue siendo una aproximación, no una medida exacta.",
        "when": "Cuando la persona compare un saldo o una rentabilidad sin ajustar por inflación.",
        "never_claim": "No afirma que el cálculo real sea exacto para una persona concreta ni que la inflación pasada se repita.",
    },
    "inflacion_descontar_no_restar": {
        "text": "Para llevar un importe de un momento a otro en términos de poder adquisitivo se descuenta la inflación acumulada, no se resta un porcentaje suelto del importe. Restar linealmente exagera la pérdida cuando hay varios periodos.",
        "when": "Cuando la persona pida ajustar un importe por inflación o interprete una resta simple como un ajuste correcto.",
        "never_claim": "No afirma que el ajuste por inflación sea una predicción ni que el resultado coincida con lo que la persona podrá comprar.",
    },
    "inflacion_limites_escenario": {
        "text": "Un escenario de inflación es una hipótesis, no un pronóstico: si el supuesto cambia, el resultado cambia. Además, la inflación media no refleja la subida de los bienes que consume una persona en particular.",
        "when": "Cuando se presente un cálculo ajustado por inflación o la persona pregunte si el resultado es lo que va a pasar.",
        "never_claim": "No afirma que la inflación futura vaya a coincidir con el supuesto ni que el resultado sea una previsión.",
    },
    "liquidez_que_es": {
        "text": "La liquidez es la facilidad para disponer del dinero sin perder valor ni asumir costes relevantes. Un producto puede parecer líquido y tardar en convertirse en efectivo, o hacerlo con penalización.",
        "when": "Cuando la persona pregunte por liquidez, disponibilidad del dinero o qué pasa si necesita el dinero antes.",
        "never_claim": "No afirma que un producto concreto sea líquido ni que la disponibilidad sea inmediata o sin coste.",
    },
    "liquidez_plazo_y_vencimiento": {
        "text": "El plazo es el periodo durante el cual se mantiene la condición; el vencimiento es el momento en que termina. Que una condición tenga fecha de fin no significa que el dinero esté disponible antes ni que la oferta se pueda contratar después.",
        "when": "Cuando la persona confunda plazo, vencimiento y disponibilidad, o pregunte cuándo recupera el dinero.",
        "never_claim": "No afirma que un producto permita cancelar antes del vencimiento ni que el vencimiento coincida con la devolución efectiva.",
    },
    "liquidez_cancelacion_anticipada": {
        "text": "La cancelación anticipada puede ser libre, estar sujeta a una penalización o no estar permitida. También puede ser parcial o total, y el tratamiento de los intereses ya abonados cambia según las condiciones.",
        "when": "Cuando la persona pregunte si puede sacar el dinero antes del plazo o qué le cuesta hacerlo.",
        "never_claim": "No afirma que la cancelación sea gratuita, posible o inmediata en un producto concreto.",
    },
    "liquidez_comisiones_y_penalizaciones": {
        "text": "Comisiones, penalizaciones y gastos pueden reducir el resultado aunque el tipo de interés no cambie. Una rentabilidad anunciada sin esos costes no equivale al resultado neto que recibe la persona.",
        "when": "Cuando se comparen ofertas por su tipo de interés o la persona pregunte cuánto recibirá de verdad.",
        "never_claim": "No afirma que un producto no tenga comisiones ni que el tipo anunciado sea el resultado neto; no da importes.",
    },
    "comparar_criterios": {
        "text": "Para comparar alternativas conviene mirar el plazo, la TAE, la frecuencia de pago de intereses, la cancelación anticipada, las comisiones, el importe mínimo, los requisitos de vinculación y la garantía aplicable. Ninguno de esos criterios decide por sí solo: hay que leerlos juntos.",
        "when": "Cuando la persona pida criterios para comparar productos o no sepa qué mirar además del tipo de interés.",
        "never_claim": "No afirma que un criterio sea el más importante ni que la lista sea exhaustiva para cualquier producto.",
    },
    "comparar_misma_base": {
        "text": "Una comparación solo es válida si los datos se refieren al mismo plazo, a la misma moneda y al mismo momento de consulta. Mezclar un dato de hoy con otro de hace meses puede producir una conclusión falsa.",
        "when": "Cuando la persona compare ofertas con plazos o fechas distintas, o pida ordenar productos por una cifra.",
        "never_claim": "No afirma que dos cifras sean comparables por el hecho de estar expresadas en la misma unidad.",
    },
    "comparar_falta_plazo": {
        "text": "Si solo se conoce el plazo de uno de los dos productos, no se puede comparar su rendimiento: falta el plazo del otro y, con él, la base de la comparación. Tampoco se puede suponer que el plazo desconocido sea igual al conocido.",
        "when": "Cuando la persona pida comparar dos productos y solo aporte el plazo de uno.",
        "never_claim": "No afirma que el producto sin plazo sea peor ni que su plazo pueda deducirse del otro.",
    },
    "comparar_sin_mejor_absoluto": {
        "text": "No hay una opción mejor en abstracto: la elección depende del objetivo, del horizonte, de la necesidad de disponer del dinero y de la tolerancia al riesgo de cada persona. Dos productos con la misma TAE pueden ser adecuados para situaciones distintas.",
        "when": "Cuando la persona pregunte qué producto es mejor, cuál elegir o cuál le conviene.",
        "never_claim": "No afirma que exista una opción óptima universal ni que la TAE más alta sea la mejor elección.",
    },
    "comparar_sin_recomendar": {
        "text": "Se pueden explicar criterios y mostrar diferencias, pero no se puede recomendar la contratación de un producto ni de una entidad. La decisión corresponde a la persona, que debe comprobar las condiciones en la documentación aplicable.",
        "when": "Cuando la persona pida una recomendación de contratación o pregunte cuál debe elegir.",
        "never_claim": "No afirma que un producto sea adecuado para una persona concreta ni que la aplicación haya evaluado su perfil.",
    },
    "garantia_de_depositos_que_es": {
        "text": "La garantía de depósitos es una protección legal para depósitos que cumplen ciertos requisitos; no es una garantía general para cualquier producto financiero. Su alcance depende de la legislación aplicable, del tipo de depósito y de la entidad, el país y el titular.",
        "when": "Cuando la persona pregunte qué significa que un depósito esté garantizado o si su dinero está protegido.",
        "never_claim": "No afirma que todos los depósitos estén cubiertos ni que la garantía alcance cualquier importe o producto.",
    },
    "garantia_limite_por_persona": {
        "text": "La cobertura tiene un límite máximo por persona y entidad, y por encima de ese límite el saldo no queda protegido por el sistema de garantía. Repartir el mismo dinero en varias cuentas de la misma entidad no multiplica la cobertura por sí solo.",
        "when": "Cuando la persona pregunte cuánto de su dinero está cubierto o si puede superar el límite repartiendo cuentas.",
        "never_claim": "No afirma una cifra de cobertura ni que el límite sea igual en todos los países o sistemas; no confirma la cobertura de un caso concreto.",
    },
    "garantia_no_cubre_inversiones": {
        "text": "La garantía de depósitos no cubre fondos de inversión, ETF ni valores, aunque se contraten a través de una entidad que también capte depósitos. En esos productos, la protección frente a una caída de valor o un impago es distinta y no equivale a la de un depósito.",
        "when": "Cuando la persona pregunte si la garantía cubre una inversión, un fondo o un producto distinto de un depósito.",
        "never_claim": "No afirma que un fondo esté garantizado por estar comercializado por una entidad de depósitos; no evalúa la solvencia de ninguna entidad.",
    },
    "garantia_frente_a_solvencia": {
        "text": "La solvencia de una entidad y la garantía de depósitos son cosas distintas: la primera describe su capacidad de responder a sus obligaciones; la segunda es una protección con requisitos y límites. Una entidad solvente no sustituye a la garantía, y la garantía no elimina el riesgo de otros productos.",
        "when": "Cuando la persona pregunte si una entidad es segura, si la garantía cubre su dinero o si la solvencia basta.",
        "never_claim": "No afirma que una entidad sea solvente ni que la garantía cubra todo el saldo; no califica de seguro ningún producto.",
    },
    "garantia_como_comprobarla": {
        "text": "Para saber qué protección tiene un depósito hay que comprobar el tipo de producto, el titular, la entidad y el régimen de garantía aplicable en la documentación del producto y en la información del propio régimen. Un resumen de un tercero no permite confirmar esos extremos.",
        "when": "Cuando la persona pregunte por la cobertura de un depósito concreto o por dónde comprobarla.",
        "never_claim": "No afirma que la cobertura esté confirmada para un caso concreto ni que la aplicación haya consultado la documentación.",
    },
    "garantia_capital_garantizado": {
        "text": "Que un producto garantice la devolución del capital al vencimiento no es lo mismo que estar cubierto por un sistema de garantía de depósitos. La primera expresión describe una obligación contractual; la segunda, una protección legal con requisitos y límites.",
        "when": "Cuando la persona lea una expresión como capital garantizado o pregunte si eso equivale a la garantía de depósitos.",
        "never_claim": "No afirma que un producto con capital garantizado esté además cubierto por la garantía de depósitos ni que ambas protecciones sean intercambiables.",
    },
    "fuente_dato_vencido_no_sirve": {
        "text": "Un dato con un periodo de aplicación terminado describe una condición pasada, no una condición que se pueda usar para decidir hoy. Aunque el dato sea correcto como registro histórico, no sirve como oferta ni como base de una comparación.",
        "when": "Cuando la persona aporte un dato con fecha de fin ya pasada o pregunte si puede tratarse como una oferta actual.",
        "never_claim": "No afirma que el dato fuera falso cuando se publicó ni que la condición siga aplicándose; no calcula una oferta sustitutiva.",
    },
    "fuente_vencido_no_se_renueva_solo": {
        "text": "Que una condición haya terminado no permite suponer que se ha prorrogado ni que se ha sustituido por otra equivalente. Para saber qué se aplica después hay que consultar la documentación del producto o preguntar a la entidad.",
        "when": "Cuando la persona pregunte si un dato vencido sigue siendo válido o si la oferta se ha renovado.",
        "never_claim": "No afirma que la condición haya sido renovada, prorrogada ni sustituida; no atribuye una intención a la entidad.",
    },
    "fuente_secundaria_que_es": {
        "text": "Una fuente secundaria es la que resume, comenta o reproduce información de otra fuente: una nota de prensa, un comparador o un blog. Puede ayudar a localizar un dato, pero no es la ficha del producto ni el documento donde la entidad fija las condiciones.",
        "when": "Cuando la persona aporte una noticia, un comparador o un resumen y pregunte si sirve como prueba.",
        "never_claim": "No afirma que toda fuente secundaria sea incorrecta ni que sus datos sean falsos; no identifica medios ni entidades.",
    },
    "fuente_secundaria_no_basta": {
        "text": "Que una fuente secundaria atribuya una tasa o una condición a una entidad no basta para tratarla como la condición aplicable. Para eso hace falta el documento de la entidad, la fecha y el punto concreto donde consta, y comprobar que ese documento no ha sido sustituido.",
        "when": "Cuando la persona pregunte si una fuente secundaria basta para afirmar qué condiciones ofrece una entidad.",
        "never_claim": "No afirma que la fuente secundaria sea oficial ni que la condición atribuida sea la que se aplica; no valida la atribución.",
    },
    "fuente_atribucion_con_prueba": {
        "text": "Atribuir un dato a una entidad exige poder señalar el documento, la fecha y el punto concreto donde aparece; sin esa cadena, la atribución es una afirmación sin respaldo. Repetir un dato citando a un tercero no crea esa cadena.",
        "when": "Cuando la persona pida atribuir una tasa a una entidad o pregunte de dónde sale un dato.",
        "never_claim": "No afirma que una atribución sea verdadera por ser repetida ni que la aplicación haya verificado el documento; no nombra entidades.",
    },
    "simulacion_es_hipotetica": {
        "text": "Una simulación es un ejercicio hipotético: aplica unos supuestos para mostrar cómo evolucionaría un importe si se cumplieran. No es una predicción, no es una oferta y no garantiza el resultado que se obtendría.",
        "when": "Cuando se muestre un cálculo o la persona pregunte si el resultado es lo que va a ocurrir.",
        "never_claim": "No afirma que el resultado vaya a realizarse ni que la simulación refleje una condición contratable.",
    },
    "simulacion_supuestos": {
        "text": "El resultado de una simulación depende de sus supuestos: el importe inicial, las aportaciones, el plazo, el tipo, la capitalización y la inflación. Cambiar uno de ellos cambia el resultado, y el cálculo no justifica por sí solo el valor elegido.",
        "when": "Cuando se presente un cálculo o la persona pregunte por qué sale una cifra y no otra.",
        "never_claim": "No afirma que los supuestos sean los adecuados para la persona ni que procedan de una oferta real.",
    },
    "simulacion_sin_costes_ni_impuestos": {
        "text": "Una simulación sencilla suele dejar fuera impuestos, comisiones y otros gastos, y no recoge penalizaciones por cancelación. Por eso el resultado bruto no coincide necesariamente con lo que la persona recibiría.",
        "when": "Cuando la persona interprete un resultado simulado como dinero disponible o pregunte si incluye impuestos y comisiones.",
        "never_claim": "No afirma que el resultado incluya todos los costes ni que sea un importe neto; no calcula impuestos.",
    },
    "simulacion_convencion_del_tipo": {
        "text": "La forma de convertir un tipo anual en un tipo por periodo cambia el resultado: no es lo mismo dividir el tipo entre los periodos que aplicar la equivalencia compuesta. Una simulación debe declarar qué convención usa para que el número se pueda interpretar.",
        "when": "Cuando la persona pregunte cómo se ha convertido el tipo anual o compare dos cálculos con resultados distintos.",
        "never_claim": "No afirma que una convención sea la correcta para todos los productos ni que el resultado sea el que aplicaría la entidad.",
    },
}

CLAIMS = MappingProxyType(
    {claim_id: MappingProxyType(entry) for claim_id, entry in _EDITORIAL.items()}
)
CLAIM_IDS = tuple(_EDITORIAL)

_PREFIXES = (
    "alcance_",
    "ahorro_",
    "interes_",
    "inflacion_",
    "liquidez_",
    "comparar_",
    "garantia_",
    "fuente_",
    "simulacion_",
)
GROUPS = MappingProxyType(
    {
        prefix: tuple(claim_id for claim_id in CLAIM_IDS if claim_id.startswith(prefix))
        for prefix in _PREFIXES
    }
)

del _EDITORIAL
