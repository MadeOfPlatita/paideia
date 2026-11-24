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


def _is_current(product):
    """¿La oferta sigue vigente según la ficha?

    `documented_not_current` es una oferta transcrita pero caducada. No se puede
    recomendar como si estuviera disponible: sería mandar al usuario a contratar
    algo que ya no existe. `documented` y `documented_partial` sí sirven.
    """
    return product.get("conditions_state") != "documented_not_current"


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
    """
    candidates = []
    for index, product in enumerate(products):
        by_metric = _known_conditions(product)
        if not by_metric:
            continue
        candidates.append((index, product, by_metric))
    if not candidates:
        return None, None

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

    # Listado: la persona quiere saber QUÉ HAY, no una elección. Se da el nombre
    # de cada producto con su dato más identificativo y nada más: decirle «el que
    # mejor encaja es X» a «¿qué productos de depósito hay?» es no contestar.
    if intent == "list":
        # Se nombran TODOS los que hay, no los primeros cuatro: a «¿qué productos
        # de depósito hay?» contestar con una lista incompleta es peor que no
        # contestar, porque el usuario no sabe que falta el resto.
        nombres = [n for n in (_product_heading(p) for p in productos_legibles) if n]
        lineas = [f"En el catálogo hay {len(nombres)} productos de este tipo: "
                  + ", ".join(nombres) + "."]
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

    # Cuerpo: una recomendación, su motivo y sus datos clave. Nada más.
    lineas = [f"Para lo que preguntas, el que mejor encaja es **{heading}**."]
    if motivo:
        lineas.append(f"{motivo[0].upper() + motivo[1:]}.")
    if facts:
        lineas.append("Lo esencial: " + "; ".join(facts) + ".")
    # Estado, solo si aporta: una oferta vencida no puede presentarse como vigente.
    if chosen.get("conditions_state") == "documented_not_current":
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
