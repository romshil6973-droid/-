"""
Тесты модуля reporter.py — генерация Excel-отчётов.
"""

import pytest
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from pathlib import Path

import openpyxl

from core.database import Database
from core.reporter import ExcelReporter, _fmt_dur, _fmt_time, _date_ru


# ─── Утилиты форматирования ───────────────────────────────────────────────────

class TestFormatters:
    def test_fmt_dur_zero(self):
        assert _fmt_dur(0) == "00:00:00"

    def test_fmt_dur_none(self):
        assert _fmt_dur(None) == "00:00:00"

    def test_fmt_dur_hour(self):
        assert _fmt_dur(3661) == "01:01:01"

    def test_fmt_time_valid(self):
        assert _fmt_time("2024-06-10 09:30:00") == "09:30:00"

    def test_fmt_time_none(self):
        assert _fmt_time(None) == "—"

    def test_fmt_time_invalid(self):
        result = _fmt_time("неверный формат")
        assert result == "неверный формат"

    def test_date_ru(self):
        dt = datetime(2024, 6, 10)  # Понедельник
        result = _date_ru(dt)
        assert "10" in result
        assert "июня" in result
        assert "2024" in result
        assert "понедельник" in result


# ─── Генерация Excel ──────────────────────────────────────────────────────────

@pytest.fixture
def reporter_env():
    """Создаёт DB + Reporter + временную папку для отчётов."""
    db = Database(db_path=":memory:")
    reporter = ExcelReporter(db)
    with tempfile.TemporaryDirectory() as tmpdir:
        yield db, reporter, tmpdir


class TestExcelGeneration:
    def test_creates_file(self, reporter_env):
        db, reporter, tmpdir = reporter_env
        emp = {"name": "Иван", "surname": "Иванов", "position": "Менеджер"}
        path = reporter.generate("2024-06-10", tmpdir, emp)
        assert Path(path).exists()

    def test_filename_contains_employee(self, reporter_env):
        db, reporter, tmpdir = reporter_env
        emp = {"name": "Пётр", "surname": "Сидоров", "position": "Аналитик"}
        path = reporter.generate("2024-06-10", tmpdir, emp)
        assert "Сидоров" in Path(path).name
        assert "Пётр" in Path(path).name

    def test_two_sheets(self, reporter_env):
        db, reporter, tmpdir = reporter_env
        emp = {"name": "А", "surname": "Б", "position": "В"}
        path = reporter.generate("2024-06-10", tmpdir, emp)
        wb = openpyxl.load_workbook(path)
        assert "Фото рабочего дня" in wb.sheetnames
        assert "Мониторинг активности" in wb.sheetnames

    def test_work_sessions_in_sheet(self, reporter_env):
        db, reporter, tmpdir = reporter_env
        # Добавляем сессию в БД
        sid = db.start_work_session("Акты сверок", datetime(2024, 6, 10, 9, 0))
        db.complete_work_session(sid, datetime(2024, 6, 10, 9, 45))

        emp = {"name": "Тест", "surname": "Тестов", "position": "—"}
        path = reporter.generate("2024-06-10", tmpdir, emp)

        wb = openpyxl.load_workbook(path)
        ws = wb["Фото рабочего дня"]
        # Находим строку с названием операции
        found = any(
            "Акты сверок" in str(cell.value or "")
            for row in ws.iter_rows()
            for cell in row
        )
        assert found, "Операция не найдена в листе Excel"

    def test_activity_in_sheet(self, reporter_env):
        db, reporter, tmpdir = reporter_env
        aid = db.log_activity_start(
            "chrome", "Google Chrome",
            datetime(2024, 6, 10, 9, 0)
        )
        db.log_activity_end(aid, datetime(2024, 6, 10, 9, 30))

        emp = {"name": "Т", "surname": "Т", "position": "Т"}
        path = reporter.generate("2024-06-10", tmpdir, emp)

        wb = openpyxl.load_workbook(path)
        ws = wb["Мониторинг активности"]
        found = any(
            "chrome" in str(cell.value or "").lower()
            for row in ws.iter_rows()
            for cell in row
        )
        assert found, "Активность не найдена в листе Excel"

    def test_empty_data_no_crash(self, reporter_env):
        """Генерация отчёта без данных не должна падать."""
        db, reporter, tmpdir = reporter_env
        emp = {"name": "П", "surname": "П", "position": "П"}
        path = reporter.generate("2024-01-01", tmpdir, emp)
        assert Path(path).exists()

    def test_achievement_in_report(self, reporter_env):
        db, reporter, tmpdir = reporter_env
        db.save_achievement("Выполнил план на 120%", "2024-06-10")

        emp = {"name": "М", "surname": "М", "position": "М"}
        path = reporter.generate("2024-06-10", tmpdir, emp)

        wb = openpyxl.load_workbook(path)
        ws = wb["Фото рабочего дня"]
        found = any(
            "120%" in str(cell.value or "")
            for row in ws.iter_rows()
            for cell in row
        )
        assert found, "Достижение не найдено в отчёте"
