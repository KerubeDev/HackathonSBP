CREATE TABLE IF NOT EXISTS agent_runs (
  run_id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK (status IN ('queued','running','completed','failed','cancelled')),
  request TEXT NOT NULL,
  result JSONB,
  execution_mode TEXT NOT NULL DEFAULT 'sync',
  idempotency_key TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS execution_mode TEXT NOT NULL DEFAULT 'sync';
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
CREATE UNIQUE INDEX IF NOT EXISTS agent_runs_idempotency_key_idx
  ON agent_runs(idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS agent_runs_created_at_idx ON agent_runs(created_at DESC);
