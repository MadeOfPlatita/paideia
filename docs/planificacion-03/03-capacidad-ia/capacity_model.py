#!/usr/bin/env python3
"""Reproducible token/quota model for a 100-user Paideia cohort.

This is arithmetic over stated assumptions and published quotas/prices, not a
load test, latency measurement, model-quality benchmark, or capacity guarantee.
Standard-library only. Run: python capacity_model.py
"""
from __future__ import annotations

import csv
import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USERS = 100
CURRENT_USER_TOKENS = 60
TOOL_CALL_OUTPUT_TOKENS = 50
TOOL_RESULT_TOKENS = 120
ONBOARDING_INPUT_TOKENS = 600
ONBOARDING_OUTPUT_TOKENS = 120

CONTEXT_PROFILES = {
    "lean": {"instructions": 400, "tools": 250, "profile": 100, "products": 250},
    "typical": {"instructions": 700, "tools": 500, "profile": 250, "products": 900},
    "heavy": {"instructions": 1200, "tools": 900, "profile": 400, "products": 1800},
}

# Prices, free allocations and limits retrieved from the official pages listed
# in report.md. Groq caps are published free-tier reference values; exact values
# are organization-specific. Cloudflare has no published TPM or concurrency cap.
MODELS = {
    "@cf/meta/llama-3.2-3b-instruct": {
        "provider": "Cloudflare Workers AI", "label": "Llama 3.2 3B", "class": "small",
        "context_window": 80000, "input_usd_per_million": 0.051, "output_usd_per_million": 0.335,
        "input_neurons_per_million": 4625, "output_neurons_per_million": 30475,
        "rpm": 300, "rpd": None, "tpm": None, "tpd": None, "neurons_per_day": 10000,
        "paid_overage_usd_per_1000_neurons": 0.011, "tool_calling": "not_listed_for_model",
        "source_refs": [1, 2, 3],
    },
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast": {
        "provider": "Cloudflare Workers AI", "label": "Llama 3.3 70B", "class": "large",
        "context_window": 24000, "input_usd_per_million": 0.293, "output_usd_per_million": 2.253,
        "input_neurons_per_million": 26668, "output_neurons_per_million": 204805,
        "rpm": 300, "rpd": None, "tpm": None, "tpd": None, "neurons_per_day": 10000,
        "paid_overage_usd_per_1000_neurons": 0.011, "tool_calling": "documented",
        "source_refs": [1, 2, 4],
    },
    "openai/gpt-oss-20b": {
        "provider": "GroqCloud", "label": "GPT-OSS 20B", "class": "small",
        "context_window": 131072, "input_usd_per_million": 0.075, "output_usd_per_million": 0.30,
        "input_neurons_per_million": None, "output_neurons_per_million": None,
        "rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 200000, "neurons_per_day": None,
        "paid_overage_usd_per_1000_neurons": None, "tool_calling": "documented",
        "source_refs": [5, 6, 7],
    },
    "openai/gpt-oss-120b": {
        "provider": "GroqCloud", "label": "GPT-OSS 120B", "class": "large",
        "context_window": 131072, "input_usd_per_million": 0.15, "output_usd_per_million": 0.60,
        "input_neurons_per_million": None, "output_neurons_per_million": None,
        "rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 200000, "neurons_per_day": None,
        "paid_overage_usd_per_1000_neurons": None, "tool_calling": "documented",
        "source_refs": [5, 6, 8],
    },
}

ASSUMPTIONS = {
    "cohort": "100 users, each completes one conversation in one UTC day",
    "current_user_message_tokens_per_turn": CURRENT_USER_TOKENS,
    "context_profiles_tokens": CONTEXT_PROFILES,
    "history_per_prior_turn": "60 user tokens + final answer tokens + one 50-token tool-call message and 120-token tool result per configured tool loop",
    "tool_loop_semantics": "Each loop adds one sequential LLM follow-up call; repeat static context and history on every request; each earlier tool-call/result pair adds 170 input tokens to later calls. Tool execution itself is deterministic and has no model-token cost.",
    "answer_tokens": "250 or 500 final-answer tokens per user turn; each tool-loop call emits 50 tokens before the final answer.",
    "onboarding": "buttons = no LLM call; llm = one bounded call/user with 600 input and 120 output tokens.",
    "cached_input": "No prompt-cache discount assumed; all input priced at uncached rates.",
    "models_and_rates": "Only listed public prices/quotas; no hidden concurrency, SLA, or throughput inferred.",
    "latency": "Unknown. No endpoint calls or load tests were performed; model-directory tokens/second are not converted to end-to-end response latency.",
    "financial_data": "Profile is treated only as a token-count component; no personal financial details or real user data are generated or sent.",
}


