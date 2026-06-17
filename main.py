"""
Точка входа приложения «Мониторинг рабочего дня».
Запуск: python main.py
"""

import sys
import os

# Добавляем корневую папку проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import config_exists


def main():
    # При первом запуске — показываем диалог настройки
    if not config_exists():
        import customtkinter as ctk
        from ui.setup_dialog import SetupDialog

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        root = ctk.CTk()
        root.withdraw()             # прячем пустое главное окно

        dlg = SetupDialog(root)
        root.wait_window(dlg)

        if dlg.result is None:
            # Пользователь отменил настройку — выходим
            root.destroy()
            sys.exit(0)

        root.destroy()

    # Запускаем основное приложение
    from ui.app_window import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
