@echo off
echo =============================================
echo  Установка зависимостей WorkdayMonitor
echo =============================================

cd /d "%~dp0"

python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo =============================================
echo  Установка завершена!
echo  Для запуска используйте run.bat
echo =============================================
pause
