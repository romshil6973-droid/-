"""
Тесты модуля database.py.
Используют временную БД в памяти (:memory:).
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from core.database import Database


@pytest.fixture
def db():
    """Создаёт свежую БД в памяти для каждого теста."""
    return Database(db_path=":memory:")


# ─── Настройки ────────────────────────────────────────────────────────────────

class TestSettings:
    def test_set_and_get(self, db):
        db.set_setting("key1", "value1")
        assert db.get_setting("key1") == "value1"

    def test_get_missing_returns_default(self, db):
        assert db.get_setting("nonexistent") is None
        assert db.get_setting("nonexistent", "fallback") == "fallback"

    def test_overwrite(self, db):
        db.set_setting("k", "old")
        db.set_setting("k", "new")
        assert db.get_setting("k") == "new"

    def test_get_all(self, db):
        db.set_setting("a", "1")
        db.set_setting("b", "2")
        settings = db.get_all_settings()
        assert settings["a"] == "1"
        assert settings["b"] == "2"


# ─── Рабочие операции ─────────────────────────────────────────────────────────

class TestWorkSessions:
    def test_start_returns_id(self, db):
        sid = db.start_work_session("Тест", datetime(2024, 1, 10, 9, 0))
        assert isinstance(sid, int)
        assert sid > 0

    def test_complete_sets_duration(self, db):
        start = datetime(2024, 1, 10, 9, 0, 0)
        end   = datetime(2024, 1, 10, 9, 30, 0)
        sid = db.start_work_session("Тест", start)
        db.complete_work_session(sid, end)

        rows = db.get_work_sessions_for_date("2024-01-10")
        assert len(rows) == 1
        assert rows[0]["duration_seconds"] == 1800   # 30 минут
        assert rows[0]["status"] == "completed"

    def test_get_sessions_for_date_empty(self, db):
        rows = db.get_work_sessions_for_date("2099-01-01")
        assert rows == []

    def test_multiple_sessions_ordered(self, db):
        db.start_work_session("Операция А", datetime(2024, 1, 10, 9, 0))
        db.start_work_session("Операция Б", datetime(2024, 1, 10, 10, 0))
        rows = db.get_work_sessions_for_date("2024-01-10")
        assert len(rows) == 2
        assert rows[0]["operation"] == "Операция А"
        assert rows[1]["operation"] == "Операция Б"

    def test_complete_nonexistent_session(self, db):
        # Не должно бросать исключение
        db.complete_work_session(9999)


# ─── Границы рабочего дня ─────────────────────────────────────────────────────

class TestDaySessions:
    def test_start_and_get(self, db):
        dt = datetime(2024, 6, 10, 8, 0, 0)
        db.start_work_day(dt)
        sess = db.get_day_session("2024-06-10")
        assert sess is not None
        assert "08:00:00" in sess["work_start"]

    def test_end_day(self, db):
        db.start_work_day(datetime(2024, 6, 10, 8, 0))
        db.end_work_day(datetime(2024, 6, 10, 17, 0))
        sess = db.get_day_session("2024-06-10")
        assert sess["work_end"] is not None
        assert "17:00:00" in sess["work_end"]

    def test_get_missing_day(self, db):
        assert db.get_day_session("1900-01-01") is None

    def test_duplicate_start_ignored(self, db):
        """Повторное нажатие 'Начало дня' не создаёт дубликат."""
        db.start_work_day(datetime(2024, 6, 10, 8, 0))
        db.start_work_day(datetime(2024, 6, 10, 9, 0))  # второй вызов
        sess = db.get_day_session("2024-06-10")
        assert "08:00:00" in sess["work_start"]  # Сохранилось первое время


# ─── Мониторинг активности ────────────────────────────────────────────────────

class TestActivityLog:
    def test_log_and_complete(self, db):
        start = datetime(2024, 6, 10, 9, 0, 0)
        end   = datetime(2024, 6, 10, 9, 15, 0)
        aid = db.log_activity_start("chrome", "Google — Chrome", start)
        db.log_activity_end(aid, end)
        rows = db.get_activity_for_date("2024-06-10")
        assert len(rows) == 1
        assert rows[0]["app_name"] == "chrome"
        assert rows[0]["end_time"] is not None

    def test_idle_activity(self, db):
        start = datetime(2024, 6, 10, 12, 0, 0)
        aid = db.log_activity_start("Режим ожидания", "Простой", start, "idle")
        rows = db.get_activity_for_date("2024-06-10")
        assert rows[0]["activity_type"] == "idle"

    def test_empty_date(self, db):
        rows = db.get_activity_for_date("2099-12-31")
        assert rows == []


# ─── Достижения ───────────────────────────────────────────────────────────────

class TestAchievements:
    def test_save_and_get(self, db):
        db.save_achievement("Завершил проект", "2024-06-10")
        rec = db.get_achievement("2024-06-10")
        assert rec is not None
        assert rec["content"] == "Завершил проект"

    def test_overwrite_same_date(self, db):
        db.save_achievement("Первая версия", "2024-06-10")
        db.save_achievement("Вторая версия", "2024-06-10")
        rec = db.get_achievement("2024-06-10")
        assert rec["content"] == "Вторая версия"

    def test_get_missing(self, db):
        assert db.get_achievement("1900-01-01") is None


# ─── Отчёты ───────────────────────────────────────────────────────────────────

class TestReportTracking:
    def test_pending_only_past_dates(self, db):
        """Даты без отчёта — только прошлые дни."""
        # Сегодняшняя дата не должна попадать в pending
        db.start_work_session("Тест")  # сегодня
        pending = db.get_dates_pending_report()
        from datetime import date
        today = date.today().isoformat()
        assert today not in pending

    def test_mark_report_done(self, db):
        db.set_setting("report_test", "2024-01-01")   # имитируем прошлую сессию
        db.mark_report_done("2024-01-01")
        assert db.get_setting("report_done_2024-01-01") == "2024-01-01"
