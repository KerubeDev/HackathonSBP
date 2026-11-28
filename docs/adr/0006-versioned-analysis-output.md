# ADR 0006: Use a Versionable Dashboard Result

## Status

Accepted

## Decision

Results contain summary, SQL, raw rows, direct ECharts options, provider/model,
execution metadata, warnings, status, and sanitized errors.

## Consequences

Frontends can remain generic and future dashboards can evolve additively. Breaking
changes require a new contract version and migration note.
