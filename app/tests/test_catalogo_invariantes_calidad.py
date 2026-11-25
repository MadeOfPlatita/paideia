"""Invariantes de calidad del catálogo: nada se sirve sin fuente, fecha ni coherencia.

Qué se comprueba, y por qué cada una es una invariante y no un detalle de estilo:

1. **Toda condición con valor tiene fuente con URL y fecha de consulta.** Un dato
   sin procedencia no es comprobable, y sin fecha no se puede saber si sigue
   vigente. Se mira la transcripción (`documented`, `source`) y el resultado ya
   derivado y servido: la ficha puede perder la fuente por una capa intermedia.
2. **Una condición desconocida no lleva valor.** El hueco se declara, no se rellena
   con una cifra aproximada; y al revés, `known` exige valor.
3. **Mínimo ≤ máximo** en todos los productos, comparando los campos de cabecera y
   las métricas transcritas (`minimum_eur`/`maximum_eur`, incluido el saldo máximo
   remunerado de una cuenta).
4. **Un valor numérico aparece en su propio literal.** Es la defensa contra el
   error de escala (751,69 M € transcrito como 75.169.000.000 €) y contra la cifra
   inventada: si el número no está donde se dice que está, no está documentado.
5. **Un tramo no mezcla una TAE con un TIN que no le corresponde**: la TAE anual no
   puede ser menor que el TIN anual del mismo tramo.
6. **Ninguna oferta vencida se sirve como vigente.** Con la fecha de hoy, un
   producto caducado no puede llegar con estado `documented`; y lo mismo con una
   fecha inyectada en el límite exacto, para no depender del calendario.
7. **El estado de la lista coincide con el de las herramientas y el del chat.** Dos
   superficies que dicen cosas distintas del mismo producto enseñan a desconfiar.
8. **No hay duplicados** de id, de nombre ni de métrica dentro de un producto.
9. **Todas las métricas transcritas son interpretables**: si el mapa de métricas no
   conoce una, se descarta en silencio y el dato desaparece sin avisar.

Las pruebas se ejecutan contra el fichero real `app/data/condiciones.json`, porque
el defecto que buscan (un dato mal transcrito) no aparece en una fixture.
"""

from __future__ import annotations

import json
import re
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import app
from catalogue_adapter import CatalogueWithConditions
from catalogue_conditions import DEFAULT_TTL_DAYS, DOCUMENTED_METRICS
from conditions_service import ConditionsService
from pai_runtime import ToolChatRunner
from pai_tools import ToolDispatcher, project_rate_tiers

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "condiciones.json"
HOY = date.today()

# Familias con tasa anual comparable. Un fondo, un ETF o una letra no la tienen.
FAMILIAS_CON_TAE = {"deposito", "cuenta_remunerada"}

# Métricas donde el valor ES un porcentaje del nominal (precio de una letra): su
# rango natural está alrededor de 100, no de un tipo de interés.
METRICAS_PRECIO = {"precio_medio", "precio_minimo_aceptado"}


def _documento() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _registros() -> list[dict]:
    return _documento()["records"]


def _servicio(today: date | None = None) -> ConditionsService:
    return ConditionsService(reference_date=today)


def _todas_las_condiciones(today: date | None = None) -> list[tuple[str, dict]]:
    report = _servicio(today).describe()
    return [(product["product_id"], condition)
            for product in report["products"]
            for condition in product["conditions"]]


def _catalogo() -> CatalogueWithConditions:
    return CatalogueWithConditions(app.SnapshotRepository(), ConditionsService())


def _url_valida(value: object) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _numeros_del_literal(texto: str) -> set[float]:
    """Todos los números del literal, en las dos lecturas de separador.

    «1.865,55» se acepta como 1865.55 y «8,780.5» como 8780.5: la fuente mezcla
    formatos y lo que se comprueba es que la cifra esté, no su formato.
    """
    encontrados = set()
    for match in re.finditer(r"\d[\d.,]*", texto):
        bruto = match.group(0).rstrip(".,")
        for candidato in (bruto,
                          bruto.replace(".", "").replace(",", "."),
                          bruto.replace(",", ""),
                          bruto.replace(",", ".")):
            try:
                encontrados.add(float(candidato))
            except ValueError:
                continue
    return encontrados


