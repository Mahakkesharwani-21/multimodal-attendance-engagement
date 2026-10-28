import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "attendance.db"

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            duration_seconds REAL,
            participant_count INTEGER,
            mean_presence_ratio REAL,
            source_type TEXT
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            participant_label TEXT,
            first_seen_seconds REAL,
            last_seen_seconds REAL,
            observed_seconds REAL,
            status TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )""")

def save_session(name, duration, count, ratio, source):
    with _connect() as con:
        cur = con.execute("INSERT INTO sessions(session_name,duration_seconds,participant_count,mean_presence_ratio,source_type) VALUES(?,?,?,?,?)",
                          (name, duration, count, ratio, source))
        return cur.lastrowid

def save_attendance(session_id, row):
    with _connect() as con:
        con.execute("""INSERT INTO attendance(session_id,participant_label,first_seen_seconds,last_seen_seconds,observed_seconds,status)
                       VALUES(?,?,?,?,?,?)""",
                    (session_id, row.get("participant"), row.get("first_seen_seconds"),
                     row.get("last_seen_seconds"), row.get("observed_seconds"), row.get("status")))

def load_sessions():
    with _connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM sessions ORDER BY id DESC").fetchall()]

def load_attendance(session_id):
    with _connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM attendance WHERE session_id=? ORDER BY id", (session_id,)).fetchall()]
