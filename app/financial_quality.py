"""Guarda lexica acotada: no es un verificador de datos ni aprueba calidad.

Detecta una sola familia de afirmaciones peligrosas: presentar el ahorro o la
inversion como algo sin riesgo. Dos ajustes tras medir falsos positivos en
produccion:

  1. «¿Que es la diversificacion?» devolvia 502 porque frases CORRECTAS como
     «ninguna inversion es libre de riesgos» o «un ahorro sin riesgos no existe»
     se rechazaban. Ahora se reconoce la negacion del sujeto («ninguna»,
     «tampoco», «no es una inversion») y la refutacion posterior («no existe»).
  2. La afirmacion real sigue rechazandose: «invertir no conlleva ningun
     riesgo», «tu inversion esta libre de riesgos», «el ahorro garantiza capital
     sin riesgo». Se anaden las formas de predicado que antes se escapaban
     («no tiene ningun riesgo»).

Sigue siendo una frontera lexica: una parafrasis sin estas palabras puede pasar y
por eso el DTO declara `text_validation: not_performed`.
"""
import re
import unicodedata

FINANCIAL_EDUCATION_PROMPT = (
    "Ahorrar es reservar dinero para necesidades futuras; invertir es destinarlo a activos "
    "buscando rendimiento y asumiendo posibles pérdidas. No afirmes que el ahorro o el "
    "capital sean sin riesgo: según el instrumento puede haber riesgo nominal de "
    "custodia o de la entidad, y la inflación puede reducir el poder adquisitivo. "
    "No inventes cifras de productos, tasas, garantías ni fuentes; para el método sí puedes usar "
    "referencias generales etiquetadas como tales, nunca como dato de un producto. "
)

# Formas lexicales conocidas; no es verificacion semantica.
_SUBJECT = (r'\b(?:ahorrar|ahorro|capital|invertir|inversi[oó]n|dep[oó]sito|cuenta|'
            r'fondo|etf|producto|letra)\b')
