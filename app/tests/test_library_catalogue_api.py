"""La biblioteca debe servir y contar las 22 fichas, no 20.

Fallos medidos en la interfaz, encadenados:

1. `/api/catalogue` servía 20 productos (el snapshot base) mientras
   `/api/conditions` y el chat trabajaban con 22. Las dos fichas transcritas
   (DEP-EBN-12, DEP-SELF-12) existían pero la lista no las contaba: el usuario
   leía «20 candidatos» y podía abrir 22 fichas.

2. La sección «Productos con condiciones transcritas» se pintaba antes que los
   resultados del catálogo, así que duplicaba las dos tarjetas (24 en pantalla).

3. La tarjeta de un producto con 15 condiciones documentadas decía «Condiciones
   pendientes» porque el estado se escribía a mano como `pending`.

4. La tarjeta de un ETF decía «Sin tasa documentada» aunque tuviera 28 métricas:
   un ETF no tiene TAE, su dato es el TER.

5. `/api/products/<id>` devolvía dos listas de condiciones: las 28 dentro de
   `product` y un campo aparte con 7. La corta parecía la buena.
"""

import json
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as appmod  # noqa: E402


def servidor():
    server = appmod.create_server(port=0)
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    return server, hilo


class CatalogueLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server, cls.hilo = servidor()
        cls.puerto = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.hilo.join(timeout=3)

    def peticion(self, ruta):
        import http.client
        conexion = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=10)
        conexion.request("GET", ruta, headers={"Host": f"127.0.0.1:{self.puerto}"})
        respuesta = conexion.getresponse()
        cuerpo = json.loads(respuesta.read().decode("utf-8"))
        conexion.close()
        return respuesta.status, cuerpo

    def test_the_list_serves_all_22_and_counts_them(self):
        estado, cuerpo = self.peticion("/api/catalogue")
        self.assertEqual(estado, 200)
        self.assertEqual(cuerpo["count"], 22)
        self.assertEqual(len(cuerpo["items"]), 22)
        ids = {item["id"] for item in cuerpo["items"]}
        self.assertIn("DEP-EBN-12", ids, "la ficha transcrita debe estar en la lista")
        self.assertIn("DEP-SELF-12", ids)

    def test_the_list_does_not_carry_every_condition(self):
        # 22 fichas con hasta 34 condiciones cada una no van en la lista.
        _, cuerpo = self.peticion("/api/catalogue")
        for item in cuerpo["items"]:
            self.assertNotIn("conditions", item,
                             f"{item['id']} no debe llevar la ficha entera en la lista")

    def test_the_detail_carries_the_full_condition_set(self):
        estado, cuerpo = self.peticion("/api/products/ETF-01")
        self.assertEqual(estado, 200)
        condiciones = cuerpo["product"].get("conditions") or []
        self.assertEqual(len(condiciones), 28)
        ter = [c for c in condiciones if c.get("metric") == "ter_percent"]
        self.assertTrue(ter, "el TER debe estar en la ficha del ETF")

    def test_the_detail_has_only_one_condition_list(self):
        _, cuerpo = self.peticion("/api/products/ETF-01")
        self.assertEqual(set(cuerpo), {"product"},
                         "no debe haber un campo `conditions` aparte y recortado")

    def test_an_unknown_product_is_404(self):
        import http.client
        conexion = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=10)
        conexion.request("GET", "/api/products/NO-EXISTE",
                         headers={"Host": f"127.0.0.1:{self.puerto}"})
        self.assertEqual(conexion.getresponse().status, 404)
        conexion.close()

    def test_transcribed_products_report_documented_not_pending(self):
        _, cuerpo = self.peticion("/api/catalogue")
        por_id = {item["id"]: item for item in cuerpo["items"]}
        for product_id in ("ETF-01", "FND-02", "DEP-EBN-12"):
            with self.subTest(product_id=product_id):
                self.assertEqual(por_id[product_id]["conditions_state"], "documented")


if __name__ == "__main__":
    unittest.main()