class ProcedenciaTests(unittest.TestCase):
    """Invariante 1: valor ⇒ fuente con URL y fecha de consulta."""

    def test_cada_fila_con_valor_trae_url_y_fecha_de_consulta(self):
        faltantes = []
        for record in _registros():
            pid = record["candidate_id"]
            for item in record.get("documented") or []:
                if item.get("value") in (None, ""):
                    continue
                if not _url_valida(item.get("source_url")):
                    faltantes.append(f"{pid}/{item.get('metric')}: sin URL")
                if not item.get("accessed"):
                    faltantes.append(f"{pid}/{item.get('metric')}: sin fecha de consulta")
        self.assertEqual(faltantes, [], f"filas con valor sin procedencia: {faltantes}")

    def test_cada_ficha_declara_una_fuente_con_url_y_fecha(self):
        faltantes = []
        for record in _registros():
            pid = record["candidate_id"]
            source = record.get("source") or {}
            if not _url_valida(source.get("url")):
                faltantes.append(f"{pid}: ficha sin URL")
            if not source.get("retrieved_at"):
                faltantes.append(f"{pid}: ficha sin fecha de consulta")
            if not source.get("kind"):
                faltantes.append(f"{pid}: ficha sin clase de fuente")
        self.assertEqual(faltantes, [], faltantes)

    def test_lo_servido_con_valor_conserva_fuente_y_fecha(self):
        # La invariante no es del JSON: es de lo que llega al usuario. Una capa
        # intermedia (o una métrica que se emite por otra rama) puede perderla.
        sin_procedencia = []
        for product_id, condition in _todas_las_condiciones(HOY):
            if condition["state"] not in {"known", "stale"}:
                continue
            if condition["value"] is None:
                continue
            if not any(_url_valida(url) for url in condition["source_ids"]):
                sin_procedencia.append(f"{product_id}/{condition['metric']}: sin fuente servida")
            if not condition.get("retrieved_at"):
                sin_procedencia.append(f"{product_id}/{condition['metric']}: sin fecha servida")
        self.assertEqual(sin_procedencia, [], sin_procedencia)

    def test_una_condicion_fechada_no_es_posterior_a_su_consulta_salvo_vencimiento(self):
        # `accessed` no puede ser anterior a la propia fecha que documenta, salvo
        # los campos que por naturaleza son futuros (vencimiento, vigencia).
        excepciones = {"maturity_date", "promotion_window", "valid_to"}
        incoherentes = []
        for record in _registros():
            pid = record["candidate_id"]
            for item in record.get("documented") or []:
                metric = DOCUMENTED_METRICS.get(item.get("metric") or "")
                valor = item.get("value")
                consultado = item.get("accessed")
                if not metric or metric[1] != "DATE" or not isinstance(valor, str) or not consultado:
                    continue
                if metric[0] in excepciones:
                    continue
                if valor > consultado:
                    incoherentes.append(f"{pid}/{item.get('metric')}: {valor} > consulta {consultado}")
        self.assertEqual(incoherentes, [], incoherentes)


