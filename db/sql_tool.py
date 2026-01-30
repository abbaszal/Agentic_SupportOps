from __future__ import annotations
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = Path("db/app.db")

@dataclass
class SQLResult:
    columns: List[str]
    rows: List[Tuple[Any, ...]]

    def to_dict(self) -> Dict[str, Any]:
        return {"columns": self.columns, "rows": [list(r) for r in self.rows]}

def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def sql_query(query: str, params: Optional[Tuple[Any, ...]] = None, limit: int = 200) -> SQLResult:
    q = query.strip().rstrip(";")
    conn = _connect()
    cur = conn.cursor()
    cur.execute(q, params or ())
    rows = cur.fetchmany(limit)
    cols = [d[0] for d in cur.description] if cur.description else []
    conn.close()
    return SQLResult(columns=cols, rows=[tuple(r) for r in rows])

def get_ticket(ticket_id: int) -> Dict[str, Any]:
    res = sql_query(
        """
        SELECT
          t.id, t.subject, t.body, t.status, t.priority, t.category, t.created_at,
          c.id AS customer_id, c.name AS customer_name, c.email AS customer_email, c.tier AS customer_tier
        FROM tickets t
        LEFT JOIN customers c ON c.id = t.customer_id
        WHERE t.id = ?
        """,
        (ticket_id,),
        limit=1,
    )
    row = res.rows[0]
    return dict(zip(res.columns, row))

def get_customer_recent_orders(customer_id: int, n: int = 5) -> List[Dict[str, Any]]:
    res = sql_query(
        """
        SELECT
          o.id AS order_id, o.status AS order_status, o.total, o.created_at,
          p.name AS product_name, p.category AS product_category
        FROM orders o
        JOIN products p ON p.id = o.product_id
        WHERE o.customer_id = ?
        ORDER BY o.created_at DESC
        LIMIT ?
        """,
        (customer_id, n),
    )
    return [dict(zip(res.columns, r)) for r in res.rows]

def get_customer_ticket_stats(customer_id: int) -> Dict[str, Any]:
    res = sql_query(
        """
        SELECT
          COUNT(*) AS total_tickets,
          SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) AS open_tickets,
          SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed_tickets,
          SUM(CASE WHEN priority IN ('high','urgent') THEN 1 ELSE 0 END) AS high_priority_tickets
        FROM tickets
        WHERE customer_id = ?
        """,
        (customer_id,),
        limit=1,
    )
    row = res.rows[0]
    return dict(zip(res.columns, row))

def similar_tickets_by_keywords(ticket_id: int, k: int = 5) -> List[Dict[str, Any]]:
    t = get_ticket(ticket_id)
    text = (t.get("body") or "")[:800].lower()
    toks = re.findall(r"[a-z]{5,}", text)
    uniq = []
    for w in toks:
        if w not in uniq:
            uniq.append(w)
        if len(uniq) >= 6:
            break

    where = " OR ".join(["lower(body) LIKE ?"] * len(uniq))
    params: Tuple[Any, ...] = tuple([f"%{w}%" for w in uniq])

    res = sql_query(
        f"""
        SELECT id, subject, status, priority, category, created_at,
               replace(replace(replace(substr(body,1,160), char(10), ' '), char(13), ' '), char(9), ' ') AS preview
        FROM tickets
        WHERE id != ? AND ({where})
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (ticket_id, *params, k),
    )
    return [dict(zip(res.columns, r)) for r in res.rows]

def ticket_dashboard_top_categories(limit: int = 10) -> List[Dict[str, Any]]:
    res = sql_query(
        """
        SELECT
          COALESCE(category,'(none)') AS category,
          COUNT(*) AS n,
          ROUND(100.0 * SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) / COUNT(*), 1) AS open_pct
        FROM tickets
        GROUP BY category
        ORDER BY n DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(zip(res.columns, r)) for r in res.rows]

def insert_ticket_event(ticket_id: int, event_type: str, payload: Dict[str, Any]) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ticket_events(ticket_id, event_type, payload_json)
        VALUES (?, ?, ?)
        """,
        (ticket_id, event_type, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()