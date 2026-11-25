"""Respuesta determinista con las condiciones verificadas del catálogo.

Cuando el turno usó herramientas, la prosa del modelo no se entrega (su
atribución no se puede validar contra la fuente). Hasta ahora se sustituía por
una nota fija que no contestaba la pregunta: a «¿qué TAE tiene el depósito de
EBN?» el usuario leía «no repito cifras en prosa» y nunca veía el 3,1 %.

Después se compuso un listado con las condiciones de cada producto. Eso resultó
ilegible en el uso real: a «¿qué productos de depósito hay?» el usuario recibía
seis fichas con familia, emisor, identidad, estado, atribución, ocho condiciones
por producto, su clase de fuente, su vigencia y las URLs al lado de cada dato.
Es un volcado, no una respuesta.

Lo que se espera de un asesor: **un producto concreto y el motivo**. «Para lo
que pides, este encaja porque…», no «aquí tienes todas las características de
seis productos».

Así que esta capa:
  1. Elige el producto que mejor encaja con lo que se ha preguntado (por la
     cifra si preguntan por tasa, por el plazo si preguntan por plazo, por el
     importe mínimo si preguntan por cuánto hace falta).
  2. Da su nombre, su emisor y **dos o tres datos clave como mucho**.
  3. Dice por qué ese y no otro, con el criterio explícito.
  4. Menciona los demás solo por nombre, como alternativas, sin sus fichas.
  5. Deja la trazabilidad en una línea, no repetida por condición.

No redacta el modelo y no inventa nada: cada cifra sale de una condición con
estado `known` y su fuente. Si no hay ninguna condición legible, devuelve None y
el servicio mantiene la nota anterior.
"""

from __future__ import annotations

import re

# Etiquetas y formato alineados con CONDITION_ROWS de app/static/app.js, para que
# el chat diga lo mismo que la ficha de la biblioteca.
_PERCENT_METRICS = {
    "annual_rate_percent": "TAE",
    "ter_percent": "TER",
    "management_fee_percent": "comisión de gestión",
    "custody_fee_percent": "comisión de depositario",
    "entry_fee_percent": "comisión de entrada",
    "exit_fee_percent": "comisión de salida",
    "performance_fee_percent": "comisión de éxito",
    "marginal_rate_percent": "tipo marginal",
    "withholding_percent": "retención fiscal",
    "minimum_price_percent": "precio mínimo aceptado",
}
_TEXT_METRICS = {
    "isin": "ISIN",
    "maximum_note": "importe máximo",
    "minimum_note": "importe mínimo",
    "subsequent_rate_note": "tipo posterior",
    "category": "categoría",
    "manager": "gestora",
    "depositary": "depositaria",
    "base_currency": "divisa",
    "replication": "réplica",
    "maturity_date": "vencimiento",
}
_EUR_METRICS = {
    "minimum_eur": "inversión mínima",
    "maximum_eur": "importe máximo",
    "nav_eur": "valor liquidativo",
}
_OTHER_METRICS = {
    "term_months": "plazo",
    "risk_scale": "riesgo (SRI)",
    "holding_period_years": "periodo recomendado",
}

# Datos que se muestran como mucho en la recomendación, por orden de interés.
# Tres bastan para decidir: más es un volcado.
_KEY_METRICS = (
    "annual_rate_percent", "term_months", "maturity_date", "ter_percent",
    "management_fee_percent", "minimum_eur", "risk_scale", "withholding_percent",
)

MAX_PRODUCTS = 4
MAX_KEY_FACTS = 3
MAX_ALTERNATIVES = 2


def _format_number(raw):
    """Devuelve el valor legible de una condición, o None si no es presentable.

    No convierte unidades ni redondea a la ligera: el catálogo ya trae el valor
    con su unidad. Solo limpia el formato para leerlo en castellano: coma
    decimal y punto de millares («5000» → «5.000», «3.1» → «3,1»).
    """
    text = str(raw).strip()
    if not text:
        return None
    if re.fullmatch(r"-?\d+", text):
        return f"{int(text):,}".replace(",", ".")
    if re.fullmatch(r"-?\d+[.,]\d+", text):
        entero, decimales = re.split(r"[.,]", text, maxsplit=1)
        return f"{int(entero):,}".replace(",", ".") + "," + decimales
    return text


def _claim_line(condition):
    metric = condition.get("metric")
    value = _format_number(condition.get("value"))
    if value is None:
        return None
    if condition.get("state") != "known":
        return None
    if metric in _PERCENT_METRICS:
        return f"{_PERCENT_METRICS[metric]}: {value} %"
    if metric in _EUR_METRICS:
        return f"{_EUR_METRICS[metric]}: {value} €"
    if metric == "term_months":
        return f"plazo: {value} meses"
    if metric == "holding_period_years":
        return f"periodo recomendado: {value} años"
    if metric == "risk_scale":
        # El catálogo ya trae la escala completa («1/6»): no se le añade nada.
        return f"riesgo (SRI): {value}"
    if metric in _TEXT_METRICS:
        return f"{_TEXT_METRICS[metric]}: {value}"
    if metric in _OTHER_METRICS:
        return f"{_OTHER_METRICS[metric]}: {value}"
    return None


