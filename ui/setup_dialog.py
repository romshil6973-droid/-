"""
Диалог первичной настройки WorkdayMonitor.

Показывается при первом запуске (когда config.ini отсутствует или неполный).
Запрашивает логин сотрудника и путь к папке Google Drive.
"""

import tkinter.filedialog as fd
import customtkinter as ctk

from core.config import save_config, validate_login, validate_gdrive_path
from . import theme as T


class SetupDialog(ctk.CTkToplevel):
    """Модальное окно первичной настройки."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None          # None = отмена/закрытие, dict = успех
        self._build()
        self._center()
        self.resizable(False, False)
        self.grab_set()             # блокирует взаимодействие с родителем
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ─── Построение интерфейса ────────────────────────────────────────────────

    def _build(self):
        self.title("WorkdayMonitor — Первичная настройка")
        self.configure(fg_color=T.BG_DARK)

        # Заголовок
        ctk.CTkLabel(
            self, text="⚙  Первичная настройка",
            font=ctk.CTkFont(T.FONT_SANS, 16, "bold"),
            text_color=T.TEXT_PRIMARY
        ).pack(padx=28, pady=(22, 2))

        ctk.CTkLabel(
            self,
            text="Настройте параметры один раз — приложение запомнит их.",
            font=ctk.CTkFont(T.FONT_SANS, 11),
            text_color=T.TEXT_MUTED
        ).pack(padx=28, pady=(0, 14))

        # ── Карточка ──────────────────────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=8)
        card.pack(padx=28, fill="x")

        # Логин
        ctk.CTkLabel(
            card, text="👤  Логин сотрудника",
            font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
            text_color=T.TEXT_SECONDARY, anchor="w"
        ).pack(padx=16, pady=(14, 2), fill="x")

        self.fld_login = ctk.CTkEntry(
            card, placeholder_text="например: shilov",
            fg_color=T.BG_INPUT, border_color=T.BORDER,
            text_color=T.TEXT_PRIMARY,
            font=ctk.CTkFont(T.FONT_SANS, 12), height=34, corner_radius=6
        )
        self.fld_login.pack(padx=16, fill="x")

        ctk.CTkLabel(
            card,
            text="Только латиница (a–z), цифры, '_'. От 3 до 20 символов. Пример: shilov",
            font=ctk.CTkFont(T.FONT_SANS, 10),
            text_color=T.TEXT_MUTED, anchor="w"
        ).pack(padx=16, pady=(3, 14), fill="x")

        # Разделитель
        ctk.CTkFrame(card, fg_color=T.BORDER, height=1).pack(fill="x")

        # Google Drive
        ctk.CTkLabel(
            card, text="📁  Папка Google Drive (Отчеты_менеджеров)",
            font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
            text_color=T.TEXT_SECONDARY, anchor="w"
        ).pack(padx=16, pady=(14, 2), fill="x")

        path_row = ctk.CTkFrame(card, fg_color="transparent")
        path_row.pack(padx=16, fill="x")
        path_row.grid_columnconfigure(0, weight=1)

        self.fld_path = ctk.CTkEntry(
            path_row,
            placeholder_text=r"C:\Users\User\Google Drive\Компания\Отчеты_менеджеров",
            fg_color=T.BG_INPUT, border_color=T.BORDER,
            text_color=T.TEXT_PRIMARY,
            font=ctk.CTkFont(T.FONT_SANS, 11), height=34, corner_radius=6
        )
        self.fld_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            path_row, text="📂 Обзор",
            fg_color=T.BG_INPUT, hover_color=T.BORDER,
            text_color=T.TEXT_PRIMARY,
            width=90, height=34, corner_radius=6,
            command=self._browse
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            card,
            text="Выберите папку /Компания/Отчеты_менеджеров/ на Google Drive Desktop",
            font=ctk.CTkFont(T.FONT_SANS, 10),
            text_color=T.TEXT_MUTED, anchor="w"
        ).pack(padx=16, pady=(3, 16), fill="x")

        # ── Сообщение об ошибке ───────────────────────────────────────────────
        self.lbl_err = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(T.FONT_SANS, 11),
            text_color=T.DANGER, wraplength=460, justify="left"
        )
        self.lbl_err.pack(padx=28, pady=(10, 0), fill="x")

        # ── Кнопки ────────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=28, pady=18, fill="x")

        ctk.CTkButton(
            btn_row, text="Отмена",
            fg_color=T.BG_CARD, hover_color=T.BORDER,
            text_color=T.TEXT_MUTED,
            height=36, corner_radius=6,
            command=self._on_cancel
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="✅  Сохранить и продолжить",
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#ffffff",
            height=36, corner_radius=6,
            font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
            command=self._on_ok
        ).pack(side="right")

    # ─── Обработчики ──────────────────────────────────────────────────────────

    def _browse(self):
        folder = fd.askdirectory(title="Выберите папку Отчеты_менеджеров")
        if folder:
            self.fld_path.delete(0, "end")
            self.fld_path.insert(0, folder)

    def _on_ok(self):
        login = self.fld_login.get().strip()
        path  = self.fld_path.get().strip()

        ok_l, err_l = validate_login(login)
        if not ok_l:
            self.lbl_err.configure(text=f"❌  {err_l}")
            return

        ok_p, err_p = validate_gdrive_path(path)
        if not ok_p:
            self.lbl_err.configure(text=f"❌  {err_p}")
            return

        save_config(login, path)
        self.result = {'login': login, 'google_drive_path': path}
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()

    def _center(self):
        self.update_idletasks()
        w, h = 540, 460
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
