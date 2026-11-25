"""Los limites del chat tienen que aguantar una sala de 50 usuarios.

Contexto medido el 25/11/2026: con `max_concurrent=4` y `max_queue=0`, de 50
usuarios simultaneos solo 4 entraban y **46 recibian `queue_full` inmediato**.
Ademas `ThreadingHTTPServer` traia un backlog de `listen()` de 5 conexiones, asi
que el kernel rechazaba al resto antes de que la app los viera.

Estos tests fijan el comportamiento nuevo: la sala entra entera.
"""
from __future__ import annotations

import importlib
import os
import socket
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CLOCK = lambda: datetime.now(timezone.utc)  # noqa: E731


def _cargar(modulo):
    return importlib.import_module(modulo)


class SalaDeCincuentaTest(unittest.TestCase):
    """La puerta de admision deja pasar a la sala entera."""

    def setUp(self):
        self.pai = _cargar("pai_setup")

    def _admission(self, *, max_concurrent, calls_per_minute, scope):
        policy = self.pai.AdmissionPolicy(
            max_concurrent=max_concurrent,
            max_queue=0,
            calls_per_minute=calls_per_minute,
            calls_per_day=self.pai.NO_DAILY_LIMIT,
            ticket_ttl_seconds=240,
            claim_ttl_seconds=300,
            scope=scope,
        )
        return self.pai.InterfazChatAdmission(
            policy,
            clock=CLOCK,
            budget_state=self.pai.InMemoryBudgetState.new_empty(scope=scope),
        )

    def _admitir_simultaneos(self, admission, cuantos):
        resultados = []
        cerrojo = threading.Lock()

        def uno(indice):
            try:
                salida = admission.submit(idempotency_key=f"d{indice}")
                codigo = salida.get("code")
            except Exception as error:  # noqa: BLE001
                codigo = f"EXC:{type(error).__name__}"
            with cerrojo:
                resultados.append(codigo)

        with ThreadPoolExecutor(max_workers=cuantos) as pool:
            list(pool.map(uno, range(cuantos)))
        conteo = {}
        for codigo in resultados:
            conteo[codigo] = conteo.get(codigo, 0) + 1
        return conteo

    def test_los_cincuenta_entran_a_la_vez(self):
        admission = self._admission(
            max_concurrent=self.pai.MAX_CONCURRENT_CHAT,
            calls_per_minute=self.pai._calls_per_minute(),
            scope="test-sala-50",
        )
        conteo = self._admitir_simultaneos(admission, 50)
        self.assertEqual(conteo.get("admitted"), 50,
                         f"la sala de 50 tiene que entrar entera: {conteo}")
        self.assertNotIn("queue_full", conteo,
                         f"nadie puede ser rechazado por cola llena: {conteo}")

    def test_el_tope_de_concurrentes_supera_la_sala(self):
        # Si alguien vuelve a bajar MAX_CONCURRENT_CHAT por debajo de la sala, este
        # test lo caza antes de que lo sufra un usuario.
        self.assertGreaterEqual(
            self.pai.MAX_CONCURRENT_CHAT, 50,
            "el tope de turnos simultaneos no puede quedar por debajo de 50 alumnos")

    def test_el_cupo_por_minuto_no_corta_la_sala(self):
        # Un alumno puede preguntar varias veces por minuto; la sala de 50 con dos
        # preguntas cada uno son 100 llamadas en el mismo minuto.
        self.assertGreaterEqual(
            self.pai._calls_per_minute(), 100,
            "el cupo por minuto tiene que cubrir a la sala preguntando varias veces")

    def test_la_regresion_se_caza(self):
        """El valor viejo (4) tiene que seguir fallando: si no, el test es inutil."""
        admission = self._admission(
            max_concurrent=4, calls_per_minute=6, scope="test-regresion-4")
        conteo = self._admitir_simultaneos(admission, 50)
        self.assertEqual(conteo.get("admitted"), 4,
                         f"con el tope viejo solo entran 4: {conteo}")
        self.assertEqual(conteo.get("queue_full"), 46,
                         f"con el tope viejo se rechazan 46: {conteo}")


class BacklogDeEscuchaTest(unittest.TestCase):
    """El servidor acepta una rafaga de conexiones, no solo cinco."""

    def setUp(self):
        self.app = _cargar("app")

    def test_el_backlog_cubre_una_rafaga(self):
        servidor = self.app.create_server(port=0)
        try:
            self.assertGreaterEqual(
                servidor.request_queue_size, 64,
                "el backlog de listen() tiene que cubrir una rafaga de la sala")
        finally:
            servidor.server_close()

    def test_cincuenta_conexiones_tcp_a_la_vez_no_se_rechazan(self):
        servidor = self.app.create_server(port=0)
        servidor.daemon_threads = True
        hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
        hilo.start()
        puerto = servidor.server_port
        conectadas = []
        try:
            def conectar(_):
                try:
                    s = socket.create_connection(("127.0.0.1", puerto), timeout=20)
                    conectadas.append(s)
                    return "ok"
                except OSError as error:
                    return f"{type(error).__name__}: {error}"

            with ThreadPoolExecutor(max_workers=50) as pool:
                resultados = list(pool.map(conectar, range(50)))
            fallos = [r for r in resultados if r != "ok"]
            self.assertEqual(fallos, [],
                             f"conexiones rechazadas por el sistema: {fallos[:5]}")
        finally:
            for s in conectadas:
                s.close()
            servidor.shutdown()
            servidor.server_close()


if __name__ == "__main__":
    unittest.main()
