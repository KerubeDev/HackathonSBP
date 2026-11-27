from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text
from .agent import run_agent, engine
app = FastAPI(title='Generic REA Agent API', version='1.0.0')
runs: dict[str, dict] = {}
class RunRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    schema_context: str | None = None
@app.get('/healthz')
def health(): return {'status':'ok'}
@app.post('/api/agent/run', status_code=202)
def start(body: RunRequest):
    run_id=str(uuid4()); result=run_agent(body.query, body.schema_context)
    runs[run_id]={'run_id':run_id,'status':'failed' if result.get('error') else 'completed','created_at':datetime.now(timezone.utc).isoformat(),'result':result}
    return {'run_id':run_id}
@app.get('/api/agent/status/{run_id}')
def status(run_id: str):
    if run_id not in runs: raise HTTPException(404,'run not found')
    return runs[run_id]
@app.get('/api/results')
def results():
    try:
        with engine.connect() as conn: rows=conn.execute(text('SELECT id, metric_date, category, value, region FROM sample_metrics ORDER BY metric_date DESC')).mappings().all()
        return {'results':[dict(row) for row in rows]}
    except Exception as exc: raise HTTPException(503, f'database unavailable: {exc}')
