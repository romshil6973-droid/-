"""
Browser history reader for pulling URLs into reports.
Supports: Chrome, Edge (Chromium-based), Firefox, Yandex Browser.
"""

import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path


# -- Chrome epoch ----------------------------------------------------------
_CHROME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _chrome_ts_to_datetime(chrome_ts: int) -> datetime:
    """Convert Chrome timestamp (microseconds since 1601-01-01) to local datetime."""
    dt_utc = _CHROME_EPOCH + timedelta(microseconds=chrome_ts)
    return dt_utc.astimezone().replace(tzinfo=None)


def _firefox_ts_to_datetime(ff_ts: int) -> datetime:
    """Convert Firefox timestamp (microseconds since Unix epoch) to local datetime."""
    return datetime.fromtimestamp(ff_ts / 1_000_000)


# -- Path finders ----------------------------------------------------------

def _chromium_history_paths(vendor_dir: str) -> list:
    base = Path.home() / "AppData" / "Local" / vendor_dir / "User Data"
    paths = []
    if base.exists():
        p = base / "Default" / "History"
        if p.exists():
            paths.append(p)
        for prof in base.glob("Profile *"):
            h = prof / "History"
            if h.exists():
                paths.append(h)
    return paths


def _chrome_history_paths() -> list:
    return _chromium_history_paths("Google/Chrome")


def _edge_history_paths() -> list:
    return _chromium_history_paths("Microsoft/Edge")


def _yandex_history_paths() -> list:
    return _chromium_history_paths("Yandex/YandexBrowser")


def _firefox_history_paths() -> list:
    base = Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"
    paths = []
    if base.exists():
        for prof in base.iterdir():
            h = prof / "places.sqlite"
            if h.exists():
                paths.append(h)
    return paths


# -- Internal URL filter ---------------------------------------------------

_SKIP = ("chrome://", "chrome-extension://", "about:", "data:", "edge://")


def _is_internal(url: str) -> bool:
    return any(url.startswith(p) for p in _SKIP)


# -- Readers ---------------------------------------------------------------

def _read_chromium_history(db_path, date_str: str) -> list:
    """Read Chrome/Edge/Yandex history for a given date. Returns [(datetime, url), ...]."""
    results = []
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        shutil.copy2(db_path, tmp_path)
        conn = sqlite3.connect("file:" + tmp_path + "?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT v.visit_time, u.url "
                "FROM visits v JOIN urls u ON v.url = u.id "
                "ORDER BY v.visit_time"
            ).fetchall()
            for ts, url in rows:
                try:
                    if _is_internal(url):
                        continue
                    dt = _chrome_ts_to_datetime(ts)
                    if dt.strftime("%Y-%m-%d") == date_str:
                        results.append((dt, url))
                except Exception:
                    pass
        finally:
            conn.close()
    except Exception:
        pass
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
    return results


def _read_firefox_history(db_path, date_str: str) -> list:
    """Read Firefox history for a given date. Returns [(datetime, url), ...]."""
    results = []
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        shutil.copy2(db_path, tmp_path)
        conn = sqlite3.connect("file:" + tmp_path + "?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT v.visit_date, p.url "
                "FROM moz_historyvisits v JOIN moz_places p ON v.place_id = p.id "
                "ORDER BY v.visit_date"
            ).fetchall()
            for ts, url in rows:
                try:
                    if _is_internal(url):
                        continue
                    dt = _firefox_ts_to_datetime(ts)
                    if dt.strftime("%Y-%m-%d") == date_str:
                        results.append((dt, url))
                except Exception:
                    pass
        finally:
            conn.close()
    except Exception:
        pass
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
    return results


# -- Public API ------------------------------------------------------------

BROWSER_PROCESSES = {
    "chrome", "msedge", "firefox", "opera", "brave", "vivaldi",
    "chromium", "yandex", "browser"
}


def is_browser(app_name: str) -> bool:
    """Return True if the process name belongs to a known browser."""
    return app_name.lower() in BROWSER_PROCESSES


def load_browser_history(date_str: str) -> list:
    """
    Load history from all installed browsers for the given date (YYYY-MM-DD).
    Returns [(datetime, url), ...] sorted by time, duplicates removed.
    """
    entries = []
    for path in _chrome_history_paths():
        entries.extend(_read_chromium_history(path, date_str))
    for path in _edge_history_paths():
        entries.extend(_read_chromium_history(path, date_str))
    for path in _yandex_history_paths():
        entries.extend(_read_chromium_history(path, date_str))
    for path in _firefox_history_paths():
        entries.extend(_read_firefox_history(path, date_str))

    entries.sort(key=lambda x: x[0])

    # Remove consecutive duplicates
    deduped = []
    prev = None
    for dt, url in entries:
        if url != prev:
            deduped.append((dt, url))
            prev = url
    return deduped


def get_urls_in_window(history: list, start_dt: datetime, end_dt: datetime) -> list:
    """
    Return unique URLs from history visited in [start_dt, end_dt].
    history must be pre-loaded via load_browser_history().
    """
    urls = []
    seen = set()
    for dt, url in history:
        if start_dt <= dt <= end_dt:
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls
