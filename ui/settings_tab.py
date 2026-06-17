"""
Вкладка «Настройки».
Отображает текущий логин и путь Google Drive, автозапуск Windows.
"""

import os
import sys
import winreg
from pathlib import Path

import customtkinter as ctk

from core.database import Database
from core.config import load_config, get_config_path
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

        # ── Конфигурация (логин + Google Drive) ───────────────────────────────
        cfg_card = self._card("📋  Конфигурация WorkdayMonitor", row=0)

        # Логин
        row_login = ctk.CTkFrame(cfg_card, fg_color="transparent")
        row_login.pack(fill="x", padx=12, pady=(4, 2))
        ctk.CTkLabel(
            row_login, text="Логин:", width=120, anchor="w",
            font=ctk.CTkFont(T.FONT_SANS, 12), text_color=T.TEXT_MUTED
        ).pack(side="left")
        self.lbl_login = ctk.CTkLabel(
            row_login, text="—",
            font=ctk.CTkFont(T.FONT_SANS, 12, "bold"), text_color=T.TEXT_PRIMARY
        )
        self.lbl_login.pack(side="left")

        # Путь Google Drive
        row_path = ctk.CTkFrame(cfg_card, fg_color="transparent")
        row_path.pack(fill="x", padx=12, pady=(2, 6))
        ctk.CTkLabel(
            row_path, text="Google Drive:", width=120, anchor="w",
            font=ctk.CTkFont(T.FONT_SANS, 12), text_color=T.TEXT_MUTED
        ).pack(side="left")
        self.lbl_gdrive = ctk.CTkLabel(
            row_path, text="—",
            font=ctk.CTkFont(T.FONT_SANS, 11), text_color=T.TEXT_SECONDARY,
            wraplength=350, anchor="w", justify="left"
        )
        self.lbl_gdrive.pack(side="left", fill="x", expand=True)

        # Кнопки конфига
        btn_cfg_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        btn_cfg_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            btn_cfg_row, text="✏️  Изменить конфигурацию",
            fg_color=T.BG_INPUT, hover_color=T.BORDER,
            text_color=T.TEXT_SECONDARY,
            height=30, corner_radius=6,
            font=ctk.CTkFont(T.FONT_SANS, 11),
            command=self._reconfigure
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_cfg_row, text="📂  Открыть config.ini",
            fg_color=T.BG_INPUT, hover_color=T.BORDER,
            text_color=T.TEXT_SECONDARY,
            height=30, corner_radius=6,
            font=ctk.CTkFont(T.FONT_SANS, 11),
            command=self._open_config_file
        ).pack(side="left")

        # ── Автозапуск ────────────────────────────────────────────────────────
        auto_card = self._card("⚙️  Автозапуск при старте Windows", row=1)

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

    # ─── Логика ───────────────────────────────────────────────────────────────

    def _load(self):
        """Загружает конфигурацию и отображает в интерфейсе."""
        cfg = load_config()
        login = cfg.get('login') or '—'
        gdrive = cfg.get('google_drive_path') or '—'
        self.lbl_login.configure(text=login)
        self.lbl_gdrive.configure(text=gdrive)

    def _reconfigure(self):
        """Открывает диалог переконфигурации."""
        from .setup_dialog import SetupDialog
        dlg = SetupDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self._load()   # Обновляем отображение

    def _open_config_file(self):
        """Открывает config.ini в Блокноте."""
        path = get_config_path()
        if path.exists():
            os.startfile(str(path))
        else:
            from tkinter import messagebox
            messagebox.showwarning(
                "Конфиг не найден",
                "Файл config.ini не создан.\nСначала настройте конфигурацию."
            )

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
        """Формирует строку запуска для реестра.

        pythonw.exe запускает скрипт без окна CMD — VBS-лаунчер не нужен.
        """
        if getattr(sys, 'frozen', False):
            return f'"{sys.executable}"'
        else:
            script_dir = Path(__file__).parent.parent
            main_py = script_dir / "main.py"
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            return f'"{pythonw}" "{main_py}"'

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
