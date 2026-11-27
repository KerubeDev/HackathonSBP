CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS source_files (
  source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  filename TEXT NOT NULL, sha256 TEXT NOT NULL, period TEXT NOT NULL,
  rule_version TEXT NOT NULL, catalog_version TEXT NOT NULL,
  source_bytes BYTEA, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (filename, sha256)
);
CREATE TABLE IF NOT EXISTS load_runs (
  load_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), source_id UUID REFERENCES source_files,
  status TEXT NOT NULL CHECK (status IN ('uploaded','previewed','confirmed','processing','published','failed','cancelled')),
  rows_read INTEGER NOT NULL DEFAULT 0, valid_rows INTEGER NOT NULL DEFAULT 0,
  e1 INTEGER NOT NULL DEFAULT 0, e2 INTEGER NOT NULL DEFAULT 0, e3 INTEGER NOT NULL DEFAULT 0, e4 INTEGER NOT NULL DEFAULT 0,
  error_message TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS quality_exclusions (
  load_id UUID REFERENCES load_runs ON DELETE CASCADE, source_row INTEGER NOT NULL,
  code TEXT NOT NULL, reason TEXT NOT NULL, PRIMARY KEY(load_id, source_row)
);
CREATE TABLE IF NOT EXISTS ranking_results (
  load_id UUID REFERENCES load_runs ON DELETE CASCADE, period TEXT NOT NULL,
  ranking TEXT NOT NULL, position INTEGER NOT NULL, bank_code TEXT NOT NULL,
  bank_name TEXT NOT NULL, activity_balance NUMERIC(20,2) NOT NULL,
  portfolio_balance NUMERIC(20,2) NOT NULL, weight_pct NUMERIC(20,4) NOT NULL,
  valid_operations INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(load_id, ranking, bank_code)
);
CREATE TABLE IF NOT EXISTS ranking_subactivities (
  load_id UUID REFERENCES load_runs ON DELETE CASCADE, period TEXT NOT NULL,
  ranking TEXT NOT NULL, subactivity TEXT NOT NULL, bank_code TEXT NOT NULL,
  balance NUMERIC(20,2) NOT NULL, PRIMARY KEY(load_id, ranking, subactivity, bank_code)
);
CREATE TABLE IF NOT EXISTS audit_events (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), load_id UUID REFERENCES load_runs,
  action TEXT NOT NULL, actor TEXT NOT NULL, request_id TEXT, details JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
