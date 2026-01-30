from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

DB_PATH = Path("db/app.db")

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)

def create_agent_run(ticket_id: Optional[int], input_text: str) -> int:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO agent_runs(ticket_id, input_text) VALUES (?, ?)",
        (ticket_id, input_text),
    )
    conn.commit()
    row_id = int(cur.lastrowid)
    conn.close()
    return row_id

def update_agent_run(agent_run_id: int, final_answer: str) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE agent_runs SET final_answer = ? WHERE id = ?",
        (final_answer, agent_run_id),
    )
    conn.commit()
    conn.close()

def log_tool_call(
    agent_run_id: int,
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_output: Dict[str, Any],
) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tool_calls(agent_run_id, tool_name, tool_input_json, tool_output_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            agent_run_id,
            tool_name,
            json.dumps(tool_input, ensure_ascii=False),
            json.dumps(tool_output, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()