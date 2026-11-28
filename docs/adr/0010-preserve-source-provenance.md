# ADR 0010: Preserve Original Inputs and Calculation Provenance

## Status

Accepted

## Decision

Uploaded AT03 files are immutable. Filesystem storage preserves originals while
PostgreSQL stores hashes, periods, profiles, versions, processing states, exclusions,
and relationships to generated results.

## Consequences

Every ranking and report can be traced to an exact input and rule version.
Reprocessing is explicit and historical outputs are not silently overwritten.
