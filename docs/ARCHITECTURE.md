# Generic AI Agent Template Architecture

## Purpose

The template accepts a natural-language data question and returns a dashboard-ready
analysis result. It contains no business-specific rules.

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

Set exactly one provider with `LLM_PROVIDER`:

- `openrouter`: requires `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`.
- `ollama`: uses `OLLAMA_BASE_URL` and `LOCAL_MODEL`.
- `qvac`: uses `QVAC_BASE_URL` and `QVAC_MODEL` through an OpenAI-compatible endpoint.
- `deterministic`: available only when `ALLOW_DETERMINISTIC_FALLBACK=true`.

Provider failures do not silently switch providers.

## Boundaries

- `backend/app/config.py`: environment configuration.
- `backend/app/agent.py`: REA graph and analysis orchestration.
- `backend/app/tools.py`: extension registry for future tools.
- `backend/app/main.py`: HTTP contract and persistence seam.
- `db/`: sample schema only.
- `frontend/`: presentation and ECharts rendering.

## Extension path

Future work should add a domain adapter, schema context, prompt version, tool, or
output interpretation layer. It should not edit the generic REA contract unless a
versioned API change is intentional.

## Operational limits

The current default execution mode is synchronous. The API and persisted run model
are designed for a worker-backed asynchronous mode, which should be implemented
before production-scale workloads. Authentication is an optional API key and does
not yet model tenants or users.
