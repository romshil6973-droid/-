"""
Конфигурация WorkdayMonitor v2.0.
"""
import configparser
import os
import re
from pathlib import Path

SERVER_URL = "https://46.149.68.148"
API_TOKEN  = "SP2026secure"

def get_config_path() -> Path:
    app_data = Path(os.environ.get('APPDATA', Path.home())) / 'WorkdayMonitor'
    app_data.mkdir(exist_ok=True)
    return app_data / 'config.ini'

def get_pending_dir() -> Path:
    d = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'WorkdayMonitor' / 'pending'
    d.mkdir(parents=True, exist_ok=True)
    return d

def config_exists() -> bool:
    p = get_config_path()
    if not p.exists():
        return False
    return bool(load_config().get('login'))

def load_config() -> dict:
    cfg = configparser.ConfigParser()
    cfg.read(str(get_config_path()), encoding='utf-8')
    return {
        'login':      cfg.get('user',   'login',  fallback=''),
        'server_url': cfg.get('server', 'url',    fallback=SERVER_URL),
        'api_token':  cfg.get('server', 'token',  fallback=API_TOKEN),
    }

def save_config(login: str) -> None:
    cfg = configparser.ConfigParser()
    cfg['server'] = {'url': SERVER_URL, 'token': API_TOKEN}
    cfg['user']   = {'login': login}
    path = get_config_path()
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# WorkdayMonitor — файл конфигурации\n\n')
        cfg.write(f)

def validate_login(login: str) -> tuple:
    if not login:
        return False, "Логин не может быть пустым"
    if not re.match(r'^[a-z0-9_]{3,20}$', login):
        return False, "Только латиница (a–z), цифры (0–9), '_'. От 3 до 20 символов. Пример: shilov"
    return True, ""
