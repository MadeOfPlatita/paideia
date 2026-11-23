"""Respuesta determinista con las condiciones verificadas del catálogo.

Cuando el turno usó herramientas, la prosa del modelo no se entrega (su
atribución no se puede validar contra la fuente). Hasta ahora se sustituía por
una nota fija que no contestaba la pregunta: a «¿qué TAE tiene el depósito de
EBN?» el usuario leía «no repito cifras en prosa» y nunca veía el 3,1 %.

Esta capa compone la respuesta con los datos que ya vienen verificados en el
DTO. No redacta el modelo y no inventa nada: cada línea es una condición con
valor, estado `known` y su fuente citada. Si no hay ninguna condición legible,
devuelve None y el servicio mantiene la nota anterior.
"""

from __future__ import annotations

import re

# Etiquetas y formato alineados con CONDITION_ROWS de app/static/app.js, para que
# el chat diga lo mismo que la ficha de la biblioteca.
_PERCENT_METRICS = {
    "annual_rate_percent": "Tasa anual (TAE)",
    "ter_percent": "TER",
    "management_fee_percent": "Comisión de gestión",
    "custody_fee_percent": "Comisión de depositario",
    "entry_fee_percent": "Comisión de entrada",
    "exit_fee_percent": "Comisión de salida",
    "performance_fee_percent": "Comisión de éxito",
    "marginal_rate_percent": "Tipo marginal",
    "withholding_percent": "Retención fiscal",
    "minimum_price_percent": "Precio mínimo aceptado",
}
_TEXT_METRICS = {
    "isin": "ISIN",
    "maximum_note": "Importe máximo",
    "minimum_note": "Importe mínimo",
    "subsequent_rate_note": "Tipo posterior",
    "category": "Categoría",
    "manager": "Gestora",
    "depositary": "Depositaria",
    "base_currency": "Divisa base",
    "replication": "Réplica",
    "maturity_date": "Vencimiento",
}
_EUR_METRICS = {
    "minimum_eur": "Inversión mínima",
    "maximum_eur": "Importe máximo",
    "nav_eur": "Valor liquidativo",
}
_OTHER_METRICS = {
    "term_months": "Plazo",
    "risk_scale": "Riesgo (SRI)",
    "holding_period_years": "Periodo recomendado",
}

# Se ordenan por relevancia para una persona que pregunta por un producto: primero
# la tasa y el plazo, luego los costes, luego el resto.
_PRIORITY = (
    "annual_rate_percent", "term_months", "maturity_date", "ter_percent",
    "management_fee_percent", "custody_fee_percent", "entry_fee_percent",
    "exit_fee_percent", "performance_fee_percent", "risk_scale", "minimum_eur",
    "maximum_eur", "isin",
)

MAX_LINES_PER_PRODUCT = 6
MAX_PRODUCTS = 4


def _format_number(raw):
    """Devuelve el valor legible de una condición, o None si no es presentable.

    No convierte unidades ni redondea a la ligera: el catálogo ya trae el valor
    con su unidad. Solo limpia el formato («3.1» → «3,1»), porque el usuario
    lee en castellano.
    """
    text = str(raw).strip()
    if not text:
        return None
    if re.fullmatch(r"-?\d+(?:[.,]\d+)?", text):
        return text.replace(".", ",")
    return text


def _claim_line(condition):
    metric = condition.get("metric")
    value = _format_number(condition.get("value"))
    if value is None:
        return None
    if condition.get("state") != "known":
        return None
    if metric in _PERCENT_METRICS:
        label = _PERCENT_METRICS[metric]
        return f"{label}: {value} %"
    if metric in _EUR_METRICS:
        return f"{_EUR_METRICS[metric]}: {value} €"
    if metric == "term_months":
        return f"Plazo: {value} meses"
    if metric == "holding_period_years":
        return f"Periodo recomendado: {value} años"
    if metric == "risk_scale":
        return f"Riesgo (SRI): {value} de 7"
    if metric in _TEXT_METRICS:
        return f"{_TEXT_METRICS[metric]}: {value}"
    if metric in _OTHER_METRICS:
        return f"{_OTHER_METRICS[metric]}: {value}"
    return None


def _source_url(condition):
    for source in condition.get("sources") or ():
        if not isinstance(source, dict):
            continue
        url = source.get("url")
        if isinstance(url, str) and url.startswith(("https://", "http://")):
            return url
    return None


def _product_lines(product):
    """Líneas de una ficha: identidad y condiciones conocidas, en orden de interés."""
    conditions = product.get("conditions")
    if not isinstance(conditions, list):
        return []
    by_metric = {}
    for condition in conditions:
        if not isinstance(condition, dict):
            continue
        metric = condition.get("metric")
        if metric not in by_metric and _claim_line(condition) is not None:
            by_metric[metric] = condition
    ordered = [by_metric[m] for m in _PRIORITY if m in by_metric]
    ordered += [c for m, c in by_metric.items() if m not in _PRIORITY]
    lines = []
    for condition in ordered[:MAX_LINES_PER_PRODUCT]:
        claim = _claim_line(condition)
        if claim is None:
            continue
        url = _source_url(condition)
        lines.append(f"{claim} ({url})" if url else claim)
    return lines


def compose_catalogue_answer(catalogue, limit=MAX_PRODUCTS):
    """Compone la respuesta con los productos y condiciones del DTO.

    Devuelve None cuando no hay ningún dato legible: en ese caso el servicio
    mantiene la nota anterior en lugar de inventar una respuesta vacía.
    """
    if not isinstance(catalogue, dict) or catalogue.get("used") is not True:
        return None
    products = catalogue.get("products")
    if not isinstance(products, list) or not products:
        return None

    blocks = []
    for product in products[:limit]:
        if not isinstance(product, dict):
            continue
        name = product.get("name")
        issuer = product.get("issuer")
        if not isinstance(name, str) or not name.strip():
            continue
        heading = f"{name} ({issuer})" if isinstance(issuer, str) and issuer.strip() else name
        lines = _product_lines(product)
        if not lines:
            continue
        blocks.append(heading + "\n- " + "\n- ".join(lines))

    if not blocks:
        return None

    total = catalogue.get("products_total")
    cuerpo = "\n\n".join(blocks)
    if isinstance(total, int) and total > len(blocks):
        cuerpo += (f"\n\nHay {total} productos en el catálogo; muestra de {len(blocks)}. "
                   "La ficha completa de cada uno está en la biblioteca.")

    return (
        "Según el catálogo local, con la fuente de cada dato entre paréntesis:\n\n"
        + cuerpo
        + "\n\nSon datos transcritos de fuentes oficiales, no una oferta ni una "
          "recomendación. No soy un asesor financiero."
    )
