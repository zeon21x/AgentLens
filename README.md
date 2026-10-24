# AgentLens — AI Agent Observability & Analytics

AgentLens is a local-first portfolio MVP that captures AI-agent runs, tool calls, errors, latency, and prompt versions, then visualizes them in a Streamlit dashboard.

## Features
- FastAPI ingestion API for agent runs and tool-call events
- SQLite storage (created automatically)
- Streamlit dashboard with KPI cards, charts, filters, and execution history
- Demo data generator so you can explore the dashboard immediately
- Simple Python logger that your own agent can call
- No API keys required for the demo

## Project structure
```text
AgentLens/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── schemas.py
│   └── logger.py
├── dashboard/
│   └── streamlit_app.py
├── scripts/
│   └── seed_demo.py
├── data/                 # SQLite database is created here
├── requirements.txt
├── .env.example
├── run_api.bat
├── run_dashboard.bat
└── README.md
```

## 1. Set up (Windows)
Open a terminal in the `AgentLens` folder:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## 2. Start the API
In terminal 1:
```bash
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## 3. Add demo data
In terminal 2, with the virtual environment active:
```bash
python scripts/seed_demo.py
```

## 4. Start the dashboard
In terminal 3:
```bash
streamlit run dashboard/streamlit_app.py
```
Open the local URL Streamlit prints (usually http://localhost:8501).

## API example
Create a run:
```bash
curl -X POST http://127.0.0.1:8000/runs ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_name\":\"SQL Assistant\",\"user_input\":\"Show top 5 customers\",\"prompt_version\":\"v1\",\"status\":\"success\",\"duration_ms\":420}"
```

Add a tool call to a run:
```bash
curl -X POST http://127.0.0.1:8000/runs/1/tool-calls ^
  -H "Content-Type: application/json" ^
  -d "{\"tool_name\":\"sql_query\",\"input_summary\":\"SELECT top customers\",\"output_summary\":\"Returned 5 rows\",\"status\":\"success\",\"duration_ms\":120}"
```

List runs:
```bash
curl http://127.0.0.1:8000/runs
```

## Connect your own agent
Import `AgentLogger` from `app.logger` and call it around your agent execution:

```python
from app.logger import AgentLogger

logger = AgentLogger("http://127.0.0.1:8000", agent_name="SQL Assistant")
run_id = logger.start_run(
    user_input="Show top 5 customers",
    prompt_version="v2",
)
try:
    # Run your agent here
    logger.log_tool_call(
        run_id,
        tool_name="sql_query",
        input_summary="SELECT ...",
        output_summary="5 rows returned",
        status="success",
        duration_ms=120,
    )
    logger.finish_run(run_id, status="success", duration_ms=420,
                      response_summary="Returned top 5 customers")
except Exception as exc:
    logger.finish_run(run_id, status="error", duration_ms=420,
                      error_message=str(exc))
    raise
```

`AgentLogger` sends events to the local API. Do not log passwords, API keys, private user data, or full sensitive SQL parameters.

## Notes
- This is an MVP, not a production observability service.
- Authentication, access control, retention policies, background processing, and multi-user tenancy are not implemented.
- Demo events are synthetic. Replace them with real events from your agent before presenting performance conclusions.