def compute_turn(base_context_tokens: int, history_tokens: int, current_message_tokens: int,
                 answer_tokens: int, tool_loops: int,
                 tool_call_output_tokens: int = TOOL_CALL_OUTPUT_TOKENS,
                 tool_result_tokens: int = TOOL_RESULT_TOKENS) -> dict:
    """Calculate repeated prompt tokens and sequential tool-loop calls for one turn."""
    if min(base_context_tokens, history_tokens, current_message_tokens, answer_tokens, tool_loops) < 0:
        raise ValueError("token counts and tool_loops must be non-negative")
    requests = 1 + tool_loops
    repeated_context = base_context_tokens + history_tokens + current_message_tokens
    tool_transcript_input = (tool_call_output_tokens + tool_result_tokens) * tool_loops * (tool_loops + 1) // 2
    input_tokens = repeated_context * requests + tool_transcript_input
    output_tokens = answer_tokens + tool_call_output_tokens * tool_loops
    max_input_one_call = repeated_context + tool_loops * (tool_call_output_tokens + tool_result_tokens)
    return {
        "requests": requests,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_base_context_tokens": base_context_tokens * requests,
        "input_history_tokens": history_tokens * requests,
        "input_current_message_tokens": current_message_tokens * requests,
        "input_tool_transcript_tokens": tool_transcript_input,
        "max_input_one_call_tokens": max_input_one_call,
        "max_output_one_call_tokens": max(answer_tokens, tool_call_output_tokens),
    }


def _cost_usd(tokens_in: int, tokens_out: int, model: dict) -> float:
    return (tokens_in * model["input_usd_per_million"] +
            tokens_out * model["output_usd_per_million"]) / 1_000_000


def _ceil_ratio(numerator, denominator):
    if denominator is None or denominator <= 0:
        return None
    return math.ceil(numerator / denominator)