def _source_url(condition):
    """URL de la fuente de una condición.

    El catálogo real no trae `sources`: trae `source_ids`, que es una lista de
    URLs, y `source_refs` con la referencia resuelta. Se aceptan las tres formas
    porque el DTO del chat y la ficha no siempre coinciden, y sin la fuente la
    cifra no es comprobable.
    """
    # Forma del DTO del chat: [{'url': ...}]
    for source in condition.get("sources") or ():
        if isinstance(source, dict):
            url = source.get("url")
            if isinstance(url, str) and url.startswith(("https://", "http://")):
                return url
    # Forma del catálogo real: source_ids = ['https://...']
    for source_id in condition.get("source_ids") or ():
        if isinstance(source_id, str) and source_id.startswith(("https://", "http://")):
            return source_id
    for ref in condition.get("source_refs") or ():
        if isinstance(ref, dict):
            url = ref.get("url")
            if isinstance(url, str) and url.startswith(("https://", "http://")):
                return url
    return None


def _known_conditions(product):
    """Condiciones con estado `known` y valor legible, una por métrica."""
    conditions = product.get("conditions")
    if not isinstance(conditions, list):
        return {}
    by_metric = {}
    for condition in conditions:
        if not isinstance(condition, dict):
            continue
        metric = condition.get("metric")
        if metric in by_metric:
            continue
        if _claim_line(condition) is not None:
            by_metric[metric] = condition
    return by_metric


def _any_condition(product, metric):
    """Condición de esa métrica en CUALQUIER estado, o None.

    Hace falta para distinguir «no hay tasa» de «hay tasa pero está vencida». La
    primera no se puede recomendar por tasa; la segunda tampoco, pero hay que
    decirlo en vez de presentar el producto sin cifra y sin explicación.
    """
    for condition in product.get("conditions") or ():
        if isinstance(condition, dict) and condition.get("metric") == metric:
            return condition
    return None


def _key_facts(by_metric, limit=MAX_KEY_FACTS):
    """Dos o tres datos clave del producto, no la ficha entera."""
    ordered = [by_metric[m] for m in _KEY_METRICS if m in by_metric]
    ordered += [c for m, c in by_metric.items() if m not in _KEY_METRICS]
    facts = []
    for condition in ordered:
        claim = _claim_line(condition)
        if claim is None:
            continue
        facts.append(claim)
        if len(facts) >= limit:
            break
    return facts


def _product_heading(product):
    name = product.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    issuer = product.get("issuer")
    if isinstance(issuer, str) and issuer.strip():
        limpio = issuer.strip()
        # No repetir el emisor si ya está en el nombre: «Self Bank (Self Bank)».
        if limpio.casefold() not in name.casefold():
            return f"{name.strip()} ({limpio})"
    return name.strip()


