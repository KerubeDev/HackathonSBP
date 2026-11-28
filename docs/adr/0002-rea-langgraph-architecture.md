# ADR 0002: Use a LangGraph REA State Machine

## Status

Accepted

## Decision

The agent is structured as input, analysis, and output nodes. The analysis node
implements the Reason, Execute, and Iterate responsibility boundary and uses the
ask-to natural-language-to-SQL seam.

## Consequences

State transitions are inspectable and extensible. Retry policy and asynchronous
workers can evolve without changing the dashboard contract.