def evaluate_scenario(config: dict) -> dict:
    model_id = config["model_id"]
    model = MODELS[model_id]
    if config.get("provider", model["provider"]) != model["provider"]:
        raise ValueError(f"{model_id} belongs to {model['provider']}")
    users = int(config.get("users", USERS))
    turns = int(config["turns"])
    answer_tokens = int(config["answer_tokens"])
    loops = int(config["tool_loops"])
    onboarding_mode = config["onboarding_mode"]
    context_profile = config["context_profile"]
    if users < 1 or turns < 1 or answer_tokens < 1 or loops < 0:
        raise ValueError("users, turns, and answer_tokens must be positive; tool_loops non-negative")
    if onboarding_mode not in {"buttons", "llm"}:
        raise ValueError("onboarding_mode must be 'buttons' or 'llm'")

    context = CONTEXT_PROFILES[context_profile]
    base_context = sum(context.values())
    conversation_in = conversation_out = conversation_requests = 0
    totals = {"instructions": 0, "tools": 0, "profile": 0, "products": 0,
              "history": 0, "current_message": 0, "tool_transcript": 0}
    max_request_context = 0
    max_output_one_call = 0
    history = 0
    first_turn = None
    for turn_no in range(1, turns + 1):
        metrics = compute_turn(base_context, history, CURRENT_USER_TOKENS, answer_tokens, loops)
        if first_turn is None:
            first_turn = metrics
        conversation_in += metrics["input_tokens"]
        conversation_out += metrics["output_tokens"]
        conversation_requests += metrics["requests"]
        for component in ("instructions", "tools", "profile", "products"):
            totals[component] += context[component] * metrics["requests"]
        totals["history"] += metrics["input_history_tokens"]
        totals["current_message"] += metrics["input_current_message_tokens"]
        totals["tool_transcript"] += metrics["input_tool_transcript_tokens"]
        max_request_context = max(max_request_context,
                                  metrics["max_input_one_call_tokens"] + metrics["max_output_one_call_tokens"])
        max_output_one_call = max(max_output_one_call, metrics["max_output_one_call_tokens"])
        # Conversation history accumulates once per completed turn, not once per retry.
        history += CURRENT_USER_TOKENS + answer_tokens + loops * (TOOL_CALL_OUTPUT_TOKENS + TOOL_RESULT_TOKENS)

    onboarding_requests_per_user = 1 if onboarding_mode == "llm" else 0
    onboarding_in_per_user = ONBOARDING_INPUT_TOKENS if onboarding_mode == "llm" else 0
    onboarding_out_per_user = ONBOARDING_OUTPUT_TOKENS if onboarding_mode == "llm" else 0
    onboarding_requests = onboarding_requests_per_user * users
    onboarding_in = onboarding_in_per_user * users
    onboarding_out = onboarding_out_per_user * users
    total_requests_per_user = conversation_requests + onboarding_requests_per_user
    total_requests = total_requests_per_user * users
    total_input_per_user = conversation_in + onboarding_in_per_user
    total_output_per_user = conversation_out + onboarding_out_per_user
    total_input = total_input_per_user * users
    total_output = total_output_per_user * users
    total_tokens = total_input + total_output

    # For the first conversational wave, only the initial model call is ready;
    # later tool-loop calls are serial and their timing depends on unknown latency.
    first_call_output = TOOL_CALL_OUTPUT_TOKENS if loops else answer_tokens
    first_call_tokens_per_user = base_context + CURRENT_USER_TOKENS + first_call_output
    burst_requests = users
    burst_tokens = first_call_tokens_per_user * users
    burst_rpm_exceeded = model["rpm"] is not None and burst_requests > model["rpm"]
    burst_tpm_exceeded = model["tpm"] is not None and burst_tokens > model["tpm"]
    burst_queue_minutes = max(
        _ceil_ratio(burst_requests, model["rpm"]) or 0,
        _ceil_ratio(burst_tokens, model["tpm"]) or 0,
    ) or 1

    listed_cost = _cost_usd(total_input, total_output, model)
    neurons = None
    daily_free_quota_ok = None
    daily_free_quota_status = "not_applicable"
    paid_plan_overage = None
    daily_capacity_users = None
    quota_usage = None
    if model["neurons_per_day"] is not None:
        neurons = (total_input * model["input_neurons_per_million"] +
                   total_output * model["output_neurons_per_million"]) / 1_000_000
        daily_free_quota_ok = neurons <= model["neurons_per_day"]
        daily_free_quota_status = "within_published_daily_quota" if daily_free_quota_ok else "exceeds_free_daily_quota"
        paid_plan_overage = max(0.0, neurons - model["neurons_per_day"]) * model["paid_overage_usd_per_1000_neurons"] / 1000
        per_user_neurons = neurons / users
        daily_capacity_users = math.floor(model["neurons_per_day"] / per_user_neurons) if per_user_neurons else users
        quota_usage = neurons / model["neurons_per_day"]
    else:
        request_cap_users = math.floor(model["rpd"] / total_requests_per_user) if total_requests_per_user else users
        token_cap_users = math.floor(model["tpd"] / (total_input_per_user + total_output_per_user)) if total_input_per_user + total_output_per_user else users
        daily_capacity_users = min(request_cap_users, token_cap_users)
        daily_free_quota_ok = total_requests <= model["rpd"] and total_tokens <= model["tpd"]
        daily_free_quota_status = "within_published_daily_quota" if daily_free_quota_ok else "exceeds_free_daily_quota"
        quota_usage = max(total_requests / model["rpd"], total_tokens / model["tpd"])

    return {
        "provider": model["provider"], "model_id": model_id, "model_label": model["label"],
        "model_class": model["class"], "documented_tool_calling": model["tool_calling"],
        "users": users, "onboarding_mode": onboarding_mode, "turns": turns,
        "context_profile": context_profile,
        "context_instructions_tokens": context["instructions"], "context_tools_tokens": context["tools"],
        "context_profile_tokens": context["profile"], "context_products_tokens": context["products"],
        "answer_tokens": answer_tokens, "tool_loops": loops, "tool_loops_per_turn": loops,
        "tool_call_output_tokens_per_loop": TOOL_CALL_OUTPUT_TOKENS,
        "tool_result_input_tokens_per_loop": TOOL_RESULT_TOKENS,
        "conversation_requests_per_user": conversation_requests,
        "onboarding_requests_per_user": onboarding_requests_per_user,
        "onboarding_requests": onboarding_requests,
        "onboarding_input_tokens": onboarding_in, "onboarding_output_tokens": onboarding_out,
        "total_requests_per_user": total_requests_per_user, "cohort_requests_per_day": total_requests,
        "conversation_input_tokens_per_user": conversation_in,
        "conversation_output_tokens_per_user": conversation_out,
        "onboarding_input_tokens_cohort": onboarding_in,
        "onboarding_output_tokens_cohort": onboarding_out,
        "cohort_input_tokens_per_day": total_input, "cohort_output_tokens_per_day": total_output,
        "cohort_total_tokens_per_day": total_tokens,
        "cohort_instruction_input_tokens": totals["instructions"] * users,
        "cohort_tool_definition_input_tokens": totals["tools"] * users,
        "cohort_profile_input_tokens": totals["profile"] * users,
        "cohort_product_input_tokens": totals["products"] * users,
        "cohort_history_input_tokens": totals["history"] * users,
        "cohort_current_message_input_tokens": totals["current_message"] * users,
        "cohort_tool_transcript_input_tokens": totals["tool_transcript"] * users,
        "max_single_request_context_plus_output_tokens": max_request_context,
        "context_window_tokens": model["context_window"],
        "exceeds_model_context_window": max_request_context > model["context_window"],
        "first_turn_initial_burst_requests": burst_requests,
        "first_turn_initial_burst_tokens": burst_tokens,
        "published_rpm_limit": model["rpm"], "published_tpm_limit": model["tpm"],
        "first_turn_burst_exceeds_rpm": bool(burst_rpm_exceeded),
        "first_turn_burst_exceeds_tpm": bool(burst_tpm_exceeded),
        "first_turn_burst_429_risk_without_queue": bool(burst_rpm_exceeded or burst_tpm_exceeded),
        "first_turn_queue_drain_lower_bound_minutes": burst_queue_minutes,
        "published_rpd_limit": model["rpd"], "published_tpd_limit": model["tpd"],
        "published_neurons_per_day": model["neurons_per_day"],
        "cohort_neurons_per_day": neurons,
        "daily_free_quota_usage_ratio": quota_usage,
        "daily_free_quota_status": daily_free_quota_status,
        "daily_free_quota_ok": daily_free_quota_ok,
        "free_tier_capacity_users_at_this_usage": daily_capacity_users,
        "published_list_cost_usd_uncached": listed_cost,
        "cloudflare_paid_plan_overage_if_enabled_usd": paid_plan_overage,
        "latency_ms": None,
        "latency_status": "unknown_not_measured",
        "source_refs": ",".join(str(ref) for ref in model["source_refs"]),
    }


