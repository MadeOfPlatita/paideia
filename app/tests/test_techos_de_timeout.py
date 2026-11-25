"""Los dos techos de timeout del proveedor tienen que ir juntos.

Fallo real, medido el 25/11/2026: al subir `MAX_TIMEOUT_SECONDS` de 60 a 120 para
que una sala de 50 usuarios no cortase turnos vivos, **produccion empezo a
devolver 503 `CHAT_PROVIDER_UNAVAILABLE` en 0,3 s con una sola peticion**.

La causa: habia DOS comprobaciones del mismo techo de 60 s, en sitios distintos.

  1. `GroqProvider.__init__` — validaba `0.1 <= timeout <= 60.0`.
  2. `GroqHTTPSJSONTransport.post` — validaba otra vez `0.1 <= timeout <= 60.0` y
     lanzaba `ValueError("invalid transport request")`, que el provider convertia en
     `ProviderError("transport_error")` y el borde en un 503 sin explicacion.

Subir solo la primera dejaba la segunda rechazando la peticion, y el mensaje no
decia nada del timeout: parecia que el proveedor estaba caido.

La suite entera pasaba con el fallo (1098 tests verdes), porque ningun test
comprobaba que los DOS techos admitiesen el mismo valor. Estos tests cubren ese
hueco: si alguien vuelve a bajar uno solo de los dos, esto se pone rojo.
"""
from __future__ import annotations

import importlib
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _cargar(modulo):
    return importlib.import_module(modulo)


class TechosDeTimeoutTest(unittest.TestCase):
    """El techo declarado y el que aplica el transporte son el mismo numero."""

    def setUp(self):
        self.providers = _cargar("providers")
        self.pai = _cargar("pai_setup")

    def test_el_provider_admite_el_timeout_configurado(self):
        timeout = self.pai._timeout()
        provider = self.providers.GroqProvider(
            self.providers.GroqHTTPSJSONTransport(),
            model=self.pai._model(),
            timeout=timeout,
            max_output_tokens=self.pai._tokens(),
        )
        self.assertEqual(provider._timeout, float(timeout))

    def test_el_transporte_admite_el_mismo_timeout(self):
        """El transporte valida el timeout por su cuenta: aqui estaba el fallo."""
        timeout = self.pai._timeout()
        transport = self.providers.GroqHTTPSJSONTransport()
        headers = {
            "Authorization": "Bearer clave-de-prueba",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Se llama al POST real con un cuerpo minimo. Si el techo del transporte no
        # admite el timeout configurado, esto lanza ValueError antes de tocar la red.
        try:
            transport.post(
                host=self.providers.GROQ_HOST,
                path=self.providers.GROQ_PATH,
                headers=headers,
                body=b'{"model":"x","messages":[]}',
                timeout=timeout,
            )
        except ValueError as error:
            if "invalid transport request" in str(error):
                self.fail(
                    f"el transporte rechaza el timeout configurado ({timeout}); "
                    "es el techo duplicado que tumbo produccion: "
                    f"{error}")
        except Exception:  # noqa: BLE001
            # Cualquier otro fallo es de red o del proveedor, no del techo: aqui solo
            # interesa que la validacion de timeout pase.
            pass

    def test_los_dos_techos_coinciden(self):
        """Si alguien cambia uno, tiene que cambiar el otro."""
        timeout = self.pai._timeout()
        self.assertGreaterEqual(timeout, 60.0,
                                "el timeout tiene que cubrir respuestas reales largas")
        # El provider acepta el valor configurado...
        self.providers.GroqProvider(
            self.providers.GroqHTTPSJSONTransport(),
            model=self.pai._model(),
            timeout=timeout,
            max_output_tokens=self.pai._tokens(),
        )
        # ...y el transporte tambien (comprobado arriba). Si los dos numeros se
        # separan, el segundo test falla.

    def test_el_provider_sigue_rechazando_valores_absurdos(self):
        """Subir el techo no puede abrir la puerta a un valor sin limite."""
        for absurdo in (0.0, -1.0, 100000.0):
            with self.subTest(timeout=absurdo):
                with self.assertRaises(ValueError):
                    self.providers.GroqProvider(
                        self.providers.GroqHTTPSJSONTransport(),
                        model=self.pai._model(),
                        timeout=absurdo,
                        max_output_tokens=self.pai._tokens(),
                    )


if __name__ == "__main__":
    unittest.main()
