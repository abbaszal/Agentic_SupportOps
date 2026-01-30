from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from agt.agent1 import run_agent

DB_PATH = Path("db/app.db")
app = FastAPI(title="OpsCopilot API")

def _q(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

class RunAgentReq(BaseModel):
    ticket_id: Optional[int] = None
    free_text: Optional[str] = None
    model: str = "gemini-1.5-flash"

@app.get("/tickets")
def list_tickets(limit: int = 50) -> List[Dict[str, Any]]:
    return _q(
        """
        SELECT t.id, t.subject, t.status, t.priority, t.category, t.created_at,
               c.name AS customer_name, c.tier AS customer_tier
        FROM tickets t
        LEFT JOIN customers c ON c.id = t.customer_id
        ORDER BY t.created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int) -> Dict[str, Any]:
    rows = _q(
        """
        SELECT t.*, c.name AS customer_name, c.email AS customer_email, c.tier AS customer_tier
        FROM tickets t
        LEFT JOIN customers c ON c.id = t.customer_id
        WHERE t.id = ?
        """,
        (ticket_id,),
    )
    return rows[0]

@app.get("/runs/{agent_run_id}/tool_calls")
def get_tool_calls(agent_run_id: int) -> List[Dict[str, Any]]:
    return _q(
        """
        SELECT id, tool_name, tool_input_json, tool_output_json, created_at
        FROM tool_calls
        WHERE agent_run_id = ?
        ORDER BY id ASC
        """,
        (agent_run_id,),
    )

@app.post("/run_agent1")
def run_agent_endpoint(req: RunAgentReq) -> Dict[str, Any]:
    res = run_agent(ticket_id=req.ticket_id, free_text=req.free_text, model=req.model)
    return {"agent_run_id": res.agent_run_id, "result": res.result}