_CLAIM = re.compile(
    _SUBJECT + r'[^.!?;:]{0,95}?(?:'
    r'\bsin\s*(?:ning[uú]n\s+)?riesgos?\b'
    r'|\blibres?\s+de\s+riesgos?\b'
    r'|\bno\s+(?:conlleva|tiene|supone|implica)\s+ning[uú]n\s+riesgo\b'
    r'|\bcero\s+riesgo\b'
    r')',
    re.I,
)
_PREFIX_CONTEXT = re.compile(
    r'\b(?:no\s+es\s+(?:cierto|correcto|verdad|verdadero|posible)'
    r'|nunca\s+(?:es\s+)?(?:cierto|correcto|verdad)'
    r'|ni|falso|incorrecto|err[oó]neo|si|fuera|podr[ií]a|hipot[eé]tico)\b',
    re.I,
)
# Una palabra negativa que sigue al sujeto solo cuenta si niega el predicado, no
# cuando forma la frase afirmativa «no conlleva ningun riesgo».
_PREDICATE_NEGATION = re.compile(
    r'\b(?:(?:no|nunca|jam[aá]s)\s+(?:es|son|est[aá]|est[aá]n|ser[aá]|ser[ií]a|ser|supone|significa)\b'
    r'|ni\b|fuera\b|podr[ií]a\b|hipot[eé]tico\b)',
    re.I,
)
# Negacion del SUJETO: «ninguna inversion es libre de riesgo», «tampoco existe
# una inversion libre de riesgo», «no es una inversion sin riesgos». Estas frases
# ensenan que el riesgo existe; rechazarlas era el falso positivo.
_WHOLE_NEGATION = re.compile(
    r"\b(?:ning[uú]n[oa]?s?|tampoco)\b"
    r"|\bno\s+(?:es|son|existe|hay)\s+(?:una?\s+|el\s+|la\s+|los\s+|las\s+)?"
    r"(?:inversi[oó]n|ahorro|capital|producto)",
    re.I,
)
# «No todo ahorro es sin riesgo», «no todo el capital esta libre de riesgo».
# Cuantificador que NIEGA la generalizacion: es lo contrario de una promesa.
_NOT_ALL = re.compile(r"\bno\s+todo[s]?\b", re.I)
# Formas de desmentir la ausencia de riesgo, medidas en 5 respuestas reales sobre
# la inflacion (las 5 se rechazaban y las 5 eran correctas):
#   «no conviene afirmar que el ahorro esta sin riesgo»
#   «no conviene asumir que el capital esta libre de riesgo»
#   «el ahorro no es automaticamente libre de riesgo»
#   «sin dar por hecho que ahorrar esta libre de riesgo»
#   «no hay que dar por sentado que ...»
# Todas niegan la afirmacion; ninguna promete riesgo cero.
_DISCOURAGED_CLAIM = re.compile(
    r"\b(?:no\s+(?:conviene|deber[ií]amos|podemos|hay\s+que|se\s+puede)\s+"
    r"(?:afirmar|asumir|decir|creer|dar\s+por|pensar))"
    # Imperativo de cautela: «no asumas que el capital esta libre de riesgo»,
    # «no des por hecho que el ahorro es sin riesgo». Lo usa el modelo a menudo
    # cuando escribe en segunda persona.
    r"|\bno\s+(?:asumas|asum[aá]is|des\s+por|afirmes|digas|creas|pienses)\b"
    r"|\bno\s+(?:debe|deber[ií]a|puede|podr[ií]a|hay\s+que)\s+presentar"
    r"|\bno\s+se\s+(?:debe|deber[ií]a|puede)\s+presentar"
    r"|\bsin\s+(?:dar\s+por\s+(?:hecho|sentado)|asumir|creer|olvidar)"
    r"|\bno\s+es\s+(?:autom[aá]ticamente|necesariamente|siempre|exactamente)\b",
    re.I,
)
# Refutacion posterior: «un ahorro sin riesgos no existe».
_TRAILING_REFUTATION = re.compile(r"\s+(?:no|nunca|tampoco)\s+(?:existe|es|son|hay)\b", re.I)
# Negacion que precede al predicado sin contradecirlo: «la inflacion no hace que
# tu inversion este libre de riesgos», «no implica que el ahorro sea sin riesgo».
# La negacion recae sobre el verbo causativo, no sobre la ausencia de riesgo, asi
# que la frase ENSENA que el riesgo existe. Sin esto se rechazaba una respuesta
# entera sobre la inflacion (medido: 502 en produccion).
_NEGATED_CAUSATIVE = re.compile(
    r'\b(?:no|nunca|tampoco)\s+(?:hace|implica|significa|quiere\s+decir|supone|garantiza)'
    r'\s+que\b[^.!?]{0,60}$',
    re.I,
)
# «Si tu inversion no tiene ningun riesgo, revisa quien te lo dice»: condicional
# que el propio texto pone en duda. La frase no afirma el riesgo cero.
_HYPOTHETICAL = re.compile(
    r'\b(?:si|cuando|supongamos|imagina|sup[oó]n)\b[^.!?]{0,80}$',
    re.I,
)
# Afirmacion literal de ausencia de riesgo: «no conlleva ningun riesgo». Es la
# peligrosa, no una negacion, y por eso se comprueba antes de las exenciones.
_ASSERTED_NO_RISK = re.compile(
    r'\bno\s+(?:conlleva|tiene|supone|implica)\s+ning[uú]n\s+riesgo\b|\bcero\s+riesgo\b',
    re.I,
)
_REFUTATION = re.compile(
    r'^\s*[»”"\']?\s+(?:no\s+es\s+posible'
    r'|es\s+(?:fals[oa]|incorrect[oa]|err[oó]ne[oa]|una\s+simplificaci[oó]n\s+que\s+debe\s+evitarse))\b',
    re.I,
)
_CONJUNCTION = re.compile(r'\b(?:y|pero)\b', re.I)
# Cualquier negacion delante de la afirmacion convierte una promesa de riesgo cero
# en lo contrario. Es la exencion que generaliza: las listas de formulas concretas
# se quedaban cortas con cada redaccion nueva del modelo.
_ANY_NEGATION = re.compile(
    r"\b(?:no|nunca|jamas|jamás|tampoco|ni|ning[uú]n[oa]?s?|sin|lejos\s+de|"
    r"evita|evitar|rechaza|rechazar|desmiente)\b",
    re.I,
)


