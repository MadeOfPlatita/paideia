"""El turno de calculadora conserva el razonamiento y no enseña encabezados.

CASO REAL medido EN PANTALLA. La pregunta era una decisión práctica:

    «Soy un estudiante con 2000 euros. El año que viene tengo un gasto de 1500
     euros por estudios. ¿Qué hago con el dinero?»

El modelo llamó a `calculate_scenario` y respondió con cuatro secciones markdown
(«## Qué hace un 2 % en tus cifras», «## Qué descarto y por qué», «## Qué sí
encaja, por categoría», «## Decisión práctica»). El backend entró en
`_withhold_unbacked_claim` con `calculation is not None` y borró 16 frases: todas
las que llevaban una cifra o un número escrito con palabras. Lo que quedó:

    ## Qué hace un 2 % en tus cifras

Es decir: un encabezado markdown crudo (almohadillas a la vista) y ningún
razonamiento. El usuario preguntaba qué hacer con su dinero y la aplicación le
contestaba con un título.

LA CAUSA, en dos partes que se suman:

1. `_redact_unbacked_figures(strict=True)` partía el texto por frases con
   `(?<=[.!?])\\s+`. Un encabezado markdown NO termina en punto, así que la
   partición lo pegaba a la primera frase de su sección. Si esa frase llevaba una
   cifra, caía el título con ella; y los títulos de las secciones que sobrevivían
   quedaban pegados EN MEDIO de una frase («…comisión. ## Qué sí encaja…»), donde
   el recorte del frontend —que solo mira el principio de línea— ya no los quita.
2. El razonamiento se perdía porque casi todas las frases que lo contaban citaban
   los importes DE LA PERSONA («no dejaría los 2.000 euros bloqueados»). La rama
   estricta las trataba igual que una cifra inventada del modelo.

LA REGLA QUE SE FIJA AQUÍ:

- un encabezado viaja con su contenido o no viaja: nunca queda solo ni con
  almohadillas;
- una frase que SOLO repite importes que la persona ha escrito se conserva: es su
  dato, no una cifra del modelo;
- en cuanto la frase añade una tasa, un resultado, un coste, un sujeto de
  producto, una atribución, una fecha o una cifra que no es de la persona, se
  redacta como cualquier otra: la exención es una cita, no un permiso.

Ninguna prueba de aquí toca la red ni un proveedor real: el «modelo» es un
`FakeChatProvider` con respuestas fijas y el motor es el determinista local.
"""

import json
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))
sys.path.insert(0, str(TESTS_DIR))

import backend_services as bs  # noqa: E402
from pai_runtime import ANSWER_TEXT_SHOWN  # noqa: E402

# La pregunta real, con sus dos importes. Se escribe sin «qué hago» a propósito:
# las preguntas de método se atienden sin herramientas (`practical=True`), y aquí
# hace falta el turno de calculadora, que sí las abre.
PREGUNTA = ("Tengo 2000 euros y el año que viene tengo un gasto de 1500 euros por "
            "estudios. Cuánto saco al 2 % en un año?")

# La respuesta real, con la forma que produce el modelo: encabezados markdown,
# secciones de una o dos frases y listas numeradas.
RESPUESTA_REAL = """## Qué hace un 2 % en tus cifras

Con 2.000 euros al 2 % sacarías unos 40 euros en un año. El gasto de 1.500 euros no queda cubierto por ese interés.

## Qué descarto y por qué

No dejaría los 2.000 euros bloqueados a 12 meses, porque el gasto de 1.500 euros llega antes del vencimiento.

## Qué sí encaja, por categoría

1. Una cuenta de ahorro remunerada: disponibilidad diaria y sin plazo.
2. Un depósito a 6 meses: si el gasto es dentro de un año, el dinero llega a tiempo.
3. Letras del Tesoro a 6 meses: se compran en subasta, no en mercado secundario.

## Decisión práctica

Separaría los 1.500 euros del gasto en una cuenta disponible y dejaría el resto en un depósito corto, y movería los 2.000 euros solo cuando el gasto esté cubierto.

## Un aviso importante

Ningún producto serio te ofrece un 8 % sin riesgo."""


