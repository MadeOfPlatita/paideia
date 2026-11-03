"""Arnés offline para comparar contexto A/B/C con seis casos sintéticos.

Este módulo no implementa clientes de proveedores ni realiza llamadas de red.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
VARIANTS = ("A", "B", "C")


class BenchmarkError(ValueError):
    """Error de dataset, contrato o uso seguro del arnés."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def ensure_inside_benchmark(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(BASE_DIR)
    except ValueError as exc:
        raise BenchmarkError(f"{label} debe permanecer dentro de {BASE_DIR}") from exc
    return resolved


def load_dataset(path: Path) -> dict[str, Any]:
    dataset_path = ensure_inside_benchmark(path, "El dataset")
    try:
        raw = dataset_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BenchmarkError(f"No se pudo leer el dataset: {dataset_path}") from exc
    try:
        dataset = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BenchmarkError(f"Dataset JSON inválido en línea {exc.lineno}, columna {exc.colno}") from exc
    if not isinstance(dataset, dict):
        raise BenchmarkError("La raíz del dataset debe ser un objeto JSON")
    return dataset


def validate_dataset(dataset: dict[str, Any]) -> None:
    if dataset.get("synthetic_only") is not True:
        raise BenchmarkError("El dataset debe declarar synthetic_only=true")
    profile_fields = dataset.get("profile_fields")
    if not isinstance(profile_fields, list) or not profile_fields or len(set(profile_fields)) != len(profile_fields):
        raise BenchmarkError("profile_fields debe ser una lista no vacía y sin duplicados")
    forbidden_fields = {"name", "full_name", "dni", "nie", "iban", "bank_account", "password", "credential", "email", "phone"}
    if forbidden_fields.intersection(profile_fields):
        raise BenchmarkError("El perfil no puede contener identificadores ni credenciales")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or len(cases) != 6:
        raise BenchmarkError("El dataset debe contener exactamente seis casos")
    case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise BenchmarkError("Cada caso debe ser un objeto")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", case_id) or case_id in case_ids:
            raise BenchmarkError("Cada case_id debe ser único y no vacío")
        case_ids.add(case_id)
        if case.get("synthetic") is not True:
            raise BenchmarkError(f"{case_id}: todos los casos deben ser sintéticos")
        profile = case.get("profile")
        if not isinstance(profile, dict) or set(profile) != set(profile_fields):
            raise BenchmarkError(f"{case_id}: el perfil debe incluir todos y solo los campos declarados")
        selected_fields = case.get("projection_fields")
        projection = case.get("relevant_projection")
        exclusion_reason = case.get("projection_exclusion_reason")
        if not isinstance(exclusion_reason, str) or not exclusion_reason.strip():
            raise BenchmarkError(f"{case_id}: debe justificarse la exclusión de campos de B")
        if not isinstance(selected_fields, list) or not selected_fields:
            raise BenchmarkError(f"{case_id}: projection_fields debe ser una lista no vacía")
        if len(selected_fields) != len(set(selected_fields)):
            raise BenchmarkError(f"{case_id}: projection_fields contiene duplicados")
        if not isinstance(projection, dict) or set(projection) != set(selected_fields):
            raise BenchmarkError(f"{case_id}: la proyección debe declarar exactamente los campos seleccionados")
        if any(not isinstance(field, str) or field not in profile for field in selected_fields):
            raise BenchmarkError(f"{case_id}: la proyección selecciona un campo inexistente")
        selected = {field: profile[field] for field in selected_fields}
        if canonical_json(selected) != canonical_json(projection):
            raise BenchmarkError(f"{case_id}: la proyección difiere del perfil; posible pérdida o mutación de datos")
        if not isinstance(case.get("question"), str) or not case["question"].strip():
            raise BenchmarkError(f"{case_id}: falta pregunta")
        if not isinstance(case.get("fixed_evidence"), dict):
            raise BenchmarkError(f"{case_id}: fixed_evidence debe ser un objeto")
        if not isinstance(case.get("expected_facts"), list) or not case["expected_facts"]:
            raise BenchmarkError(f"{case_id}: faltan hechos esperados")
        if not isinstance(case.get("critical_errors"), list) or not case["critical_errors"]:
            raise BenchmarkError(f"{case_id}: faltan errores críticos")
    rubric = dataset.get("human_rubric")
    if not isinstance(rubric, dict) or not rubric.get("non_compensable_gates"):
        raise BenchmarkError("Falta una rúbrica humana con puertas no compensables")
    dimensions = rubric.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise BenchmarkError("La rúbrica debe incluir dimensiones")
    weights = [dimension.get("weight_percent") for dimension in dimensions if isinstance(dimension, dict)]
    if len(weights) != len(dimensions) or sum(weights) != 100:
        raise BenchmarkError("Los pesos de la rúbrica deben sumar 100%")
    variants = dataset.get("variants")
    if not isinstance(variants, dict) or set(variants) != set(VARIANTS):
        raise BenchmarkError("Se requieren exactamente las variantes A, B y C")