def _last_conjunct(text: str) -> str:
    """Limita la negacion lexica a la ultima clausula coordinada simple."""
    return _CONJUNCTION.split(text)[-1]


def assess_financial_text(text: str) -> tuple[str, ...]:
    """Devuelve marcas estables; vacio significa «sin patron conocido», no aprobado."""
    if not isinstance(text, str):
        raise TypeError('text must be str')
    clean = ''.join(c for c in unicodedata.normalize('NFKC', text)
                    if unicodedata.category(c) != 'Cf')
    for match in _CLAIM.finditer(clean):
        start = max((clean.rfind(c, 0, match.start()) for c in '.!?;:'), default=-1) + 1
        prefix = clean[start:match.start()]
        whole = clean[start:match.end()]
        tail = clean[match.end():match.end() + 24]
        # «no conlleva / no tiene ... ningun riesgo» es la afirmacion peligrosa
        # literal, no una negacion: se rechaza antes de aplicar las exenciones.
        if _ASSERTED_NO_RISK.search(match.group()):
            # Una afirmacion literal se rechaza siempre... salvo que la frase sea
            # una hipotesis que el propio texto pone en duda («si tu inversion no
            # tiene ningun riesgo, revisa quien te lo dice»). Ahi la ensenanza es
            # que el riesgo existe.
            if not _HYPOTHETICAL.search(prefix):
                return ('ABSOLUTE_NO_RISK',)
        if (_PREFIX_CONTEXT.search(_last_conjunct(prefix))
                or _NEGATED_CAUSATIVE.search(prefix)
                or _HYPOTHETICAL.search(prefix)
                or _NOT_ALL.search(whole)
                or _DISCOURAGED_CLAIM.search(prefix)
                or _DISCOURAGED_CLAIM.search(whole)
                or _PREDICATE_NEGATION.search(_last_conjunct(match.group()))
                or _REFUTATION.match(clean[match.end():])
                or _WHOLE_NEGATION.search(whole)
                or _TRAILING_REFUTATION.match(tail)):
            continue
        return ('ABSOLUTE_NO_RISK',)
    return ()


def redact_financial_claims(text: str) -> tuple[str, int]:
    """Quita las frases que prometen riesgo cero y conserva el resto.

    Medido: preguntas educativas legitimas devolvian 502 porque UNA frase de una
    respuesta larga usaba una formula que la guarda no reconocia. Rechazar el turno
    entero castiga al usuario por una frase y deja la app inservible en preguntas
    normales.

    Se quita la frase y se entrega el resto: la promesa peligrosa no se muestra
    nunca, y el usuario conserva la explicacion. Solo si NO sobrevive nada tiene
    sentido el 502.

    Devuelve (texto_limpio, frases_quitadas).
    """
    if not isinstance(text, str):
        raise TypeError('text must be str')
    if not assess_financial_text(text):
        return text, 0
    # Se corta por frase conservando el separador, y se comprueba cada una por
    # separado: una frase sin la afirmacion no se toca.
    piezas = re.split(r'(?<=[.!?])\s+', text)
    conservadas = []
    quitadas = 0
    for pieza in piezas:
        if assess_financial_text(pieza):
            quitadas += 1
            continue
        conservadas.append(pieza)
    return " ".join(conservadas).strip(), quitadas