class EncabezadosMarkdownTests(unittest.TestCase):
    """B4-C5-01: un encabezado nunca llega crudo a la pantalla."""

    def test_el_aplanado_une_el_titulo_a_su_primera_frase(self):
        aplanado = bs._flatten_markdown_headings(RESPUESTA_REAL)

        self.assertNotIn("##", aplanado, aplanado)
        self.assertNotIn("#", aplanado, aplanado)
        # El texto del título se conserva: es información, no ruido.
        self.assertIn("Qué descarto y por qué", aplanado)
        self.assertIn("Decisión práctica", aplanado)
        # Y va unido a su contenido, no suelto en su propia línea.
        self.assertIn("Qué descarto y por qué: no dejaría", aplanado)

    def test_un_texto_sin_almohadillas_no_se_toca(self):
        texto = "El TIN es el tipo nominal. La TAE incorpora comisiones."
        self.assertEqual(bs._flatten_markdown_headings(texto), texto)

    def test_una_almohadilla_dentro_de_una_frase_no_es_un_encabezado(self):
        texto = "La TAE #1 del mercado no es la que te ofrecen."
        self.assertEqual(bs._flatten_markdown_headings(texto), texto)

    def test_un_titulo_sin_cuerpo_no_se_queda_como_ultima_linea(self):
        aplanado = bs._flatten_markdown_headings(
            "Miraría primero la fecha del gasto.\n## Qué descarto y por qué")
        self.assertNotIn("##", aplanado)
        self.assertTrue(aplanado.startswith("Miraría primero la fecha"))

    def test_un_titulo_sobre_una_tabla_no_se_fusiona_con_las_barras(self):
        aplanado = bs._flatten_markdown_headings(
            "## Qué mirar\n| Elemento | Qué mirar |\n| --- | --- |\n| TAE | la tasa anual |")
        self.assertNotIn("##", aplanado)
        # La tabla sigue siendo una tabla: la convierte `_strip_markdown_tables`.
        self.assertIn("| Elemento |", aplanado)


class RazonamientoConservadoTests(unittest.TestCase):
    """B4-C5-02: la respuesta de una decisión práctica conserva el razonamiento."""

    def test_la_redaccion_estricta_no_borra_las_cifras_del_usuario(self):
        limpio, quitadas = bs._redact_unbacked_figures(
            RESPUESTA_REAL, strict=True, user_text=PREGUNTA)

        self.assertGreater(limpio.strip(), "", "el razonamiento no puede desaparecer")
        self.assertNotIn("##", limpio, "no puede quedar un encabezado crudo")
        # Lo que la persona dijo, citado dentro del razonamiento, sobrevive.
        self.assertIn("no dejaría los 2.000 euros bloqueados", limpio)
        self.assertIn("el gasto de 1.500 euros llega antes", limpio)
        # Y lo que el modelo se inventó, no.
        self.assertNotIn("40 euros", limpio, "el interés estimado por el modelo no se publica")
        self.assertNotIn("8 %", limpio, "una rentabilidad inventada no se publica")
        self.assertGreater(quitadas, 0, "alguna frase sí tenía que caer")

    def test_sin_los_textos_del_usuario_la_frontera_sigue_siendo_cerrada(self):
        """Sin sus datos no hay exención: fail-closed, como antes."""
        limpio, _ = bs._redact_unbacked_figures(RESPUESTA_REAL, strict=True)
        self.assertNotIn("2.000 euros", limpio)
        self.assertNotIn("1.500 euros", limpio)
        self.assertNotIn("##", limpio)

    def test_la_respuesta_ya_no_empieza_por_un_encabezado(self):
        limpio, _ = bs._redact_unbacked_figures(
            RESPUESTA_REAL, strict=True, user_text=PREGUNTA)
        self.assertFalse(limpio.lstrip().startswith("#"))
        self.assertFalse(limpio.lstrip().startswith("##"))
        # Y no empieza por un título huérfano: si el primer trozo es un título, le
        # falta su contenido. Se comprueba que la primera frase tiene verbo, es
        # decir, que no es solo una etiqueta.
        primera = limpio.split(".")[0]
        self.assertGreater(len(primera.split()), 4, f"arranca con una etiqueta: {primera!r}")

    def test_la_explicacion_del_catalogo_tambien_conserva_el_razonamiento(self):
        """La misma frontera alimenta la respuesta compuesta del catálogo."""
        limpio = bs._catalogue_explanation(RESPUESTA_REAL, user_text=PREGUNTA)

        self.assertIsNotNone(limpio, "una respuesta con razonamiento no puede quedarse en nada")
        assert limpio is not None
        self.assertNotIn("##", limpio)
        self.assertNotIn("8 %", limpio)
        self.assertIn("no dejaría", limpio)


