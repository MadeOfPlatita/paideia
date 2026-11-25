"""Una lista numerada no puede perder sus pasos al redactar cifras.

Medido EN PANTALLA con el escenario del estudiante: la respuesta traía

    1. Cuenta remunerada o cuenta de ahorro: liquidez inmediata…
    2. La rentabilidad depende del resultado de la subasta: no se puede prometer.
    3. Fondo monetario de bajo riesgo: liquidez alta…

El paso 2 no era un paso: era el RESTO del paso sobre las Letras del Tesoro, cuyo
enunciado se había borrado. Y la numeración quedaba desordenada. El usuario lee una
lista rota.

Dos causas, las dos en `_redact_unbacked_figures`:

1. `re.split(r"(?<=[.!?])\\s+")` partía en el punto de la NUMERACIÓN: «1. Cuenta
   remunerada» se convertía en «1.» + «Cuenta remunerada», así que el trozo dejaba
   de reconocerse como paso y se trataba como prosa suelta.
2. El número del paso («2.») bastaba para que la frase se marcara como «tiene una
   cifra» y se borrara entera.

La frontera de seguridad NO se relaja: una tasa o un importe del modelo se siguen
quitando. Lo que se distingue es la numeración de una lista, que no es un dato
financiero.
"""

import unittest

from backend_services import _redact_unbacked_figures


LISTA = ("Los tipos que encajan son: 1. Cuenta remunerada: liquidez inmediata. "
         "2. Letras del Tesoro a 6-12 meses: rentabilidad ligada a la subasta. "
         "3. Fondo monetario: liquidez alta pero no garantizado.")


class ListaNumeradaTests(unittest.TestCase):
    def test_una_lista_numerada_conserva_todos_sus_pasos(self):
        limpio, quitadas = _redact_unbacked_figures(LISTA, strict=True)
        self.assertEqual(quitadas, 0,
                         "ninguna frase de la lista contiene una cifra financiera")
        # Los tres pasos siguen ahí y en orden.
        self.assertIn("1. Cuenta remunerada", limpio)
        self.assertIn("2. Letras del Tesoro a 6-12 meses", limpio)
        self.assertIn("3. Fondo monetario", limpio)

    def test_un_rango_de_meses_no_es_una_tasa(self):
        # «6-12 meses» es un plazo, no una tasa: no puede marcar la frase como cifra.
        limpio, quitadas = _redact_unbacked_figures(
            "2. Letras del Tesoro a 6-12 meses: riesgo de precio.", strict=True)
        self.assertEqual(quitadas, 0)
        self.assertIn("6-12 meses", limpio)

    def test_la_numeracion_no_deja_puntos_sueltos(self):
        # Al restaurar el punto del paso no puede quedar «3.Fondo» pegado.
        limpio, _ = _redact_unbacked_figures(LISTA, strict=True)
        self.assertNotIn("3.Fondo", limpio)
        self.assertNotIn("1.Cuenta", limpio)
        self.assertNotIn("2.Letras", limpio)

    def test_un_paso_que_si_lleva_una_tasa_se_quita(self):
        # La exención es solo para la numeración: el contenido con tasa cae.
        texto = "1. Cuenta al 3,10 % TAE: liquidez inmediata. 2. Fondo monetario."
        limpio, quitadas = _redact_unbacked_figures(texto, strict=True)
        self.assertGreaterEqual(quitadas, 1,
                                "una tasa del modelo no se publica")
        self.assertNotIn("3,10", limpio)


class FronteraIntactaTests(unittest.TestCase):
    """Lo que este cambio NO puede debilitar."""

    def test_una_tasa_del_modelo_se_sigue_quitando(self):
        for texto in ("La TAE del depósito es 3,10 %.",
                      "Daría un 4 % anual.",
                      "La TAE del fondo es 1,2 %",
                      "un 3 % TAE"):
            with self.subTest(texto=texto):
                limpio, quitadas = _redact_unbacked_figures(texto, strict=True)
                self.assertEqual(quitadas, 1, texto)
                self.assertNotIn("3,10", limpio)
                self.assertNotIn("4 %", limpio)

    def test_una_tasa_sin_el_simbolo_tambien_se_quita(self):
        # El símbolo no es obligatorio: «paga 3,25 al año» es una tasa aunque no lleve
        # «%». Al afinar el patrón para no confundir «6-12 meses» con una tasa, estas
        # cuatro formas se colaban y el test de la frontera las cazó.
        for texto in ("TEST ONLY: el producto paga 3,25 al año.",
                      "TEST ONLY: ese depósito ofrece 4,10 anual.",
                      "TEST ONLY: el producto rinde 3,25.",
                      "TEST ONLY: abona 3,25 mensual."):
            with self.subTest(texto=texto):
                limpio, quitadas = _redact_unbacked_figures(texto, strict=True)
                self.assertEqual(quitadas, 1, texto)
                self.assertNotIn("3,25", limpio)
                self.assertNotIn("4,10", limpio)

    def test_un_importe_bajo_un_concepto_erroneo_se_quita(self):
        limpio, quitadas = _redact_unbacked_figures(
            "El interés es 46,50 euros.", strict=True)
        self.assertEqual(quitadas, 1)
        self.assertNotIn("46,50", limpio)

    def test_una_cifra_inventada_sin_unidad_se_quita(self):
        limpio, quitadas = _redact_unbacked_figures(
            "TEST ONLY: el saldo final es 9999.00.", strict=True)
        self.assertEqual(quitadas, 1)
        self.assertNotIn("9999", limpio)

    def test_la_prosa_conceptual_intacta_se_conserva(self):
        for texto in ("El TIN es el tipo nominal que aplica la entidad.",
                      "La TAE incorpora comisiones y capitalización.",
                      "En doce meses puedes estar por debajo del importe aportado."):
            with self.subTest(texto=texto):
                _, quitadas = _redact_unbacked_figures(texto, strict=True)
                self.assertEqual(quitadas, 0, texto)


if __name__ == "__main__":
    unittest.main()
