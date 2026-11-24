"""La guarda de «sin riesgo» no puede rechazar una respuesta que enseña que hay riesgo.

Medido en producción: «¿Qué es la inflación y cómo afecta a mis ahorros?» devolvió
502 CHAT_FINANCIAL_QUALITY_REJECTED. La pregunta es educativa y la respuesta
correcta; lo que fallaba era la guarda.

Dos causas, las dos de la misma familia: la frase enseña que el riesgo existe pero
la guarda la leía como una afirmación de riesgo cero.

  1. «La inflación no hace que tu inversión esté libre de riesgos». La negación
     recae sobre el verbo causativo («no hace que»), no sobre la ausencia de
     riesgo. Faltaba la exención.
  2. «Si tu inversión no tiene ningún riesgo, revisa quién te lo dice». Un
     condicional que el propio texto pone en duda. `_ASSERTED_NO_RISK` se
     comprobaba antes de las exenciones, así que se rechazaba.

Y dos huecos en el otro sentido, que sí importan: el sujeto solo miraba
ahorro/capital/inversión, así que «este depósito tiene cero riesgo» y «la cuenta no
tiene ningún riesgo» PASABAN. Una afirmación de riesgo cero sobre un producto
concreto es exactamente lo que hay que frenar.

La regla: la guarda protege al usuario de una promesa de riesgo cero, no de una
explicación que dice que el riesgo existe.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from financial_quality import assess_financial_text  # noqa: E402

# Frases correctas: enseñan que el riesgo existe. Deben pasar.
EDUCATIVAS = (
    "La inflación no hace que tu inversión esté libre de riesgos.",
    "Si tu inversión no tiene ningún riesgo, revisa quién te lo dice.",
    "Ningún ahorro está libre de riesgos.",
    "Una inversión sin riesgos no existe.",
    "El ahorro en efectivo tiene riesgo de inflación.",
    "La inflación reduce el poder adquisitivo de tus ahorros.",
    "El ahorro sin riesgos no existe: la inflación siempre está ahí.",
    "Tampoco existe una inversión libre de riesgo.",
)

# Afirmaciones peligrosas: prometen riesgo cero. Deben rechazarse.
AFIRMACIONES = (
    "Invertir no conlleva ningún riesgo.",
    "Tu inversión está libre de riesgos.",
    "El ahorro garantiza capital sin riesgo.",
    "Este depósito tiene cero riesgo.",
    "La cuenta no tiene ningún riesgo.",
    "Ese fondo está libre de riesgo.",
    "El producto no supone ningún riesgo.",
    "Esta letra del Tesoro es libre de riesgos.",
)


class NoRiskGuardTests(unittest.TestCase):
    def test_correct_teaching_is_not_rejected(self):
        for frase in EDUCATIVAS:
            with self.subTest(frase=frase):
                self.assertEqual(assess_financial_text(frase), (),
                                 f"una frase que enseña que hay riesgo no puede rechazarse: {frase!r}")

    def test_promises_of_zero_risk_are_rejected(self):
        for frase in AFIRMACIONES:
            with self.subTest(frase=frase):
                self.assertTrue(assess_financial_text(frase),
                                f"una promesa de riesgo cero no puede pasar: {frase!r}")

    def test_the_inflation_answer_that_failed_in_production_passes(self):
        # El texto completo que devolvió 502, resumido a las frases que lo causaban.
        respuesta = (
            "La inflación es la subida general de los precios. Cuando sube más que "
            "la remuneración de tus ahorros, pierdes poder adquisitivo aunque el "
            "saldo no baje. La inflación no hace que tu inversión esté libre de "
            "riesgos: el riesgo real es perder capacidad de compra."
        )
        self.assertEqual(assess_financial_text(respuesta), ())


if __name__ == "__main__":
    unittest.main()