class ExencionCerradaTests(unittest.TestCase):
    """B4-C5-03: la exención es una cita, no un permiso para afirmar."""

    def test_solo_se_exime_el_importe_que_la_persona_escribio(self):
        permitido = bs._piece_only_quotes_user_amounts(
            "No dejaría los 1.500 euros bloqueados un año.",
            bs._user_supplied_amounts(PREGUNTA))
        self.assertTrue(permitido)

    CASOS_PROHIBIDOS = (
        # El importe es del usuario, pero la frase le añade un rendimiento.
        "Puedes sacar 1.500 euros al año.",
        # El importe es del usuario, pero la frase lo atribuye a un producto.
        "Ese depósito exige 1.500 euros.",
        # El importe es del usuario, pero la frase lo presenta como coste.
        "El banco cobra 1.500 euros de comisión.",
        # El importe es del usuario, pero la frase dice que es un mínimo.
        "La cuenta exige un mínimo de 1.500 euros.",
        # El importe es del usuario, pero la frase lo presenta como resultado.
        "El resultado sería 1.500 euros.",
        # Una cifra con palabras no es una cita del importe aunque el importe esté.
        "Ganarás mil euros con 1.500 euros.",
        # Un segundo importe que la persona no dijo.
        "Deja 1.500 euros y otros 3.000 euros aparte.",
        # Una atribución, aunque el importe sea del usuario.
        "Según la ficha, el gasto de 1.500 euros es el mínimo.",
        # Una fecha, aunque el importe sea del usuario.
        "El 1 de enero de 2026 tendrás 1.500 euros.",
    )

    def test_una_cifra_suelta_sin_moneda_ni_tasa_no_la_ve_la_frontera(self):
        """Un número suelto sin moneda ni tasa no es una cifra para esta frontera.

        Es comportamiento PREVIO y deliberado: la rama estricta persigue importes
        («1.000 €», «500 euros») y tasas («3 %»), y un «1.500» a secas es un plazo o
        una enumeración (`_MONEY_FIGURE`). Se deja fijado aquí para que nadie
        confunda esta holgura con la exención nueva: la exención NUNCA exime una
        cifra que la frontera ya considere cifra.
        """
        limpio, quitadas = bs._redact_unbacked_figures(
            "Puedes poner 1.500 en la cuenta.", strict=True, user_text=PREGUNTA)
        self.assertEqual(quitadas, 0)
        self.assertIn("1.500", limpio)

    def test_una_afirmacion_adicional_anula_la_exencion(self):
        cantidades = bs._user_supplied_amounts(PREGUNTA)
        for frase in self.CASOS_PROHIBIDOS:
            with self.subTest(frase=frase):
                self.assertFalse(
                    bs._piece_only_quotes_user_amounts(frase, cantidades),
                    f"no puede eximirse una frase que afirma algo más: {frase!r}")
                limpio, quitadas = bs._redact_unbacked_figures(
                    frase, strict=True, user_text=PREGUNTA)
                self.assertEqual(limpio.strip(), "",
                                 f"la frase tenía que caer entera: {frase!r}")
                self.assertEqual(quitadas, 1)

    def test_los_formatos_del_mismo_importe_se_reconocen(self):
        cantidades = bs._user_supplied_amounts("Tengo 1500 euros.")
        for variante in ("1.500 euros", "1500 euros", "1.500,00 euros"):
            with self.subTest(variante=variante):
                self.assertIn(bs._canonical_amount(variante.split()[0]),
                              cantidades, f"no se reconoció {variante!r}")


