# Hackathon SBP Architecture

## Purpose

The application has two separate calculation boundaries: a deterministic SBP
ranking engine for official results and a read-only AI analysis seam for
explaining persisted results. The AI is never used to calculate, classify, rank,
or mutate an official result.

## Deterministic ranking engine

`backend/app/rankings.py` is a pure domain module. Its caller supplies preserved
text codes, `Decimal` balances, the frozen CINU/SB109 activity catalog, and the
bank/facility catalogs. It processes one period at a time and emits:

- an exclusive E1–E4 quality report and per-record exclusion evidence;
- SB21 CONSUMO subactivity reclassification and catalog-reference alerts;
- six rankings with all catalogued banks, integer-cent/`Decimal` totals,
  four-decimal half-up weights, and bank-code tie-breaking;
- subactivity totals, reconciliation outcomes, source hash, and rule/catalog
  version identity.

This module does not import the LLM graph, database, or web framework, making its
official outputs deterministic and independently testable.

## Runtime flow

1. FastAPI validates the request and creates a `run_id`.
2. `input_node` loads the request and PostgreSQL schema metadata.
3. `analysis_node` applies the ask-to prompt through the explicitly selected LLM
   provider, validates read-only SQL, executes it, and processes rows with Pandas.
4. `output_node` produces the versionable result contract and ECharts option.
5. PostgreSQL persists the run and the frontend polls its status.

The LangGraph graph is the REA state machine. Provider adapters are isolated behind
the `_ask_to_sql` seam and can be replaced without changing the API contract.

## Provider configuration

Set exactly one provider with `LLM_PROVIDER`; no provider is prescribed by an
environment profile:

- `openrouter`: requires `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`.
- `ollama`: uses `OLLAMA_BASE_URL` and `LOCAL_MODEL`.
- `qvac`: uses `QVAC_BASE_URL` and `QVAC_MODEL` through an OpenAI-compatible endpoint.
- `deterministic`: available only when `ALLOW_DETERMINISTIC_FALLBACK=true`.

Provider failures do not silently switch providers.

## Hackathon baseline and production roadmap

The hackathon baseline is a reproducible, business-agnostic demo: Compose startup,
PostgreSQL sample data, explicit provider configuration, deterministic fallback only
when explicitly enabled, end-to-end analysis, tests, smoke checks, documentation,
and sanitized errors.

The production roadmap is separate: durable asynchronous workers, formal migrations,
versioned contracts, OAuth/OIDC and tenant authorization, complete observability,
cost/security controls, load testing, CI/CD, and hardened deployment.

## Boundaries

- `backend/app/config.py`: environment configuration.
- `backend/app/agent.py`: REA graph and analysis orchestration.
- `backend/app/rankings.py`: deterministic E1–E4, SB21, ranking, and
  reconciliation domain logic.
- `backend/app/tools.py`: extension registry for future tools.
- `backend/app/main.py`: HTTP contract and persistence seam.
- `db/`: sample schema only.
- `frontend/`: presentation and ECharts rendering.

## Extension path

Future work may add or change a domain adapter, schema context, prompt version,
tool, or output interpretation layer. When the challenge requires changing the
base, update `CONTEXT.md`, the applicable ADRs, contracts, tests, and this document
together.

## Operational limits

The current baseline execution mode is synchronous. A production worker-backed
asynchronous mode is not yet implemented. Authentication is an optional API key and
does not yet model tenants or users. The current visualization implementation is
smaller than the planned catalog; see `docs/VISUALIZATIONS.md` and the gap audit.
