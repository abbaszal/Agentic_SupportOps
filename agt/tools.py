from __future__ import annotations

from typing import Any, Dict, List, Optional

from db.sql_tool import (
    get_ticket,
    get_customer_recent_orders,
    get_customer_ticket_stats,
    similar_tickets_by_keywords,
    insert_ticket_event,
)
from rag.search import search, format_context

def tool_get_ticket_context(ticket_id: int) -> Dict[str, Any]:
    t = get_ticket(ticket_id)
    cid = t.get("customer_id")
    orders = get_customer_recent_orders(cid, n=5) if cid else []
    stats = get_customer_ticket_stats(cid) if cid else {}
    sims = similar_tickets_by_keywords(ticket_id, k=5)
    return {
        "ticket": t,
        "customer_stats": stats,
        "recent_orders": orders,
        "similar_tickets": sims,
    }

def tool_rag_search(query: str, k: int = 5) -> Dict[str, Any]:
    hits = search(query, k=k)
    return {
        "hits": [
            {
                "score": h.score,
                "cite": h.cite(),
                "text": h.text,
            }
            for h in hits
        ],
        "context_block": format_context(hits),
    }

def tool_create_ticket_event(ticket_id: int, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    insert_ticket_event(ticket_id, event_type, payload)
    return {"ok": True}
