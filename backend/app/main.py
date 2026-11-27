from fastapi import FastAPI, HTTPException, Header
from .config import settings
import logging, json
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text
from .agent import run_agent, engine
logging.basicConfig(level=settings.log_level)
log = logging.getLogger('rea-agent')
app = FastAPI(title='Generic REA Agent API', version='1.0.0')
runs: dict[str, dict] = {}
class RunRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    schema_context: str | None = None
def authorize(x_api_key: str | None):
    if settings.api_key and x_api_key != settings.api_key: raise HTTPException(401, 'invalid API key')

@app.get('/healthz')
def health(): return {'status':'ok'}
@app.post('/api/agent/run', status_code=202)
def start(body: RunRequest, x_api_key: str | None = Header(default=None)):
    authorize(x_api_key)
    run_id=str(uuid4()); result=run_agent(body.query, body.schema_context)
    runs[run_id]={'run_id':run_id,'status':'failed' if result.get('error') else 'completed','created_at':datetime.now(timezone.utc).isoformat(),'result':result}
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE IF NOT EXISTS agent_runs (run_id TEXT PRIMARY KEY, status TEXT NOT NULL, request TEXT NOT NULL, result JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT now())'))
        conn.execute(text('INSERT INTO agent_runs(run_id,status,request,result) VALUES (:id,:status,:request,:result) ON CONFLICT (run_id) DO UPDATE SET status=:status,result=:result'), {'id':run_id,'status':runs[run_id]['status'],'request':body.query,'result':json.dumps(result)})
    log.info('agent_run_complete run_id=%s provider=%s status=%s', run_id, result.get('provider'), runs[run_id]['status'])
    return {'run_id':run_id}
@app.get('/api/agent/status/{run_id}')
def status(run_id: str, x_api_key: str | None = Header(default=None)):
    authorize(x_api_key)
    if run_id not in runs: raise HTTPException(404,'run not found')
    return runs[run_id]
@app.get('/api/results')
def results(x_api_key: str | None = Header(default=None)):
    authorize(x_api_key)
    try:
        with engine.connect() as conn: rows=conn.execute(text('SELECT id, metric_date, category, value, region FROM sample_metrics ORDER BY metric_date DESC')).mappings().all()
        return {'results':[dict(row) for row in rows]}
    except Exception as exc: raise HTTPException(503, f'database unavailable: {exc}')
