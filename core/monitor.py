"""
Фоновый монитор активности компьютера.
Запускается в отдельном потоке-демоне.
Не трогает UI — только пишет в БД.
"""

import threading
import ctypes
from datetime import datetime

from .database import Database

# Порог простоя (секунды) для фиксации "Режим ожидания"
IDLE_THRESHOLD = 300   # 5 минут
# Интервал опроса активного окна (секунды)
POLL_INTERVAL = 5

# Пробуем импортировать Windows API
try:
    import win32gui
    import win32process
    import psutil
    _WIN32_OK = True
except ImportError:
    _WIN32_OK = False


def get_idle_seconds() -> float:
    """Секунд с момента последнего ввода мыши/клавиатуры (только Windows)."""
    if not _WIN32_OK:
        return 0.0
    try:
        class _LASTINPUT(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
        li = _LASTINPUT()
        li.cbSize = ctypes.sizeof(li)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(li))
        return (ctypes.windll.kernel32.GetTickCount() - li.dwTime) / 1000.0
    except Exception:
        return 0.0


def get_active_window() -> tuple[str, str]:
    """
    Возвращает (имя_приложения, заголовок_окна) текущего активного окна.
    Если определить не удаётся — ('Неизвестно', '').
    """
    if not _WIN32_OK:
        return "Мониторинг недоступен", ""
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            # Убираем .exe для читабельности
            app_name = proc.name().removesuffix('.exe')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            app_name = "Неизвестно"
        return app_name, title
    except Exception:
        return "Неизвестно", ""


class ActivityMonitor:
    """
    Отслеживает активное окно каждые POLL_INTERVAL секунд.
    При смене окна закрывает предыдущую запись и открывает новую.
    Простой > IDLE_THRESHOLD — пишется как "Режим ожидания".
    """

    def __init__(self, db: Database):
        self.db = db
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

        # Текущая активность
        self._cur_app: str | None = None
        self._cur_title: str | None = None
        self._cur_type: str | None = None
        self._cur_id: int | None = None

    def start(self):
        """Запускает мониторинг в фоновом потоке."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="ActivityMonitor", daemon=True
        )
        self._thread.start()

    def stop(self):
        """Останавливает мониторинг и закрывает текущую запись."""
        self._stop.set()
        self._close_current()

    def _loop(self):
        """Основной цикл опроса."""
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception:
                pass  # Не прерываем мониторинг из-за разовых ошибок
            self._stop.wait(POLL_INTERVAL)

    def _tick(self):
        """Один шаг опроса: определяем текущую активность и обновляем БД."""
        idle = get_idle_seconds()
        is_idle = idle >= IDLE_THRESHOLD

        if is_idle:
            app   = "Режим ожидания"
            title = f"Простой {int(idle // 60)} мин"
            atype = "idle"
        else:
            app, title = get_active_window()
            atype = "app"

        # Если приложение сменилось — закрываем старую запись, открываем новую
        if app != self._cur_app or atype != self._cur_type:
            self._close_current()
            now = datetime.now()
            self._cur_app   = app
            self._cur_title = title
            self._cur_type  = atype
            self._cur_id    = self.db.log_activity_start(app, title, now, atype)

    def _close_current(self):
        """Закрывает текущую запись активности."""
        if self._cur_id is not None:
            self.db.log_activity_end(self._cur_id, datetime.now())
            self._cur_id = None
