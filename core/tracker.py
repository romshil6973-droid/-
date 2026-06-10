"""
Operations tracker.
State machine: idle -> running <-> paused -> idle
All changes are saved to DB.
"""

from datetime import datetime, timedelta
from enum import Enum

from .database import Database


class TrackerState(Enum):
    IDLE    = "idle"
    RUNNING = "running"
    PAUSED  = "paused"


class WorkdayTracker:
    """
    Manages current employee operation.
    No UI interaction - only logic and DB.
    """

    def __init__(self, db: Database):
        self.db = db
        self.state: TrackerState = TrackerState.IDLE
        self.current_operation: str = ""
        self._session_id: int | None = None
        self._op_start: datetime | None = None
        self._pause_start: datetime | None = None
        self._total_paused: timedelta = timedelta(0)
        self.day_started: bool = False

        self._restore_day_state()

    def _restore_day_state(self):
        """Restores day-started flag on app restart."""
        today = datetime.now().strftime('%Y-%m-%d')
        session = self.db.get_day_session(today)
        if session and session.get('work_start') and not session.get('work_end'):
            self.day_started = True

    # ---- Day management --------------------------------------------------------

    def start_day(self) -> tuple[bool, str]:
        """Starts the working day. Returns (success, message)."""
        if self.day_started:
            return False, "Working day already started"
        self.db.start_work_day()
        self.day_started = True
        return True, "Working day started"

    def end_day(self) -> tuple[bool, str]:
        """Ends the working day. Automatically stops current operation."""
        if self.state != TrackerState.IDLE:
            self.stop_operation()
        self.db.end_work_day()
        self.day_started = False
        return True, "Working day ended"

    # ---- Operations ------------------------------------------------------------

    def start_operation(self, operation_name: str) -> tuple[bool, str]:
        """
        Starts an operation or resumes from pause.
        Auto-starts the day if not yet started.
        Returns (success, message).
        """
        if not operation_name.strip():
            return False, "Введите название операции"

        if self.state == TrackerState.RUNNING:
            return False, "Операция уже выполняется"

        # Auto-start day on first activity
        if not self.day_started:
            self.start_day()

        if self.state == TrackerState.PAUSED:
            # Resume from pause - count pause duration
            self._total_paused += datetime.now() - self._pause_start
            self._pause_start = None
            self.state = TrackerState.RUNNING
            return True, f"Возобновлено: {self.current_operation}"

        # New operation
        self.current_operation = operation_name.strip()
        self._op_start = datetime.now()
        self._total_paused = timedelta(0)
        self._pause_start = None
        self._session_id = self.db.start_work_session(
            self.current_operation, self._op_start
        )
        self.state = TrackerState.RUNNING
        return True, f"Начата: {self.current_operation}"

    def pause_operation(self) -> tuple[bool, str]:
        """Pauses the current operation."""
        if self.state != TrackerState.RUNNING:
            return False, "Нет активной операции"
        self._pause_start = datetime.now()
        self.state = TrackerState.PAUSED
        return True, "Пауза"

    def stop_operation(self) -> tuple[bool, str]:
        """Stops the current operation."""
        if self.state == TrackerState.IDLE:
            return False, "Нет активной операции"

        end_time = datetime.now()

        if self.state == TrackerState.PAUSED and self._pause_start:
            self._total_paused += end_time - self._pause_start

        if self._session_id is not None:
            self.db.complete_work_session(self._session_id, end_time)

        op = self.current_operation
        self.state = TrackerState.IDLE
        self.current_operation = ""
        self._session_id = None
        self._op_start = None
        self._pause_start = None
        self._total_paused = timedelta(0)

        return True, f"Завершено: {op}"

    # ---- Helpers ---------------------------------------------------------------

    def get_elapsed_seconds(self) -> int:
        """Returns net work time in seconds (excluding pauses)."""
        if self.state == TrackerState.IDLE or self._op_start is None:
            return 0
        now = datetime.now()
        paused = self._total_paused
        if self.state == TrackerState.PAUSED and self._pause_start:
            paused += now - self._pause_start
        elapsed = now - self._op_start - paused
        return max(0, int(elapsed.total_seconds()))

    def get_today_total_seconds(self) -> int:
        """Total seconds of completed operations today."""
        today = datetime.now().strftime('%Y-%m-%d')
        sessions = self.db.get_work_sessions_for_date(today)
        total = sum(s.get('duration_seconds') or 0 for s in sessions
                    if s.get('status') == 'completed')
        return total

    @staticmethod
    def format_duration(seconds: int) -> str:
        """Formats seconds -> HH:MM:SS string."""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