class DesconocidoTests(unittest.TestCase):
    """Invariante 2: el hueco se declara, no se rellena."""

    def test_una_condicion_desconocida_no_lleva_valor(self):
        con_valor = [
            f"{pid}/{c['metric']}={c['value']!r}"
            for pid, c in _todas_las_condiciones(HOY)
            if c["state"] == "unknown" and c["value"] is not None
        ]
        self.assertEqual(con_valor, [], f"un desconocido no puede traer cifra: {con_valor}")

    def test_una_condicion_conocida_lleva_valor(self):
        sin_valor = [
            f"{pid}/{c['metric']}"
            for pid, c in _todas_las_condiciones(HOY)
            if c["state"] == "known" and c["value"] is None
        ]
        self.assertEqual(sin_valor, [], f"un conocido sin cifra es una contradicción: {sin_valor}")

    def test_lo_declarado_desconocido_en_el_json_llega_a_la_ficha(self):
        # `value: null` + `note` es la forma de decir «la fuente no publica esto».
        # Si la derivación lo descarta, el usuario ve una ausencia sin motivo.
        declarados = set()
        for record in _registros():
            pid = record["candidate_id"]
            for item in record.get("documented") or []:
                if item.get("value") in (None, "") and item.get("note"):
                    metric = DOCUMENTED_METRICS.get(item.get("metric") or "")
                    if metric:
                        declarados.add((pid, metric[0]))
        self.assertTrue(declarados, "el catálogo debería declarar algún hueco explícito")

        servidos = {(pid, c["metric"]) for pid, c in _todas_las_condiciones(HOY)
                    if c["state"] == "unknown"}
        perdidos = sorted(declarados - servidos)
        self.assertEqual(perdidos, [],
                         f"huecos declarados en el JSON que no llegan a la ficha: {perdidos}")

    def test_cada_hueco_declarado_trae_su_motivo(self):
        # La tabla de desconocidos de la interfaz no puede quedarse en «no hay dato».
        sin_motivo = [
            f"{pid}/{c['metric']}"
            for pid, c in _todas_las_condiciones(HOY)
            if c["state"] == "unknown" and not c["notes"]
        ]
        self.assertEqual(sin_motivo, [], f"un hueco sin motivo no explica nada: {sin_motivo}")


