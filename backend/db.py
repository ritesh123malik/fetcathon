import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES (1);
CREATE TABLE IF NOT EXISTS suppliers (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, area TEXT NOT NULL,
 eta_hours INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1,
 color TEXT NOT NULL, initials TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
 supplier_id TEXT REFERENCES suppliers(id), product TEXT NOT NULL,
 stock INTEGER NOT NULL CHECK(stock >= 0), unit_paise INTEGER NOT NULL CHECK(unit_paise > 0),
 PRIMARY KEY(supplier_id, product)
);
CREATE TABLE IF NOT EXISTS quotes (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, requirements TEXT NOT NULL,
 options TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL, parent_id TEXT REFERENCES quotes(id)
);
CREATE TABLE IF NOT EXISTS orders (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, quote_id TEXT NOT NULL UNIQUE REFERENCES quotes(id),
 option_id TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, entity_id TEXT NOT NULL,
 kind TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_sessions (
 id TEXT PRIMARY KEY, quote_id TEXT, updated_at TEXT NOT NULL
);
"""

SUPPLIERS = [
    ("campus", "Campus Paper Co.", "Yelahanka", 4, 1, "violet", "CP"),
    ("metro", "Metro Office Supply", "Hebbal", 6, 1, "blue", "MO"),
    ("express", "QuickKit Express", "Bengaluru North", 2, 1, "orange", "QK"),
]
INVENTORY = [
    ("campus", "notebook", 40, 3500),
    ("campus", "pen", 80, 800),
    ("campus", "lanyard", 30, 1800),
    ("metro", "notebook", 80, 4200),
    ("metro", "pen", 100, 1000),
    ("metro", "lanyard", 100, 2200),
    ("express", "notebook", 100, 5500),
    ("express", "pen", 120, 1200),
    ("express", "lanyard", 100, 2800),
]


class Database:
    def __init__(self, path: str):
        self.path = path

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=15000")
        return conn

    def initialize(self, seed: bool = False):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)
            if seed:
                conn.executemany(
                    "INSERT OR IGNORE INTO suppliers VALUES (?,?,?,?,?,?,?)", SUPPLIERS
                )
                conn.executemany("INSERT OR IGNORE INTO inventory VALUES (?,?,?,?)", INVENTORY)
            conn.commit()

    @contextmanager
    def connection(self):
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
