# Template Refinement Artifact

- Objective: Refine and document the current generic AI Agent template as a hackathon-ready baseline without adding business-specific context.
- Operation: grill-template-refinement-2026-11-27
- Next consumer: future Spanish grilling session for business-context refinement

## Decisions

- Document the current generic architecture.
- Use OpenRouter, Ollama, or QVAC through explicit configuration.
- Keep future business context deferred to a later session.

## Residual risks

- Production asynchronous worker mode is designed but not yet implemented.
- Tenant-aware authorization is deferred.
- Provider-specific QVAC response compatibility must be verified against the deployed QVAC version.
