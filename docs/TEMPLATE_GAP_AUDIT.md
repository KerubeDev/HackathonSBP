# Template Gap Audit

## Scope

This audit compares the current implementation with the decisions confirmed during
the template-only grill session. It is a planning artifact, not a claim that all
items are implemented.

## Hackathon baseline

### Implemented or partially implemented

- FastAPI, LangGraph REA nodes, PostgreSQL, Pandas, Next.js, ECharts, and Compose.
- Explicit `LLM_PROVIDER` configuration for OpenRouter, Ollama, QVAC, and deterministic
  demo mode.
- Read-only SQL validation and schema metadata discovery.
- Persisted run records, API-key seam, request limits, and basic lifecycle logging.
- Basic dashboard, healthcheck, smoke path, and SQL safety tests.

### Implemented in this pass

- API `v1` request/response envelope with strict input fields, poll URL, metadata,
  warnings, and sanitized provider errors.
- Synchronous and thread-backed asynchronous execution modes with persisted
  `queued`, `running`, `completed`, and `failed` states.
- Idempotency-key reuse, paginated `/api/results`, cancellation endpoint, and
  restart-safe database retrieval.
- Versioned ECharts chart metadata, accessible table fallback, deterministic bar
  generation, and an extensible visualization documentation contract.
- PostgreSQL run migration with compatibility `ALTER TABLE` statements.
- Backend contract and chart/SQL tests; Compose backend/frontend builds.

### Remaining baseline improvements

- Expand visualization adapters with richer semantics, visual regression fixtures,
  and automated accessibility checks.
- Add broader integration and browser E2E coverage beyond the verified Compose
  smoke path.
- Add a full dependency/image/license scanner in CI beyond the baseline secret
  check.

## Production roadmap

- Worker-backed durable asynchronous execution.
- OAuth/OIDC and authorization before schema discovery or SQL execution.
- Tenant/user isolation.
- Formal migrations and operational database controls.
- Complete metrics, traces, alerts, retention, and cost controls.
- Load/performance testing, CI/CD, TLS, secret manager integration, and hardened
  deployment.

## Verification rule

The template may show `Template ready for the hackathon.` only after all blocker
items are verified as passing, no known code/documentation contradictions remain,
the end-to-end demo works, and residual risks are documented. This user-visible
 message is intentionally brief; technical evidence remains in engineering artifacts.

## Current verification

The current baseline has passed Python compilation, nine backend tests in the
container, backend and frontend image builds, Compose configuration validation,
sync and async smoke requests, idempotency reuse, and a read-only data query.
