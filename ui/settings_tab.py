"""
Вкладка «Настройки» — WorkdayMonitor v2.0.
"""
import os, sys, winreg
from pathlib import Path
import customtkinter as ctk
from core.database import Database
from core.config import load_config, get_config_path
from . import theme as T

APP_NAME = "WorkdayMonitor"

class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, db: Database, **kwargs):
        super().__init__(parent, fg_color=T.BG_DARK, **kwargs)
        self.db = db
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        cfg_card = self._card("📋  Конфигурация WorkdayMonitor", row=0)
        row_login = ctk.CTkFrame(cfg_card, fg_color="transparent")
        row_login.pack(fill="x", padx=12, pady=(4,2))
        ctk.CTkLabel(row_login, text="Логин:", width=120, anchor="w",
                     font=ctk.CTkFont(T.FONT_SANS, 12), text_color=T.TEXT_MUTED).pack(side="left")
        self.lbl_login = ctk.CTkLabel(row_login, text="—",
                                       font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
                                       text_color=T.TEXT_PRIMARY)
        self.lbl_login.pack(side="left")
        btn_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(6,10))
        ctk.CTkButton(btn_row, text="✏️  Изменить логин",
                      fg_color=T.BG_INPUT, hover_color=T.BORDER,
                      text_color=T.TEXT_SECONDARY, height=30, corner_radius=6,
                      font=ctk.CTkFont(T.FONT_SANS, 11),
                      command=self._reconfigure).pack(side="left", padx=(0,8))
        ctk.CTkButton(btn_row, text="📂  Открыть config.ini",
                      fg_color=T.BG_INPUT, hover_color=T.BORDER,
                      text_color=T.TEXT_SECONDARY, height=30, corner_radius=6,
                      font=ctk.CTkFont(T.FONT_SANS, 11),
                      command=self._open_config_file).pack(side="left")

        srv_card = self._card("🌐  Сервер отчётов", row=1)
        row_srv = ctk.CTkFrame(srv_card, fg_color="transparent")
        row_srv.pack(fill="x", padx=12, pady=(4,2))
        ctk.CTkLabel(row_srv, text="Статус:", width=120, anchor="w",
                     font=ctk.CTkFont(T.FONT_SANS, 12), text_color=T.TEXT_MUTED).pack(side="left")
        self.lbl_server = ctk.CTkLabel(row_srv, text="—",
                                        font=ctk.CTkFont(T.FONT_SANS, 12),
                                        text_color=T.TEXT_SECONDARY)
        self.lbl_server.pack(side="left")
        btn_srv = ctk.CTkFrame(srv_card, fg_color="transparent")
        btn_srv.pack(fill="x", padx=12, pady=(6,10))
        ctk.CTkButton(btn_srv, text="🔄  Проверить соединение",
                      fg_color=T.BG_INPUT, hover_color=T.BORDER,
                      text_color=T.TEXT_SECONDARY, height=30, corner_radius=6,
                      font=ctk.CTkFont(T.FONT_SANS, 11),
                      command=self._check_server).pack(side="left", padx=(0,8))
        self.btn_retry = ctk.CTkButton(btn_srv, text="📤  Повторить отправку",
                                        fg_color=T.BG_INPUT, hover_color=T.BORDER,
                                        text_color=T.TEXT_SECONDARY, height=30, corner_radius=6,
                                        font=ctk.CTkFont(T.FONT_SANS, 11),
                                        command=self._retry_pending)
        self.btn_retry.pack(side="left")

        auto_card = self._card("⚙️  Автозапуск при старте Windows", row=2)
        auto_row = ctk.CTkFrame(auto_card, fg_color="transparent")
        auto_row.pack(fill="x", padx=12, pady=8)
        self.autostart_var = ctk.BooleanVar(value=self._autostart_enabled())
        ctk.CTkSwitch(auto_row,
                      text="Запускать автоматически при старте компьютера",
                      variable=self.autostart_var,
                      font=ctk.CTkFont(T.FONT_SANS, 12), text_color=T.TEXT_SECONDARY,
                      progress_color=T.ACCENT,
                      command=self._toggle_autostart).pack(side="left")
        self.lbl_autostart = ctk.CTkLabel(auto_row, text="",
                                           font=ctk.CTkFont(T.FONT_SANS, 11),
                                           text_color=T.SUCCESS)
        self.lbl_autostart.pack(side="left", padx=12)

    def _load(self):
        cfg = load_config()
        self.lbl_login.configure(text=cfg.get('login') or '—')
        self._refresh_pending_btn()

    def _check_server(self):
        from core.uploader import check_server
        self.lbl_server.configure(text="Проверяю...", text_color=T.TEXT_MUTED)
        self.update()
        if check_server():
            self.lbl_server.configure(text="🟢 Подключено", text_color=T.SUCCESS)
        else:
            self.lbl_server.configure(text="🔴 Нет связи", text_color=T.DANGER)

    def _retry_pending(self):
        from core.uploader import retry_pending_uploads, pending_count
        sent = retry_pending_uploads()
        remaining = pending_count()
        if sent > 0:
            self.lbl_server.configure(
                text=f"✅ Отправлено {sent} файл(ов). Осталось: {remaining}",
                text_color=T.SUCCESS)
        else:
            self.lbl_server.configure(text="⚠️ Не удалось отправить",
                                       text_color=T.WARNING)
        self._refresh_pending_btn()

    def _refresh_pending_btn(self):
        from core.uploader import pending_count
        n = pending_count()
        self.btn_retry.configure(
            text=f"📤  Повторить отправку ({n})" if n else "📤  Повторить отправку")

    def _reconfigure(self):
        from .setup_dialog import SetupDialog
        dlg = SetupDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self._load()

    def _open_config_file(self):
        path = get_config_path()
        if path.exists():
            os.startfile(str(path))
        else:
            from tkinter import messagebox
            messagebox.showwarning("Конфиг не найден", "Файл config.ini не создан.")

    def _autostart_enabled(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  r"Software\Microsoft\Windows\CurrentVersion\Run",
                                  0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except (FileNotFoundError, OSError):
            return False

    def _toggle_autostart(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  r"Software\Microsoft\Windows\CurrentVersion\Run",
                                  0, winreg.KEY_SET_VALUE)
            if self.autostart_var.get():
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, self._get_exe_path())
                self.lbl_autostart.configure(text="✓ Автозапуск включён", text_color=T.SUCCESS)
            else:
                try: winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError: pass
                self.lbl_autostart.configure(text="Автозапуск отключён", text_color=T.WARNING)
            winreg.CloseKey(key)
        except Exception as e:
            self.lbl_autostart.configure(text=f"Ошибка: {e}", text_color=T.DANGER)
        self.after(4000, lambda: self.lbl_autostart.configure(text=""))

    @staticmethod
    def _get_exe_path() -> str:
        if getattr(sys, 'frozen', False):
            return f'"{sys.executable}"'
        script_dir = Path(__file__).parent.parent
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        return f'"{pythonw}" "{script_dir / "main.py"}"'

    def _card(self, title: str, row: int) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=8)
        outer.grid(row=row, column=0, sticky="ew", padx=12, pady=(8,0))
        ctk.CTkLabel(outer, text=title, font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
                     text_color=T.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(8,2))
        return outer