class CoherenciaNumericaTests(unittest.TestCase):
    """Invariantes 3, 4 y 5: rangos, escala y aritmética de los tramos."""

    def test_minimo_no_supera_maximo(self):
        excesos = []
        for record in _registros():
            pid = record["candidate_id"]
            try:
                minimo = Decimal(str(record["minimum_eur"]))
                maximo = Decimal(str(record["maximum_eur"]))
            except (KeyError, TypeError, ValueError, ArithmeticError):
                continue
            if minimo > maximo:
                excesos.append(f"{pid}: mínimo {minimo} > máximo {maximo}")
        self.assertEqual(excesos, [], excesos)

    def test_minimo_y_maximo_transcritos_tampoco_se_contradicen(self):
        # Los campos de cabecera y las métricas transcritas son dos copias del
        # mismo hecho: si discrepan, una de las dos está mal.
        excesos = []
        for record in _registros():
            pid = record["candidate_id"]
            minimos = [i["value"] for i in record.get("documented") or []
                       if i.get("metric") in {"importe_minimo", "inversion_minima", "suscripcion_minima"}
                       and i.get("value") not in (None, "")]
            maximos = [i["value"] for i in record.get("documented") or []
                       if i.get("metric") in {"importe_maximo", "saldo_maximo_remunerado"}
                       and i.get("value") not in (None, "")]
            for minimo in minimos:
                for maximo in maximos:
                    try:
                        if Decimal(str(minimo)) > Decimal(str(maximo)):
                            excesos.append(f"{pid}: mínimo {minimo} > máximo {maximo}")
                    except ArithmeticError:
                        continue
        self.assertEqual(excesos, [], excesos)

    def test_un_minimo_cero_no_se_sirve_como_cifra_sin_respaldo(self):
        # `0` es un mínimo legítimo («desde el primer euro»), pero solo si la fuente
        # lo dice. Se comprueba que la nota asociada no lo desmienta.
        contradictorios = []
        for record in _registros():
            pid = record["candidate_id"]
            for item in record.get("documented") or []:
                if item.get("metric") != "importe_minimo" or str(item.get("value")) != "0":
                    continue
                nota = (item.get("note") or "").casefold()
                if "no publica cifra" in nota or "no un importe de 0" in nota:
                    contradictorios.append(f"{pid}: el valor 0 está desmentido por su propia nota")
        self.assertEqual(contradictorios, [], contradictorios)

    def test_toda_tasa_es_un_porcentaje_plausible(self):
        fuera = []
        for record in _registros():
            pid = record["candidate_id"]
            for item in record.get("documented") or []:
                valor = item.get("value")
                if valor in (None, ""):
                    continue
                metric = DOCUMENTED_METRICS.get(item.get("metric") or "")
                if not metric or metric[1] != "PERCENT":
                    continue
                nombre = item["metric"]
                try:
                    numero = Decimal(str(valor))
                except ArithmeticError:
                    fuera.append(f"{pid}/{nombre}: valor no numérico {valor!r}")
                    continue
                limite = Decimal("1000") if nombre in METRICAS_PRECIO else Decimal("100")
                if not Decimal("-100") < numero <= limite:
                    fuera.append(f"{pid}/{nombre}={numero} fuera de rango")
        self.assertEqual(fuera, [], fuera)

    def test_la_tae_de_un_tramo_no_es_menor_que_su_tin(self):
        # Una TAE anual por debajo del TIN anual del mismo tramo es aritméticamente
        # imposible: o los dos números son de bloques distintos de la página, o uno
        # está mal transcrito. El par se declara inválido, no se sirve.
        imposibles = []
        for record in _registros():
            pid = record["candidate_id"]
            for tier in record.get("tiers") or []:
                try:
                    tae = Decimal(str(tier["tae"]))
                    tin = Decimal(str(tier["tin"]))
                except (KeyError, TypeError, ValueError, ArithmeticError):
                    continue
                if tae < tin:
                    imposibles.append(
                        f"{pid}/{tier.get('condition')}: TAE {tae} < TIN {tin}")
        self.assertEqual(imposibles, [], imposibles)

    def test_un_tramo_servido_nunca_mezcla_tasas_de_bloques_distintos(self):
        # La comprobación equivalente sobre lo que se sirve: si el tramo es
        # incoherente, `project_rate_tiers` debe haberlo retirado.
        defectuosos = []
        for record in _registros():
            tiers, state = project_rate_tiers(record.get("tiers"))
            if record.get("tiers") and state != "documented":
                defectuosos.append(f"{record['candidate_id']}: tramos {state}")
            for tier in tiers:
                if tier.get("tae") and tier.get("tin"):
                    if Decimal(tier["tae"]) < Decimal(tier["tin"]):
                        defectuosos.append(f"{record['candidate_id']}: tramo servido incoherente")
        self.assertEqual(defectuosos, [], defectuosos)

    def test_todo_tramo_publicado_llega_a_la_ficha(self):
        # Un depósito con ocho plazos publica ocho tramos. Un tope estructural por
        # debajo de la realidad descarta el producto entero en silencio.
        perdidos = []
        for record in _registros():
            crudos = record.get("tiers") or []
            if not crudos:
                continue
            servidos, state = project_rate_tiers(crudos)
            if state != "documented" or len(servidos) != len(crudos):
                perdidos.append(
                    f"{record['candidate_id']}: {len(crudos)} transcritos, {len(servidos)} servidos ({state})")
        self.assertEqual(perdidos, [], perdidos)

    def test_ninguna_cifra_esta_fuera_de_su_propio_literal(self):
        # La defensa contra el error de escala y contra la cifra inventada. Se
        # exceptúan los importes que la transcripción declara en millones: ahí el
        # valor almacenado es el producto por 10^6 y el literal trae el millón.
        exentos = {"saldo_vivo", "nominal_adjudicado", "patrimonio"}
        discrepancias = []
        for record in _registros():
            pid = record["candidate_id"]
            for item in record.get("documented") or []:
                valor = item.get("value")
                metric = DOCUMENTED_METRICS.get(item.get("metric") or "")
                if valor in (None, "") or not metric or metric[1] not in {"PERCENT", "EUR"}:
                    continue
                if item["metric"] in exentos:
                    continue
                literal = (item.get("literal") or "").strip()
                if not literal:
                    discrepancias.append(f"{pid}/{item['metric']}: valor sin literal")
                    continue
                try:
                    numero = float(str(valor))
                except ValueError:
                    continue
                if numero == 0:
                    # «Sin comisiones» / «desde el primer euro»: el cero se
                    # documenta con palabras, no con la cifra.
                    continue
                if numero not in _numeros_del_literal(literal):
                    discrepancias.append(
                        f"{pid}/{item['metric']}={valor} no aparece en {literal[:60]!r}")
        self.assertEqual(discrepancias, [], discrepancias)

    def test_un_importe_en_millones_se_guarda_en_euros_y_a_la_escala_correcta(self):
        # El fallo medido: 751,69 M € almacenado como 75.169.000.000 € (×100). El
        # número seguía siendo plausible y ninguna prueba de presencia lo veía.
        errores = []
        for record in _registros():
            pid = record["candidate_id"]
            for item in record.get("documented") or []:
                if item.get("metric") not in {"nominal_adjudicado"}:
                    continue
                valor = item.get("value")
                literal = item.get("literal") or ""
                millones = re.findall(r"\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:[.,]\d+)?", literal)
                if not millones or valor in (None, ""):
                    continue
                try:
                    esperado = Decimal(millones[-1].replace(".", "").replace(",", ".")) * Decimal(1_000_000)
                    almacenado = Decimal(str(valor))
                except ArithmeticError:
                    continue
                if almacenado != esperado:
                    errores.append(
                        f"{pid}: literal {millones[-1]} M € → {esperado}, almacenado {almacenado}")
        self.assertEqual(errores, [], errores)


