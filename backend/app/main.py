import json, logging, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import FastAPI, Header, HTTPException, Request
from sqlalchemy import create_engine, text
from .agent import run_agent, engine
from .config import settings
from .contracts import API_VERSION, ErrorBody, RunEnvelope, RunRequest
from .rankings import calculate_from_files
writer_engine = create_engine(settings.database_url, pool_pre_ping=True)

logging.basicConfig(level=settings.log_level)
log = logging.getLogger("rea-agent")
app = FastAPI(title="Generic REA Agent API", version="1.0.0")
executor = ThreadPoolExecutor(max_workers=4)
DATA_DIR = __import__("pathlib").Path(__file__).resolve().parents[2] / "docs" / "track" / "datos"

def now() -> str: return datetime.now(timezone.utc).isoformat()

def official_rankings() -> dict:
    return calculate_from_files(
        DATA_DIR / "AT03_sintetico_202609.csv",
        DATA_DIR / "Catalogo_CINU_SB109_reto.csv",
        DATA_DIR / "Bancos_ficticios.csv",
        DATA_DIR / "Tabla_SB21_simplificada.csv",
    )
def authorize(key: str | None):
    if settings.api_key and key != settings.api_key:
        raise HTTPException(401, detail={"code": "AUTHENTICATION_ERROR", "message": "Invalid API key"})

def persist(run_id: str, status: str, request: str, result: dict | None = None,
            created_at: str | None = None, mode: str = "sync", idempotency_key: str | None = None):
    with writer_engine.begin() as conn:
        conn.execute(text("""INSERT INTO agent_runs
            (run_id,status,request,result,created_at,execution_mode,idempotency_key,updated_at)
            VALUES (:id,:status,:request,:result,:created,:mode,:key,now())
            ON CONFLICT (run_id) DO UPDATE SET status=:status,result=:result,updated_at=now()"""),
            {"id": run_id, "status": status, "request": request,
             "result": json.dumps(result) if result is not None else None,
             "created": created_at or now(), "mode": mode, "key": idempotency_key})

def execute_run(run_id: str, body: RunRequest, created_at: str, mode: str):
    with writer_engine.begin() as conn:
        conn.execute(text("UPDATE agent_runs SET status='running', updated_at=now() WHERE run_id=:id"), {"id": run_id})
    result = run_agent(body.query, body.schema_context, body.requested_chart_types)
    with writer_engine.connect() as conn:
        current = conn.execute(text("SELECT status FROM agent_runs WHERE run_id=:id"), {"id": run_id}).scalar()
    if current == "cancelled":
        return
    result["execution_mode"] = mode
    status = "failed" if result.get("error") else "completed"
    persist(run_id, status, body.query, result, created_at, mode)

def envelope(run_id: str, row: dict) -> dict:
    result = dict(row.get("result") or {}) if row.get("result") else None
    error = None
    if result and result.get("error"):
        error = {"code": "PROVIDER_UNAVAILABLE", "message": "The configured analysis provider failed.", "run_id": run_id}
        result["error"] = "The configured analysis provider failed."
    return {"api_version": API_VERSION, "run_id": run_id, "status": row["status"],
            "execution_mode": row.get("execution_mode", settings.execution_mode),
            "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else row["created_at"],
            "poll_url": f"/api/agent/status/{run_id}", "result": result,
            "warnings": result.get("warnings", []) if result else [], "error": error}

@app.get("/healthz")
def health(): return {"status": "ok"}

@app.get("/api/profile")
def profile():
    return {"api_version": API_VERSION, "profiles": [
        {"id": "publico", "label": "Público", "capabilities": ["rankings", "filters", "charts", "downloads"]},
        {"id": "analista", "label": "Analista", "capabilities": ["rankings", "filters", "charts", "downloads", "comparisons", "explanations"]},
        {"id": "administrador", "label": "Administrador", "capabilities": ["rankings", "quality", "operations"]},
    ]}

