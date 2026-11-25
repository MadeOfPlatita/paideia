"""Producto recomendado: el que la app elige, publicado para que la tarjeta lo use.

POR QUÉ EXISTE ESTE MÓDULO

Medido en producción: a «¿qué TAE tiene el depósito de EBN Banco?» el JSON de
`/api/chat` devolvía **3,10 % (Depósito Nuevo Ahorro 12 meses, EBN Banco)** en el
texto compuesto, mientras la pantalla enseñaba **2,4 % (Sinycon)**. Dos superficies
del mismo turno daban productos distintos.

La causa: la tarjeta del catálogo pintaba `products[0]`, el primero que llegaba en
el array, mientras el texto lo componía `compose_catalogue_answer`, que elige el
producto con `_pick_best` aplicando el criterio de la pregunta, el importe del
usuario y el descarte de ofertas vencidas. Nadie transmitía cuál se había elegido.

Este módulo expone esa elección para que viaje en el DTO. La tarjeta deja de
adivinar: si el servidor dice «este es el que encaja», la tarjeta enseña ese y
ningún otro.
"""

from catalogue_answer import (
    _is_current,
    _mentions_issuer,
    _minimum_eur,
    _pick_best,
    _product_heading,
    _question_intent,
    extract_amount_eur,
)


def recommended_product_id(catalogue, question=None, previous_questions=None):
    """El `id` del producto que la app recomienda en este turno, o None.

    Aplica EXACTAMENTE los mismos filtros que `compose_catalogue_answer`, en el
    mismo orden: legibilidad, mención del emisor, importe del usuario y descarte de
    ofertas vencidas. Si la composición cambiara de criterio y esto no, volverían a
    discrepar; por eso el orden se replica aquí paso a paso y no se inventa uno
    nuevo.

    Devuelve None cuando no hay ninguno legible: en ese caso la tarjeta mantiene su
    comportamiento anterior (pintar el que haya), que es mejor que no pintar nada.
    """
    if not isinstance(catalogue, dict) or catalogue.get("used") is not True:
        return None
    products = catalogue.get("products")
    if not isinstance(products, list) or not products:
        return None

    legibles = [p for p in products
                if isinstance(p, dict) and _product_heading(p) is not None]
    if not legibles:
        return None

    validos = legibles
    nombrados = [p for p in validos if _mentions_issuer(p, question)]
    if nombrados:
        validos = nombrados
        # Si la pregunta NOMBRA un producto o un banco, la recomendación es ese:
        # a «¿qué TAE tiene el depósito de Sinycon?» no se puede contestar con el
        # de EBN por muy buena que sea su tasa. Medido: sin este corte,
        # `_pick_best(intent="rate")` devolvía el de MAYOR tasa aunque la pregunta
        # pidiera otro producto concreto, y la pantalla y el texto discrepareban.
        if len(validos) == 1:
            identificador = validos[0].get("id")
            return identificador if isinstance(identificador, str) and identificador else None

    previos = [t for t in (previous_questions or ()) if isinstance(t, str) and t.strip()]
    cantidad = extract_amount_eur(question)
    if cantidad is None:
        for previo in reversed(previos):
            cantidad = extract_amount_eur(previo)
            if cantidad is not None:
                break
    if cantidad is not None:
        alcanzables = []
        for product in validos:
            minimo = _minimum_eur(product)
            if minimo is None or minimo <= cantidad:
                alcanzables.append(product)
        if alcanzables:
            validos = alcanzables

    vigentes = [p for p in validos if _is_current(p)]
    conjunto = vigentes or validos
    intent = _question_intent(question)
    best, _motivo = _pick_best(conjunto, intent)
    if best is None:
        return None
    _, chosen, _by_metric = best
    identificador = chosen.get("id")
    return identificador if isinstance(identificador, str) and identificador else None
