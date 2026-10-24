from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from app.database import get_connection, init_db
from app.schemas import RunCreate, RunUpdate, ToolCallCreate

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="AgentLens API",
    description="Capture AI-agent runs and tool-call telemetry for the AgentLens dashboard.",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/")
def root():
    return {"name": "AgentLens API", "status": "ok", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/runs", status_code=201)
def create_run(payload: RunCreate):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO runs
            (agent_name,user_input,prompt_version,status,duration_ms,response_summary,error_message)
            VALUES (?,?,?,?,?,?,?)""",
            (payload.agent_name, payload.user_input, payload.prompt_version, payload.status,
             payload.duration_ms, payload.response_summary, payload.error_message)
        )
        row = conn.execute("SELECT * FROM runs WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)

@app.get("/runs")
def list_runs(
    limit: int = Query(default=100, ge=1, le=1000),
    status: str | None = Query(default=None, pattern="^(running|success|error)$"),
    agent_name: str | None = None,
):
    sql = "SELECT * FROM runs WHERE 1=1"
    params = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if agent_name:
        sql += " AND agent_name=?"
        params.append(agent_name)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

@app.get("/runs/{run_id}")
def get_run(run_id: int):
    with get_connection() as conn:
        run = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        calls = conn.execute(
            "SELECT * FROM tool_calls WHERE run_id=? ORDER BY id", (run_id,)
        ).fetchall()
        result = dict(run)
        result["tool_calls"] = [dict(c) for c in calls]
        return result

@app.patch("/runs/{run_id}")
def update_run(run_id: int, payload: RunUpdate):
    with get_connection() as conn:
        cur = conn.execute(
            """UPDATE runs SET status=?, duration_ms=?, response_summary=?, error_message=?
            WHERE id=?""",
            (payload.status, payload.duration_ms, payload.response_summary, payload.error_message, run_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Run not found")
        return dict(conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone())

@app.post("/runs/{run_id}/tool-calls", status_code=201)
def create_tool_call(run_id: int, payload: ToolCallCreate):
    with get_connection() as conn:
        if not conn.execute("SELECT id FROM runs WHERE id=?", (run_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Run not found")
        cur = conn.execute(
            """INSERT INTO tool_calls
            (run_id,tool_name,input_summary,output_summary,status,duration_ms,error_message)
            VALUES (?,?,?,?,?,?,?)""",
            (run_id, payload.tool_name, payload.input_summary, payload.output_summary,
             payload.status, payload.duration_ms, payload.error_message)
        )
        return dict(conn.execute("SELECT * FROM tool_calls WHERE id=?", (cur.lastrowid,)).fetchone())

@app.get("/tool-calls")
def list_tool_calls(limit: int = Query(default=200, ge=1, le=2000)):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT tc.*, r.agent_name, r.prompt_version
            FROM tool_calls tc JOIN runs r ON r.id=tc.run_id
            ORDER BY tc.created_at DESC, tc.id DESC LIMIT ?""", (limit,)
        ).fetchall()]

@app.get("/analytics/summary")
def analytics_summary():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) n FROM runs").fetchone()["n"]
        success = conn.execute("SELECT COUNT(*) n FROM runs WHERE status='success'").fetchone()["n"]
        errors = conn.execute("SELECT COUNT(*) n FROM runs WHERE status='error'").fetchone()["n"]
        avg = conn.execute("SELECT AVG(duration_ms) n FROM runs WHERE duration_ms > 0").fetchone()["n"] or 0
        calls = conn.execute("SELECT COUNT(*) n FROM tool_calls").fetchone()["n"]
        call_errors = conn.execute("SELECT COUNT(*) n FROM tool_calls WHERE status='error'").fetchone()["n"]
        return {
            "total_runs": total, "successful_runs": success, "failed_runs": errors,
            "success_rate_pct": round(success / total * 100, 1) if total else 0,
            "avg_duration_ms": round(avg, 1), "tool_calls": calls, "tool_call_errors": call_errors
        }
