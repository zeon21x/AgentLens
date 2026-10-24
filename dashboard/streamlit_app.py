import os
import sqlite3
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="AgentLens", page_icon="ðŸ”­", layout="wide")
DB_PATH = os.getenv("AGENTLENS_DB_PATH", "data/agentlens.db")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: rgba(120,130,150,.08); padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(120,130,150,.18);}
</style>
""", unsafe_allow_html=True)

def load_data():
    if not Path(DB_PATH).exists():
        return pd.DataFrame(), pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        runs = pd.read_sql_query("SELECT * FROM runs ORDER BY created_at DESC", conn)
        calls = pd.read_sql_query(
            """SELECT tc.*, r.agent_name, r.prompt_version
               FROM tool_calls tc JOIN runs r ON r.id=tc.run_id
               ORDER BY tc.created_at DESC""", conn)
    finally:
        conn.close()
    return runs, calls

st.title("­ AgentLens")
st.caption("AI Agent Observability & Analytics â€¢ Monitor executions, tool usage, errors, and prompt versions")
runs, calls = load_data()

if runs.empty:
    st.info("No runs found yet. Start the API, then run `python scripts/seed_demo.py` to load sample data.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    agents = ["All"] + sorted(runs["agent_name"].dropna().unique().tolist())
    selected_agent = st.selectbox("Agent", agents)
    statuses = ["All", "success", "error", "running"]
    selected_status = st.selectbox("Run status", statuses)
    versions = ["All"] + sorted(runs["prompt_version"].dropna().unique().tolist())
    selected_version = st.selectbox("Prompt version", versions)
    if st.button("Refresh dashboard", use_container_width=True):
        st.rerun()

filtered = runs.copy()
if selected_agent != "All":
    filtered = filtered[filtered.agent_name == selected_agent]
if selected_status != "All":
    filtered = filtered[filtered.status == selected_status]
if selected_version != "All":
    filtered = filtered[filtered.prompt_version == selected_version]
filtered_calls = calls[calls.run_id.isin(filtered.id)] if not calls.empty else calls

total = len(filtered)
success = int((filtered.status == "success").sum())
failed = int((filtered.status == "error").sum())
success_rate = success / total * 100 if total else 0
avg_duration = filtered.loc[filtered.duration_ms > 0, "duration_ms"].mean() if total else 0
call_count = len(filtered_calls)
call_errors = int((filtered_calls.status == "error").sum()) if call_count else 0

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Agent runs", f"{total:,}")
c2.metric("Success rate", f"{success_rate:.1f}%")
c3.metric("Failed runs", f"{failed:,}")
c4.metric("Avg. latency", f"{avg_duration:,.0f} ms" if pd.notna(avg_duration) else "â€”")
c5.metric("Tool calls", f"{call_count:,}", f"{call_errors} errors" if call_errors else None)

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Run outcomes")
    outcome = filtered["status"].value_counts().rename_axis("status").reset_index(name="runs")
    if not outcome.empty:
        fig = px.pie(outcome, names="status", values="runs", hole=0.58)
        fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Runs by prompt version")
    pv = filtered.groupby(["prompt_version","status"]).size().reset_index(name="runs")
    if not pv.empty:
        fig = px.bar(pv, x="prompt_version", y="runs", color="status", barmode="group")
        fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), xaxis_title="Prompt version", yaxis_title="Runs")
        st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Most-used tools")
    if filtered_calls.empty:
        st.write("No tool-call events for these filters.")
    else:
        tools = filtered_calls["tool_name"].value_counts().head(10).rename_axis("tool").reset_index(name="calls")
        st.plotly_chart(px.bar(tools, x="calls", y="tool", orientation="h"), use_container_width=True)
with right:
    st.subheader("Latency by run")
    latency = filtered[filtered.duration_ms > 0].copy()
    if latency.empty:
        st.write("No latency measurements available.")
    else:
        latency["run_label"] = latency.apply(lambda r: f"#{r['id']} Â· {str(r['agent_name'])[:18]}", axis=1)
        fig = px.scatter(latency.head(100), x="created_at", y="duration_ms", color="status",
                         hover_data=["id","agent_name","prompt_version"], labels={"duration_ms":"Duration (ms)"})
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Execution history")
display_cols = ["id","created_at","agent_name","prompt_version","status","duration_ms","user_input","error_message"]
st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)

st.subheader("Tool-call history")
if filtered_calls.empty:
    st.write("No tool calls found.")
else:
    cols = ["id","created_at","run_id","agent_name","prompt_version","tool_name","status","duration_ms","input_summary","error_message"]
    st.dataframe(filtered_calls[cols], use_container_width=True, hide_index=True)

errors = filtered[filtered.status == "error"]
if not errors.empty:
    st.subheader("Error reports")
    st.dataframe(errors[["id","created_at","agent_name","prompt_version","user_input","error_message"]], use_container_width=True, hide_index=True)

st.caption("Demo data is synthetic. Treat these charts as examples until you connect a real agent.")


