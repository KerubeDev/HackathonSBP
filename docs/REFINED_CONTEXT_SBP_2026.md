# Refined Context — Hackathon SBP 2026

## Objective

Adapt the existing generic LangGraph/FastAPI/Next.js/PostgreSQL template into a
local, reproducible platform for interactive banking-credit rankings and analysis.
The platform must transform the supplied synthetic AT03 files into verifiable
rankings by bank and economic activity.

## Authoritative inputs

`docs/track/INDICACIONES_RETO_RANKING_CREDITO.md` is normative. The slide deck
describes the product and evaluation expectations; the indications document wins
when they differ.

Inputs:

- three monthly AT03 CSVs for `20260731`, `20260831`, and `20260930`;
- frozen CINU/SB109 activity catalog;
- simplified SB21 facility catalog;
- fictitious-bank catalog;
- AT03 data dictionary.

All input codes remain text, including leading zeroes. Original files are retained
unchanged with content hash and load metadata.

## Deterministic calculation contract

For each period, apply the exclusive cascade:

1. E1: retain the first row for duplicate `Numero_Prestamo`;
2. E2: exclude `Destino != 'L'`;
3. E3: exclude `Saldo <= 0`;
4. E4: exclude uncatalogued `Tipo_Actividad`.

The remaining rows form the local-valid universe. Classify only through CINU/SB109,
apply the SB21 CONSUMO rule, aggregate exact balances, calculate the full-bank
portfolio denominator, calculate four-decimal percentage weights, and rank all 12
banks with the official tie-break.

Required rankings are HIPOTECARIO, CONSTRUCCION, INDUSTRIA, AGROPECUARIO,
COMERCIO, and CONSUMO. The first four are mandatory; the last two are required by
the evaluation key and should be present in the product.

## Product modules

1. Configurable dashboard.
2. Ranking query.
3. Filters and exploration.
4. Period/entity visualization and comparison.
5. Reports and exports.
6. Administrator upload and operations/quality view.

The dashboard always exposes source, period, update time, rule version, quality
status, and `Datos ficticios para fines de demostración`.

## Profiles

- **Público:** read-only rankings, filters, tables, charts, and authorized downloads.
- **Analista:** comparisons, movements, explorations, explanations, and custom reports.
- **Administrador:** AT03 upload/replacement, catalog version activation, parameters,
  quality reports, and operational audit.

The prototype uses a profile selector prepared for future authentication.

## Automation and AI boundary

The system automatically recalculates on a new period, compares consecutive periods,
detects configurable significant movements, explains movements, and prepares reports.
The deterministic engine is authoritative. AI can explain existing results, answer
grounded exploratory questions, suggest visualizations, and summarize reports. AI
cannot calculate official positions, alter balances, decide E1–E4, change SB21, edit
catalogs, or publish unvalidated results.

## Persistence and provenance

Planned core entities are `source_files`, `load_runs`, `quality_exclusions`,
`at03_records`, `ranking_results`, `ranking_subactivities`, `period_comparisons`,
and `audit_events`. Catalogs and rules are versioned. Reprocessing a period is
explicit and never silently changes historical results.

## Output contract

Exports include CSV, XLSX, PDF, and JSON. The official ranking export contains
period, ranking, position, bank code/name, activity balance, total valid local
portfolio, weight, valid operations, source, rule version, and fictitious-data notice.
Quality exports contain E1–E4, valid universe, alerts, row reconciliation, and source
hash. Movement exports contain position delta, balance delta, percentage delta, and
significance reason.

## Template mapping

- **Agent graph:** retain REA/LangGraph; add deterministic ranking and report nodes;
  keep ask-to as a grounded query/explanation seam.
- **Database:** replace `sample_metrics` with versioned source, normalized AT03,
  quality, ranking, comparison, catalog, and audit tables.
- **API:** add profile, upload/preview/confirm, quality, rankings, comparisons,
  exports, catalog versions, and audit endpoints.
- **Frontend:** add profile-aware navigation, dashboard, rankings, filters,
  comparisons, upload preview, quality, operations, and export components.

## Current non-goals

No production deployment, external publication, tenant isolation, full OAuth/OIDC,
or AI-dependent ranking calculation is required for the local hackathon prototype.
