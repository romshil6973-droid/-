"""
Database module for WorkdayMonitor.
Stores: work sessions, activity log, achievements, settings.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path


def get_db_path():
    """Returns path to the SQLite database file (AppData/WorkdayMonitor)."""
    app_data = Path(os.environ.get('APPDATA', Path.home())) / 'WorkdayMonitor'
    app_data.mkdir(exist_ok=True)
    return app_data / 'workday.db'


class Database:
    """All database operations for WorkdayMonitor."""

    def __init__(self, db_path=None):
        """
        Args:
            db_path: Path to DB file. None = default AppData path.
                     ':memory:' = in-memory DB (for tests).
        """
        self.db_path = str(db_path or get_db_path())

        # For :memory: we keep ONE persistent connection.
        # sqlite3.connect(":memory:") creates a fresh empty DB on every call,
        # so we must reuse the same connection object throughout the instance.
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
        else:
            self._mem_conn = None

        self._init_db()

    def _connect(self):
        """Returns a database connection. row_factory enables column access by name."""
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates tables on first run."""
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS work_sessions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                date             TEXT NOT NULL,
                operation        TEXT NOT NULL,
                start_time       TEXT NOT NULL,
                end_time         TEXT,
                duration_seconds INTEGER,
                status           TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS day_sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                date       TEXT NOT NULL UNIQUE,
                work_start TEXT,
                work_end   TEXT
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                date          TEXT NOT NULL,
                start_time    TEXT NOT NULL,
                end_time      TEXT,
                app_name      TEXT,
                window_title  TEXT,
                activity_type TEXT DEFAULT 'app'
            );

            CREATE TABLE IF NOT EXISTS achievements (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                date       TEXT NOT NULL UNIQUE,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        conn.commit()

    # -------------------------------------------------------------------------
    # Settings
    # -------------------------------------------------------------------------

    def get_setting(self, key, default=None):
        conn = self._connect()
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row['value'] if row else default

    def set_setting(self, key, value):
        conn = self._connect()
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value) if value is not None else '')
        )
        conn.commit()

    def get_all_settings(self):
        conn = self._connect()
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r['key']: r['value'] for r in rows}

    # -------------------------------------------------------------------------
    # Work sessions (photo of working day)
    # -------------------------------------------------------------------------

    def start_work_session(self, operation, start_time=None):
        """Creates a work session record. Returns its ID."""
        now = start_time or datetime.now()
        conn = self._connect()
        cursor = conn.execute(
            "INSERT INTO work_sessions (date, operation, start_time, status) "
            "VALUES (?, ?, ?, 'active')",
            (now.strftime('%Y-%m-%d'), operation, now.strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        return cursor.lastrowid

    def complete_work_session(self, session_id, end_time=None):
        """Marks a session as completed with end time and duration."""
        now = end_time or datetime.now()
        conn = self._connect()
        row = conn.execute(
            "SELECT start_time FROM work_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            return
        start_dt = datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M:%S')
        duration = int((now - start_dt).total_seconds())
        conn.execute(
            "UPDATE work_sessions SET end_time = ?, duration_seconds = ?, "
            "status = 'completed' WHERE id = ?",
            (now.strftime('%Y-%m-%d %H:%M:%S'), duration, session_id)
        )
        conn.commit()

    def get_work_sessions_for_date(self, date_str):
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM work_sessions WHERE date = ? ORDER BY start_time",
            (date_str,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_dates_pending_report(self):
        """Returns past dates that have sessions but no generated report."""
        conn = self._connect()
        rows = conn.execute("""
            SELECT DISTINCT date FROM work_sessions
            WHERE date < date('now', 'localtime')
              AND date NOT IN (
                  SELECT value FROM settings WHERE key LIKE 'report_done_%'
              )
            ORDER BY date
        """).fetchall()
        return [r['date'] for r in rows]

    def mark_report_done(self, date_str):
        self.set_setting('report_done_' + date_str, date_str)

    # -------------------------------------------------------------------------
    # Day boundaries
    # -------------------------------------------------------------------------

    def start_work_day(self, dt=None):
        now = dt or datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        conn = self._connect()
        conn.execute(
            "INSERT OR IGNORE INTO day_sessions (date, work_start) VALUES (?, ?)",
            (date_str, time_str)
        )
        conn.commit()

    def end_work_day(self, dt=None):
        now = dt or datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        conn = self._connect()
        conn.execute(
            "INSERT OR IGNORE INTO day_sessions (date) VALUES (?)", (date_str,)
        )
        conn.execute(
            "UPDATE day_sessions SET work_end = ? WHERE date = ?",
            (time_str, date_str)
        )
        conn.commit()

    def get_day_session(self, date_str):
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM day_sessions WHERE date = ?", (date_str,)
        ).fetchone()
        return dict(row) if row else None

    # -------------------------------------------------------------------------
    # Activity monitoring
    # -------------------------------------------------------------------------

    def log_activity_start(self, app_name, window_title, start_time, activity_type='app'):
        """Logs the start of an activity. Returns record ID."""
        conn = self._connect()
        cursor = conn.execute(
            "INSERT INTO activity_log "
            "(date, start_time, app_name, window_title, activity_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                start_time.strftime('%Y-%m-%d'),
                start_time.strftime('%Y-%m-%d %H:%M:%S'),
                app_name, window_title, activity_type
            )
        )
        conn.commit()
        return cursor.lastrowid

    def log_activity_end(self, activity_id, end_time):
        """Sets the end time of an activity record."""
        conn = self._connect()
        conn.execute(
            "UPDATE activity_log SET end_time = ? WHERE id = ?",
            (end_time.strftime('%Y-%m-%d %H:%M:%S'), activity_id)
        )
        conn.commit()

    def get_activity_for_date(self, date_str):
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM activity_log WHERE date = ? ORDER BY start_time",
            (date_str,)
        ).fetchall()
        return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Achievements
    # -------------------------------------------------------------------------

    def save_achievement(self, content, date_str=None):
        """Saves daily achievements (one record per date, overwrites if exists)."""
        today = date_str or datetime.now().strftime('%Y-%m-%d')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = self._connect()
        conn.execute(
            "INSERT OR REPLACE INTO achievements (date, content, created_at) "
            "VALUES (?, ?, ?)",
            (today, content, now_str)
        )
        conn.commit()

    def get_achievement(self, date_str):
        """Returns achievement record for the given date, or None."""
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM achievements WHERE date = ?", (date_str,)
        ).fetchone()
        return dict(row) if row else None