class TurnoDeCalculadoraHttpTests(unittest.TestCase):
    """B4-C5-04: por HTTP, el turno entrega razonamiento y resultado del motor.

    Sin red: proveedor falso con respuestas fijas y dispatcher real.
    """

    ARGS = {
        "principal": "2000.00", "annual_rate_percent": "2.00", "years": 1,
        "monthly_contribution": "0.00", "method": "simple",
        "inflation_percent": "0.00",
    }

    def service(self, answer):
        from backend_services import LocalChatService
        from catalogue_adapter import CatalogueWithConditions
        from pai_tools import ToolDispatcher
        from providers import ChatResult, ToolCall
        from structured_provider_adapter import FakeChatProvider
        from test_b4_condition_provenance import SyntheticConditionsService, SyntheticRepository
        from test_backend_integration import request, running_server
        from test_functional05_http import CONSENT, make_gate

        provider = FakeChatProvider(None, test_only=True, outcomes=(
            ChatResult("", None, (ToolCall("c1", "calculate_scenario", dict(self.ARGS)),), "tool_calls"),
            ChatResult(answer, None, (), "stop"),
        ))
        service = LocalChatService(
            provider=provider, enabled=True, test_only=True,
            dispatcher=ToolDispatcher(
                CatalogueWithConditions(SyntheticRepository(), SyntheticConditionsService()),
                comparison_service=None),
            tools_enabled=True, admission=make_gate(), catalogue_usage_approved=True,
        )
        with running_server(chat_service=service) as server:
            return request(server, "/api/chat", {"message": PREGUNTA, "consent": CONSENT})

    def test_la_respuesta_trae_razonamiento_cifra_del_motor_y_ninguna_almohadilla(self):
        status, body = self.service(RESPUESTA_REAL)

        self.assertEqual(status, 200, body)
        respuesta = body["answer"]
        self.assertNotIn("##", respuesta, f"encabezado crudo en pantalla: {respuesta!r}")
        self.assertNotIn("**", respuesta)
        # El razonamiento que la respuesta perdía.
        self.assertIn("no dejaría", respuesta)
        self.assertIn("disponibilidad diaria", respuesta)
        # La cifra que el modelo se inventó, fuera.
        self.assertNotIn("8 %", respuesta)
        self.assertEqual(body["answer_text_state"], "shown_unverified")
        self.assertEqual(body["answer_provenance"]["text_validation"], "not_performed")
        # El resultado del motor viaja en `calculation`, que es de donde lo pinta la
        # interfaz (`renderChatCalculation`). No se pega al texto: pegado, el motor
        # aparecería dos veces cuando la prosa se retiene entera, y hay un contrato
        # que exige que este turno entregue exactamente la prosa cuando sobrevive.
        calculo = body.get("calculation")
        self.assertIsInstance(calculo, dict, body)
        self.assertEqual(calculo["summary"]["final_balance"], "2040.00")
        self.assertEqual(calculo["summary"]["interest"], "40.00")
        self.assertTrue(any("motor determinista" in nota
                            for nota in body["answer_provenance"]["limitations"]),
                        body["answer_provenance"]["limitations"])

    def test_una_respuesta_de_solo_cifras_del_modelo_no_publica_ninguna(self):
        """Si todo el texto es cifra inventada, queda el motor y nada más."""
        status, body = self.service(
            "## Qué ganas\nEl resultado sería 2500.00 EUR al 9 %.\n\n## Cuánto\nAcabas con 3000.00 EUR.")

        self.assertEqual(status, 200, body)
        respuesta = body["answer"]
        self.assertNotIn("2500", respuesta)
        self.assertNotIn("3000", respuesta)
        self.assertNotIn("9 %", respuesta)
        self.assertNotIn("##", respuesta)
        # El hueco no se queda: el motor sí calculó y su resultado se entrega.
        self.assertIn("motor local", respuesta)
        self.assertIn("2.040,00", respuesta)
        self.assertEqual(body["answer_text_state"], "shown_unverified")
        self.assertEqual(body["answer_provenance"]["withheld_reason"], "calculation")


