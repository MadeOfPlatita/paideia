"""Narrow lexical guard, not a financial fact checker or quality approval."""
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

# Known lexical forms only; this is not semantic verification.
_SUBJECT = r'\b(?:ahorrar|ahorro|capital|invertir|inversi[oó]n)\b'
_CLAIM = re.compile(_SUBJECT + r'[^.!?;:]{0,95}?(?:\bsin\s*(?:ning[uú]n\s+)?riesgos?\b|\blibres?\s+de\s+riesgos?\b|\bno\s+conlleva\s+ning[uú]n\s+riesgo\b)', re.I)
_PREFIX_CONTEXT = re.compile(r'\b(?:no\s+es\s+(?:cierto|correcto|verdad|verdadero|posible)|nunca\s+(?:es\s+)?(?:cierto|correcto|verdad)|ni|falso|incorrecto|err[oó]neo|si|fuera|podr[ií]a|hipot[eé]tico)\b', re.I)
# A negative word following the subject counts only when it negates the
# predicate, not when it is the affirmative phrase "no conlleva ningún riesgo".
_PREDICATE_NEGATION = re.compile(r'\b(?:(?:no|nunca|jam[aá]s)\s+(?:es|son|est[aá]|est[aá]n|ser[aá]|ser[ií]a|ser|supone|significa)\b|ni\b|fuera\b|podr[ií]a\b|hipot[eé]tico\b)', re.I)
_REFUTATION = re.compile(r'^\s*[»”"\']?\s+(?:no\s+es\s+posible|es\s+(?:fals[oa]|incorrect[oa]|err[oó]ne[oa]|una\s+simplificaci[oó]n\s+que\s+debe\s+evitarse))\b', re.I)
_CONJUNCTION = re.compile(r'\b(?:y|pero)\b', re.I)

def _last_conjunct(text: str) -> str:
    """Limit lexical negation to the last simple coordinated clause."""
    return _CONJUNCTION.split(text)[-1]

def assess_financial_text(text: str) -> tuple[str, ...]:
    """Return stable flags only; empty means no known pattern, not approval."""
    if not isinstance(text, str):
        raise TypeError('text must be str')
    clean = ''.join(c for c in unicodedata.normalize('NFKC', text)
                    if unicodedata.category(c) != 'Cf')
    for match in _CLAIM.finditer(clean):
        start = max((clean.rfind(c, 0, match.start()) for c in '.!?;:'), default=-1) + 1
        prefix = clean[start:match.start()]
        if (_PREFIX_CONTEXT.search(_last_conjunct(prefix))
                or _PREDICATE_NEGATION.search(_last_conjunct(match.group()))
                or _REFUTATION.match(clean[match.end():])):
            continue
        return ('ABSOLUTE_NO_RISK',)
    return ()
