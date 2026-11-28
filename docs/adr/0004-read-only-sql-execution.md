# ADR 0004: Enforce Read-Only SQL

## Status

Accepted

## Decision

The agent may execute only one `SELECT` or `WITH` statement against a read-only
database connection. Metadata discovery, row limits, timeouts, and SQL validation
are mandatory safeguards.

## Consequences

The template is safer for unknown business data. Mutating workflows require separate,
explicit tools and approvals.
