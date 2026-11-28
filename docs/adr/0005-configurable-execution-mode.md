# ADR 0005: Support Synchronous and Asynchronous Execution

## Status

Accepted

## Decision

Development defaults to synchronous execution for fast feedback. Production can use
the same run contract with a worker-backed asynchronous executor.

## Consequences

The API remains stable while deployment profiles change. The asynchronous worker is
an explicit follow-up before high-volume production use.
