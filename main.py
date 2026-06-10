"""
Точка входа приложения «Мониторинг рабочего дня».
Запуск: python main.py
"""

import sys
import os

# Добавляем корневую папку проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app_window import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
