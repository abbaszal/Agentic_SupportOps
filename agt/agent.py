from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
from openai import OpenAI
from agt.tools import (
    tool_get_ticket_context,
    tool_rag_search,
    tool_create_ticket_event,
)
from db.logging import create_agent_run, log_tool_call, update_agent_run

SYSTEM_INSTRUCTIONS = """You are OpsCopilot, an internal support operations agent.
You MUST:
- Use the provided SQL context (customer, orders, similar tickets) when available.
- Use the provided RAG policy context, and cite it when making decisions.
- Produce a final customer-facing response, plus a short internal action plan.
- If policies are missing, say so and proceed conservatively.

Output MUST be valid JSON with this schema:
{
  "customer_reply": "string",
  "recommended_actions": [
    {"type": "TAG|ESCALATE|REFUND|REPLACE|REQUEST_INFO|OTHER", "reason": "string"}
  ],
  "citations": [
    {"source": "doc#chunk (title)", "used_for": "string"}
  ],
  "risk_notes": ["string"]
}
"""

@dataclass
class AgentResult:
    agent_run_id: int
    result: Dict[str, Any]

def _client() -> OpenAI:
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_agent(ticket_id: Optional[int] = None, free_text: Optional[str] = None, model: str = "gpt-5") -> AgentResult:
    input_text = free_text
    ctx = {}
    if ticket_id is not None:
        ctx = tool_get_ticket_context(ticket_id)
        input_text = (ctx["ticket"].get("body") or "").strip()

    agent_run_id = create_agent_run(ticket_id, input_text or "")

    if ticket_id is not None:
        log_tool_call(agent_run_id, "get_ticket_context", {"ticket_id": ticket_id}, ctx)

    rag_query = input_text[:500] if input_text else "support policy question"
    rag = tool_rag_search(rag_query, k=5)
    log_tool_call(agent_run_id, "rag_search", {"query": rag_query, "k": 5}, {"hits": rag["hits"]})

    prompt = {
        "ticket_id": ticket_id,
        "user_issue": input_text,
        "sql_context": ctx,
        "policy_context": rag["context_block"],
        "note": "Use citations from policy_context where relevant.",
    }

    client = _client()
    resp = client.responses.create(
        model=model,
        reasoning={"effort": "low"},
        instructions=SYSTEM_INSTRUCTIONS,
        input=json.dumps(prompt, ensure_ascii=False),
    )
    out_text = resp.output_text.strip()
    result = json.loads(out_text)

    log_tool_call(agent_run_id, "llm_generate", {"model": model}, {"raw_output": out_text})

    if ticket_id is not None:
        for a in result.get("recommended_actions", [])[:5]:
            etype = a.get("type", "OTHER")
            reason = a.get("reason", "")
            tool_create_ticket_event(ticket_id, f"AGENT_{etype}", {"reason": reason})
        log_tool_call(
            agent_run_id, 
            "create_ticket_events", 
            {"ticket_id": ticket_id}, 
            {"ok": True, "count": len(result.get("recommended_actions", []))}
        )

    update_agent_run(agent_run_id, result.get("customer_reply", out_text))

    return AgentResult(agent_run_id=agent_run_id, result=result)