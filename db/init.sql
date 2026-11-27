CREATE TABLE IF NOT EXISTS sample_metrics (id SERIAL PRIMARY KEY, metric_date DATE NOT NULL, category TEXT NOT NULL, value NUMERIC NOT NULL, region TEXT NOT NULL);
INSERT INTO sample_metrics(metric_date,category,value,region) VALUES ('2026-01-01','alpha',120,'North'),('2026-01-02','beta',180,'South'),('2026-01-03','alpha',95,'South'),('2026-01-04','gamma',240,'North');
