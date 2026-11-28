CREATE TABLE IF NOT EXISTS sample_metrics (id SERIAL PRIMARY KEY, metric_date DATE NOT NULL, category TEXT NOT NULL, value NUMERIC NOT NULL, region TEXT NOT NULL);
INSERT INTO sample_metrics(metric_date,category,value,region) VALUES ('2026-01-01','alpha',120,'North'),('2026-01-02','beta',180,'South'),('2026-01-03','alpha',95,'South'),('2026-01-04','gamma',240,'North');
DO $$ BEGIN
  CREATE USER agent_readonly WITH PASSWORD 'agent_readonly';
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
GRANT CONNECT ON DATABASE agent_template TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO agent_readonly;
