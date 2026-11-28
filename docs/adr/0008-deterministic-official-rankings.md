# ADR 0008: Keep Official Rankings Deterministic

## Status

Accepted

## Decision

Official rankings, exclusions, SB21 classification, aggregations, percentages,
positions, and reconciliations are calculated deterministically. LLMs may explain
or explore validated results but cannot calculate or mutate official values.

## Consequences

Results are reproducible and auditable. AI availability cannot compromise the
evaluation-critical ranking outputs.