class FronteraIntactaTests(unittest.TestCase):
    """B4-C5-05: lo que la frontera ya hacía bien sigue igual.

    Estos casos son el contrato de seguridad; se repiten aquí para que un cambio
    futuro en la exención de importes no los rompa en silencio.
    """

    def test_una_cifra_del_motor_atribuida_a_un_producto_se_sigue_quitando(self):
        limpio, quitadas = bs._redact_unbacked_figures(
            "La TAE del depósito es 2 %.", strict=True, user_text=PREGUNTA)
        self.assertEqual(limpio.strip(), "")
        self.assertEqual(quitadas, 1)

    def test_una_cifra_inventada_por_el_modelo_no_se_publica(self):
        for texto in ("El resultado sería 2500.00 EUR.",
                      "El saldo final es 9999.00.",
                      "TEST ONLY: el saldo final es 1.030,00 €."):
            with self.subTest(texto=texto):
                limpio, _ = bs._redact_unbacked_figures(
                    texto, strict=True, user_text=PREGUNTA)
                self.assertEqual(limpio.strip(), "")

    def test_el_texto_conceptual_sigue_saliendo_intacto(self):
        texto = "El cálculo es hipotético y lo hace el motor local."
        limpio, quitadas = bs._redact_unbacked_figures(
            texto, strict=True, user_text=PREGUNTA)
        self.assertEqual(limpio, texto)
        self.assertEqual(quitadas, 0)

    def test_el_vocabulario_de_manual_sigue_pasando(self):
        texto = ("El TIN es el tipo de interés nominal que aplica una entidad. "
                 "La TAE sí incorpora comisiones, por eso suele ser más alta.")
        limpio, quitadas = bs._redact_unbacked_figures(
            texto, strict=True, user_text=PREGUNTA)
        self.assertEqual(limpio, texto)
        self.assertEqual(quitadas, 0)

    def test_un_ejemplo_numerico_etiquetado_como_metodo_se_conserva(self):
        texto = "Por ejemplo, un 3 % anual sobre 1.000 euros."
        limpio, quitadas = bs._redact_unbacked_figures(
            texto, strict=True, user_text="")
        self.assertEqual(limpio, texto)
        self.assertEqual(quitadas, 0)

    def test_una_cifra_desmentida_no_se_borra(self):
        texto = "No existe una TAE garantizada del 8 % para el año que viene."
        limpio, quitadas = bs._redact_unbacked_figures(
            texto, strict=True, user_text="")
        self.assertIn("No existe una TAE garantizada", limpio)


class SinTablaTests(unittest.TestCase):
    """B4-C5-06: la respuesta no puede leerse como una tabla."""

    def test_no_quedan_tuberias_ni_filas_de_separacion(self):
        texto = RESPUESTA_REAL + "\n\n| Elemento | Qué mirar |\n| --- | --- |\n| TAE | la tasa |"
        limpio, _ = bs._redact_unbacked_figures(texto, strict=True, user_text=PREGUNTA)
        limpio = bs._strip_markdown_tables(limpio)
        self.assertNotIn("|", limpio)
        self.assertNotIn("---", limpio)

    def test_no_quedan_listas_con_numeros_huerfanos(self):
        """Al caer un paso numerado, su número se va con él."""
        texto = ("1. Mira el plazo del gasto. "
                 "2. Reserva 1.500 euros al 9 % en un producto inventado. "
                 "3. Comprueba la liquidez.")
        limpio, quitadas = bs._redact_unbacked_figures(
            texto, strict=True, user_text=PREGUNTA)
        self.assertGreater(quitadas, 0)
        self.assertNotRegex(limpio, r"\d\.\s+\d\.")
        self.assertIn("Mira el plazo", limpio)
        self.assertIn("Comprueba la liquidez", limpio)


class DtoYProcedenciaTests(unittest.TestCase):
    """B4-C5-07: cuando se muestra prosa, la procedencia lo dice sin contradecirse."""

    def test_si_el_razonamiento_se_muestra_no_se_declara_omitido(self):
        # `_withhold_unbacked_claim` con cálculo y prosa parcial: se muestra y NO
        # puede llevar el aviso de «se ha omitido el texto del modelo».
        texto, estado, resultado = bs._withhold_unbacked_claim(
            {"limitations": [], "catalogue": {"used": False}},
            RESPUESTA_REAL, ANSWER_TEXT_SHOWN, {"summary": {"final_balance": "2040.00"}},
            user_text=PREGUNTA)

        self.assertTrue(texto.strip(), "el razonamiento no puede perderse")
        self.assertEqual(estado, ANSWER_TEXT_SHOWN)
        self.assertNotIn("withheld_reason", resultado,
                         "no se declaró retención porque hay texto mostrado")
        self.assertNotIn("##", texto)
        self.assertGreater(resultado["redacted_figures"], 0)
        # Y el número que se declara coincide con el que se ha quitado de verdad.
        self.assertTrue(any("calculadora" in nota for nota in resultado["limitations"]))


if __name__ == "__main__":
    unittest.main()