class VigenciaTests(unittest.TestCase):
    """Invariante 6: nada vencido se sirve como vigente."""

    def test_ningun_producto_vencido_se_sirve_como_documentado(self):
        catalogue = _catalogo().list_products()
        hoy = date.today().isoformat()
        vencidos_mal = []
        for item in catalogue:
            conditions = item.get("conditions") or []
            caducado = [c for c in conditions
                        if c.get("state") == "stale"
                        or (isinstance(c.get("effective_to"), str) and c["effective_to"] < hoy)]
            if caducado and item.get("conditions_state") == "documented":
                vencidos_mal.append(f"{item['id']}: {sorted({c['metric'] for c in caducado})}")
        self.assertEqual(vencidos_mal, [], f"vencidos servidos como vigentes: {vencidos_mal}")

    def test_el_estado_del_listado_coincide_con_el_de_las_herramientas(self):
        # Dos superficies del mismo dato en desacuerdo: la lista decía `documented`
        # mientras el chat decía `documented_not_current` para el mismo producto.
        discrepancias = []
        for item in _catalogo().list_products():
            dto = ToolDispatcher._project_product(item)
            chat = ToolChatRunner._evidence_product(item)
            if dto["conditions_state"] != chat["conditions_state"]:
                discrepancias.append(f"{item['id']}: herramientas={dto['conditions_state']} "
                                     f"chat={chat['conditions_state']}")
        self.assertEqual(discrepancias, [], discrepancias)

    def test_una_promocion_vencida_se_declara_no_vigente(self):
        # Con la fecha del día: DEP-03 venció el 31/10/2026 y ACC-01/DEP-01 el 18/11.
        # Esta prueba NO se rompe sola el día que caduque otra: solo exige que lo
        # que ya venció no se presente como actual.
        hoy = date.today()
        catalogue = {item["id"]: item for item in _catalogo().list_products()}
        for record in _registros():
            valid_to = record.get("valid_to")
            if not isinstance(valid_to, str):
                continue
            try:
                caduca = date.fromisoformat(valid_to)
            except ValueError:
                continue
            if caduca >= hoy:
                continue
            item = catalogue.get(record["candidate_id"])
            self.assertIsNotNone(item, record["candidate_id"])
            self.assertNotEqual(
                item["conditions_state"], "documented",
                f"{record['candidate_id']} venció el {valid_to} y se sirve como vigente")

    def test_el_limite_de_vigencia_se_calcula_por_dias_completos(self):
        # Inyectar la fecha: el día del término todavía cuenta y el día siguiente
        # ya no. Sin fecha fija la prueba se pondría roja sola al caducar la oferta.
        record = next(r for r in _registros() if r["candidate_id"] == "DEP-03")
        caduca = date.fromisoformat(record["valid_to"])
        el_mismo_dia = _servicio(caduca).for_product("DEP-03")
        al_dia_siguiente = _servicio(caduca + timedelta(days=1)).for_product("DEP-03")

        tasa_ultimo_dia = next(c for c in el_mismo_dia["conditions"]
                               if c["metric"] == "annual_rate_percent")
        tasa_caducada = next(c for c in al_dia_siguiente["conditions"]
                             if c["metric"] == "annual_rate_percent")
        self.assertEqual(tasa_ultimo_dia["state"], "known")
        self.assertEqual(tasa_caducada["state"], "stale")
        self.assertEqual(tasa_caducada["reason"], "PROMOTION_EXPIRED")

    def test_la_regla_de_antiguedad_se_aplica_a_las_fichas_transcritas(self):
        # El catálogo real entra por la ruta `curated`, así que la regla de TTL
        # tiene que gobernar ahí: si solo se aplicara al snapshot, no gobernaría
        # ningún dato servido.
        record = next(r for r in _registros()
                      if r["candidate_id"] == "ACC-04" and r["valid_to"] is None)
        consultado = date.fromisoformat(record["source"]["retrieved_at"])
        ttl = DEFAULT_TTL_DAYS[record["family"]]
        dentro = consultado + timedelta(days=ttl)
        fuera = consultado + timedelta(days=ttl + 1)

        def estado(fecha):
            ficha = _servicio(fecha).for_product("ACC-04")
            return next(c["state"] for c in ficha["conditions"]
                        if c["metric"] == "annual_rate_percent")

        self.assertEqual(estado(dentro), "known")
        self.assertEqual(estado(fuera), "stale")

    def test_una_fecha_de_vigencia_discrepante_no_se_resuelve_en_silencio(self):
        # DEP-03 tiene dos fechas para la misma oferta sobre la misma URL: el
        # `valid_to` (31/10/2026) y el literal de la transcripción (30/11/2026).
        # No se elige una: el estado se deriva del campo documentado y la
        # discrepancia queda declarada en la ficha.
        ficha = _servicio(date(2026, 11, 10)).for_product("DEP-03")
        ventana = [c for c in ficha["conditions"] if c["metric"] == "promotion_window"]
        self.assertTrue(ventana, "la ventana discrepante no puede desaparecer de la ficha")
        self.assertEqual(ventana[0]["state"], "unknown")
        self.assertIn("30/11/2026", " ".join(ventana[0]["notes"]))


