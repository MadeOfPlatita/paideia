"""La ficha deja de listar como desconocido lo que ya documenta con fuente.

La instantánea de investigación marcó campos que después se transcribieron. El
catálogo no puede seguir diciendo «plazos disponibles: desconocido» cuando la
ficha trae los tres plazos con su URL. Tampoco puede borrar la etiqueta si el
dato sigue sin publicarse: eso sería inventar.
"""

import http.client
import json
import threading
import unittest

import app


class ConditionsStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def get(self, path):
        conexion = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conexion.request("GET", path, headers={"Host": f"127.0.0.1:{self.server.server_port}"})
        respuesta = conexion.getresponse()
        datos = json.loads(respuesta.read().decode("utf-8"))
        conexion.close()
        self.assertEqual(respuesta.status, 200)
        return datos

    def item(self, product_id):
        catalogo = self.get("/api/catalogue")
        return next(i for i in catalogo["items"] if i["id"] == product_id)

    def test_a_documented_product_is_no_longer_pending(self):
        deposito = self.item("DEP-01")
        self.assertEqual(deposito["conditions_state"], "documented")

    def test_unknown_labels_already_documented_disappear(self):
        desconocidos = self.item("DEP-01")["unknown_fields"]
        self.assertNotIn("plazos disponibles", desconocidos)
        self.assertNotIn("TIN/TAE por plazo", desconocidos)
        self.assertNotIn("mínimo/máximo", desconocidos)
        self.assertNotIn("liquidación de intereses", desconocidos)

    def test_labels_without_a_published_value_stay(self):
        # DEP-01 no publica divisa ni condiciones de alta: siguen como desconocidas.
        desconocidos = self.item("DEP-01")["unknown_fields"]
        self.assertIn("divisa explícita", desconocidos)
        self.assertIn("disponibilidad de alta y elegibilidad por cliente", desconocidos)

    def test_a_balance_without_maximum_keeps_the_label(self):
        # ACC-01 dice que no hay saldo máximo, pero no publica una cifra: no se afirma.
        self.assertIn("saldo máximo remunerado", self.item("ACC-01")["unknown_fields"])

    def test_the_detail_view_uses_the_same_state(self):
        ficha = self.get("/api/products/DEP-01")["product"]
        self.assertEqual(ficha["conditions_state"], "documented")
        self.assertNotIn("plazos disponibles", ficha["unknown_fields"])

    def test_a_label_without_a_rule_is_never_removed(self):
        # El recorte empareja por texto y exige todos los campos de la regla: una
        # etiqueta que no encaja se queda, aunque la ficha documente otras cosas.
        self.assertFalse(app._unknown_label_is_documented(
            "divisa explícita", {"rate", "term", "min", "max", "payment", "validity", "documented"}))
        self.assertFalse(app._unknown_label_is_documented(
            "saldo máximo remunerado", {"rate", "term"}))
        self.assertTrue(app._unknown_label_is_documented(
            "plazos disponibles", {"rate", "term"}))

    def test_documented_currency_and_promotion_end_stop_being_unknown(self):
        # ACC-01 publica divisa base y tipo posterior: no pueden seguir como huecos.
        desconocidos = self.item("ACC-01")["unknown_fields"]
        self.assertNotIn("divisa de la cuenta explícita", desconocidos)
        self.assertNotIn("tipo aplicable después de la promoción", desconocidos)
        self.assertIn("saldo máximo remunerado", desconocidos)
        self.assertIn("derechos de copia/cache/display", desconocidos)

    def test_new_rules_only_fire_with_their_own_field(self):
        self.assertTrue(app._unknown_label_is_documented("comisiones aplicadas", {"fees"}))
        self.assertTrue(app._unknown_label_is_documented("garantía de depósitos", {"deposit_guarantee"}))
        self.assertTrue(app._unknown_label_is_documented("elegibilidad por cliente", {"eligibility"}))
        self.assertFalse(app._unknown_label_is_documented("comisiones aplicadas", {"rate", "term"}))


if __name__ == "__main__":
    unittest.main()
