# Observability

The API emits structured lifecycle logs for `agent_run_complete` with run ID, provider, and status. Health is exposed at `/healthz`. Initial SLOs for the generic template are 99% successful `/api/agent/run` responses and p95 completion under 30 seconds. Alert on health failures for five minutes or run errors above 5% over ten minutes. Do not log prompts, SQL parameters, API keys, or result payloads. Extend this seam with OpenTelemetry before production deployment.
