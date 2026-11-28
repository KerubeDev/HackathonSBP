# Repository Context

## Current scope

This repository contains a generic, business-agnostic AI Agent template for rapid
hackathon adaptation. It is a starting point, not an implementation of a specific
business domain. Future domain vocabulary, data contracts, users, roles, KPIs, and
workflows must be added in a later context refinement session.

## Current architecture vocabulary

- **REA loop:** Reason, Execute, and Iterate.
- **ask-to seam:** Converts a natural-language question into a read-only SQL query.
- **Provider selection:** The configured `LLM_PROVIDER` is the only provider used for
  a run: `openrouter`, `ollama`, `qvac`, or explicitly enabled `deterministic`.
- **Analysis result:** Versionable JSON containing summary, SQL, rows, ECharts
  configuration, provider/model metadata, warnings, and errors.
- **Template boundary:** Domain logic belongs in future adapters, prompts, schemas,
  and tools; it must not be added to the generic core.

## Engineering rules

Use explicit module boundaries, typed API contracts, environment-based configuration,
read-only database access, safe SQL validation, observable run IDs, tests at unit,
integration, and end-to-end seams, and English repository artifacts.

## Deferred context

The future business challenge is intentionally unknown. Do not infer its domain or
modify this context with business assumptions until the next refinement session.