class IntegridadTests(unittest.TestCase):
    """Invariantes 8 y 9: sin duplicados y sin métricas que se pierdan."""

    def test_no_hay_identificadores_ni_nombres_duplicados(self):
        records = _registros()
        ids = [r["candidate_id"] for r in records]
        nombres = [r["name"] for r in records]
        self.assertEqual(len(ids), len(set(ids)), "hay candidate_id repetidos")
        self.assertEqual(len(nombres), len(set(nombres)), "hay nombres repetidos")

    def test_ningun_producto_se_queda_sin_condiciones(self):
        vacios = [product["product_id"] for product in _servicio(HOY).describe()["products"]
                  if not product["conditions"]]
        self.assertEqual(vacios, [], f"productos sin ninguna condición: {vacios}")

    def test_cada_producto_declara_su_familia_y_su_fuente(self):
        # Una familia fuera del enum hace que el producto desaparezca del catálogo
        # sin error visible.
        familias = {"deposito", "cuenta_remunerada", "letra_deuda_publica",
                    "fondo_tradicional", "etf_ucits"}
        invalidos = [r["candidate_id"] for r in _registros() if r.get("family") not in familias]
        self.assertEqual(invalidos, [], invalidos)

    def test_toda_metrica_transcrita_es_interpretable(self):
        # Una métrica que el mapa no conoce se descarta en silencio: el dato existe
        # en el JSON y no llega nunca a la ficha.
        desconocidas = sorted({
            item.get("metric")
            for record in _registros()
            for item in record.get("documented") or []
            if item.get("metric") not in DOCUMENTED_METRICS
        })
        self.assertEqual(desconocidas, [],
                         f"métricas que el mapa no conoce y se perderían: {desconocidas}")

    def test_no_se_repite_una_metrica_en_lo_servido(self):
        # Dos filas con la misma métrica dejan al consumidor eligiendo al azar.
        repetidas = []
        for product in _servicio(HOY).describe()["products"]:
            metricas = [c["metric"] for c in product["conditions"]]
            if len(metricas) != len(set(metricas)):
                repetidas.append(product["product_id"])
        self.assertEqual(repetidas, [], repetidas)

    def test_las_familias_sin_tasa_no_inventan_una_fila_de_tasa(self):
        # Un fondo, un ETF o una letra no tienen TAE. Una fila «sin dato» los
        # marcaba como incompletos y contagiaba el estado del chat.
        inventadas = [
            f"{pid}/{c['metric']}"
            for pid, c in _todas_las_condiciones(HOY)
            if c["metric"] == "annual_rate_percent"
            and next(p for p in _servicio(HOY).describe()["products"]
                     if p["product_id"] == pid)["family"] not in FAMILIAS_CON_TAE
        ]
        self.assertEqual(inventadas, [], inventadas)


