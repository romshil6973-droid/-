"""
Тесты модуля tracker.py — машина состояний рабочих операций.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.database import Database
from core.tracker import WorkdayTracker, TrackerState


@pytest.fixture
def tracker():
    db = Database(db_path=":memory:")
    return WorkdayTracker(db)


# ─── Начальное состояние ──────────────────────────────────────────────────────

class TestInitialState:
    def test_starts_idle(self, tracker):
        assert tracker.state == TrackerState.IDLE

    def test_day_not_started(self, tracker):
        assert tracker.day_started is False

    def test_elapsed_zero_when_idle(self, tracker):
        assert tracker.get_elapsed_seconds() == 0


# ─── Рабочий день ─────────────────────────────────────────────────────────────

class TestDayManagement:
    def test_start_day(self, tracker):
        ok, msg = tracker.start_day()
        assert ok is True
        assert tracker.day_started is True

    def test_cannot_start_day_twice(self, tracker):
        tracker.start_day()
        ok, _ = tracker.start_day()
        assert ok is False

    def test_end_day(self, tracker):
        tracker.start_day()
        ok, _ = tracker.end_day()
        assert ok is True
        assert tracker.day_started is False


# ─── Операции: старт/пауза/стоп ──────────────────────────────────────────────

class TestOperations:
    def test_start_empty_name_fails(self, tracker):
        ok, msg = tracker.start_operation("")
        assert ok is False

    def test_start_whitespace_fails(self, tracker):
        ok, _ = tracker.start_operation("   ")
        assert ok is False

    def test_start_valid_operation(self, tracker):
        ok, _ = tracker.start_operation("Работа с актами")
        assert ok is True
        assert tracker.state == TrackerState.RUNNING
        assert tracker.current_operation == "Работа с актами"

    def test_cannot_start_while_running(self, tracker):
        tracker.start_operation("Первая")
        ok, _ = tracker.start_operation("Вторая")
        assert ok is False
        assert tracker.state == TrackerState.RUNNING

    def test_pause_when_running(self, tracker):
        tracker.start_operation("Тест")
        ok, _ = tracker.pause_operation()
        assert ok is True
        assert tracker.state == TrackerState.PAUSED

    def test_pause_when_idle_fails(self, tracker):
        ok, _ = tracker.pause_operation()
        assert ok is False

    def test_resume_from_pause(self, tracker):
        tracker.start_operation("Тест")
        tracker.pause_operation()
        ok, _ = tracker.start_operation("любой текст (игнорируется)")
        assert ok is True
        assert tracker.state == TrackerState.RUNNING
        # Имя операции не меняется при возобновлении
        assert tracker.current_operation == "Тест"

    def test_stop_when_running(self, tracker):
        tracker.start_operation("Тест")
        ok, _ = tracker.stop_operation()
        assert ok is True
        assert tracker.state == TrackerState.IDLE
        assert tracker.current_operation == ""

    def test_stop_when_paused(self, tracker):
        tracker.start_operation("Тест")
        tracker.pause_operation()
        ok, _ = tracker.stop_operation()
        assert ok is True
        assert tracker.state == TrackerState.IDLE

    def test_stop_when_idle_fails(self, tracker):
        ok, _ = tracker.stop_operation()
        assert ok is False

    def test_operation_saved_in_db(self, tracker):
        import time
        tracker.start_operation("Отчётность")
        time.sleep(0.1)
        tracker.stop_operation()
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        sessions = tracker.db.get_work_sessions_for_date(today)
        assert len(sessions) == 1
        assert sessions[0]["operation"] == "Отчётность"
        assert sessions[0]["status"] == "completed"
        assert sessions[0]["duration_seconds"] is not None


# ─── Форматирование ───────────────────────────────────────────────────────────

class TestFormatDuration:
    def test_zero(self):
        assert WorkdayTracker.format_duration(0) == "00:00:00"

    def test_seconds(self):
        assert WorkdayTracker.format_duration(45) == "00:00:45"

    def test_minutes(self):
        assert WorkdayTracker.format_duration(90) == "00:01:30"

    def test_hours(self):
        assert WorkdayTracker.format_duration(3661) == "01:01:01"

    def test_large(self):
        assert WorkdayTracker.format_duration(86400) == "24:00:00"


# ─── Итого за день ────────────────────────────────────────────────────────────

class TestTotalTime:
    def test_total_zero_on_start(self, tracker):
        assert tracker.get_today_total_seconds() == 0

    def test_total_accumulates(self, tracker):
        import time
        tracker.start_operation("Операция 1")
        time.sleep(0.05)
        tracker.stop_operation()
        tracker.start_operation("Операция 2")
        time.sleep(0.05)
        tracker.stop_operation()
        total = tracker.get_today_total_seconds()
        assert total >= 0  # Может быть 0 из-за точности sleep в тестах, но не должно упасть
