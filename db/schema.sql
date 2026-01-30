-- db/schema.sql
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS tool_calls;
DROP TABLE IF EXISTS agent_runs;
DROP TABLE IF EXISTS ticket_events;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  id           INTEGER PRIMARY KEY,
  name         TEXT NOT NULL,
  email        TEXT UNIQUE,
  tier         TEXT DEFAULT 'standard',
  created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE products (
  id        INTEGER PRIMARY KEY,
  name      TEXT NOT NULL,
  category  TEXT
);

CREATE TABLE orders (
  id          INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  product_id  INTEGER NOT NULL,
  status      TEXT DEFAULT 'delivered',
  total       REAL DEFAULT 0,
  created_at  TEXT,
  FOREIGN KEY(customer_id) REFERENCES customers(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE tickets (
  id           INTEGER PRIMARY KEY,
  customer_id  INTEGER,
  subject      TEXT,
  body         TEXT NOT NULL,
  status       TEXT DEFAULT 'open',
  priority     TEXT DEFAULT 'normal',
  category     TEXT,
  created_at   TEXT,
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE ticket_events (
  id          INTEGER PRIMARY KEY,
  ticket_id   INTEGER NOT NULL,
  event_type  TEXT NOT NULL,
  payload_json TEXT,
  created_at  TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(ticket_id) REFERENCES tickets(id)
);

CREATE TABLE agent_runs (
  id           INTEGER PRIMARY KEY,
  ticket_id    INTEGER,
  input_text   TEXT NOT NULL,
  final_answer TEXT,
  created_at   TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(ticket_id) REFERENCES tickets(id)
);

CREATE TABLE tool_calls (
  id             INTEGER PRIMARY KEY,
  agent_run_id   INTEGER NOT NULL,
  tool_name      TEXT NOT NULL,
  tool_input_json  TEXT,
  tool_output_json TEXT,
  created_at     TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(agent_run_id) REFERENCES agent_runs(id)
);

CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_tool_calls_run ON tool_calls(agent_run_id);
