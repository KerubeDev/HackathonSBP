import csv, hashlib, io, json, logging, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import Body, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.responses import Response
from sqlalchemy import create_engine, text
from .agent import run_agent, engine
from .config import settings
from .contracts import API_VERSION, ErrorBody, LoadCancellation, RankingQuery, RunEnvelope, RunRequest, UploadConfirmation
from .rankings import calculate_from_files, compare_rankings
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

@app.get("/api/rankings/subactivities")
def subactivities(ranking: str | None = None, bank: str | None = None):
    rows = official_rankings()["subactivities"]
    if ranking:
        rows = [row for row in rows if row["Ranking"] == ranking]
    if bank:
        rows = [row for row in rows if row["Codigo_Banco"] == bank]
    return {"api_version": API_VERSION, "subactivities": rows}

@app.get("/api/exports/rankings.csv")
def export_rankings(ranking: str | None = None):
    rows = official_rankings()["rankings"]
    if ranking:
        rows = [row for row in rows if row["Ranking"] == ranking]
    fields = ["Fecha", "Ranking", "Posicion", "Codigo_Banco", "Banco",
              "Saldo_Actividad", "Total_Cartera_Local_Valida", "Ponderacion_Pct", "Operaciones_Validas"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows({field: row[field] for field in fields} for row in rows)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=sbp-rankings.csv"})

@app.get("/api/exports/rankings.json")
def export_rankings_json(ranking: str | None = None):
    rows = official_rankings()["rankings"]
    if ranking:
        rows = [row for row in rows if row["Ranking"] == ranking]
    return {"source": "AT03_sintetico_202609.csv", "rule_version": "sbp-2026-v2", "rankings": rows}

@app.get("/api/exports/rankings.xlsx")
def export_rankings_xlsx(ranking: str | None = None):
    from openpyxl import Workbook
    rows = official_rankings()["rankings"]
    if ranking:
        rows = [row for row in rows if row["Ranking"] == ranking]
    fields = ["Fecha", "Ranking", "Posicion", "Codigo_Banco", "Banco", "Saldo_Actividad",
              "Total_Cartera_Local_Valida", "Ponderacion_Pct", "Operaciones_Validas"]
    workbook, sheet = Workbook(), None
    sheet = workbook.active
    sheet.append(fields)
    for row in rows:
        sheet.append([row[field] for field in fields])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return Response(buffer.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment; filename=sbp-rankings.xlsx"})

@app.get("/api/exports/rankings.pdf")
def export_rankings_pdf(ranking: str | None = None):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen.canvas import Canvas
    rows = official_rankings()["rankings"]
    if ranking:
        rows = [row for row in rows if row["Ranking"] == ranking]
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=letter)
    canvas.setTitle("SBP Rankings")
    canvas.drawString(40, 760, "SBP synthetic credit rankings")
    canvas.drawString(40, 744, "Source: AT03_sintetico_202609.csv | Rule: sbp-2026-v2")
    y = 720
    for row in rows:
        canvas.drawString(40, y, f'{row["Ranking"]} #{row["Posicion"]} {row["Banco"]} {row["Saldo_Actividad"]}')
        y -= 14
        if y < 40:
            canvas.showPage()
            y = 760
    canvas.save()
    return Response(buffer.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=sbp-rankings.pdf"})

@app.post("/api/rankings/preview")
async def preview_upload(file: UploadFile = File(...), x_api_key: str | None = Header(default=None),
                         x_profile: str | None = Header(default=None)):
    authorize(x_api_key)
    if x_profile != "administrador":
        raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Administrator capability required"})
    payload = await file.read()
    try:
        rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
        errors = __import__("app.rankings", fromlist=["validate_at03"]).validate_at03(rows)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise HTTPException(422, detail={"code": "INVALID_AT03", "message": str(exc)})
    digest = hashlib.sha256(payload).hexdigest()
    return {"api_version": API_VERSION, "filename": file.filename, "sha256": digest,
            "rows": len(rows), "errors": errors, "status": "previewed" if not errors else "failed"}

@app.post("/api/rankings/publish")
def publish_fixture(period: str = Body(..., embed=True), x_api_key: str | None = Header(default=None),
                    x_profile: str | None = Header(default=None)):
    """Publish a supplied fixture atomically through the local administrator seam."""
    authorize(x_api_key)
    if x_profile != "administrador":
        raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Administrator capability required"})
    source = DATA_DIR / f"AT03_sintetico_{period[:6]}.csv"
    if not source.exists():
        raise HTTPException(404, detail={"code": "PERIOD_NOT_FOUND", "message": "Fixture period not found"})
    result = calculate_from_files(source, DATA_DIR / "Catalogo_CINU_SB109_reto.csv",
                                  DATA_DIR / "Bancos_ficticios.csv", DATA_DIR / "Tabla_SB21_simplificada.csv")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with writer_engine.begin() as conn:
        source_id = conn.execute(text("""INSERT INTO source_files(filename,sha256,period,rule_version,catalog_version)
          VALUES (:filename,:sha,:period,'sbp-2026-v2','supplied-catalogs-v1')
          ON CONFLICT(filename,sha256) DO UPDATE SET period=EXCLUDED.period RETURNING source_id"""),
          {"filename": source.name, "sha": digest, "period": result["period"]}).scalar_one()
        load_id = conn.execute(text("""INSERT INTO load_runs(source_id,status,rows_read,valid_rows,e1,e2,e3,e4)
          VALUES (:source,'processing',:read,:valid,:e1,:e2,:e3,:e4) RETURNING load_id"""),
          {"source": source_id, "read": result["quality"]["rows_read"], "valid": result["quality"]["valid_universe"],
           "e1": result["quality"]["E1"], "e2": result["quality"]["E2"], "e3": result["quality"]["E3"], "e4": result["quality"]["E4"]}).scalar_one()
        for row in result["quality"]["excluded_rows"]:
            conn.execute(text("INSERT INTO quality_exclusions(load_id,source_row,code,reason) VALUES (:id,:row,:code,:reason)"),
                         {"id": load_id, "row": row["row"], "code": row["reason"], "reason": row["reason"]})
        for row in result["rankings"]:
            conn.execute(text("""INSERT INTO ranking_results(load_id,period,ranking,position,bank_code,bank_name,activity_balance,portfolio_balance,weight_pct,valid_operations)
              VALUES (:id,:period,:ranking,:position,:bank,:name,:balance,:portfolio,:weight,:operations)"""),
              {"id": load_id, "period": row["Fecha"], "ranking": row["Ranking"], "position": row["Posicion"],
               "bank": row["Codigo_Banco"], "name": row["Banco"], "balance": row["Saldo_Actividad"],
               "portfolio": row["Total_Cartera_Local_Valida"], "weight": row["Ponderacion_Pct"], "operations": row["Operaciones_Validas"]})
        for row in result["subactivities"]:
            conn.execute(text("""INSERT INTO ranking_subactivities(load_id,period,ranking,subactivity,bank_code,balance)
              VALUES (:id,:period,:ranking,:subactivity,:bank,:balance)"""),
              {"id": load_id, "period": row["Fecha"], "ranking": row["Ranking"], "subactivity": row["Subactividad"],
               "bank": row["Codigo_Banco"], "balance": row["Saldo"]})
        conn.execute(text("UPDATE load_runs SET status='published' WHERE load_id=:id"), {"id": load_id})
        conn.execute(text("INSERT INTO audit_events(load_id,action,actor,details) VALUES (:id,'publish','administrador',:details)"),
                     {"id": load_id, "details": json.dumps({"sha256": digest, "period": result["period"]})})
    return {"api_version": API_VERSION, "load_id": str(load_id), "status": "published",
            "quality": result["quality"], "source_sha256": digest}

@app.post("/api/rankings/confirm")
def confirm_upload(body: UploadConfirmation, x_api_key: str | None = Header(default=None),
                   x_profile: str | None = Header(default=None)):
    """Confirm a validated period through the same atomic publication path."""
    return publish_fixture(body.period, x_api_key, x_profile)

@app.post("/api/rankings/cancel")
def cancel_upload(body: LoadCancellation, x_api_key: str | None = Header(default=None),
                  x_profile: str | None = Header(default=None)):
    authorize(x_api_key)
    if x_profile != "administrador":
        raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Administrator capability required"})
    with writer_engine.begin() as conn:
        load_id = conn.execute(text("""INSERT INTO load_runs(status,error_message)
          VALUES ('cancelled',:reason) RETURNING load_id"""), {"reason": body.reason}).scalar_one()
        conn.execute(text("INSERT INTO audit_events(load_id,action,actor,details) VALUES (:id,'cancel','administrador',:details)"),
                     {"id": load_id, "details": json.dumps({"reason": body.reason})})
    return {"api_version": API_VERSION, "load_id": str(load_id), "status": "cancelled"}

@app.get("/api/rankings/loads")
def load_history(x_api_key: str | None = Header(default=None), x_profile: str | None = Header(default=None)):
    authorize(x_api_key)
    if x_profile not in {"administrador", "analista"}:
        raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Administrator or analyst capability required"})
    with writer_engine.connect() as conn:
        rows = conn.execute(text("""SELECT load_id,status,rows_read,valid_rows,e1,e2,e3,e4,created_at
          FROM load_runs ORDER BY created_at DESC LIMIT 100""")).mappings().all()
    return {"api_version": API_VERSION, "loads": [dict(row) for row in rows]}

@app.get("/api/comparisons")
def comparisons():
    current = official_rankings()
    previous = calculate_from_files(
        DATA_DIR / "AT03_sintetico_202608.csv",
        DATA_DIR / "Catalogo_CINU_SB109_reto.csv",
        DATA_DIR / "Bancos_ficticios.csv",
        DATA_DIR / "Tabla_SB21_simplificada.csv",
    )
    return {"api_version": API_VERSION, "movements": compare_rankings(previous, current),
            "previous_period": previous["period"], "current_period": current["period"]}

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
