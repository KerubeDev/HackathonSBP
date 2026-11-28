# ADR 0006: Use a Versionable Dashboard Result

## Status

Accepted

## Decision

Results contain summary, SQL, raw rows, direct ECharts options, provider/model,
execution metadata, warnings, status, sanitized errors, and version metadata.
`chart_config` is extensible, validated, accessible, and includes a table fallback.

## Consequences

Frontends can remain generic and future dashboards can evolve additively. Breaking
changes require a new contract version and migration note.