def materialize_request(dataset: dict[str, Any], case: dict[str, Any], variant: str) -> dict[str, Any]:
    if variant == "A":
        context_status = "not_provided"
        context_data = None
        selected_fields: list[str] = []
        excluded_fields = [
            {"field": field, "reason": "Omisión intencional del perfil completo en la variante A (sin perfil)."}
            for field in dataset["profile_fields"]
        ]
    elif variant == "B":
        context_status = "projected"
        context_data = case["relevant_projection"]
        selected_fields = list(case["projection_fields"])
        excluded_fields = [
            {"field": field, "reason": case["projection_exclusion_reason"]}
            for field in dataset["profile_fields"] if field not in selected_fields
        ]
    elif variant == "C":
        context_status = "complete_synthetic_profile"
        context_data = case["profile"]
        selected_fields = list(dataset["profile_fields"])
        excluded_fields = []
    else:
        raise BenchmarkError(f"Variante desconocida: {variant}")

    base = {
        "system": dataset["prompt_contract"]["system"],
        "output_constraints": dataset["prompt_contract"]["output_constraints"],
        "fixed_evidence": case["fixed_evidence"],
        "question": case["question"],
    }
    base_sha256 = hashlib.sha256(canonical_json(base).encode("utf-8")).hexdigest()
    user_parts = [
        "EVIDENCIA SINTÉTICA FIJA\n" + canonical_json(base["fixed_evidence"]),
    ]
    if context_data is not None:
        label = "PROYECCIÓN RELEVANTE B" if variant == "B" else "PERFIL SINTÉTICO COMPLETO C"
        user_parts.append(label + "\n" + canonical_json(context_data))
    user_parts.append("PREGUNTA\n" + base["question"])
    messages = [
        {"role": "system", "content": base["system"]},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]
    rendered_prompt = "SYSTEM\n" + base["system"] + "\n\nUSER\n" + messages[1]["content"]
    return {
        "request_schema": "pai-context-request/v1",
        "case_id": case["case_id"],
        "variant": variant,
        "provider_call_status": "not_called",
        "provider": None,
        "model": None,
        "base": base,
        "base_sha256": base_sha256,
        "profile_context": {
            "status": context_status,
            "data": context_data,
            "selected_fields": selected_fields,
            "excluded_fields": excluded_fields,
        },
        "messages": messages,
        "rendered_prompt": rendered_prompt,
        "adapter_contract": "Enviar solo messages; provider/model se configuran fuera de este artefacto. No contiene credenciales ni ejecuta red.",
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_requests(dataset: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir = ensure_inside_benchmark(output_dir, "El directorio de salida")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise BenchmarkError("El directorio de salida debe no existir o estar vacío; no se sobrescribe contenido")
    generated: list[str] = []
    materialized: list[tuple[Path, dict[str, Any]]] = []
    for case in dataset["cases"]:
        for variant in VARIANTS:
            request = materialize_request(dataset, case, variant)
            relative = Path("requests") / case["case_id"] / f"{variant}.json"
            materialized.append((relative, request))
            generated.append(relative.as_posix())
    manifest = {
        "manifest_schema": "pai-context-manifest/v1",
        "dataset_version": dataset.get("dataset_version"),
        "request_count": len(materialized),
        "provider_calls": 0,
        "result_count": 0,
        "winner": None,
        "requests": generated,
    }
    for relative, request in materialized:
        write_json(output_dir / relative, request)
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def read_request(path: Path) -> dict[str, Any]:
    request_path = ensure_inside_benchmark(path, "El request")
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError("No se pudo leer el request JSON") from exc
    if not isinstance(request, dict) or request.get("request_schema") != "pai-context-request/v1":
        raise BenchmarkError("El archivo no es un request materializado por este arnés")
    if request.get("variant") not in VARIANTS or request.get("provider_call_status") != "not_called":
        raise BenchmarkError("El request no tiene variante/estado admitidos")
    if not isinstance(request.get("case_id"), str) or not isinstance(request.get("base_sha256"), str):
        raise BenchmarkError("El request no incluye case_id y huella base")
    expected = hashlib.sha256(canonical_json(request.get("base")).encode("utf-8")).hexdigest()
    if expected != request["base_sha256"]:
        raise BenchmarkError("La huella del contenido base del request no coincide")
    return request


def read_results(path: Path) -> list[dict[str, Any]]:
    results_path = ensure_inside_benchmark(path, "El registro de resultados")
    if not results_path.exists():
        return []
    try:
        lines = results_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise BenchmarkError("No se pudo leer el registro de resultados") from exc
    results: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BenchmarkError(f"Registro JSONL inválido en línea {line_number}") from exc
        if not isinstance(result, dict) or result.get("result_schema") != "pai-context-result/v1":
            raise BenchmarkError(f"Registro no reconocido en línea {line_number}")
        if result.get("provider_call_confirmed") is not True:
            raise BenchmarkError(f"Registro sin confirmación de llamada en línea {line_number}")
        results.append(result)
    return results


def nonnegative_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un entero no negativo") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("debe ser un entero no negativo")
    return number


def parse_settings_json(value: str) -> dict[str, Any]:
    try:
        settings = json.loads(value)
    except json.JSONDecodeError as exc:
        raise BenchmarkError("--settings-json debe contener JSON válido no secreto") from exc
    if not isinstance(settings, dict) or not settings:
        raise BenchmarkError("--settings-json debe ser un objeto no vacío de parámetros comparables")
    secret_key_pattern = re.compile(r"api[_-]?key|secret|password|credential|authorization|bearer|token", re.IGNORECASE)

    def reject_secret_names(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                if secret_key_pattern.search(str(key)):
                    raise BenchmarkError("--settings-json no puede contener campos de credenciales o tokens")
                reject_secret_names(nested)
        elif isinstance(item, list):
            for nested in item:
                reject_secret_names(nested)

    reject_secret_names(settings)
    return settings


def record_result(args: argparse.Namespace) -> dict[str, Any]:
    if not args.model.strip():
        raise BenchmarkError("--model debe contener el identificador exacto del modelo ejecutado")
    settings = parse_settings_json(args.settings_json)
    request = read_request(args.request)
    try:
        response_text = args.response_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise BenchmarkError("No se pudo leer el archivo local de respuesta real") from exc
    if not response_text.strip():
        raise BenchmarkError("La respuesta está vacía; no se registra ningún resultado")
    result = {
        "result_schema": "pai-context-result/v1",
        "result_id": uuid.uuid4().hex,
        "case_id": request["case_id"],
        "variant": request["variant"],
        "provider": args.provider,
        "model": args.model,
        "settings": settings,
        "provider_call_confirmed": True,
        "request_base_sha256": request["base_sha256"],
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "response_text": response_text,
        "response_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
        "metrics": {
            "latency_ms": args.latency_ms,
            "input_tokens": args.input_tokens,
            "output_tokens": args.output_tokens,
        },
        "provider_request_id": args.provider_request_id,
    }
    results_path = ensure_inside_benchmark(args.results, "El registro de resultados")
    existing = read_results(results_path)
    serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(serialized)
    return {
        "recorded": True,
        "record_number": len(existing) + 1,
        "case_id": result["case_id"],
        "variant": result["variant"],
        "provider": result["provider"],
        "model": result["model"],
        "winner": None,
    }


def summarize_results(path: Path) -> dict[str, Any]:
    results = read_results(path)
    by_variant = {variant: 0 for variant in VARIANTS}
    by_provider = {provider: 0 for provider in ("gemini", "groq")}
    for result in results:
        variant = result.get("variant")
        provider = result.get("provider")
        if variant in by_variant:
            by_variant[variant] += 1
        if provider in by_provider:
            by_provider[provider] += 1
    return {
        "provider_call_count": len(results),
        "result_count": len(results),
        "by_variant": by_variant,
        "by_provider": by_provider,
        "winner": None,
        "winner_status": "not_evaluated; requiere rúbrica humana, revisión de errores y puertas no compensables",
    }


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Arnés offline de contexto Pai; no llama a proveedores.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validar los seis casos y sus proyecciones")
    validate_parser.add_argument("--dataset", type=Path, default=BASE_DIR / "dataset.json")
    generate_parser = subparsers.add_parser("generate", help="materializar 18 prompts locales sin llamada externa")
    generate_parser.add_argument("--dataset", type=Path, default=BASE_DIR / "dataset.json")
    generate_parser.add_argument("--out", type=Path, default=BASE_DIR / "generated")
    record_parser = subparsers.add_parser("record", help="registrar una respuesta real ya obtenida fuera del arnés")
    record_parser.add_argument("--request", type=Path, required=True)
    record_parser.add_argument("--provider", choices=("gemini", "groq"), required=True)
    record_parser.add_argument("--model", required=True, help="identificador exacto observado; no se asume un modelo")
    record_parser.add_argument("--settings-json", required=True,
                               help="JSON no secreto con configuración efectiva (p. ej. sampling y límite de salida)")
    record_parser.add_argument("--response-file", type=Path, required=True)
    record_parser.add_argument("--confirmed-provider-call", action="store_true", required=True,
                               help="atestigua que se llamó realmente al proveedor; no convierte un stub en IA")
    record_parser.add_argument("--results", type=Path, default=BASE_DIR / "results.jsonl")
    record_parser.add_argument("--latency-ms", type=nonnegative_int)
    record_parser.add_argument("--input-tokens", type=nonnegative_int)
    record_parser.add_argument("--output-tokens", type=nonnegative_int)
    record_parser.add_argument("--provider-request-id")
    summary_parser = subparsers.add_parser("summary", help="contar resultados reales; no proclama ganador")
    summary_parser.add_argument("--results", type=Path, default=BASE_DIR / "results.jsonl")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == "validate":
            dataset = load_dataset(args.dataset)
            validate_dataset(dataset)
            print(json.dumps({
                "valid": True,
                "dataset_version": dataset.get("dataset_version"),
                "case_count": len(dataset["cases"]),
                "provider_calls": 0,
                "result_count": 0,
                "winner": None,
            }, ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "generate":
            dataset = load_dataset(args.dataset)
            validate_dataset(dataset)
            manifest = generate_requests(dataset, args.out)
            print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "record":
            if not args.confirmed_provider_call:
                raise BenchmarkError("Debe confirmarse una llamada real al proveedor")
            recorded = record_result(args)
            print(json.dumps(recorded, ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "summary":
            summary = summarize_results(args.results)
            print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
            return 0
    except BenchmarkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
