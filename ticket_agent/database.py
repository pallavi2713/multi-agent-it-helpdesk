import os
from dotenv import load_dotenv
load_dotenv()
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = Path(os.getenv("DATABASE_PATH", "./data/helpdesk.db"))

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with connection() as conn:
        conn.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            department TEXT NOT NULL DEFAULT 'Not provided',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE,
            user_id INTEGER NOT NULL,
            issue TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'open',
            resolution TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS ticket_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            event TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id)
        );
        """)

def register_user(name: str, email: str, department: str = "Not provided") -> dict:
    init_db()
    stamp = now_iso()
    email = email.strip().lower()
    with connection() as conn:
        conn.execute("""
            INSERT INTO users(name,email,department,created_at,updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(email) DO UPDATE SET
              name=excluded.name,
              department=CASE WHEN excluded.department='Not provided'
                THEN users.department ELSE excluded.department END,
              updated_at=excluded.updated_at
        """, (name.strip(), email, department.strip() or "Not provided", stamp, stamp))
        row = conn.execute(
            "SELECT user_id,name,email,department FROM users WHERE email=?", (email,)
        ).fetchone()
    return dict(row)

def create_ticket(email: str, issue: str, priority: str = "medium") -> dict:
    init_db()
    priority = priority.lower().strip()
    if priority not in {"low","medium","high","critical"}:
        priority = "medium"
    with connection() as conn:
        user = conn.execute(
            "SELECT user_id FROM users WHERE email=?", (email.strip().lower(),)
        ).fetchone()
        if not user:
            return {"ok": False, "error": "User is not registered. Register the user first."}
        stamp = now_iso()
        cur = conn.execute("""
            INSERT INTO tickets(user_id,issue,priority,status,created_at,updated_at)
            VALUES(?,?,?,'open',?,?)
        """, (user["user_id"], issue.strip(), priority, stamp, stamp))
        ticket_id = f"HD-{cur.lastrowid:06d}"
        conn.execute("UPDATE tickets SET ticket_id=? WHERE id=?", (ticket_id, cur.lastrowid))
        conn.execute(
            "INSERT INTO ticket_history(ticket_id,event,details,created_at) VALUES(?,?,?,?)",
            (ticket_id, "created", f"Ticket created with {priority} priority.", stamp)
        )
        row = conn.execute("""
            SELECT t.ticket_id,u.name,u.email,t.issue,t.priority,t.status,t.created_at
            FROM tickets t JOIN users u ON u.user_id=t.user_id WHERE t.ticket_id=?
        """, (ticket_id,)).fetchone()
    return {"ok": True, "ticket": dict(row)}

def get_ticket_status(ticket_id: str = "", email: str = "") -> dict:
    init_db()
    with connection() as conn:
        if ticket_id.strip():
            rows = conn.execute("""
                SELECT t.ticket_id,u.name,u.email,t.issue,t.priority,t.status,t.resolution,
                       t.created_at,t.updated_at
                FROM tickets t JOIN users u ON u.user_id=t.user_id WHERE t.ticket_id=?
            """, (ticket_id.strip().upper(),)).fetchall()
        elif email.strip():
            rows = conn.execute("""
                SELECT t.ticket_id,u.name,u.email,t.issue,t.priority,t.status,t.resolution,
                       t.created_at,t.updated_at
                FROM tickets t JOIN users u ON u.user_id=t.user_id
                WHERE u.email=? ORDER BY t.created_at DESC LIMIT 10
            """, (email.strip().lower(),)).fetchall()
        else:
            return {"ok": False, "error": "Provide a ticket ID or registered email."}
    if not rows:
        return {"ok": False, "error": "No matching ticket was found."}
    return {"ok": True, "tickets": [dict(r) for r in rows]}

def update_ticket(ticket_id: str, resolution: str, new_status: str = "resolved") -> dict:
    init_db()
    new_status = new_status.lower().strip()
    allowed = {"open","in_progress","pending","resolved","closed"}
    if new_status not in allowed:
        return {"ok": False, "error": f"Status must be one of: {', '.join(sorted(allowed))}."}
    stamp = now_iso()
    ticket_id = ticket_id.strip().upper()
    with connection() as conn:
        exists = conn.execute(
            "SELECT ticket_id FROM tickets WHERE ticket_id=?", (ticket_id,)
        ).fetchone()
        if not exists:
            return {"ok": False, "error": "Ticket not found."}
        conn.execute(
            "UPDATE tickets SET status=?,resolution=?,updated_at=? WHERE ticket_id=?",
            (new_status, resolution.strip(), stamp, ticket_id)
        )
        conn.execute(
            "INSERT INTO ticket_history(ticket_id,event,details,created_at) VALUES(?,?,?,?)",
            (ticket_id, f"status_{new_status}", resolution.strip(), stamp)
        )
        row = conn.execute(
            "SELECT ticket_id,status,resolution,updated_at FROM tickets WHERE ticket_id=?",
            (ticket_id,)
        ).fetchone()
    return {"ok": True, "ticket": dict(row)}

def get_history(ticket_id: str) -> dict:
    init_db()
    with connection() as conn:
        rows = conn.execute(
            "SELECT event,details,created_at FROM ticket_history WHERE ticket_id=? ORDER BY id",
            (ticket_id.strip().upper(),)
        ).fetchall()
    if not rows:
        return {"ok": False, "error": "No history found for that ticket."}
    return {"ok": True, "history": [dict(r) for r in rows]}
