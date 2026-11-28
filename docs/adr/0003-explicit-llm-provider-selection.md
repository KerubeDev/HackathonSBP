# ADR 0003: Select One LLM Provider Explicitly

## Status

Accepted

## Decision

`LLM_PROVIDER` selects exactly one configured provider. The initial supported
options are OpenRouter, Ollama, QVAC, and explicitly enabled deterministic demo
mode. No environment has a provider preference embedded in the product design;
the team chooses the provider later through configuration. Provider failures return
an error; the system never silently switches providers.

## Consequences

Operators control cost, privacy, and availability. Provider adapters must preserve
the shared SQL-generation contract.
