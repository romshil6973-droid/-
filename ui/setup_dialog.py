"""
Диалог первичной настройки WorkdayMonitor v2.0.
Запрашивает только логин сотрудника.
"""
import customtkinter as ctk
from core.config import save_config, validate_login
from . import theme as T

class SetupDialog(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None
        self._build()
        self._center()
        self.resizable(False, False)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build(self):
        self.title("WorkdayMonitor — Первичная настройка")
        self.configure(fg_color=T.BG_DARK)
        ctk.CTkLabel(self, text="⚙  Первичная настройка",
                     font=ctk.CTkFont(T.FONT_SANS, 16, "bold"),
                     text_color=T.TEXT_PRIMARY).pack(padx=28, pady=(22, 2))
        ctk.CTkLabel(self, text="Введите ваш логин — приложение запомнит его.",
                     font=ctk.CTkFont(T.FONT_SANS, 11),
                     text_color=T.TEXT_MUTED).pack(padx=28, pady=(0, 14))
        card = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=8)
        card.pack(padx=28, fill="x")
        ctk.CTkLabel(card, text="👤  Логин сотрудника",
                     font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
                     text_color=T.TEXT_SECONDARY, anchor="w").pack(padx=16, pady=(14,2), fill="x")
        self.fld_login = ctk.CTkEntry(card, placeholder_text="например: shilov",
                                       fg_color=T.BG_INPUT, border_color=T.BORDER,
                                       text_color=T.TEXT_PRIMARY,
                                       font=ctk.CTkFont(T.FONT_SANS, 12),
                                       height=34, corner_radius=6)
        self.fld_login.pack(padx=16, fill="x")
        ctk.CTkLabel(card,
                     text="Только латиница (a–z), цифры, '_'. От 3 до 20 символов.",
                     font=ctk.CTkFont(T.FONT_SANS, 10),
                     text_color=T.TEXT_MUTED, anchor="w").pack(padx=16, pady=(3,16), fill="x")
        self.lbl_err = ctk.CTkLabel(self, text="",
                                     font=ctk.CTkFont(T.FONT_SANS, 11),
                                     text_color=T.DANGER, wraplength=460)
        self.lbl_err.pack(padx=28, pady=(10,0), fill="x")
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=28, pady=18, fill="x")
        ctk.CTkButton(btn_row, text="Отмена",
                      fg_color=T.BG_CARD, hover_color=T.BORDER,
                      text_color=T.TEXT_MUTED, height=36, corner_radius=6,
                      command=self._on_cancel).pack(side="left")
        ctk.CTkButton(btn_row, text="✅  Сохранить и продолжить",
                      fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
                      text_color="#ffffff", height=36, corner_radius=6,
                      font=ctk.CTkFont(T.FONT_SANS, 12, "bold"),
                      command=self._on_ok).pack(side="right")

    def _on_ok(self):
        login = self.fld_login.get().strip()
        ok, err = validate_login(login)
        if not ok:
            self.lbl_err.configure(text=f"❌  {err}")
            return
        save_config(login)
        self.result = {'login': login}
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()

    def _center(self):
        self.update_idletasks()
        w, h = 540, 320
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
