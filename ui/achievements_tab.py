"""
Вкладка «Мои достижения за день».
Сотрудник вводит только завершённые задачи/процессы.
"""

import customtkinter as ctk
from datetime import datetime

from core.database import Database
from . import theme as T


class AchievementsTab(ctk.CTkFrame):
    """Вкладка для ввода достижений за текущий день."""

    def __init__(self, parent, db: Database, **kwargs):
        super().__init__(parent, fg_color=T.BG_DARK, **kwargs)
        self.db = db
        self._build()
        self._load_today()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Подсказка ─────────────────────────────────────────────────────────
        hint_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=8)
        hint_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            hint_frame,
            text="💡  Вносите ТОЛЬКО завершённые процессы и выполненную работу",
            font=ctk.CTkFont(T.FONT_SANS, 11),
            text_color=T.TEXT_MUTED
        ).pack(padx=12, pady=8)

        # ── Область ввода ─────────────────────────────────────────────────────
        self.text_box = ctk.CTkTextbox(
            self,
            fg_color=T.BG_INPUT,
            text_color=T.TEXT_PRIMARY,
            font=ctk.CTkFont(T.FONT_SANS, 13),
            border_color=T.BORDER,
            border_width=1,
            corner_radius=8,
            wrap="word"
        )
        self.text_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)

        # Плейсхолдер (имитируем, т.к. CTkTextbox не имеет встроенного)
        self._placeholder = "Например:\n• Согласовал договор с поставщиком №123\n• Завершил обработку 50 актов сверок\n• Провёл собрание отдела"
        self._show_placeholder()
        self.text_box.bind("<FocusIn>",  self._clear_placeholder)
        self.text_box.bind("<FocusOut>", self._maybe_placeholder)

        # ── Кнопка сохранения ─────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 10))

        self.lbl_saved = ctk.CTkLabel(
            btn_frame, text="",
            font=ctk.CTkFont(T.FONT_SANS, 11), text_color=T.SUCCESS
        )
        self.lbl_saved.pack(side="left")

        ctk.CTkButton(
            btn_frame, text="💾  Сохранить достижения",
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
            height=34, corner_radius=6,
            command=self._save
        ).pack(side="right")

    # ─── Логика ───────────────────────────────────────────────────────────────

    def _load_today(self):
        """Загружает сохранённые достижения за сегодня."""
        today = datetime.now().strftime('%Y-%m-%d')
        record = self.db.get_achievement(today)
        if record and record.get('content'):
            self._set_text(record['content'])

    def _save(self):
        content = self._get_text()
        if not content or content == self._placeholder:
            self.lbl_saved.configure(text="Нечего сохранять", text_color=T.WARNING)
            return
        today = datetime.now().strftime('%Y-%m-%d')
        self.db.save_achievement(content, today)
        self.lbl_saved.configure(text="✓ Сохранено", text_color=T.SUCCESS)
        self.after(3000, lambda: self.lbl_saved.configure(text=""))

    def _get_text(self) -> str:
        return self.text_box.get("1.0", "end").strip()

    def _set_text(self, text: str):
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text)
        self.text_box.configure(text_color=T.TEXT_PRIMARY)
        self._is_placeholder = False

    def _show_placeholder(self):
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", self._placeholder)
        self.text_box.configure(text_color=T.TEXT_MUTED)
        self._is_placeholder = True

    def _clear_placeholder(self, _event=None):
        if getattr(self, '_is_placeholder', False):
            self.text_box.delete("1.0", "end")
            self.text_box.configure(text_color=T.TEXT_PRIMARY)
            self._is_placeholder = False

    def _maybe_placeholder(self, _event=None):
        if not self._get_text():
            self._show_placeholder()