def build_scenarios() -> list[dict]:
    rows = []
    for model_id, model in MODELS.items():
        for onboarding in ("buttons", "llm"):
            for turns in (3, 5, 10):
                for context_profile in ("lean", "typical", "heavy"):
                    for answer_tokens in (250, 500):
                        for tool_loops in (0, 1, 2):
                            rows.append(evaluate_scenario({
                                "provider": model["provider"], "model_id": model_id,
                                "onboarding_mode": onboarding, "turns": turns,
                                "context_profile": context_profile, "answer_tokens": answer_tokens,
                                "tool_loops": tool_loops, "users": USERS,
                            }))
    return rows


def _burst_for_case(model_id: str, users: int, context_profile: str, answer_tokens: int) -> dict:
    model = MODELS[model_id]
    base = sum(CONTEXT_PROFILES[context_profile].values())
    tokens_per_request = base + CURRENT_USER_TOKENS + answer_tokens
    calls = users
    tokens = calls * tokens_per_request
    request_minutes = _ceil_ratio(calls, model["rpm"])
    token_minutes = _ceil_ratio(tokens, model["tpm"])
    return {
        "requests": calls, "tokens": tokens, "rpm_limit": model["rpm"],
        "tpm_limit": model["tpm"],
        "would_429_without_queue": bool(calls > model["rpm"] or (model["tpm"] and tokens > model["tpm"])),
        "queue_drain_lower_bound_minutes": max(request_minutes or 0, token_minutes or 0, 1),
    }


