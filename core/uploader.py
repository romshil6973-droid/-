"""
Модуль загрузки отчётов на сервер — WorkdayMonitor v2.0.
"""
import os
import shutil
import logging
import requests
import urllib3
from core.config import load_config, get_pending_dir

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
log = logging.getLogger(__name__)

def check_server() -> bool:
    cfg = load_config()
    try:
        r = requests.get(f"{cfg['server_url']}/health",
                         headers={"X-API-Token": cfg['api_token']},
                         timeout=5, verify=False)
        return r.status_code == 200
    except Exception:
        return False

def upload_report(filepath: str, login: str) -> bool:
    cfg = load_config()
    url = f"{cfg['server_url']}/upload/{login}"
    headers = {"X-API-Token": cfg['api_token']}
    try:
        with open(filepath, "rb") as f:
            files = {"file": (os.path.basename(filepath), f, "application/octet-stream")}
            r = requests.post(url, files=files, headers=headers, timeout=30, verify=False)
        if r.status_code == 200:
            log.info("Отчёт отправлен: %s", os.path.basename(filepath))
            return True
        log.warning("Сервер вернул %s", r.status_code)
        _save_to_pending(filepath)
        return False
    except Exception as e:
        log.warning("Ошибка отправки (%s), сохранён в pending", e)
        _save_to_pending(filepath)
        return False

def retry_pending_uploads() -> int:
    cfg = load_config()
    login = cfg.get('login', '')
    if not login:
        return 0
    pending_dir = get_pending_dir()
    sent = 0
    for filename in list(os.listdir(pending_dir)):
        filepath = os.path.join(pending_dir, filename)
        if not os.path.isfile(filepath):
            continue
        if upload_report(filepath, login):
            try:
                os.remove(filepath)
            except OSError:
                pass
            sent += 1
    return sent

def pending_count() -> int:
    d = get_pending_dir()
    return sum(1 for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)))

def _save_to_pending(filepath: str) -> None:
    pending_dir = get_pending_dir()
    dest = os.path.join(pending_dir, os.path.basename(filepath))
    if not os.path.exists(dest):
        try:
            shutil.copy2(filepath, dest)
        except OSError as e:
            log.error("Не удалось сохранить в pending: %s", e)