def _numeric(by_metric, metric):
    """Valor numérico de una condición, para ordenar.

    Lee el valor CRUDO, no el formateado: «5000» formateado es «5.000» y
    `float("5.000")` vale 5,0, no 5000. Ese error hacía que el comparador de
    importes mínimos eligiera el depósito de 5.000 € como el más barato.
    """
    condition = by_metric.get(metric)
    if condition is None:
        return None
    raw = condition.get("value")
    if not isinstance(raw, str) or not raw.strip():
        return None
    # El catálogo usa el punto como separador decimal («2.4», «0.12»).
    try:
        return float(raw.strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def _question_intent(question):
    """Qué está preguntando la persona, para elegir el criterio.

    No hace falta un clasificador: el catálogo solo se abre cuando la pregunta
    nombra algo concreto, y estas palabras cubren los casos reales medidos.

    Se distingue el LISTADO («¿qué productos de depósito hay?») de la ELECCIÓN
    («¿cuál me conviene?»). A una pregunta de listado, contestar «el que mejor
    encaja es X» es no responder: quiere saber qué hay.
    """
    text = question if isinstance(question, str) else ""
    text = text.casefold()
    # Listado: preguntan por la existencia del conjunto, no por una elección.
    if any(word in text for word in ("qué productos", "que productos", "qué hay",
                                     "que hay", "cuáles hay", "cuales hay",
                                     "qué ofreces", "que ofreces", "qué tienes",
                                     "que tienes", "lista", "enumera")):
        return "list"
    if any(word in text for word in ("tae", "tasa", "interés", "interes", "rentabilidad", "remuner")):
        return "rate"
    if any(word in text for word in ("comisi", "ter", "coste", "barato", "caro")):
        return "cost"
    if any(word in text for word in ("mínim", "minim", "cuánto", "cuanto", "importe", "desde",
                                     "menos dinero", "poco dinero", "empezar", "entrada",
                                     "inversión inicial", "inversion inicial", "asequible")):
        return "minimum"
    if any(word in text for word in ("seguro", "riesgo", "garantiz", "sri")):
        return "risk"
    if any(word in text for word in ("plazo", "meses", "año", "ano", "vencimi")):
        return "term"
    return "general"


def _money_text(valor):
    """Formato de dinero para leer: sin decimales si son .00, con coma si no.

    2000 → «2.000», 1500.0 → «1.500», 62.5 → «62,50».
    """
    if valor is None:
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if abs(numero - round(numero)) < 0.005:
        return f"{int(round(numero)):,}".replace(",", ".")
    return f"{numero:,.2f}".replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")


def _rate_text(valor):
    """Tasa con dos decimales, que es como se lee una TAE: 3.1 → «3,10».

    Sin esto, «3,10 %» se quedaba en «3,1 %»: el dato es correcto pero pierde
    precisión justo donde el usuario compara productos.
    """
    if valor is None:
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return f"{numero:.2f}".replace(".", ",")


def _missing_key_datum(question, cantidad, planificado, intent=None):
    """Qué dato falta y cambia la recomendación, o None si no falta nada.

    El prompt ya dice «si falta un dato que cambia la respuesta, pide solo ese
    dato», pero cuando el turno usa el catálogo la prosa del modelo se retiene y
    compone esta función: la política se perdía y la app recomendaba a ciegas.
    Un asesor pregunta antes de recomendar cuando la respuesta depende de algo que
    no le han dicho.

    NO se pregunta cuando la persona ha pedido un DATO concreto («¿qué TAE tiene el
    depósito de EBN?»). Ahí la respuesta es la cifra, no una recomendación, y pedir
    el dinero sería no contestar lo que se ha preguntado. Solo se pregunta en una
    pregunta de DECISIÓN, donde de verdad cambia la elección:
      - cuánto dinero hay (decide el filtro por importe mínimo);
      - para cuándo lo necesita (decide el plazo y la liquidez).
    """
    if not isinstance(question, str) or not question.strip():
        return None
    if intent is not None and intent not in {"general"}:
        # rate, cost, minimum, risk, term, list: son consultas, no decisiones.
        return None
    texto = question.casefold()
    # Una consulta de FICHA («detalla DEP-KNOWN», «dame la ficha de…», «háblame de
    # este producto») pide datos de un producto concreto, no una recomendación. Pedir
    # el importe disponible ahí sería no contestar lo que se ha preguntado.
    if re.search(r"\b(?:detalla|detalle|ficha|h[aá]blame\s+de|dime\s+los?\s+datos|"
                 r"informaci[oó]n\s+de|qu[eé]\s+sabes\s+de)\b", texto):
        return None
    if cantidad is None:
        return "¿Cuánto dinero tienes pensado poner?"
    if planificado is None:
        # El horizonte puede venir por palabra («un año», «6 meses», «año y medio»)
        # sin que haya un gasto concreto.
        if re.search(r"\b(?:\d{1,2}\s*(?:meses|años?)|un\s+año|dos\s+años|"
                     r"medio\s+año|año\s+y\s+medio|a\s+largo\s+plazo|"
                     r"sin\s+tocar(?:lo)?\s+(?:en\s+)?\d+)", texto):
            return None
        return "¿Para cuándo lo necesitas? Con el plazo puedo decirte si te encaja algo a 6 o a 12 meses."
    return None


def _is_current(product):
    """¿La oferta sigue vigente según la ficha?

    `documented_not_current` es una oferta transcrita pero caducada. No se puede
    recomendar como si estuviera disponible: sería mandar al usuario a contratar
    algo que ya no existe. `documented` y `documented_partial` sí sirven.
    """
    return product.get("conditions_state") != "documented_not_current"


# Cantidades en euros tal como las escribe una persona: «2000 euros», «2.000 €»,
# «1.500 euros», «mil euros», «2.000,50 €». Se exige que lleve la palabra euro o
# el símbolo, para no confundir un plazo («12 meses») ni una tasa («3 %») con el
# dinero del que habla el usuario.
_AMOUNT_PATTERNS = (
    # 2.000,50 / 2000.50 / 2.000 / 2000 seguidos de euro/€/EUR. El símbolo «€» no
    # es carácter de palabra, así que tras él no se puede exigir \b (daba None con
    # «tengo 2.000 €»); se admite tanto fin de palabra como el propio símbolo.
    re.compile(
        r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*"
        r"(?:euros?(?![a-záéíóúñ])|€|eur(?:os)?(?![a-záéíóúñ]))",
        re.IGNORECASE,
    ),
    # «mil euros», «dos mil euros» (solo el caso exacto de mil, que es el habitual)
    re.compile(r"\b(?:un\s+)?mil\s+(?:euros?(?![a-záéíóúñ])|€)", re.IGNORECASE),
)

# Cantidades de dinero SIN la palabra euro, para el gasto previsto («un gasto de
# 1500 para los estudios»). Se exige un verbo o preposición de gasto delante para
# no confundirla con un plazo ni con una tasa.
_EXPENSE_PATTERN = re.compile(
    r"(?:gasto|gastar|gastar[eé]|necesit[oa]s?|necesitar[eé]|pago|pagar|"
    r"me\s+cuesta|presupuesto|para\s+los\s+estudios|matr[íi]cula)"
    r"[^.\d]{0,30}?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d{1,7}(?:[.,]\d{1,2})?)"
    r"\s*(?:euros?|€)?",
    re.IGNORECASE,
)


def _parse_spanish_number(bruto):
    """«2.000» → 2000.0, «2000,50» → 2000.5, «1.500» → 1500.0."""
    if not isinstance(bruto, str) or not bruto.strip():
        return None
    texto = bruto.strip()
    if "," in texto:
        # Coma decimal; los puntos son de millares.
        limpio = texto.replace(".", "").replace(",", ".")
    elif "." in texto:
        entero, _, decimales = texto.rpartition(".")
        # «2.000» es dos mil; «2000.50» es dos mil con cincuenta.
        limpio = texto.replace(".", "") if len(decimales) == 3 else texto
    else:
        limpio = texto
    try:
        valor = float(limpio)
    except (TypeError, ValueError):
        return None
    return valor if 0 < valor <= 100_000_000 else None


def extract_amount_eur(text):
    """Cantidad en euros con la palabra euro o el símbolo, o None.

    Sirve para no recomendar un producto cuyo importe mínimo no se alcanza. Es el
    fallo medido: a un estudiante con 2.000 € se le recomendaban depósitos que
    exigen 5.000 € y 6.000 €, y se le calculaba la rentabilidad del 3,10 % de uno
    de ellos. Un asesor no manda a nadie a contratar lo que no puede pagar.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    for pattern in _AMOUNT_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        if not match.groups():
            return 1000.0
        valor = _parse_spanish_number(match.group(1))
        if valor is not None:
            return valor
    return None


def extract_expense_eur(text):
    """Gasto previsto mencionado sin la palabra «euro», o None."""
    if not isinstance(text, str) or not text.strip():
        return None
    match = _EXPENSE_PATTERN.search(text)
    if not match:
        return None
    return _parse_spanish_number(match.group(1))


def _minimum_eur(product):
    """Importe mínimo documentado del producto, o None si no consta.

    Se leen las formas que usa el catálogo: `minimum_eur` numérico,
    `minimum_note` («Min. 5.000€») y las claves antiguas `importe_minimo` /
    `importe_minimo_texto`. Si el texto dice «sin mínimo», el mínimo es 1 €.
    """
    raw = None
    for metric in ("minimum_eur", "importe_minimo", "minimum_note", "importe_minimo_texto"):
        for condition in product.get("conditions") or ():
            if not isinstance(condition, dict) or condition.get("metric") != metric:
                continue
            raw = condition.get("value")
            if raw not in (None, ""):
                break
        if raw not in (None, ""):
            break
    if raw is None:
        return None
    texto = str(raw).strip()
    if not texto:
        return None
    if re.search(r"sin\s+m[íi]nimo|no\s+(?:hay|existe)\s+m[íi]nimo", texto, re.IGNORECASE):
        return 1.0
    numeros = re.findall(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?", texto)
    if not numeros:
        return None
    return _parse_spanish_number(numeros[0])


def _mentions_issuer(product, text):
    """¿La pregunta nombra a este producto o a su emisor?

    Es el fallo que se midió con datos reales: a «¿qué TAE tiene el depósito de
    EBN Banco?» se recomendaba el depósito de Openbank, porque elegía el de tasa
    más alta del conjunto. Si la persona nombra un banco, quiere ESE banco.
    """
    if not isinstance(text, str) or not text.strip():
        return False
    pregunta = text.casefold()
    emisor = product.get("issuer")
    if isinstance(emisor, str) and emisor.strip():
        # «EBN Banco» → también vale «ebn». Se compara la primera palabra
        # significativa para no exigir el nombre completo.
        limpio = emisor.strip().casefold()
        if limpio and limpio in pregunta:
            return True
        primera = limpio.split()[0] if limpio.split() else ""
        if len(primera) >= 3 and primera in pregunta:
            return True
    nombre = product.get("name")
    if isinstance(nombre, str) and nombre.strip():
        if nombre.strip().casefold() in pregunta:
            return True
    return False


def _pick_best(products, intent):
    """Elige el producto que mejor encaja y devuelve (elegido, motivo).

    El criterio es explícito y determinista: se ordena por la métrica que
    corresponde a lo preguntado y se toma el primero. Nunca inventa: si no hay
    datos para el criterio, cae al orden del catálogo.

    Antes de ordenar, una preferencia fuerte: una tasa VIGENTE vale más que una
    vencida. Es el fallo medido con Pibank: su TAE está en estado `stale` y, al no
    haber otro producto con tasa viva en el conjunto, se recomendaba igualmente sin
    poder dar la cifra. Si hay alguno con tasa viva, se recomienda ese.
    """
    candidates = []
    for index, product in enumerate(products):
        by_metric = _known_conditions(product)
        if not by_metric:
            continue
        candidates.append((index, product, by_metric))
    if not candidates:
        return None, None

    def tiene_tasa_viva(candidate):
        return _numeric(candidate[2], "annual_rate_percent") is not None

    if intent in {"rate", "cost", "general", "term"}:
        con_viva = [c for c in candidates if tiene_tasa_viva(c)]
        if con_viva:
            candidates = con_viva

    if intent == "rate":
        with_rate = [c for c in candidates if _numeric(c[2], "annual_rate_percent") is not None]
        if with_rate:
            best = max(with_rate, key=lambda c: (_numeric(c[2], "annual_rate_percent"), -c[0]))
            rate = _format_number(best[2]["annual_rate_percent"].get("value"))
            return best, f"es el mejor remunerado de los que tienen la tasa documentada ({rate} % TAE)"
    if intent == "cost":
        with_ter = [c for c in candidates if _numeric(c[2], "ter_percent") is not None]
        if with_ter:
            best = min(with_ter, key=lambda c: (_numeric(c[2], "ter_percent"), c[0]))
            ter = _format_number(best[2]["ter_percent"].get("value"))
            return best, f"es el de menor coste de los que tienen el TER documentado ({ter} %)"
        with_fee = [c for c in candidates if _numeric(c[2], "management_fee_percent") is not None]
        if with_fee:
            best = min(with_fee, key=lambda c: (_numeric(c[2], "management_fee_percent"), c[0]))
            fee = _format_number(best[2]["management_fee_percent"].get("value"))
            return best, f"es el de menor comisión de gestión de los documentados ({fee} %)"
    if intent == "minimum":
        with_min = [c for c in candidates if _numeric(c[2], "minimum_eur") is not None]
        if with_min:
            best = min(with_min, key=lambda c: (_numeric(c[2], "minimum_eur"), c[0]))
            minimo = _format_number(best[2]["minimum_eur"].get("value"))
            return best, f"es el que pide menos dinero para empezar ({minimo} €)"
    if intent == "risk":
        with_risk = [c for c in candidates if _numeric(c[2], "risk_scale") is not None]
        if with_risk:
            best = min(with_risk, key=lambda c: (_numeric(c[2], "risk_scale"), c[0]))
            sri = _format_number(best[2]["risk_scale"].get("value"))
            return best, f"es el de menor riesgo declarado en la ficha (SRI {sri} de 7)"

    index, product, by_metric = candidates[0]
    return (index, product, by_metric), None


def compose_catalogue_answer(catalogue, limit=MAX_PRODUCTS, explanation=None, question=None):
    """Un producto concreto con su motivo, no un volcado de fichas.

    `explanation` llega redactada por el modelo y NO se usa para ningún dato: se
    coloca al final, ya sin sus cifras, para que oriente sin poder introducir una
    tasa, un importe ni una atribución no verificada.

    Devuelve None cuando no hay ningún dato legible: en ese caso el servicio
    mantiene la nota anterior en lugar de inventar una respuesta vacía.
    """
    if not isinstance(catalogue, dict) or catalogue.get("used") is not True:
        return None
    products = catalogue.get("products")
    if not isinstance(products, list) or not products:
        return None

    productos_legibles = [p for p in products
                          if isinstance(p, dict) and _product_heading(p) is not None]
    if not productos_legibles:
        return None
    valid_products = productos_legibles[:limit]

    intent = _question_intent(question)
    # Si la pregunta nombra un banco o un producto, el conjunto se reduce a ese:
    # a «¿qué TAE tiene el depósito de EBN Banco?» no se puede contestar con el
    # depósito de Openbank por muy buena que sea su tasa.
    nombrados = [p for p in valid_products if _mentions_issuer(p, question)]
    if nombrados:
        valid_products = nombrados
    # El dinero del que habla el usuario manda: no se recomienda lo que no puede
    # contratar. Fallo medido: a un estudiante con 2.000 € se le ofrecían depósitos
    # de 5.000 € y 6.000 € y se le calculaba la rentabilidad del 3,10 % de uno de
    # ellos. Un asesor no manda a nadie a contratar lo que no puede pagar.
    cantidad = extract_amount_eur(question)
    descartados_por_importe = []
    if cantidad is not None:
        alcanzables = []
        for product in valid_products:
            minimo = _minimum_eur(product)
            if minimo is not None and minimo > cantidad:
                descartados_por_importe.append((_product_heading(product), minimo))
            else:
                alcanzables.append(product)
        if alcanzables:
            valid_products = alcanzables
        # Si no queda ninguno, NO se vacía la lista: se explica el motivo con los
        # mínimos reales, que es la respuesta útil. Dejar el conjunto vacío haría
        # que el turno cayera a la nota genérica.
    # Una oferta vencida no se recomienda. Si todas lo están, se dice: es más
    # honesto que empujar a contratar algo que ya no existe.
    vigentes = [p for p in valid_products if _is_current(p)]
    if vigentes:
        best, motivo = _pick_best(vigentes, intent)
    else:
        best, motivo = _pick_best(valid_products, intent)
    if best is None:
        return None
    _, chosen, by_metric = best
    heading = _product_heading(chosen)
    facts = _key_facts(by_metric)
    # Lo que el usuario ha dicho de su situación: cuánto tiene y cuánto necesita.
    cantidad_txt = _format_number(str(int(cantidad))) if cantidad is not None else None
    planificado = extract_expense_eur(question)
    if planificado is not None and cantidad is not None and planificado >= cantidad:
        planificado = None

    # Listado: la persona quiere saber QUÉ HAY, no una elección. Se da el nombre
    # de cada producto con su dato más identificativo y nada más: decirle «el que
    # mejor encaja es X» a «¿qué productos de depósito hay?» es no contestar.
    if intent == "list":
        # Se nombran TODOS los que hay, no los primeros cuatro: a «¿qué productos
        # de depósito hay?» contestar con una lista incompleta es peor que no
        # contestar, porque el usuario no sabe que falta el resto.
        nombres = [n for n in (_product_heading(p) for p in productos_legibles) if n]
        # Concordancia: «1 producto», no «1 productos».
        cuantos = f"{len(nombres)} producto" if len(nombres) == 1 else f"{len(nombres)} productos"
        lineas = [f"En el catálogo hay {cuantos} de este tipo: " + ", ".join(nombres) + "."]
        lineas.append("Dime cuál te interesa y te doy su TAE, su plazo y su "
                      "inversión mínima con la fuente.")
        caducados = [_product_heading(p) for p in productos_legibles if not _is_current(p)]
        caducados = [n for n in caducados if n]
        if caducados:
            # «A, B están marcados» → falta la conjunción: se enumera con «y».
            if len(caducados) == 1:
                lineas.append(f"Ojo: {caducados[0]} está marcado como no vigente en la ficha.")
            else:
                lineas.append("Ojo: " + ", ".join(caducados[:-1]) + " y " + caducados[-1]
                              + " están marcados como no vigentes en la ficha.")
        partes = ["\n\n".join(lineas)]
        if isinstance(explanation, str) and explanation.strip():
            partes.append(explanation.strip())
        partes.append("Son datos transcritos de fuentes oficiales, no una oferta ni una "
                      "recomendación personalizada.")
        return "\n\n".join(partes)

    # CUERPO CONVERSACIONAL. Antes esto era una ficha («Para lo que preguntas, el
    # que mejor encaja es X. Es el mejor remunerado… Lo esencial: …»), que el
    # usuario describió como «demasiado robotizado, demasiado texto numérico».
    # Un asesor razona con las cifras en vez de enumerarlas: primero la situación,
    # luego qué implica, luego el producto y cuánto supone en euros.
    tasa = _numeric(by_metric, "annual_rate_percent")
    plazo = _numeric(by_metric, "term_months")
    # El mínimo se lee con _minimum_eur, que entiende «Sin mínimo» y los formatos
    # del catálogo; _numeric fallaba con ese texto y el mínimo desaparecía.
    minimo = _minimum_eur(chosen)
    # Una tasa vencida no se publica como si fuera la vigente. Es lo que pasó con
    # Pibank: su TAE (3,03 %) está en estado `stale` porque la promoción caducó, y
    # la respuesta la omitía sin explicar por qué, dejando el producto sin cifra.
    tasa_vencida = _any_condition(chosen, "annual_rate_percent")
    if tasa_vencida is not None and tasa_vencida.get("state") != "known":
        tasa = None
        valor_vencido = _format_number(tasa_vencida.get("value"))
    else:
        valor_vencido = None
    lineas = []

    # 1) Si falta un dato que cambia la respuesta, se pregunta ANTES de recomendar.
    #    El prompt ya lo pedía, pero cuando el turno usa el catálogo la prosa del
    #    modelo se retiene y esa política se perdía: la app recomendaba a ciegas.
    falta = _missing_key_datum(question, cantidad, planificado, intent)
    if falta:
        # Se da lo que sí se puede dar ya —el producto y su cifra— y se pide el dato
        # que falta, en vez de una respuesta incompleta o una pregunta a secas.
        if tasa is not None:
            extra = f" a {_format_number(str(int(plazo)))} meses" if plazo else ""
            lineas.append(f"Para orientarte de verdad me falta un dato. {falta}")
            lineas.append(f"Te adelanto lo que sí sé: **{heading}** está a "
                          f"{_rate_text(tasa)} % TAE{extra}.")
        else:
            lineas.append(f"Para orientarte de verdad me falta un dato. {falta}")
            lineas.append(f"Cuando me lo digas miro qué encaja; en el catálogo está "
                          f"**{heading}**.")
        partes = ["\n\n".join(lineas)]
        if isinstance(explanation, str) and explanation.strip():
            partes.append(explanation.strip())
        partes.append("Son datos transcritos de fuentes oficiales, no una oferta ni una "
                      "recomendación personalizada.")
        return "\n\n".join(partes)

    # 2) La situación, en sus términos. Si dijo cuánto tiene y cuánto necesita, eso
    #    es lo primero: es el marco de la decisión.
    if cantidad is not None and planificado is not None:
        libre = cantidad - planificado
        lineas.append(
            f"Con {_money_text(cantidad)} € y {_money_text(planificado)} € comprometidos "
            f"para dentro de un año, la clave es que esos {_money_text(planificado)} € "
            f"estén disponibles sí o sí. Te quedan {_money_text(libre)} € que puedes "
            f"mover sin tocar lo que ya tienes comprometido.")
    elif cantidad is not None:
        lineas.append(
            f"Partiendo de {_money_text(cantidad)} €, lo que buscas es que el dinero no "
            f"se quede parado sin quedarse atrapado.")

    # 2) El producto y qué aporta, en una frase con la cifra integrada. NO se repite
    #    la tasa en el motivo: ya va aquí, y repetirla era el «demasiado texto
    #    numérico» que se reportó.
    if tasa is not None and plazo is not None:
        lineas.append(
            f"Para eso encaja **{heading}**: {_rate_text(tasa)} % TAE a "
            f"{_format_number(str(int(plazo)))} meses.")
    elif tasa is not None:
        lineas.append(f"Para eso encaja **{heading}**: {_rate_text(tasa)} % TAE.")
    else:
        lineas.append(f"Para eso encaja **{heading}**.")
    # Si la única tasa que hay está vencida, se dice con la cifra y su condición, en
    # vez de presentar el producto sin número y sin explicación.
    if valor_vencido:
        lineas.append(
            f"Su TAE documentada era el {valor_vencido} %, pero la ficha la marca como "
            f"vencida: esa promoción ya no está en vigor, así que el tipo que te "
            f"ofrezcan hoy puede ser distinto. Confírmalo antes de contratar.")
    # El motivo, sin la cifra que ya se ha dado arriba.
    if motivo:
        limpio = re.sub(r"\s*\([^)]*\)\s*$", "", motivo).strip()
        if limpio:
            lineas.append(f"{limpio[0].upper() + limpio[1:]}.")

    # 3) Trabajar la cifra: cuánto dinero supone de verdad. Esto es lo que faltaba:
    #    el 3,03 % no significa nada hasta que se traduce a euros. Se calcula sobre
    #    el dinero LIBRE (lo que no está comprometido), no sobre el gasto: el gasto
    #    no se invierte, se paga. Sin tasa vigente no se calcula: inventar el
    #    interés con un tipo caducado sería peor que no darlo.
    if tasa is not None and cantidad is not None:
        base = cantidad - planificado if planificado is not None else cantidad
        anios = (plazo / 12) if plazo else 1.0
        if base and base > 0:
            interes = base * (tasa / 100) * anios
            if interes >= 1:
                lineas.append(
                    f"Si pones esos {_money_text(base)} € a ese tipo durante el año, "
                    f"sacan unos {_money_text(round(interes, 2))} € de intereses. Poco, "
                    f"pero es dinero que no pierdes y que recuperas al vencer.")
            else:
                lineas.append(
                    f"Sobre {_money_text(base)} € el interés sería de unos "
                    f"{_money_text(round(interes, 2))} € al año: son migajas, y el motivo "
                    f"es que el dinero tiene que estar disponible, no que el producto sea malo.")
    # El mínimo se dice SIEMPRE que conste: es el dato que decide si la ficha sirve
    # o no, tanto si el usuario dijo cuánto tiene como si no.
    if minimo is not None:
        if cantidad is not None and minimo > cantidad:
            lineas.append(f"El problema es el mínimo: pide {_money_text(minimo)} € y con "
                          f"{_money_text(cantidad)} € no llegas.")
        elif minimo <= 1:
            if cantidad is not None:
                lineas.append(f"Y puedes entrar desde 1 €, así que con "
                              f"{_money_text(cantidad)} € no tienes problema de mínimo.")
            else:
                lineas.append("Y puedes entrar desde 1 €, así que el mínimo no es un estorbo.")
        else:
            if cantidad is not None:
                lineas.append(f"El mínimo son {_money_text(minimo)} €, que sí alcanzas con "
                              f"{_money_text(cantidad)} €.")
            else:
                lineas.append(f"Pide un mínimo de {_money_text(minimo)} €.")

    # 4) Los datos clave que aún no se han dicho y que ayudan a decidir (riesgo,
    #    retención, vencimiento…). Se excluyen por MÉTRICA, no por el texto del
    #    valor: comparar cadenas dejaba pasar «TAE: 3,03 %» otra vez.
    ya_dichas = {"annual_rate_percent", "term_months", "minimum_eur", "minimum_note"}
    extras = []
    for metric, condition in by_metric.items():
        if metric in ya_dichas:
            continue
        claim = _claim_line(condition)
        if claim:
            extras.append(claim)
    if extras:
        lineas.append("Además: " + "; ".join(extras[:2]) + ".")

    # Estado, solo si aporta: una oferta vencida no puede presentarse como vigente.
    # Si ya se ha avisado arriba con la cifra, no se repite: dos avisos seguidos del
    # mismo hecho eran parte del ruido.
    if chosen.get("conditions_state") == "documented_not_current" and not valor_vencido:
        lineas.append("Ojo: la ficha marca esta oferta como no vigente, así que "
                      "comprueba el tipo antes de contar con ella.")

    # Alternativas: SOLO el nombre, sin sus fichas. Es la diferencia entre
    # «estos otros existen» y «aquí tienes seis fichas para que leas».
    otros = [p for p in valid_products if p is not chosen]
    nombres = [n for n in (_product_heading(p) for p in otros) if n]
    if nombres:
        muestra = nombres[:MAX_ALTERNATIVES]
        resto = len(nombres) - len(muestra)
        cola = f" y {resto} más" if resto > 0 else ""
        lineas.append("También están " + ", ".join(muestra) + cola +
                      "; dime si quieres que mire alguno en concreto.")
    # Los que no se pueden contratar con su dinero se dicen, con el mínimo real: es
    # la información que evita que pierda el tiempo mirando una ficha inalcanzable.
    if descartados_por_importe and cantidad is not None:
        partes_min = [f"{nombre.split(' (')[0]} pide {_money_text(minimo)} €"
                      for nombre, minimo in descartados_por_importe[:2]]
        lineas.append(f"Los he descartado por importe: " + " y ".join(partes_min)
                      + f", y con {_money_text(cantidad)} € no llegas.")

    # Trazabilidad en una sola línea, no repetida por condición.
    fuente = None
    for metric in _KEY_METRICS:
        condition = by_metric.get(metric)
        if condition is None:
            continue
        fuente = _source_url(condition)
        if fuente:
            break
    if fuente:
        lineas.append(f"Dato verificado en la ficha del producto: {fuente}")

    partes = ["\n\n".join(lineas)]
    if isinstance(explanation, str) and explanation.strip():
        partes.append(explanation.strip())
    partes.append("Son datos transcritos de fuentes oficiales, no una oferta ni una "
                  "recomendación personalizada.")
    return "\n\n".join(partes)


def _pending_products(catalogue, limit=MAX_PRODUCTS):
    """Productos del DTO que existen pero no tienen ninguna condición legible.

    Medido en produccion: a «¿cuál es el TER del ETF de iShares Core MSCI
    Europe?» la herramienta encuentra el producto (ETF-01), pero su ficha tiene
    `conditions: 0` y `conditions_state: pending`. La composición no inventa
    nada, que es lo correcto, pero la nota fija no explicaba por qué.
    """
    if not isinstance(catalogue, dict) or catalogue.get("used") is not True:
        return []
    products = catalogue.get("products")
    if not isinstance(products, list):
        return []
    pendientes = []
    for product in products[:limit]:
        if not isinstance(product, dict):
            continue
        name = product.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        if _known_conditions(product):
            continue
        heading = _product_heading(product)
        if heading:
            pendientes.append(heading)
    return pendientes


def pending_evidence_answer(catalogue, limit=MAX_PRODUCTS):
    """Explica que el producto está en el catálogo pero su ficha está pendiente."""
    pendientes = _pending_products(catalogue, limit)
    if not pendientes:
        return None
    listado = "\n".join(f"- {item}" for item in pendientes)
    return (
        "He encontrado estos productos en el catálogo local, pero su ficha todavía "
        "no tiene las condiciones transcritas, así que no puedo darte la cifra:\n\n"
        + listado
        + "\n\nPuedes ver el estado en la biblioteca; no invento el dato que falta. "
          "No soy un asesor financiero."
    )
