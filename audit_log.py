import sqlite3
import os
from datetime import datetime
from paths import LOGS

DB_PATH = os.path.join(LOGS, "audit.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            action TEXT,
            filename TEXT,
            status TEXT
        )
    """)
    return conn


def log_event(username, action, filename, status):
    conn = _connect()
    conn.execute(
        "INSERT INTO audit (timestamp, username, action, filename, status) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, action, filename, status),
    )
    conn.commit()
    conn.close()


def show_logs():
    conn = _connect()
    for row in conn.execute("SELECT timestamp, username, action, filename, status FROM audit"):
        print(" | ".join(str(x) for x in row))
    conn.close()

def user_from_key(key_path):
    # keys/aryan_private.pem -> "aryan"
    return os.path.basename(key_path).split("_")[0]

def get_logs():
    conn = _connect()
    rows = conn.execute(
        "SELECT timestamp, username, action, filename, status FROM audit ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows