# ADR 0001: Keep the Template Business-Agnostic

## Status

Accepted

## Decision

The current baseline contains reusable agent infrastructure only. Domain rules,
terminology, KPIs, authorization roles, and workflows are deferred until the
business challenge is known. The template is expected to evolve when that challenge
arrives; the existing context, ADRs, code, and documentation may be updated.

## Consequences

The template is adaptable and avoids premature coupling. Future work may change the
base where required, but changes must remain explicit, documented, tested, and
traceable.
