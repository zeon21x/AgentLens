import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv("AGENTLENS_DB_PATH", "data/agentlens.db")

def get_connection():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            agent_name TEXT NOT NULL,
            user_input TEXT NOT NULL,
            response_summary TEXT DEFAULT '',
            prompt_version TEXT NOT NULL DEFAULT 'v1',
            status TEXT NOT NULL DEFAULT 'running',
            duration_ms INTEGER NOT NULL DEFAULT 0,
            error_message TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            tool_name TEXT NOT NULL,
            input_summary TEXT DEFAULT '',
            output_summary TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            duration_ms INTEGER NOT NULL DEFAULT 0,
            error_message TEXT DEFAULT '',
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at);
        CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
        CREATE INDEX IF NOT EXISTS idx_tool_calls_run_id ON tool_calls(run_id);
        """)
