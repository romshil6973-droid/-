@echo off
chcp 65001 > nul
echo =============================================
echo  Подключение к GitHub
echo =============================================
cd /d "%~dp0"

set /p USERNAME="Введите ваш логин GitHub (Enter для подтверждения): "

git remote remove origin 2>nul
git remote add origin https://github.com/%USERNAME%/WorkdayMonitor.git
git branch -M main
git push -u origin main

echo.
echo =============================================
echo  Готово! Репозиторий доступен по адресу:
echo  https://github.com/%USERNAME%/WorkdayMonitor
echo.
echo  Для будущих сохранений используйте:
echo  git_save.bat
echo =============================================
pause
