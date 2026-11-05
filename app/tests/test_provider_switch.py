"""El proveedor del chat se elige con una variable, sin abrir el destino de la clave.

Solo hay dos destinos posibles y los dos están anclados en código: Groq (por
defecto) y la suscripción de Command Code. Un valor desconocido vuelve a Groq en
vez de dejar la clave sin destino.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def run(code, **env):
    base = {k: v for k, v in os.environ.items()
            if k not in {"PAIDEIA_LLM_PROVIDER", "GROQ_API_KEY", "COMMANDCODE_API_KEY"}}
    base.update(env)
    result = subprocess.run([sys.executable, "-c", code], cwd=str(PROJECT), env=base,
                            capture_output=True, text=True, timeout=60)
    return result


class ProviderSelectionTests(unittest.TestCase):
    def test_default_is_groq(self):
        result = run("import providers as p; print(p.API_HOST, p.API_KEY_ENV, p.DEFAULT_MODEL)")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip().split(),
                         ["api.groq.com", "GROQ_API_KEY", "openai/gpt-oss-20b"])

    def test_vercel_gateway_serves_beam_for_free(self):
        result = run("import providers as p; print(p.API_HOST, p.API_PATH, p.API_KEY_ENV, p.DEFAULT_MODEL)",
                     PAIDEIA_LLM_PROVIDER="vercel")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip().split(),
                         ["ai-gateway.vercel.sh", "/v1/chat/completions",
                          "AI_GATEWAY_API_KEY", "reflection/beam-free"])

    def test_commandcode_switches_host_key_and_model(self):
        result = run("import providers as p; print(p.API_HOST, p.API_PATH, p.API_KEY_ENV, p.DEFAULT_MODEL, p.PROVIDER_LABEL)",
                     PAIDEIA_LLM_PROVIDER="commandcode")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip().split(), [
            "api.commandcode.ai", "/provider/v1/chat/completions",
            "COMMANDCODE_API_KEY", "deepseek/deepseek-v4.1-flash", "Command", "Code",
        ])

    def test_an_unknown_name_falls_back_to_groq(self):
        result = run("import providers as p; print(p.API_HOST)", PAIDEIA_LLM_PROVIDER="otro")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "api.groq.com")

    def test_model_names_accepted_per_provider(self):
        code = ("import providers as p; print(p.model_is_allowed('openai/gpt-oss-120b'),"
                " p.model_is_allowed('deepseek/deepseek-v4.1-flash'), p.model_is_allowed('dos palabras'))")
        groq = run(code)
        self.assertEqual(groq.stdout.strip(), "True False False", groq.stderr)
        cc = run(code, PAIDEIA_LLM_PROVIDER="commandcode")
        self.assertEqual(cc.stdout.strip(), "True True False", cc.stderr)


class TransportGuardTests(unittest.TestCase):
    """La clave solo puede viajar al host activo, no al otro proveedor."""

    def test_the_other_provider_host_is_rejected(self):
        code = (
            "import providers as p\n"
            "t = p.GroqHTTPSJSONTransport()\n"
            "try:\n"
            "    t.post(host='api.groq.com', path=p.API_PATH, headers={'Authorization':'Bearer x',"
            "'Content-Type':'application/json','Accept':'application/json'}, body=b'{}', timeout=5)\n"
            "except ValueError:\n"
            "    print('rechazado')\n"
            "except Exception as error:\n"
            "    print(type(error).__name__)\n"
        )
        for nombre in ("commandcode", "vercel"):
            with self.subTest(proveedor=nombre):
                result = run(code, PAIDEIA_LLM_PROVIDER=nombre)
                self.assertEqual(result.stdout.strip(), "rechazado", result.stderr)


class ModelEnvTests(unittest.TestCase):
    """El nombre antiguo del modelo no se arrastra al cambiar de proveedor."""

    def test_groq_ignores_the_provider_model_variable(self):
        result = run("import pai_setup as s; print(s._model())", PAIDEIA_LLM_MODEL="deepseek/deepseek-v4.1-pro")
        self.assertEqual(result.stdout.strip(), "openai/gpt-oss-20b", result.stderr)

    def test_commandcode_ignores_the_legacy_groq_model(self):
        result = run("import pai_setup as s; print(s._model())",
                     PAIDEIA_LLM_PROVIDER="commandcode", PAIDEIA_GROQ_MODEL="openai/gpt-oss-120b")
        self.assertEqual(result.stdout.strip(), "deepseek/deepseek-v4.1-flash", result.stderr)

    def test_commandcode_takes_its_own_model_variable(self):
        result = run("import pai_setup as s; print(s._model())",
                     PAIDEIA_LLM_PROVIDER="commandcode", PAIDEIA_LLM_MODEL="deepseek/deepseek-v4.1-pro")
        self.assertEqual(result.stdout.strip(), "deepseek/deepseek-v4.1-pro", result.stderr)


if __name__ == "__main__":
    unittest.main()
