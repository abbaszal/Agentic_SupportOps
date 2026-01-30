import sqlite3
from pathlib import Path

DB_PATH = Path("db/app.db")

Q1 = """
SELECT t.id, c.name, c.tier, t.status, t.priority, t.category, substr(t.body,1,80) AS preview
FROM tickets t
LEFT JOIN customers c ON c.id = t.customer_id
ORDER BY t.created_at DESC
LIMIT 10;
"""
Q2 = """
SELECT
  COALESCE(category,'(none)') AS category,
  COUNT(*) AS n,
  ROUND(100.0 * SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) / COUNT(*), 1) AS open_pct
FROM tickets
GROUP BY category
ORDER BY n DESC
LIMIT 10;
"""
Q3 = """
SELECT c.tier, COUNT(*) AS tickets
FROM tickets t
JOIN customers c ON c.id = t.customer_id
GROUP BY c.tier
ORDER BY tickets DESC;
"""
Q4 = """
SELECT
  p.category,
  COUNT(*) AS orders,
  ROUND(AVG(o.total),2) AS avg_total
FROM orders o
JOIN products p ON p.id = o.product_id
GROUP BY p.category
ORDER BY orders DESC;
"""

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for q in [Q1, Q2, Q3, Q4]:
        rows = cur.execute(q).fetchall()
        for r in rows:
            print(r)
    conn.close()

if __name__ == "__main__":
    main()