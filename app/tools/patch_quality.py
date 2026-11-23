"""La guarda financiera no debe rechazar frases que niegan el riesgo.

Falso positivo medido en produccion: «¿Que es la diversificacion?» devolvio
HTTP 502 CHAT_FINANCIAL_QUALITY_REJECTED porque la respuesta contenia una frase
correcta del tipo «ninguna inversion es libre de riesgos» o «no es una inversion
libre de riesgo». El detector busca sujeto (ahorro/inversion) + «sin riesgos» /
«libre de riesgo», pero solo miraba el prefijo y el predicado, no la negacion
que aparece ANTES del sujeto («ninguna», «no es una»).

La regla nueva: si entre el inicio de la frase y el final de la coincidencia hay
una negacion que afecta al conjunto («ninguna», «ningun», «no es», «no son»,
«tampoco», «ni»), la frase niega el riesgo absoluto y pasa. Se mantiene el
rechazo de la afirmacion real («invertir no conlleva ningun riesgo» ya se
detectaba por el predicado, y «una inversion sin riesgos» sigue rechazandose).

Todo sigue siendo una frontera lexica, no una validacion semantica.
"""

from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "financial_quality.py"

OLD = """_PREDICATE_NEGATION = re.compile(r'\\b(?:(?:no|nunca|jam[aá]s)\\s+(?:es|son|est[aá]|est[aá]n|ser[aá]|ser[ií]a|ser|supone|significa)\\b|ni\\b|fuera\\b|podr[ií]a\\b|hipot[eé]tico\\b)', re.I)"""

NEW = """_PREDICATE_NEGATION = re.compile(r'\\b(?:(?:no|nunca|jam[aá]s)\\s+(?:es|son|est[aá]|est[aá]n|ser[aá]|ser[ií]a|ser|supone|significa)\\b|ni\\b|fuera\\b|podr[ií]a\\b|hipot[eé]tico\\b)', re.I)
# Negacion que afecta al conjunto de la afirmacion, no solo al predicado:
# «ninguna inversion es libre de riesgo», «no es un ahorro sin riesgos»,
# «tampoco existe una inversion libre de riesgo». Estas frases ENSENAN que el
# riesgo existe; retenerlas era un falso positivo.
_WHOLE_NEGATION = re.compile(r"\\b(?:ning[uú]n[oa]?s?|tampoco|jam[aá]s|nunca)\\b|\\bno\\s+(?:es|son|existe|hay|significa)\\b", re.I)"""


def main() -> None:
    raw = TARGET.read_bytes().decode("utf-8")
    old, new = OLD, NEW
    if "\r\n" in raw:
        old = old.replace("\n", "\r\n")
        new = new.replace("\n", "\r\n")
    count = raw.count(old)
    if count != 1:
        raise SystemExit("se esperaba 1 coincidencia, hay %d" % count)
    raw = raw.replace(old, new)

    old_body = """        if (_PREFIX_CONTEXT.search(_last_conjunct(prefix))
                or _PREDICATE_NEGATION.search(_last_conjunct(match.group()))
                or _REFUTATION.match(clean[match.end():])):
            continue"""
    new_body = """        whole = clean[start:match.end()]
        if (_PREFIX_CONTEXT.search(_last_conjunct(prefix))
                or _PREDICATE_NEGATION.search(_last_conjunct(match.group()))
                or _REFUTATION.match(clean[match.end():])
                or _WHOLE_NEGATION.search(whole)):
            continue"""
    if "\r\n" in raw:
        old_body = old_body.replace("\n", "\r\n")
        new_body = new_body.replace("\n", "\r\n")
    count = raw.count(old_body)
    if count != 1:
        raise SystemExit("cuerpo: se esperaba 1 coincidencia, hay %d" % count)
    TARGET.write_bytes(raw.replace(old_body, new_body).encode("utf-8"))
    print("guarda financiera: negacion global reconocida")


if __name__ == "__main__":
    main()
