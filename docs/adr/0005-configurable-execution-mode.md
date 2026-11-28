# ADR 0005: Support Synchronous and Asynchronous Execution

## Status

Accepted

## Decision

The baseline supports synchronous execution for fast feedback. The API contract and
persisted run model must support a worker-backed asynchronous executor as a separate
production capability. The provider remains independently configurable in every
environment.

## Consequences

The API remains stable while deployment profiles change. The asynchronous worker is
an explicit follow-up before high-volume production use.
