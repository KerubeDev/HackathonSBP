# ADR 0009: Use Local Profile Capability Boundaries

## Status

Accepted

## Decision

The prototype uses a profile selector for Público, Analista, and Administrador.
Each profile exposes differentiated capabilities. The boundary is prepared for
future authentication without storing passwords in the repository.

## Consequences

The demo can show role differences locally while keeping production identity and
authorization outside the hackathon baseline.