@app.get("/api/rankings")
def rankings(ranking: str | None = None, bank: str | None = None, period: str | None = None,
             limit: int = 100, offset: int = 0):
    result = official_rankings()
    rows = result["rankings"]
    if ranking:
        rows = [row for row in rows if row["Ranking"] == ranking]
    if bank:
        rows = [row for row in rows if row["Codigo_Banco"] == bank]
    if period:
        rows = [row for row in rows if row["Fecha"] == period]
    bounded_limit = min(max(limit, 1), 1000)
    return {"api_version": API_VERSION, "source": "AT03_sintetico_202609.csv",
            "rule_version": "sbp-2026-v2", "fictitious_data": True,
            "quality": result["quality"], "rankings": rows[max(offset, 0):max(offset, 0) + bounded_limit],
            "total": len(rows), "limit": bounded_limit, "offset": max(offset, 0)}

@app.get("/api/quality/{period}")
def quality(period: str):
    result = official_rankings()
    if result["period"] != period:
        raise HTTPException(404, detail={"code": "PERIOD_NOT_FOUND", "message": "Period not found"})
    return {"api_version": API_VERSION, "quality": result["quality"], "source": "AT03_sintetico_202609.csv",
            "rule_version": "sbp-2026-v2"}

@app.post("/api/agent/run", status_code=202)
def start(body: RunRequest, request: Request, x_api_key: str | None = Header(default=None),
          idempotency_key: str | None = Header(default=None)):
    authorize(x_api_key)
    mode = body.execution_mode or settings.execution_mode
    if mode not in {"sync", "async"}: raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "Invalid execution mode"})
    if idempotency_key:
        with writer_engine.connect() as conn:
            old = conn.execute(text("SELECT * FROM agent_runs WHERE idempotency_key=:key"), {"key": idempotency_key}).mappings().first()
        if old: return envelope(old["run_id"], old)
    run_id, created_at = str(uuid4()), now()
    persist(run_id, "queued" if mode == "async" else "running", body.query, None, created_at, mode, idempotency_key)
    if mode == "async":
        executor.submit(execute_run, run_id, body, created_at, mode)
        return envelope(run_id, {"run_id": run_id, "status": "queued", "created_at": created_at, "execution_mode": mode})
    execute_run(run_id, body, created_at, mode)
    with writer_engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM agent_runs WHERE run_id=:id"), {"id": run_id}).mappings().first()
    return envelope(run_id, row)

@app.get("/api/agent/status/{run_id}")
def status(run_id: str, x_api_key: str | None = Header(default=None)):
    authorize(x_api_key)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM agent_runs WHERE run_id=:id"), {"id": run_id}).mappings().first()
    if not row: raise HTTPException(404, detail={"code": "RUN_NOT_FOUND", "message": "Run not found"})
    return envelope(run_id, row)

@app.post("/api/agent/cancel/{run_id}")
def cancel(run_id: str, x_api_key: str | None = Header(default=None)):
    authorize(x_api_key)
    with writer_engine.begin() as conn:
        row = conn.execute(text("SELECT status FROM agent_runs WHERE run_id=:id FOR UPDATE"), {"id": run_id}).mappings().first()
        if not row: raise HTTPException(404, detail={"code": "RUN_NOT_FOUND", "message": "Run not found"})
        if row["status"] not in {"queued", "running"}:
            raise HTTPException(409, detail={"code": "RUN_CONFLICT", "message": "Run is already terminal"})
        conn.execute(text("UPDATE agent_runs SET status='cancelled', updated_at=now() WHERE run_id=:id"), {"id": run_id})
    return {"api_version": API_VERSION, "run_id": run_id, "status": "cancelled"}

@app.get("/api/results")
def results(x_api_key: str | None = Header(default=None), limit: int = 100, offset: int = 0):
    authorize(x_api_key)
    with writer_engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM agent_runs ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
                            {"limit": min(max(limit, 1), 1000), "offset": max(offset, 0)}).mappings().all()
    return {"api_version": API_VERSION, "results": [dict(row) for row in rows], "limit": limit, "offset": offset}
