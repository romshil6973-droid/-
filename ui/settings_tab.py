"""
Вкладка «Настройки».
ФИО, должность, папка для отчётов, автозапуск Windows.
"""

import os
import sys
import winreg
from pathlib import Path
import tkinter.filedialog as fd

import customtkinter as ctk

from core.database import Database
from . import theme as T

APP_NAME = "WorkdayMonitor"   # Имя в реестре автозапуска


class SettingsTab(ctk.CTkFrame):
    """Вкладка настроек."""

    def __init__(self, parent, db: Database, **kwargs):
        super().__init__(parent, fg_color=T.BG_DARK, **kwargs)
        self.db = db
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Данные сотрудника ─────────────────────────────────────────────────
        emp_card = self._card("👤  Данные сотрудника", row=0)

        self.fld_surname = self._field(emp_card, "Фамилия")
        self.fld_name    = self._field(emp_card, "Имя")
        self.fld_pos     = self._field(emp_card, "Должность")

        # ── Папка отчётов ─────────────────────────────────────────────────────
        rep_card = self._card("📁  Папка для отчётов", row=1)

        rep_row = ctk.CTkFrame(rep_card, fg_color="transparent")
        rep_row.pack(fill="x", padx=12, pady=6)
        rep_row.grid_columnconfigure(0, weight=1)

        self.fld_dir = ctk.CTkEntry(
            rep_row,
            fg_color=T.BG_INPUT, border_color=T.BORDER, text_color=T.TEXT_PRIMARY,
            font=ctk.CTkFont(T.FONT_SANS, 12), height=32, corner_radius=6
        )
        self.fld_dir.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            rep_row, text="Обзор…",
            fg_color=T.BG_CARD, hover_color=T.BORDER, text_color=T.TEXT_SECONDARY,
            width=80, height=32, corner_radius=6,
            command=self._browse_dir
        ).grid(row=0, column=1)

        # ── Автозапуск ────────────────────────────────────────────────────────
        auto_card = self._card("⚙️  Автозапуск при старте Windows", row=2)

        auto_row = ctk.CTkFrame(auto_card, fg_color="transparent")
        auto_row.pack(fill="x", padx=12, pady=8)

        self.autostart_var = ctk.BooleanVar(value=self._autostart_enabled())
        ctk.CTkSwitch(
            auto_row,
            text="Запускать автоматически при старте компьютера",
            variable=self.autostart_var,
            font=ctk.CTkFont(T.FONT_SANS, 12),
            text_color=T.TEXT_SECONDARY,
            progress_color=T.ACCENT,
            command=self._toggle_autostart
        ).pack(side="left")

        self.lbl_autostart = ctk.CTkLabel(
            auto_row, text="",
            font=ctk.CTkFont(T.FONT_SANS, 11), text_color=T.SUCCESS
        )
        self.lbl_autostart.pack(side="left", padx=12)

        # ── Кнопка сохранения ─────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="e", padx=12, pady=(8, 12))

        self.lbl_saved = ctk.CTkLabel(
            btn_row, text="",
            font=ctk.CTkFont(T.FONT_SANS, 11), text_color=T.SUCCESS
        )
        self.lbl_saved.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            btn_row, text="💾  Сохранить",
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
            height=34, corner_radius=6,
            command=self._save
        ).pack(side="right")

    # ─── Логика ───────────────────────────────────────────────────────────────

    def _load(self):
        """Загружает настройки из БД."""
        s = self.db.get_all_settings()
        self._set(self.fld_surname, s.get('emp_surname', ''))
        self._set(self.fld_name,    s.get('emp_name', ''))
        self._set(self.fld_pos,     s.get('emp_position', ''))
        default_dir = str(Path.home() / "Documents" / "WorkdayReports")
        self._set(self.fld_dir, s.get('report_dir', default_dir))

    def _save(self):
        """Сохраняет все настройки в БД."""
        self.db.set_setting('emp_surname',  self.fld_surname.get().strip())
        self.db.set_setting('emp_name',     self.fld_name.get().strip())
        self.db.set_setting('emp_position', self.fld_pos.get().strip())
        self.db.set_setting('report_dir',   self.fld_dir.get().strip())
        self.lbl_saved.configure(text="✓ Сохранено", text_color=T.SUCCESS)
        self.after(3000, lambda: self.lbl_saved.configure(text=""))

    def _browse_dir(self):
        """Диалог выбора папки."""
        folder = fd.askdirectory(title="Выберите папку для отчётов")
        if folder:
            self.fld_dir.delete(0, "end")
            self.fld_dir.insert(0, folder)

    # ── Автозапуск через реестр Windows ──────────────────────────────────────

    def _autostart_enabled(self) -> bool:
        """Проверяет, зарегистрирован ли автозапуск в реестре."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except (FileNotFoundError, OSError):
            return False

    def _toggle_autostart(self):
        """Включает/выключает автозапуск."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            if self.autostart_var.get():
                # Путь к исполняемому файлу / main.py
                exe_path = self._get_exe_path()
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
                self.lbl_autostart.configure(text="✓ Автозапуск включён", text_color=T.SUCCESS)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
                self.lbl_autostart.configure(text="Автозапуск отключён", text_color=T.WARNING)
            winreg.CloseKey(key)
        except Exception as e:
            self.lbl_autostart.configure(
                text=f"Ошибка: {e}", text_color=T.DANGER
            )
        self.after(4000, lambda: self.lbl_autostart.configure(text=""))

    @staticmethod
    def _get_exe_path() -> str:
        """Формирует строку запуска для реестра."""
        if getattr(sys, 'frozen', False):
            # Запуск из .exe (собранный PyInstaller)
            return f'"{sys.executable}"'
        else:
            # Запуск через Python — используем pythonw.exe чтобы не открывалось CMD-окно
            script = str(Path(__file__).parent.parent / "main.py")
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            return f'"{pythonw}" "{script}"'

    # ─── Вспомогательные методы ───────────────────────────────────────────────

    def _card(self, title: str, row: int) -> ctk.CTkFrame:
        """Создаёт карточку-секцию с заголовком."""
        outer = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=8)
        outer.grid(row=row, column=0, sticky="ew", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            outer, text=title,
            font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
            text_color=T.TEXT_SECONDARY
        ).pack(anchor="w", padx=12, pady=(8, 2))

        return outer

    def _field(self, parent, label: str) -> ctk.CTkEntry:
        """Создаёт поле ввода с подписью."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 6))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text=label, width=100, anchor="w",
            font=ctk.CTkFont(T.FONT_SANS, 12), text_color=T.TEXT_MUTED
        ).grid(row=0, column=0)

        entry = ctk.CTkEntry(
            row,
            fg_color=T.BG_INPUT, border_color=T.BORDER, text_color=T.TEXT_PRIMARY,
            font=ctk.CTkFont(T.FONT_SANS, 12), height=30, corner_radius=6
        )
        entry.grid(row=0, column=1, sticky="ew")
        return entry

    @staticmethod
    def _set(entry: ctk.CTkEntry, value: str):
        entry.delete(0, "end")
        entry.insert(0, value)

    def get_employee_info(self) -> dict:
        """Возвращает данные сотрудника (для генерации отчёта)."""
        return {
            'surname':  self.db.get_setting('emp_surname', ''),
            'name':     self.db.get_setting('emp_name', ''),
            'position': self.db.get_setting('emp_position', ''),
        }

    def get_report_dir(self) -> str:
        """Возвращает папку для отчётов."""
        default = str(Path.home() / "Documents" / "WorkdayReports")
        return self.db.get_setting('report_dir', default)