class ServidoTests(unittest.TestCase):
    """Lo que llega al usuario por HTTP, no solo lo que dice el JSON."""

    @classmethod
    def setUpClass(cls):
        import threading
        cls.server = app.create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def peticion(self, ruta):
        import http.client
        conexion = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=15)
        conexion.request("GET", ruta, headers={"Host": f"127.0.0.1:{self.server.server_port}"})
        respuesta = conexion.getresponse()
        cuerpo = json.loads(respuesta.read().decode("utf-8"))
        conexion.close()
        return respuesta.status, cuerpo

    def test_la_lista_no_publica_cifras_solo_estados(self):
        # La lista lleva estado y tramos con sus tasas, pero no el texto del
        # conflicto ni las condiciones completas: eso vive en la ficha.
        estado, cuerpo = self.peticion("/api/catalogue")
        self.assertEqual(estado, 200)
        for item in cuerpo["items"]:
            self.assertNotIn("conditions", item, item["id"])
            self.assertNotIn("available_fields", item, item["id"])

    def test_la_ficha_completa_llega_por_el_detalle(self):
        for product_id in ("DEP-03", "ACC-01", "DEP-04", "ETF-01"):
            estado, cuerpo = self.peticion(f"/api/products/{product_id}")
            self.assertEqual(estado, 200, product_id)
            self.assertTrue(cuerpo["product"]["conditions"], product_id)

    def test_un_producto_vencido_no_se_sirve_como_vigente_por_http(self):
        for product_id in ("DEP-03", "ACC-01", "ACC-03", "DEP-01"):
            estado, cuerpo = self.peticion(f"/api/products/{product_id}")
            self.assertEqual(estado, 200, product_id)
            self.assertNotEqual(cuerpo["product"]["conditions_state"], "documented",
                                f"{product_id} está vencido")

    def test_lo_que_la_fuente_no_publica_se_declara_en_la_ficha(self):
        estado, cuerpo = self.peticion("/api/products/ACC-01")
        self.assertEqual(estado, 200)
        maximos = [c for c in cuerpo["product"]["conditions"] if c["metric"] == "maximum_eur"]
        self.assertTrue(maximos, "el hueco declarado tiene que viajar a la ficha")
        self.assertEqual(maximos[0]["state"], "unknown")
        self.assertIsNone(maximos[0]["value"])

    def test_las_condiciones_de_una_letra_conservan_la_escala_del_nominal(self):
        estado, cuerpo = self.peticion("/api/products/DEBT-01")
        self.assertEqual(estado, 200)
        nominal = next(c for c in cuerpo["product"]["conditions"]
                       if c["metric"] == "awarded_nominal_eur")
        # 751,69 M € son 751.690.000 €, no 75.169.000.000 €.
        self.assertEqual(Decimal(nominal["value"]), Decimal("751690000"))
        self.assertEqual(nominal["unit"], "EUR")


if __name__ == "__main__":
    unittest.main()
