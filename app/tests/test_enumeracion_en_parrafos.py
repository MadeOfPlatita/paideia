"""Las enumeraciones llegan al frontend con saltos de línea, no dentro de un párrafo.

Medido EN PANTALLA con la captura del colchón: la respuesta traía cinco pasos

    1. Mide tus esenciales reales durante 2-3 meses…
    2. Fija el objetivo…
    3. Separa físicamente el dinero…
    4. Automatiza la aportación…
    5. Define qué es emergencia…

y los cinco llegaban en un ÚNICO bloque de 3.100 caracteres. Los números «2.»,
«3.», «4.» y «5.» aparecían a mitad de línea. El frontend parte el texto por
línea en blanco y mete cada trozo en un <p>: sin saltos no hay lista que pintar.

Tres causas, las tres en `_redact_unbacked_figures`:

1. La agrupación en párrafos era ciega —«cada dos frases»— y metía los pasos de
   dos en dos: el paso 1 y el 2 caían en el mismo bloque.
2. El atajo de `removed == 0` devolvía el texto ORIGINAL sin agrupar siquiera.
   El turno del colchón no tenía ninguna frase que quitar, así que salía intacto:
   ni un solo salto. Es el caso real de la captura.
3. En la rama con frases quitadas, `_flatten_headings` y `_drop_orphan_headings`
   re-unían todas las frases con espacios y destruían los saltos recién puestos.

El arreglo abre los párrafos al final (`_paragraph_blocks`), sobre la numeración
ya reparada: los pasos sobreviven, cada uno encabeza su bloque y la prosa normal
sigue respirando cada dos frases.

La frontera de seguridad NO cambia: una tasa del modelo se sigue quitando, y un
paso que la lleve se cae entero (lo fija `test_lista_numerada_intacta.py`).
"""

import unittest

from backend_services import _paragraph_blocks, _redact_unbacked_figures


# La enumeración real de la captura: cinco pasos, con la frase de continuación de
# cada uno. Sin ninguna cifra financiera, que es por lo que llega intacta.
COLA = ("Eso cambia la pregunta: el problema no es montarlo, es repartir lo que ya tienes. "
        "Cómo lo montaría yo, en 5 pasos. "
        "1. Mide tus esenciales reales durante 2-3 meses (no los estimes). "
        "Apunta todo lo que pagarías aunque te quedaras sin ingresos. "
        "2. Fija el objetivo: 3 meses de esenciales y una partida para gastos anuales. "
        "Los fondos de hundimiento se separan del colchón: son gastos ciertos. "
        "3. Separa físicamente el dinero: una cuenta distinta, sin tarjeta vinculada. "
        "4. Automatiza la aportación el mismo día que entra el ingreso. "
        "5. Define qué es emergencia y la regla de reposición: si lo usas, se rellena. "
        "Un colchón sobredimensionado es dinero parado mientras la inflación lo erosiona.")

PASOS = ("1. Mide tus esenciales", "2. Fija el objetivo", "3. Separa físicamente",
         "4. Automatiza la aportación", "5. Define qué es emergencia")


def bloques(texto):
    return [bloque for bloque in texto.split("\n\n") if bloque.strip()]


class EnumeracionEnBloquesTests(unittest.TestCase):
    def test_cinco_pasos_producen_cinco_bloques(self):
        limpio, quitadas = _redact_unbacked_figures(COLA, strict=True)
        self.assertEqual(quitadas, 0, "ninguna frase lleva una cifra financiera")
        autos = [bloque for bloque in bloques(limpio)
                 if any(bloque.startswith(paso) for paso in PASOS)]
        self.assertEqual(len(autos), 5,
                         f"esperaba 5 bloques de paso, salieron {len(autos)}: {bloques(limpio)}")
        for paso, bloque in zip(PASOS, autos):
            with self.subTest(paso=paso):
                self.assertTrue(bloque.startswith(paso),
                                f"«{paso}» no encabeza su bloque: {bloque[:80]!r}")

    def test_cada_paso_va_separado_por_linea_en_blanco(self):
        # No basta con que existan los pasos: cada «N.» tiene que empezar tras \n\n.
        limpio, _ = _redact_unbacked_figures(COLA, strict=True)
        for paso in PASOS:
            with self.subTest(paso=paso):
                marca = limpio.find(paso)
                self.assertGreater(marca, 0, f"falta el paso {paso!r}")
                self.assertTrue(limpio[:marca].endswith("\n\n"),
                                f"«{paso}» no empieza párrafo (antes: "
                                f"{limpio[max(0, marca - 12):marca]!r})")

    def test_la_numeracion_no_queda_a_mitad_de_linea(self):
        # El síntoma medido: «…es la base. 2. Fija el objetivo…». En el texto de
        # salida, cada «N. » de paso tiene que ir precedido de un salto de párrafo.
        limpio, _ = _redact_unbacked_figures(COLA, strict=True)
        for paso in PASOS[1:]:
            with self.subTest(paso=paso):
                inicio = 0
                while True:
                    marca = limpio.find(paso, inicio)
                    if marca < 0:
                        break
                    self.assertTrue(limpio[:marca].endswith("\n\n"),
                                    f"«{paso}» aparece a mitad de línea (antes: "
                                    f"{limpio[max(0, marca - 14):marca]!r})")
                    inicio = marca + len(paso)

    def test_el_paso_2_no_se_pega_al_1(self):
        # El fallo exacto de la captura: el paso 1 y el 2 en el mismo párrafo.
        limpio, _ = _redact_unbacked_figures(COLA, strict=True)
        for bloque in bloques(limpio):
            self.assertFalse(bloque.startswith(PASOS[0]) and PASOS[1] in bloque,
                             f"el paso 2 vuelve a ir dentro del bloque del paso 1: {bloque!r}")


