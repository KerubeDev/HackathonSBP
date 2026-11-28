# ADR 0003: Select One LLM Provider Explicitly

## Status

Accepted

## Decision

`LLM_PROVIDER` selects exactly one of OpenRouter, Ollama, QVAC, or explicitly enabled
deterministic demo mode. Provider failures return an error; the system never silently
switches providers.

## Consequences

Operators control cost, privacy, and availability. Provider adapters must preserve
the shared SQL-generation contract.
