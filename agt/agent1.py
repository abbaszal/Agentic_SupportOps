from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
from google import genai
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

CITATION REQUIREMENTS:
- If policy_context contains any sources, you MUST include at least 1 item in citations[].
- If you recommend REFUND/REPLACE/ESCALATE or mention warranty/refund/shipping/SLA rules, citations[] MUST include the exact source string from policy_context.
- If policy_context is empty, citations may be empty.

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

def _gemini_client() -> genai.Client:
    return genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def run_agent(
    ticket_id: Optional[int] = None,
    free_text: Optional[str] = None,
    model: str = "gemini-1.5-flash",
) -> AgentResult:
    input_text = free_text
    ctx = {}
    if ticket_id is not None:
        ctx = tool_get_ticket_context(ticket_id)
        input_text = (ctx["ticket"].get("body") or "").strip()

    agent_run_id = create_agent_run(ticket_id, input_text or "")

    if ticket_id is not None:
        log_tool_call(agent_run_id, "get_ticket_context", {"ticket_id": ticket_id}, ctx)

    rag_query = (input_text or "")[:500] if input_text else "support policy question"
    rag = tool_rag_search(rag_query, k=5)
    log_tool_call(
        agent_run_id,
        "rag_search",
        {"query": rag_query, "k": 5},
        {"hits": rag.get("hits", []), "context_block": rag.get("context_block", "")},
    )

    prompt = {
        "system": SYSTEM_INSTRUCTIONS,
        "ticket_id": ticket_id,
        "user_issue": input_text,
        "sql_context": ctx,
        "policy_context": rag.get("context_block", ""),
        "note": "Use citations from policy_context (doc#chunk (title)) when relevant.",
        "required_output_schema": {
            "customer_reply": "string",
            "recommended_actions": [{"type": "TAG|ESCALATE|REFUND|REPLACE|REQUEST_INFO|OTHER", "reason": "string"}],
            "citations": [{"source": "doc#chunk (title)", "used_for": "string"}],
            "risk_notes": ["string"],
        },
    }

    client = _gemini_client()
    resp = client.models.generate_content(
        model=model,
        contents=json.dumps(prompt, ensure_ascii=False),
        config={
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "required": ["customer_reply", "recommended_actions", "citations", "risk_notes"],
                "properties": {
                    "customer_reply": {"type": "string"},
                    "recommended_actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type", "reason"],
                            "properties": {
                                "type": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                    "citations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["source", "used_for"],
                            "properties": {
                                "source": {"type": "string"},
                                "used_for": {"type": "string"},
                            },
                        },
                    },
                    "risk_notes": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    )

    out_text = (resp.text or "").strip()
    result = json.loads(out_text)

    log_tool_call(
        agent_run_id,
        "llm_generate",
        {"model": model, "prompt": prompt},
        {"raw_output": out_text},
    )

    if ticket_id is not None:
        actions = result.get("recommended_actions", []) or []
        for a in actions[:5]:
            etype = (a.get("type") or "OTHER").strip()
            reason = (a.get("reason") or "").strip()
            tool_create_ticket_event(ticket_id, f"AGENT_{etype}", {"reason": reason})

        log_tool_call(
            agent_run_id,
            "create_ticket_events",
            {"ticket_id": ticket_id},
            {"ok": True, "count": len(actions)},
        )

    update_agent_run(agent_run_id, result.get("customer_reply", out_text))

    return AgentResult(agent_run_id=agent_run_id, result=result)