class ProsaSigueRespirandoTests(unittest.TestCase):
    """Lo que este cambio NO puede romper: la respiración de los párrafos normales."""

    def test_la_prosa_sin_enumeracion_se_agrupa_de_dos_en_dos(self):
        texto = ("El colchón es dinero reservado para imprevistos. "
                 "No es inversión: su función es estar disponible, no rentar. "
                 "Se dimensiona en meses de gasto esencial, no en una cifra redonda. "
                 "Vive en un sitio con liquidez inmediata y sin riesgo nominal. "
                 "Un colchón sobredimensionado es dinero parado.")
        limpio, quitadas = _redact_unbacked_figures(texto, strict=True)
        self.assertEqual(quitadas, 0)
        grupos = bloques(limpio)
        self.assertEqual(len(grupos), 3, f"esperaba 2+2+1, salió: {grupos}")
        self.assertIn("El colchón es dinero reservado para imprevistos. "
                      "No es inversión: su función es estar disponible, no rentar.", grupos[0])
        self.assertEqual(grupos[-1], "Un colchón sobredimensionado es dinero parado.")

    def test_una_sola_frase_no_se_parte(self):
        limpio, _ = _redact_unbacked_figures("El TIN es el tipo nominal.", strict=True)
        self.assertEqual(limpio, "El TIN es el tipo nominal.")

    def test_el_texto_sin_frases_quitadas_tambien_llega_con_parrafos(self):
        # La causa 2 de la captura: `removed == 0` devolvía el original sin agrupar.
        texto = ("El colchón cubre imprevistos. No depende de vender nada. "
                 "Se mide en meses de gasto. Un exceso es dinero parado.")
        limpio, quitadas = _redact_unbacked_figures(texto)
        self.assertEqual(quitadas, 0)
        self.assertGreaterEqual(len(bloques(limpio)), 2,
                                "sin frases quitadas también hay que abrir párrafos")

    def test_las_filas_de_tabla_conservan_su_linea(self):
        # Una tabla convertida en lista: si las filas se pegaran, dejarían de
        # reconocerse como elementos de lista y se leerían como prosa corrida.
        texto = ("| Producto | Qué mirar |\n| --- | --- |\n"
                 "| Depósito A | penalización por cancelación |\n"
                 "| Depósito B | comisión de mantenimiento |")
        limpio, _ = _redact_unbacked_figures(texto)
        for fila in ("- Depósito A", "- Depósito B"):
            with self.subTest(fila=fila):
                self.assertIn(fila, limpio)
        self.assertIn("\n\n- Depósito A", limpio,
                      "la primera fila tiene que empezar su propio bloque")
        self.assertIn("\n\n- Depósito B", limpio,
                      "cada fila de la tabla va en su propia línea")


class _ParagraphBlocksUnitTests(unittest.TestCase):
    """El helper, aislado: solo decide dónde van los saltos."""

    def test_un_paso_encabeza_bloque_y_arrastra_su_continuacion(self):
        texto = ("Introducción. Algo más. "
                 "1. Primer paso. Su explicación. Su cierre. "
                 "2. Segundo paso.")
        salida = bloques(_paragraph_blocks(texto))
        self.assertEqual(salida, ["Introducción. Algo más.",
                                  "1. Primer paso. Su explicación. Su cierre.",
                                  "2. Segundo paso."])

    def test_una_enumeracion_pegada_en_un_solo_parrafo_se_despega(self):
        texto = ("Primero. 1. Uno. 2. Dos. 3. Tres.")
        self.assertEqual(bloques(_paragraph_blocks(texto)),
                         ["Primero.", "1. Uno.", "2. Dos.", "3. Tres."])

    def test_no_toca_lo_que_no_es_texto(self):
        self.assertIsNone(_paragraph_blocks(None))
        self.assertEqual(_paragraph_blocks("   "), "")


if __name__ == "__main__":
    unittest.main()
