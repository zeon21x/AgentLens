"""Insert reproducible synthetic AgentLens events. Safe to rerun; adds another batch."""
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import get_connection, init_db

random.seed()
init_db()
prompts = ["v1", "v2", "v3"]
requests = [
    "Show the top 5 customers by revenue",
    "How many orders were placed last month?",
    "Find products with low inventory",
    "Summarize monthly sales by region",
    "Which customers have overdue invoices?",
    "Compare revenue this quarter vs last quarter",
    "List the 10 most frequently purchased products",
]
tools = ["sql_query", "schema_lookup", "query_validator", "formatter"]
now = datetime.now(timezone.utc)

with get_connection() as conn:
    for i in range(36):
        status = random.choices(["success", "error"], weights=[0.84, 0.16])[0]
        duration = random.randint(180, 2600)
        prompt = random.choice(prompts)
        err = random.choice(["SQL syntax error near 'FROM'", "Query timeout after 2 seconds",
                             "Unknown column in result set"]) if status == "error" else ""
        created = (now - timedelta(minutes=random.randint(1, 60*72))).isoformat()
        cur = conn.execute(
            """INSERT INTO runs(created_at,agent_name,user_input,response_summary,prompt_version,status,duration_ms,error_message)
            VALUES(?,?,?,?,?,?,?,?)""",
            (created, random.choice(["SQL Assistant","Support Agent"]), random.choice(requests),
             "" if status == "error" else "Generated a response using retrieved tool results.",
             prompt, status, duration, err)
        )
        run_id = cur.lastrowid
        for _ in range(random.randint(1, 4)):
            call_status = "error" if status == "error" and random.random() < 0.55 else "success"
            call_duration = random.randint(20, 900)
            tool_err = "Tool execution failed" if call_status == "error" else ""
            conn.execute(
                """INSERT INTO tool_calls(run_id,created_at,tool_name,input_summary,output_summary,status,duration_ms,error_message)
                VALUES(?,?,?,?,?,?,?,?)""",
                (run_id, created, random.choice(tools), "Agent-generated tool input",
                 "Tool returned structured output" if call_status == "success" else "",
                 call_status, call_duration, tool_err)
            )
print("Inserted 36 synthetic runs with tool-call events.")
print("Restart/refresh the Streamlit dashboard if it is already open.")
