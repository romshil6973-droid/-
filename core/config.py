"""
Конфигурация WorkdayMonitor.

Хранит логин сотрудника и путь к папке Google Drive.
Файл: AppData\\WorkdayMonitor\\config.ini
"""

import configparser
import os
import re
from pathlib import Path


def get_config_path() -> Path:
    """Путь к файлу config.ini (рядом с базой данных)."""
    app_data = Path(os.environ.get('APPDATA', Path.home())) / 'WorkdayMonitor'
    app_data.mkdir(exist_ok=True)
    return app_data / 'config.ini'


def config_exists() -> bool:
    """Возвращает True, если конфиг заполнен (логин и путь не пустые)."""
    p = get_config_path()
    if not p.exists():
        return False
    cfg = load_config()
    return bool(cfg.get('login')) and bool(cfg.get('google_drive_path'))


def load_config() -> dict:
    """
    Загружает конфиг из файла.

    Returns:
        {'login': str, 'google_drive_path': str}
    """
    cfg = configparser.ConfigParser()
    cfg.read(str(get_config_path()), encoding='utf-8')
    return {
        'login':             cfg.get('user', 'login',             fallback=''),
        'google_drive_path': cfg.get('user', 'google_drive_path', fallback=''),
    }


def save_config(login: str, google_drive_path: str) -> None:
    """Сохраняет конфиг в файл."""
    cfg = configparser.ConfigParser()
    cfg['user'] = {
        'login':             login,
        'google_drive_path': google_drive_path,
    }
    path = get_config_path()
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# WorkdayMonitor — файл конфигурации\n')
        f.write('# login              : логин сотрудника (латиница, нижний регистр)\n')
        f.write('# google_drive_path  : путь к папке /Компания/Отчеты_менеджеров/\n\n')
        cfg.write(f)


def validate_login(login: str) -> tuple[bool, str]:
    """
    Проверяет логин.

    Returns:
        (True, '')            — логин корректен
        (False, 'сообщение') — ошибка
    """
    if not login:
        return False, "Логин не может быть пустым"
    if not re.match(r'^[a-z0-9_]{3,20}$', login):
        return False, "Только латиница (a–z), цифры (0–9), '_'. От 3 до 20 символов. Пример: shilov"
    return True, ""


def validate_gdrive_path(path: str) -> tuple[bool, str]:
    """
    Проверяет путь к папке Google Drive.

    Returns:
        (True, '')            — путь корректен
        (False, 'сообщение') — ошибка
    """
    if not path:
        return False, "Путь не может быть пустым"
    p = Path(path)
    if not p.exists():
        return False, (
            "Папка не найдена. Проверьте:\n"
            "1. Google Drive Desktop установлен и запущен?\n"
            "2. Путь указан правильно?"
        )
    if not p.is_dir():
        return False, "Указан файл, а не папка"
    return True, ""
