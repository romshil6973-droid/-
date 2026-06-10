"""
Workday tab - operation input, controls (START/PAUSE/STOP), log.
"""

import hashlib
import customtkinter as ctk
from datetime import datetime

from core.tracker import WorkdayTracker, TrackerState
from . import theme as T


class WorkdayTab(ctk.CTkFrame):
    """Main working tab."""

    def __init__(self, parent, tracker: WorkdayTracker,
                 on_day_change=None, **kwargs):
        super().__init__(parent, fg_color=T.BG_DARK, **kwargs)
        self.tracker = tracker
        # Callback called when day auto-starts (to update sidebar buttons)
        self._on_day_change = on_day_change
        # Hash of last rendered sessions - skip rebuild if unchanged
        self._last_log_hash = ""
        self._build()
        self._refresh_log()
        self._tick_timer()

    # ---- Build UI --------------------------------------------------------------

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # -- Operation input block -----------------------------------------------
        input_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=8)
        input_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        input_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            input_frame, text="Название операции",
            font=ctk.CTkFont(T.FONT_SANS, 11), text_color=T.TEXT_MUTED
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

        self.op_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Введите, что вы делаете...",
            fg_color=T.BG_INPUT, border_color=T.BORDER, text_color=T.TEXT_PRIMARY,
            font=ctk.CTkFont(T.FONT_SANS, 13),
            height=36, corner_radius=6
        )
        self.op_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 10))
        self.op_entry.bind("<Return>", lambda e: self._on_start())

        # -- Control buttons -----------------------------------------------------
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=4)

        btn_cfg = dict(height=34, corner_radius=6,
                       font=ctk.CTkFont(T.FONT_SANS, 12, "bold"))

        self.btn_start = ctk.CTkButton(
            ctrl_frame, text="▶  СТАРТ",
            fg_color=T.SUCCESS, hover_color=T.SUCCESS_H,
            text_color="#000000", command=self._on_start, **btn_cfg
        )
        self.btn_start.pack(side="left", padx=(0, 6))

        self.btn_pause = ctk.CTkButton(
            ctrl_frame, text="⏸  ПАУЗА",
            fg_color=T.WARNING, hover_color=T.WARNING_H,
            text_color="#000000", command=self._on_pause, **btn_cfg
        )
        self.btn_pause.pack(side="left", padx=(0, 6))

        self.btn_stop = ctk.CTkButton(
            ctrl_frame, text="⏹  ЗАВЕРШИТЬ",
            fg_color=T.DANGER, hover_color=T.DANGER_H,
            command=self._on_stop, **btn_cfg
        )
        self.btn_stop.pack(side="left", padx=(0, 16))

        # Operation timer
        self.lbl_timer = ctk.CTkLabel(
            ctrl_frame, text="00:00:00",
            font=ctk.CTkFont(T.FONT_MONO, 16, "bold"),
            text_color=T.TEXT_MUTED
        )
        self.lbl_timer.pack(side="left")

        # Voice input button (Win+H)
        self.btn_voice = ctk.CTkButton(
            ctrl_frame, text="🎤",
            fg_color=T.BG_CARD, hover_color=T.BORDER,
            width=36, height=34, corner_radius=6,
            command=self._on_voice,
            font=ctk.CTkFont(size=14)
        )
        self.btn_voice.pack(side="right")

        # -- Log header ----------------------------------------------------------
        log_header = ctk.CTkFrame(self, fg_color="transparent")
        log_header.grid(row=2, column=0, sticky="ew", padx=12, pady=(6, 0))

        ctk.CTkLabel(
            log_header, text="Журнал операций",
            font=ctk.CTkFont(T.FONT_SANS, 11, "bold"),
            text_color=T.TEXT_SECONDARY
        ).pack(side="left")

        self.lbl_total = ctk.CTkLabel(
            log_header, text="Итого: 00:00:00",
            font=ctk.CTkFont(T.FONT_MONO, 11), text_color=T.TEXT_MUTED
        )
        self.lbl_total.pack(side="right")

        # Scrollable log
        self.log_frame = ctk.CTkScrollableFrame(
            self, fg_color=T.BG_CARD, corner_radius=8
        )
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(4, 8))

        # Status bar
        self.lbl_status = ctk.CTkLabel(
            self, text="Готов к работе",
            font=ctk.CTkFont(T.FONT_SANS, 11), text_color=T.TEXT_MUTED
        )
        self.lbl_status.grid(row=4, column=0, pady=(0, 4))

        self._update_buttons()

    # ---- Button handlers -------------------------------------------------------

    def _on_start(self):
        op_text = self.op_entry.get().strip()
        day_was_started = self.tracker.day_started

        if self.tracker.state == TrackerState.PAUSED:
            ok, msg = self.tracker.start_operation(self.tracker.current_operation)
        else:
            ok, msg = self.tracker.start_operation(op_text)

        self._update_status(msg, ok)
        if ok and self.tracker.state == TrackerState.RUNNING:
            self.op_entry.delete(0, "end")
        self._update_buttons()

        # If day was auto-started - notify sidebar to update buttons
        if ok and not day_was_started and self.tracker.day_started:
            if self._on_day_change:
                self._on_day_change()

    def _on_pause(self):
        ok, msg = self.tracker.pause_operation()
        self._update_status(msg, ok)
        self._update_buttons()

    def _on_stop(self):
        ok, msg = self.tracker.stop_operation()
        self._update_status(msg, ok)
        self._update_buttons()
        self._refresh_log(force=True)

    def _on_voice(self):
        """Activates Windows voice input (Win+H)."""
        try:
            import win32api, win32con
            self.op_entry.focus_set()
            win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
            win32api.keybd_event(ord('H'), 0, 0, 0)
            win32api.keybd_event(ord('H'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
            self._update_status("Говорите... (Windows Voice Typing активирован)", True)
        except Exception:
            self._update_status("Голосовой ввод: нажмите Win+H вручную", False)

    # ---- UI state update -------------------------------------------------------

    def _update_buttons(self):
        state   = self.tracker.state
        idle    = state == TrackerState.IDLE
        running = state == TrackerState.RUNNING
        paused  = state == TrackerState.PAUSED

        self.btn_start.configure(state="normal" if (idle or paused) else "disabled")
        self.btn_pause.configure(state="normal" if running else "disabled")
        self.btn_stop.configure(state="normal" if (running or paused) else "disabled")

        if running:
            self.lbl_timer.configure(text_color=T.SUCCESS)
        elif paused:
            self.lbl_timer.configure(text_color=T.WARNING)
        else:
            self.lbl_timer.configure(text_color=T.TEXT_MUTED)

    def _update_status(self, msg: str, ok: bool):
        color = T.TEXT_SECONDARY if ok else T.DANGER
        self.lbl_status.configure(text=msg, text_color=color)

    def _tick_timer(self):
        """Updates operation timer every second."""
        secs = self.tracker.get_elapsed_seconds()
        new_text = WorkdayTracker.format_duration(secs)
        # Only configure if text changed - avoids unnecessary redraws
        if self.lbl_timer.cget("text") != new_text:
            self.lbl_timer.configure(text=new_text)
        self.after(1000, self._tick_timer)

    def _sessions_hash(self, sessions: list) -> str:
        """Returns a short hash of sessions data to detect changes."""
        key = str([(s.get('id'), s.get('status'), s.get('end_time'))
                   for s in sessions])
        return hashlib.md5(key.encode()).hexdigest()[:8]

    def _refresh_log(self, force: bool = False):
        """
        Rebuilds the operations log.
        Skips rebuild if data hasn't changed (prevents flickering).
        force=True always rebuilds (e.g. after stop).
        """
        today = datetime.now().strftime('%Y-%m-%d')
        sessions = self.tracker.db.get_work_sessions_for_date(today)

        new_hash = self._sessions_hash(sessions)
        if not force and new_hash == self._last_log_hash:
            return
        self._last_log_hash = new_hash

        # Rebuild
        for widget in self.log_frame.winfo_children():
            widget.destroy()

        if not sessions:
            ctk.CTkLabel(
                self.log_frame, text="Операций пока нет",
                text_color=T.TEXT_MUTED, font=ctk.CTkFont(T.FONT_SANS, 12)
            ).pack(pady=20)
        else:
            for s in reversed(sessions):
                self._add_log_entry(s)

        total = self.tracker.get_today_total_seconds()
        self.lbl_total.configure(
            text=f"Итого: {WorkdayTracker.format_duration(total)}"
        )

    def _add_log_entry(self, session: dict):
        """Adds one log row."""
        row = ctk.CTkFrame(self.log_frame, fg_color=T.BG_INPUT, corner_radius=6)
        row.pack(fill="x", padx=6, pady=3)
        row.grid_columnconfigure(1, weight=1)

        start = self._fmt_time(session.get('start_time'))
        end   = self._fmt_time(session.get('end_time'))
        dur   = WorkdayTracker.format_duration(
                    session.get('duration_seconds') or 0)
        op    = session.get('operation', '')
        done  = session.get('status') == 'completed'

        dot_color = T.SUCCESS if done else T.WARNING
        ctk.CTkLabel(
            row, text="●", text_color=dot_color, width=16,
            font=ctk.CTkFont(size=10)
        ).grid(row=0, column=0, padx=(8, 4), pady=6)

        ctk.CTkLabel(
            row, text=op, text_color=T.TEXT_PRIMARY,
            font=ctk.CTkFont(T.FONT_SANS, 12), anchor="w"
        ).grid(row=0, column=1, sticky="w", pady=6)

        time_text = (f"{start} → {end}  {dur}" if done
                     else f"{start} → ...")
        ctk.CTkLabel(
            row, text=time_text, text_color=T.TEXT_MUTED,
            font=ctk.CTkFont(T.FONT_MONO, 10)
        ).grid(row=0, column=2, padx=10, pady=6)

    @staticmethod
    def _fmt_time(ts: str | None) -> str:
        if not ts:
            return "—"
        try:
            return datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
        except ValueError:
            return ts

    def on_day_ended(self):
        """Called from main window on end-day click."""
        self._refresh_log(force=True)
