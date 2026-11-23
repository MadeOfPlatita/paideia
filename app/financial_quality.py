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
_SUBJECT = r'\b(?:ahorrar|ahorro|capital|invertir|inversi[oó]n)\b'
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
# Refutacion posterior: «un ahorro sin riesgos no existe».
_TRAILING_REFUTATION = re.compile(r"\s+(?:no|nunca|tampoco)\s+(?:existe|es|son|hay)\b", re.I)
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
            return ('ABSOLUTE_NO_RISK',)
        if (_PREFIX_CONTEXT.search(_last_conjunct(prefix))
                or _PREDICATE_NEGATION.search(_last_conjunct(match.group()))
                or _REFUTATION.match(clean[match.end():])
                or _WHOLE_NEGATION.search(whole)
                or _TRAILING_REFUTATION.match(tail)):
            continue
        return ('ABSOLUTE_NO_RISK',)
    return ()
