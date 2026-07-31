"""
SQLite database layer for FocusTimer.
Handles all persistent storage: sessions, goals, quotes, settings, playlists.
"""

import sqlite3
import os
from datetime import date, datetime, timedelta
from typing import Optional

from config.settings import (
    DEFAULT_FOCUS_MINUTES,
    DEFAULT_BREAK_MINUTES,
    DEFAULT_POMODORO_CYCLES,
    DEFAULT_DAILY_GOAL_MINUTES,
    DEFAULT_MUSIC_VOLUME,
    DEFAULT_AMBIENT_VOLUME,
    DEFAULT_THEME,
    BUILTIN_QUOTES,
    QUOTE_CHANGE_FREQUENCY,
)


def _get_db_path() -> str:
    """Return the path to the SQLite database file in the project root."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "focustimer.db")


class Database:
    """Manages all SQLite operations for FocusTimer."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _get_db_path()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_tables()
        self._seed_defaults()

    # ── Schema initialization ─────────────────────────────────────────

    def _init_tables(self) -> None:
        """Create all tables if they do not exist."""
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date DATE NOT NULL,
                start_time  TIME NOT NULL,
                duration    INTEGER NOT NULL,   -- seconds
                task_desc   TEXT DEFAULT '',
                completed   INTEGER DEFAULT 1   -- 1 = completed, 0 = abandoned
            );

            CREATE TABLE IF NOT EXISTS daily_goals (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_date      DATE UNIQUE NOT NULL,
                target_minutes INTEGER NOT NULL,
                subject        TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS quotes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                text       TEXT NOT NULL,
                author     TEXT DEFAULT '',
                is_builtin INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS playlists (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS playlist_tracks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                file_path   TEXT NOT NULL,
                track_name  TEXT DEFAULT '',
                FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
            );
        """)
        self.conn.commit()

    def _seed_defaults(self) -> None:
        """Insert built-in quotes and default settings on first run."""
        cur = self.conn.cursor()

        # Seed built-in quotes if none exist
        cur.execute("SELECT COUNT(*) FROM quotes WHERE is_builtin = 1")
        if cur.fetchone()[0] == 0:
            for text, author in BUILTIN_QUOTES:
                cur.execute(
                    "INSERT INTO quotes (text, author, is_builtin) VALUES (?, ?, 1)",
                    (text, author),
                )

        # Seed default settings
        defaults = {
            "focus_minutes": str(DEFAULT_FOCUS_MINUTES),
            "break_minutes": str(DEFAULT_BREAK_MINUTES),
            "pomodoro_cycles": str(DEFAULT_POMODORO_CYCLES),
            "pomodoro_enabled": "0",
            "daily_goal_minutes": str(DEFAULT_DAILY_GOAL_MINUTES),
            "music_volume": str(DEFAULT_MUSIC_VOLUME),
            "ambient_volume": str(DEFAULT_AMBIENT_VOLUME),
            "theme": DEFAULT_THEME,
            "quote_frequency": QUOTE_CHANGE_FREQUENCY,
            "startup_behavior": "timer",  # timer | statistics | history
            "last_music_folder": "",
            "last_ambient_sounds": "",
        }
        for key, value in defaults.items():
            cur.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )

        self.conn.commit()

    # ── Settings helpers ───────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    # ── Focus sessions ────────────────────────────────────────────────

    def save_session(
        self,
        session_date: date,
        start_time: str,
        duration_seconds: int,
        task_desc: str = "",
        completed: bool = True,
    ) -> int:
        """Persist a completed or abandoned focus session. Returns new row id."""
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO focus_sessions
               (session_date, start_time, duration, task_desc, completed)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session_date.isoformat(),
                start_time,
                duration_seconds,
                task_desc,
                1 if completed else 0,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_sessions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search_text: str = "",
        limit: int = 500,
    ) -> list[dict]:
        """Return focus sessions, optionally filtered by date range and text."""
        query = "SELECT * FROM focus_sessions WHERE 1=1"
        params: list = []

        if start_date:
            query += " AND session_date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND session_date <= ?"
            params.append(end_date.isoformat())
        if search_text:
            query += " AND task_desc LIKE ?"
            params.append(f"%{search_text}%")

        query += " ORDER BY session_date DESC, start_time DESC LIMIT ?"
        params.append(limit)

        cur = self.conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def get_today_total_seconds(self, target_date: Optional[date] = None) -> int:
        """Total completed focus seconds for a given date (defaults to today)."""
        d = target_date or date.today()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(duration), 0) FROM focus_sessions "
            "WHERE session_date = ? AND completed = 1",
            (d.isoformat(),),
        )
        return cur.fetchone()[0]

    def get_today_session_count(self, target_date: Optional[date] = None) -> int:
        """Number of completed sessions today."""
        d = target_date or date.today()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM focus_sessions "
            "WHERE session_date = ? AND completed = 1",
            (d.isoformat(),),
        )
        return cur.fetchone()[0]

    def get_daily_totals(
        self, start_date: date, end_date: date
    ) -> dict[str, int]:
        """Return {date_str: total_seconds} for completed sessions in range."""
        cur = self.conn.cursor()
        cur.execute(
            """SELECT session_date, SUM(duration) AS total
               FROM focus_sessions
               WHERE session_date BETWEEN ? AND ?
                 AND completed = 1
               GROUP BY session_date""",
            (start_date.isoformat(), end_date.isoformat()),
        )
        return {row["session_date"]: row["total"] for row in cur.fetchall()}

    def delete_session(self, session_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM focus_sessions WHERE id = ?", (session_id,))
        self.conn.commit()

    # ── Daily goals ────────────────────────────────────────────────────

    def get_today_goal_minutes(self, target_date: Optional[date] = None) -> int:
        """Return today's goal in minutes, or the default if not set."""
        d = target_date or date.today()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT target_minutes FROM daily_goals WHERE goal_date = ?",
            (d.isoformat(),),
        )
        row = cur.fetchone()
        if row:
            return row["target_minutes"]
        return int(self.get_setting("daily_goal_minutes", str(DEFAULT_DAILY_GOAL_MINUTES)))

    def set_today_goal(self, target_minutes: int, subject: str = "") -> None:
        """Upsert today's daily goal."""
        today = date.today().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO daily_goals (goal_date, target_minutes, subject)
               VALUES (?, ?, ?)
               ON CONFLICT(goal_date) DO UPDATE SET
                 target_minutes = excluded.target_minutes,
                 subject = excluded.subject""",
            (today, target_minutes, subject),
        )
        self.conn.commit()

    def get_goal_subject(self, target_date: Optional[date] = None) -> str:
        d = target_date or date.today()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT subject FROM daily_goals WHERE goal_date = ?",
            (d.isoformat(),),
        )
        row = cur.fetchone()
        return row["subject"] if row else ""

    # ── Quotes ─────────────────────────────────────────────────────────

    def get_quotes(self, include_builtin: bool = True) -> list[dict]:
        cur = self.conn.cursor()
        if include_builtin:
            cur.execute("SELECT * FROM quotes ORDER BY is_builtin DESC, id DESC")
        else:
            cur.execute("SELECT * FROM quotes WHERE is_builtin = 0 ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]

    def add_quote(self, text: str, author: str = "") -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO quotes (text, author, is_builtin) VALUES (?, ?, 0)",
            (text, author),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_quote(self, quote_id: int, text: str, author: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE quotes SET text = ?, author = ? WHERE id = ? AND is_builtin = 0",
            (text, author, quote_id),
        )
        self.conn.commit()

    def delete_quote(self, quote_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM quotes WHERE id = ? AND is_builtin = 0",
            (quote_id,),
        )
        self.conn.commit()

    # ── Playlists ──────────────────────────────────────────────────────

    def create_playlist(self, name: str) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def get_playlists(self) -> list[dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM playlists ORDER BY id")
        return [dict(row) for row in cur.fetchall()]

    def delete_playlist(self, playlist_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        self.conn.commit()

    def add_track(self, playlist_id: int, file_path: str) -> None:
        track_name = os.path.splitext(os.path.basename(file_path))[0]
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO playlist_tracks (playlist_id, file_path, track_name) "
            "VALUES (?, ?, ?)",
            (playlist_id, file_path, track_name),
        )
        self.conn.commit()

    def get_tracks(self, playlist_id: int) -> list[dict]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM playlist_tracks WHERE playlist_id = ? ORDER BY id",
            (playlist_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def remove_track(self, track_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM playlist_tracks WHERE id = ?", (track_id,))
        self.conn.commit()

    def clear_playlist_tracks(self, playlist_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,)
        )
        self.conn.commit()

    def get_all_track_paths(self) -> list[str]:
        """Return all unique file paths across all playlists (for music folder scan)."""
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT file_path FROM playlist_tracks")
        return [row["file_path"] for row in cur.fetchall()]

    # ── Cleanup ────────────────────────────────────────────────────────

    def close(self) -> None:
        self.conn.close()
