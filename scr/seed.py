import sqlite3
import pandas as pd
import random
import re
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("db/app.db")
SCHEMA_SQL = Path("db/schema.sql")
TICKETS_CSV = Path("dat/raw/tickets_clean.csv")

PRODUCT_NAMES = [
    "Laptop Pro X",
    "Phone Max 12",
    "Earbuds Air",
    "Router WiFi 6",
    "Smartwatch Fit",
    "Tablet Plus",
]

def init_db(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()

def main():
    df = pd.read_csv(TICKETS_CSV)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    init_db(conn)

    products = [(p, p.split()[0].lower()) for p in PRODUCT_NAMES]
    cur.executemany("INSERT INTO products(name, category) VALUES (?, ?)", products)

    customers = []
    seen_email = set()
    for i, row in df.head(400).iterrows():
        name = str(row.get("customer_name", f"Customer {i+1}"))
        email = str(row.get("customer_email", f"user{i+1}@example.com")).strip().lower()
        if email not in seen_email:
            seen_email.add(email)
            tier = random.choice(["standard", "standard", "standard", "premium"])
            customers.append((name, email, tier))

    cur.executemany("INSERT OR IGNORE INTO customers(name, email, tier) VALUES (?, ?, ?)", customers)
    conn.commit()

    cust_map = {r[1]: r[0] for r in cur.execute("SELECT id, email FROM customers").fetchall()}
    product_ids = [r[0] for r in cur.execute("SELECT id FROM products").fetchall()]
    customer_ids = [r[0] for r in cur.execute("SELECT id FROM customers").fetchall()]

    orders = []
    base_date = datetime.now() - timedelta(days=365)
    for oid in range(1, min(800, len(customer_ids) * 3) + 1):
        cid = random.choice(customer_ids)
        pid = random.choice(product_ids)
        status = random.choice(["delivered", "delivered", "delivered", "shipped", "refunded"])
        total = round(random.uniform(29, 1999), 2)
        created_at = (base_date + timedelta(days=random.randint(0, 360))).strftime("%Y-%m-%d %H:%M:%S")
        orders.append((oid, cid, pid, status, total, created_at))

    cur.executemany("INSERT OR REPLACE INTO orders(id, customer_id, product_id, status, total, created_at) VALUES (?, ?, ?, ?, ?, ?)", orders)
    conn.commit()

    tickets = []
    for _, row in df.head(800).iterrows():
        product_name = random.choice(PRODUCT_NAMES)
        body = str(row.get("body", ""))
        subject = str(row.get("subject", f"Issue with {product_name}"))
        category = str(row.get("category", "General"))
        priority = str(row.get("priority", "normal")).lower()
        status = str(row.get("status", "open")).lower()
        customer_id = cust_map.get(str(row.get("customer_email", "")).strip().lower()) or random.choice(customer_ids)
        created_at = (base_date + timedelta(days=random.randint(0, 360))).strftime("%Y-%m-%d %H:%M:%S")
        tickets.append((customer_id, subject, body, status, priority, category, created_at))

    cur.executemany("INSERT INTO tickets(customer_id, subject, body, status, priority, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", tickets)
    cur.execute("INSERT INTO ticket_events(ticket_id, event_type, payload_json) VALUES (1,'CREATED','{\"by\":\"seed\"}')")
    cur.execute("INSERT INTO ticket_events(ticket_id, event_type, payload_json) VALUES (1,'TAGGED','{\"tag\":\"battery\"}')")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()