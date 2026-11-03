"""Pruebas locales del arnés de comparación de contexto Pai."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "pai_context_benchmark.py"
DATASET = ROOT / "dataset.json"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class DatasetValidationTests(unittest.TestCase):
    def test_validate_reports_six_synthetic_cases_and_lossless_projection_contract(self) -> None:
        result = run_cli("validate", "--dataset", str(DATASET))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["case_count"], 6)
        self.assertEqual(payload["provider_calls"], 0)
        self.assertEqual(payload["winner"], None)


class RequestGenerationTests(unittest.TestCase):
    def test_generation_is_offline_preserves_dataset_and_materializes_only_selected_context(self) -> None:
        source_hash = hashlib.sha256(DATASET.read_bytes()).hexdigest()
        dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            output = Path(temporary) / "requests"
            result = run_cli("generate", "--dataset", str(DATASET), "--out", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["request_count"], 18)
            self.assertEqual(manifest["provider_calls"], 0)
            self.assertEqual(manifest["result_count"], 0)
            self.assertIsNone(manifest["winner"])
            for case in dataset["cases"]:
                requests = {
                    variant: json.loads((output / "requests" / case["case_id"] / f"{variant}.json").read_text(encoding="utf-8"))
                    for variant in ("A", "B", "C")
                }
                baseline = requests["A"]["base"]
                baseline_hash = requests["A"]["base_sha256"]
                for variant, request in requests.items():
                    self.assertEqual(request["base"], baseline)
                    self.assertEqual(request["base_sha256"], baseline_hash)
                    self.assertEqual(request["provider_call_status"], "not_called")
                    self.assertEqual(request["messages"][0]["content"], baseline["system"])
                    self.assertIn(case["question"], request["messages"][1]["content"])
                self.assertIsNone(requests["A"]["profile_context"]["data"])
                self.assertEqual(requests["B"]["profile_context"]["data"], case["relevant_projection"])
                self.assertEqual(requests["C"]["profile_context"]["data"], case["profile"])
        self.assertEqual(hashlib.sha256(DATASET.read_bytes()).hexdigest(), source_hash)

    def test_projection_preserves_unknown_zero_and_omission_as_distinct_states(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            output = Path(temporary) / "requests"
            result = run_cli("generate", "--out", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            def context(case_id: str, variant: str) -> dict:
                request_path = output / "requests" / case_id / f"{variant}.json"
                return json.loads(request_path.read_text(encoding="utf-8"))["profile_context"]["data"]
            liquidity_b = context("SYN-01-LIQUIDEZ", "B")
            liquidity_c = context("SYN-01-LIQUIDEZ", "C")
            debt_b = context("SYN-03-DEUDA-RESERVA", "B")
            unknown_b = context("SYN-05-DATOS-NO-DECLARADOS", "B")
            self.assertNotIn("planned_contribution_eur", liquidity_b)
            self.assertEqual(liquidity_c["planned_contribution_eur"], 0)
            self.assertEqual(debt_b["planned_contribution_eur"], 0)
            self.assertIn("monthly_net_income_eur", unknown_b)
            self.assertIsNone(unknown_b["monthly_net_income_eur"])
            self.assertIn("debts", unknown_b)
            self.assertIsNone(unknown_b["debts"])


    def test_b_request_records_all_excluded_fields_and_their_reason(self) -> None:
        dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            output = Path(temporary) / "requests"
            result = run_cli("generate", "--out", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            for case in dataset["cases"]:
                request_path = output / "requests" / case["case_id"] / "B.json"
                request = json.loads(request_path.read_text(encoding="utf-8"))
                context = request["profile_context"]
                self.assertEqual(set(context["selected_fields"]), set(case["projection_fields"]))
                excluded = context["excluded_fields"]
                self.assertEqual({item["field"] for item in excluded}, set(case["profile"]) - set(case["projection_fields"]))
                self.assertTrue(all(item["reason"].strip() for item in excluded))


class ResultRegistrationTests(unittest.TestCase):
    def test_summary_starts_with_zero_results_and_no_winner(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            results = Path(temporary) / "not-created.jsonl"
            result = run_cli("summary", "--results", str(results))
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["provider_call_count"], 0)
            self.assertEqual(summary["result_count"], 0)
            self.assertIsNone(summary["winner"])
            self.assertFalse(results.exists())

    def test_record_requires_explicit_real_provider_call_attestation(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            temporary_path = Path(temporary)
            requests_dir = temporary_path / "requests"
            generated = run_cli("generate", "--out", str(requests_dir))
            self.assertEqual(generated.returncode, 0, generated.stderr)
            request = requests_dir / "requests" / "SYN-01-LIQUIDEZ" / "A.json"
            response = temporary_path / "empty-response.txt"
            response.write_text("", encoding="utf-8")
            results = temporary_path / "results.jsonl"
            result = run_cli(
                "record", "--request", str(request), "--provider", "gemini",
                "--model", "explicit-model-id", "--response-file", str(response),
                "--results", str(results),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--confirmed-provider-call", result.stderr)
            self.assertFalse(results.exists())

    def test_record_requires_explicit_non_secret_settings_for_controlled_comparison(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            temporary_path = Path(temporary)
            requests_dir = temporary_path / "requests"
            generated = run_cli("generate", "--out", str(requests_dir))
            self.assertEqual(generated.returncode, 0, generated.stderr)
            request = requests_dir / "requests" / "SYN-01-LIQUIDEZ" / "A.json"
            response = temporary_path / "empty-response.txt"
            response.write_text("", encoding="utf-8")
            results = temporary_path / "results.jsonl"
            result = run_cli(
                "record", "--request", str(request), "--provider", "gemini",
                "--model", "model-id-to-be-reported", "--response-file", str(response),
                "--confirmed-provider-call", "--results", str(results),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--settings-json", result.stderr)
            self.assertFalse(results.exists())
            secret_setting = run_cli(
                "record", "--request", str(request), "--provider", "gemini",
                "--model", "model-id-to-be-reported", "--settings-json", '{"api_key":null}',
                "--response-file", str(response), "--confirmed-provider-call",
                "--results", str(results),
            )
            self.assertIn("credenciales o tokens", secret_setting.stderr)
            self.assertFalse(results.exists())


if __name__ == "__main__":
    unittest.main()
