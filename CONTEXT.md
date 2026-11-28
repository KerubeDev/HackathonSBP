# Repository Context

## Current scope

This repository now contains the refined baseline for Hackathon SBP 2026:
an interactive, local platform for banking-credit rankings and analysis using
synthetic AT03 data. The domain adaptation is intentional and may continue to
update this context, existing ADRs, code, and documentation as the challenge
implementation evolves.

## Current architecture vocabulary

- **REA loop:** Reason, Execute, and Iterate.
- **ask-to seam:** Converts a natural-language question into a read-only SQL query.
- **Provider selection:** The configured `LLM_PROVIDER` is the only provider used for
  a run: `openrouter`, `ollama`, `qvac`, or explicitly enabled `deterministic`.
- **Analysis result:** Versionable JSON containing summary, SQL, rows, ECharts
  configuration, provider/model metadata, warnings, and errors.
- **Visualization catalog:** Extensible ECharts adapters selected by deterministic
  data rules with optional constrained model suggestions and a tabular fallback.
- **Template evolution:** The future challenge will be integrated by updating this
  context, existing ADRs, and architecture documentation rather than creating a
  permanently separate context document.
- **AT03:** 61-field synthetic regulatory-shaped credit record.
- **SB21:** Facility catalog and the special CONSUMO reclassification rule.
- **CINU/SB109:** Frozen activity catalog used as the only activity classification key.
- **E1–E4:** Cascading exclusions: duplicates, foreign destination, non-positive
  balance, and uncatalogued activity.
- **Local valid universe:** Records remaining after E1–E4.
- **Ranking:** Six macroactivities by 12 fictitious banks and three monthly periods.
- **Profiles:** Público, Analista, and Administrador with differentiated capabilities.
- **Official result:** Deterministic ranking calculations; AI may explain or explore,
  but cannot calculate or alter official rankings.

## Engineering rules

Use explicit module boundaries, typed API contracts, environment-based configuration,
explicit single-provider selection, read-only database access, safe SQL validation,
observable request/run IDs, accessibility, tests at unit/integration/contract/E2E
seams, reproducible environments, and English repository artifacts.

## Hackathon domain rules

- Source files and supplied catalogs are authoritative; the indications document
  prevails over presentation slides if they differ.
- Original uploaded files are immutable and retained with hash, period, uploader,
  rule/catalog versions, and processing status.
- Rankings use exact decimal/cent values, official E1–E4 cascade, SB21, full-bank
  denominators, four-decimal percentages, and official tie-breaking.
- All six rankings are computed for all 12 banks in all three periods, including
  zero-balance banks.
- The application always shows source, period, update time, fictitious-data notice,
  rule version, and quality status.
- No customer names, IDs, or customer attributes may classify economic activity.

## Deferred implementation decisions

Browser visual regression, durable production workers, OAuth/OIDC, tenant isolation,
advanced observability, and load testing remain production-roadmap work. The current
refined context is documentation-only; coding begins after this refinement artifact
is reviewed.