def build_edge_cases() -> list[dict]:
    exhausted_scenario = evaluate_scenario({
        "model_id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        "onboarding_mode": "buttons", "turns": 10, "context_profile": "heavy",
        "answer_tokens": 500, "tool_loops": 2, "users": USERS,
    })
    queue = _burst_for_case("openai/gpt-oss-20b", USERS, "typical", 250)
    rate_burst = _burst_for_case("openai/gpt-oss-20b", USERS, "lean", 250)
    return [
        {
            "case_id": "quota_exhausted", "provider": "Cloudflare Workers AI",
            "model_id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            "state": "exhausted" if not exhausted_scenario["daily_free_quota_ok"] else "not_exhausted",
            "neurons_requested": exhausted_scenario["cohort_neurons_per_day"],
            "neurons_free_limit": exhausted_scenario["published_neurons_per_day"],
            "expected_handling": "Stop inference when the shared free budget is exhausted; deterministic fallback, no paid upgrade without approval.",
        },
        {
            "case_id": "queue_required", "provider": "GroqCloud", "model_id": "openai/gpt-oss-20b",
            "state": "queue_required" if queue["would_429_without_queue"] else "no_queue_by_published_caps",
            "requests": queue["requests"], "tokens": queue["tokens"],
            "rpm_limit": queue["rpm_limit"], "tpm_limit": queue["tpm_limit"],
            "queue_drain_lower_bound_minutes": queue["queue_drain_lower_bound_minutes"],
            "latency_ms": None,
            "expected_handling": "Bounded FIFO queue with shared global limits; lower bound is quota arithmetic, not completion-time prediction.",
        },
        {
            "case_id": "rate_exceeded", "provider": "GroqCloud", "model_id": "openai/gpt-oss-20b",
            "state": "rate_exceeded" if rate_burst["would_429_without_queue"] else "within_rate_caps",
            "requests": rate_burst["requests"], "tokens": rate_burst["tokens"],
            "rpm_limit": rate_burst["rpm_limit"], "tpm_limit": rate_burst["tpm_limit"],
            "would_429_without_queue": rate_burst["would_429_without_queue"],
            "expected_handling": "Do not retry in a tight loop; honor Retry-After if supplied, jittered backoff, then fallback/queue.",
        },
        {
            "case_id": "latency_unknown", "provider": "All modeled providers", "model_id": None,
            "state": "unknown_not_measured", "latency_ms": None,
            "expected_handling": "Expose latency as unknown until endpoint tests collect p50/p95; no synthetic latency value.",
        },
    ]


def _write_outputs() -> tuple[list[dict], list[dict]]:
    rows = build_scenarios()
    edge_cases = build_edge_cases()
    csv_path = ROOT / "scenarios.csv"
    json_path = ROOT / "scenarios.json"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "format_version": 1,
        "generated_on": date.today().isoformat(),
        "scenario_count": len(rows),
        "users_per_scenario": USERS,
        "units": {"prices": "USD", "tokens": "tokens", "Cloudflare quota": "Neurons/day", "latency": "milliseconds or null"},
        "assumptions": ASSUMPTIONS,
        "models": list(MODELS.values()),
        "scenarios": rows,
        "edge_cases": edge_cases,
        "fairness_policy": {
            "identity": "Per authenticated account or signed anonymous session; never rely on source IP as the sole quota key.",
            "shared_networks": "Treat NAT/shared-IP bursts as one network signal only; do not pool or revoke the per-user allowance because users share an IP.",
            "allocation": "Reserve 10% of the published free daily cap for service overhead; divide the other 90% equally across 100 active users and debit by actual tokens/Neurons and requests.",
            "global_control": "One account-global atomic counter and queue per provider/model, honoring documented RPM/TPM/RPD/TPD/Neuron limits. No multi-account/key quota splitting.",
            "fallback": "When a user's fair share or the global free quota is exhausted, pause AI for that user and show deterministic catalog search, calculator, FAQ or an explicit unavailable message.",
        },
        "limitations": [
            "Quota arithmetic is not a measurement of throughput, concurrency or latency.",
            "No calls to provider APIs, accounts, keys, payments or external load were used.",
            "Groq limits are public free-plan reference values and vary by organization; Cloudflare publishes no TPM or concurrency guarantee for the modeled standard text generation path.",
            "Tool loops are modeled token/request overhead; native function-calling support for Cloudflare Llama 3.2 3B is not listed on its model page, so its tool integration is unverified.",
            "No exchange-rate conversion; zero-euro recommendation means no paid spend, not that any paid USD list-price amount converts to a particular EUR value.",
        ],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows, edge_cases


if __name__ == "__main__":
    scenarios, cases = _write_outputs()
    print(json.dumps({
        "generated_on": date.today().isoformat(),
        "scenario_count": len(scenarios),
        "edge_case_count": len(cases),
        "csv": str(ROOT / "scenarios.csv"),
        "json": str(ROOT / "scenarios.json"),
        "users": USERS,
    }, ensure_ascii=False))
