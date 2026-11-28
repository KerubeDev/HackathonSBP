# ADR 0001: Keep the Template Business-Agnostic

## Status

Accepted

## Decision

The baseline contains reusable agent infrastructure only. Domain rules, terminology,
KPIs, authorization roles, and workflows are deferred until the business challenge
is known.

## Consequences

The template is adaptable and avoids premature coupling. Future work must introduce
domain behavior through explicit adapters and documented contracts.
