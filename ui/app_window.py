"""
Main application window.
Header with clock + sidebar + content area.
"""

import customtkinter as ctk
from datetime import datetime
from pathlib import Path

from core.database import Database
from core.tracker import WorkdayTracker
from core.monitor import ActivityMonitor
from core.reporter import ExcelReporter

from .workday_tab      import WorkdayTab
from .achievements_tab import AchievementsTab
from .settings_tab     import SettingsTab
from . import theme as T

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


MONTHS_RU = [
    "января","февраля","марта","апреля","мая","июня",
    "июля","августа","сентября","октября","ноября","декабря"
]
DAYS_RU = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.db      = Database()
        self.tracker = WorkdayTracker(self.db)
        self.monitor = ActivityMonitor(self.db)

        self._setup_window()
        self._build_header()
        self._build_sidebar()
        self._build_content()
        self._check_pending_reports()

        self.monitor.start()
        self._show_tab("workday")
        self._update_clock()

    # ---- Window setup ----------------------------------------------------------

    def _setup_window(self):
        self.title("Мониторинг рабочего дня")
        self.geometry(f"{T.WIN_W}x{T.WIN_H}")
        self.minsize(T.WIN_W, T.WIN_H)
        self.configure(fg_color=T.BG_DARK)

        icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # ---- Header ----------------------------------------------------------------

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=0, height=64)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        logo_box = ctk.CTkFrame(header, fg_color=T.ACCENT,
                                width=44, height=44, corner_radius=8)
        logo_box.grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")
        logo_box.grid_propagate(False)
        ctk.CTkLabel(
            logo_box, text="М", text_color=T.BG_DARK,
            font=ctk.CTkFont(T.FONT_SANS, 20, "bold")
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            title_col, text="Мониторинг рабочего дня",
            font=ctk.CTkFont(T.FONT_SANS, 14, "bold"),
            text_color=T.TEXT_PRIMARY
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col, text="Учёт времени и активности",
            font=ctk.CTkFont(T.FONT_SANS, 10), text_color=T.TEXT_MUTED
        ).pack(anchor="w")

        clock_col = ctk.CTkFrame(header, fg_color="transparent")
        clock_col.grid(row=0, column=2, padx=16, sticky="e")
        self.lbl_time = ctk.CTkLabel(
            clock_col, text="00:00:00",
            font=ctk.CTkFont(T.FONT_MONO, 20, "bold"), text_color=T.ACCENT
        )
        self.lbl_time.pack(anchor="e")
        self.lbl_date = ctk.CTkLabel(
            clock_col, text="",
            font=ctk.CTkFont(T.FONT_SANS, 10), text_color=T.TEXT_MUTED
        )
        self.lbl_date.pack(anchor="e")

    # ---- Sidebar ---------------------------------------------------------------

    def _build_sidebar(self):
        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.grid(row=1, column=0, sticky="nsew")
        main_area.grid_rowconfigure(0, weight=1)
        main_area.grid_columnconfigure(1, weight=1)
        self._main_area = main_area

        sidebar = ctk.CTkFrame(main_area, fg_color=T.BG_SIDEBAR,
                               width=170, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(10, weight=1)
        self._sidebar = sidebar

        btn_cfg = dict(
            anchor="w", height=38, corner_radius=6,
            font=ctk.CTkFont(T.FONT_SANS, 12),
            fg_color="transparent",
            hover_color=T.BG_CARD,
            text_color=T.TEXT_SECONDARY
        )

        self._nav_btns = {}
        for row, (key, icon, label) in enumerate([
            ("workday",      "⏱", "Фото рабочего дня"),
            ("achievements", "🏆", "Достижения"),
            ("settings",     "⚙", "Настройки"),
        ]):
            btn = ctk.CTkButton(
                sidebar, text=f"  {icon}  {label}",
                command=lambda k=key: self._show_tab(k),
                **btn_cfg
            )
            btn.grid(row=row, column=0, sticky="ew",
                     padx=6, pady=(6 if row == 0 else 2, 0))
            self._nav_btns[key] = btn

        # Separator
        ctk.CTkFrame(sidebar, fg_color=T.BORDER, height=1).grid(
            row=10, column=0, sticky="ew", padx=8, pady=8
        )

        # Report now button (generates without marking done -> auto-generates tomorrow too)
        self.btn_report_now = ctk.CTkButton(
            sidebar, text="📊 Отчёт сейчас",
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER, text_color="#ffffff",
            height=30, corner_radius=6,
            font=ctk.CTkFont(T.FONT_SANS, 11),
            command=self._on_report_now
        )
        self.btn_report_now.grid(row=11, column=0, sticky="ew",
                                 padx=6, pady=(0, 4))

        # End day button
        self.btn_end_day = ctk.CTkButton(
            sidebar, text="⏹ Завершить день",
            fg_color=T.BG_CARD, hover_color=T.DANGER,
            text_color=T.TEXT_MUTED,
            height=32, corner_radius=6,
            font=ctk.CTkFont(T.FONT_SANS, 11),
            command=self._on_end_day
        )
        self.btn_end_day.grid(row=12, column=0, sticky="ew",
                              padx=6, pady=(0, 10))

        self._update_day_buttons()

    # ---- Content ---------------------------------------------------------------

    def _build_content(self):
        content = ctk.CTkFrame(self._main_area,
                               fg_color=T.BG_DARK, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        self._content = content

        self._tabs = {
            "workday": WorkdayTab(
                content, self.tracker,
                on_day_change=self._update_day_buttons   # callback for auto-start
            ),
            "achievements": AchievementsTab(content, self.db),
            "settings":     SettingsTab(content, self.db),
        }
        for tab in self._tabs.values():
            tab.grid(row=0, column=0, sticky="nsew")
            tab.grid_remove()

    # ---- Tab switching ---------------------------------------------------------

    def _show_tab(self, name: str):
        for key, tab in self._tabs.items():
            if key == name:
                tab.grid()
            else:
                tab.grid_remove()

        for key, btn in self._nav_btns.items():
            btn.configure(
                fg_color=T.BG_CARD if key == name else "transparent",
                text_color=T.TEXT_PRIMARY if key == name else T.TEXT_SECONDARY
            )
        self._active_tab = name

    # ---- Day management --------------------------------------------------------

    def _on_end_day(self):
        ok, msg = self.tracker.end_day()
        if ok:
            self._update_day_buttons()
            self._tabs["workday"].on_day_ended()
            # End day generates AND marks done (day is officially over)
            self._generate_for_dates([datetime.now().strftime('%Y-%m-%d')],
                                     mark_done=True)

    def _update_day_buttons(self):
        """Updates sidebar button states based on day_started flag."""
        if self.tracker.day_started:
            self.btn_end_day.configure(
                state="normal",
                fg_color=T.DANGER, hover_color=T.DANGER_H,
                text_color="#ffffff"
            )
        else:
            self.btn_end_day.configure(
                state="disabled",
                fg_color=T.BG_CARD, text_color=T.TEXT_MUTED
            )

    # ---- Reports ---------------------------------------------------------------

    def _check_pending_reports(self):
        """On startup: generate reports for past dates that have no report."""
        dates = self.db.get_dates_pending_report()
        if dates:
            self._generate_for_dates(dates, mark_done=True)

    def _on_report_now(self):
        """
        Generates today's report immediately for preview/testing.
        Does NOT mark as done -> auto-generation will still run tomorrow.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        self._generate_for_dates([today], mark_done=False)

    def _generate_for_dates(self, dates: list, mark_done: bool = True):
        from core.config import load_config
        cfg      = load_config()
        login    = cfg.get('login') or 'user'
        gdrive   = cfg.get('google_drive_path') or str(Path.home() / "Documents" / "WorkdayReports")

        reporter  = ExcelReporter(self.db)
        generated = []
        for date_str in dates:
            try:
                path = reporter.generate(date_str, login, gdrive)
                if mark_done:
                    self.db.mark_report_done(date_str)
                generated.append(path)
            except Exception as e:
                print(f"Report error {date_str}: {e}")

        if generated:
            names      = "\n".join(Path(p).name for p in generated)
            save_dir   = str(Path(gdrive) / login)
            label      = "" if mark_done else " (предварительный)"
            from tkinter import messagebox
            messagebox.showinfo(
                f"Отчёт сформирован{label}",
                f"Файл:\n{names}\n\nПапка: {save_dir}"
            )

    # ---- Clock -----------------------------------------------------------------

    def _update_clock(self):
        now = datetime.now()
        new_time = now.strftime('%H:%M:%S')
        new_date = (f"{now.day} {MONTHS_RU[now.month-1]} {now.year}, "
                    f"{DAYS_RU[now.weekday()]}")

        if self.lbl_time.cget("text") != new_time:
            self.lbl_time.configure(text=new_time)
        if self.lbl_date.cget("text") != new_date:
            self.lbl_date.configure(text=new_date)

        self.after(1000, self._update_clock)

    # ---- Close -----------------------------------------------------------------

    def _on_close(self):
        self.monitor.stop()
        self.destroy()
