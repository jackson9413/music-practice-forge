"""SQLite storage for the practice journal."""

from __future__ import annotations

import os
import sqlite3
from datetime import date
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("PRACTICE_DB", os.path.join(BASE_DIR, "data", "practice.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_date TEXT NOT NULL,
    piece TEXT NOT NULL DEFAULT '',
    instrument TEXT NOT NULL DEFAULT '',
    area TEXT NOT NULL DEFAULT '',
    tempo INTEGER,
    minutes INTEGER NOT NULL DEFAULT 0,
    quality INTEGER NOT NULL DEFAULT 3,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_piece ON sessions(piece);
"""


def get_connection(path: Optional[str] = None) -> sqlite3.Connection:
    target = path or DB_PATH
    os.makedirs(os.path.dirname(target), exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def init_db(path: Optional[str] = None) -> None:
    conn = get_connection(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def list_sessions(limit: int = 300, piece: str = "", path: Optional[str] = None) -> List[dict]:
    conn = get_connection(path)
    try:
        sql = "SELECT * FROM sessions"
        params: List = []
        if piece:
            sql += " WHERE piece = ?"
            params.append(piece)
        sql += " ORDER BY session_date DESC, id DESC LIMIT ?"
        params.append(int(limit))
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_session(
    session_date: str = "",
    piece: str = "",
    instrument: str = "",
    area: str = "",
    tempo: Optional[int] = None,
    minutes: int = 0,
    quality: int = 3,
    notes: str = "",
    path: Optional[str] = None,
) -> dict:
    conn = get_connection(path)
    try:
        d = session_date or date.today().isoformat()
        cur = conn.execute(
            "INSERT INTO sessions (session_date, piece, instrument, area, tempo, minutes, quality, notes)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (d, piece.strip(), instrument.strip(), area.strip(), tempo, int(minutes or 0),
             int(quality or 3), notes.strip()),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def delete_session(session_id: int, path: Optional[str] = None) -> bool:
    conn = get_connection(path)
    try:
        cur = conn.execute("DELETE FROM sessions WHERE id = ?", (int(session_id),))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def pieces(path: Optional[str] = None) -> List[str]:
    conn = get_connection(path)
    try:
        rows = conn.execute(
            "SELECT piece, COUNT(*) AS n FROM sessions WHERE piece != '' GROUP BY piece ORDER BY n DESC"
        ).fetchall()
        return [r["piece"] for r in rows]
    finally:
        conn.close()
