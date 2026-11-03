# Extracted primary-source evidence

> Nota de revisión: estos extractos originales se conservan como contexto histórico. Tras una sobrescritura cruzada del ledger, el coordinador volvió a recuperar las ocho páginas y reconstruyó las citas. La evidencia vinculada a las URLs correctas está en `restauracion/01.txt`–`08.txt`, `restauracion/comprobaciones.json` y `source-ledger.json`. No utilizar el archivo de incidente como bibliografía.

The quotations below are copied verbatim from the official pages fetched for this model.

Last updated Oct 20, 2026

## Cloudflare Workers AI pricing

Our free allocation allows anyone to use a total of **10,000 Neurons per day at no charge**.

On Workers Paid, you will be charged at $0.011 / 1,000 Neurons for any usage above the free allocation of 10,000 Neurons per day.

All limits reset daily at 00:00 UTC. If you exceed any one of the above limits, further operations will fail with an error.

| @cf/meta/llama-3.2-3b-instruct | $0.051 per M input tokens <br> $0.335 per M output tokens | 4625 neurons per M input tokens <br> 30475 neurons per M output tokens |

| @cf/meta/llama-3.3-70b-instruct-fp8-fast | $0.293 per M input tokens <br> $2.253 per M output tokens | 26668 neurons per M input tokens <br> 204805 neurons per M output tokens |

## Cloudflare Workers AI limits

- 300 requests per minute, unless the model requires the Workers Paid plan

## Cloudflare model capabilities

| Context Window[ ↗](/workers-ai/platform/glossary/) | 80,000 tokens |

| Unit Pricing | $0.0509 per M input tokens, $0.335 per M output tokens |

| Context Window[ ↗](/workers-ai/platform/glossary/) | 24,000 tokens |

| Function calling [ ↗](/workers-ai/function-calling/) | Yes |

| Unit Pricing | $0.293 per M input tokens, $2.253 per M output tokens |

## GroqCloud free rate limits

Rate limits apply at the organization level, not individual users. You can hit any limit type depending on which threshold you reach first.

| openai/gpt-oss-120b | 30 | 1K | 8K | 200K | - | - |
| openai/gpt-oss-20b | 30 | 1K | 8K | 200K | - | - |

## Groq model pricing

| [![OpenAI](/_next/static/media/openailogo.523c87a0.svg)GPT OSS 120B](/docs/model/openai/gpt-oss-120b) openai/gpt-oss-120b | 500 | $0.15 input$0.60 output | 250K TPM1K RPM | 131,072 | 65,536 | - |
| [![OpenAI](/_next/static/media/openailogo.523c87a0.svg)GPT OSS 20B](/docs/model/openai/gpt-oss-20b) openai/gpt-oss-20b | 1000 | $0.075 input$0.30 output | 250K TPM1K RPM | 131,072 | 65,536 | - |

## Groq GPT-OSS model capability/pricing excerpts

OpenAI's compact open-weight Mixture-of-Experts (MoE) model with 20B total parameters. Optimized for cost-efficient deployment and agentic workflows, it supports long-context reasoning, tool use, and function calling in a small memory footprint.

CAPABILITIES

[Tool Use](/docs/tool-use), [Browser Search](/docs/browser-search), [Code Execution](/docs/code-execution), [JSON Object Mode](/docs/structured-outputs#json-object-mode), [JSON Schema Mode](/docs/structured-outputs), [Reasoning](/docs/reasoning)

Input

$0.075

Cached Input

$0.037

Output

$0.30

OpenAI's flagship open-weight MoE model with 120B total parameters.

CAPABILITIES

[Tool Use](/docs/tool-use), [Browser Search](/docs/browser-search), [Code Execution](/docs/code-execution), [JSON Object Mode](/docs/structured-outputs#json-object-mode), [JSON Schema Mode](/docs/structured-outputs), [Reasoning](/docs/reasoning)

Input

$0.15

Cached Input

$0.075

Output

$0.60
