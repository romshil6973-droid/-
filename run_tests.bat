@echo off
echo =============================================
echo  Запуск тестов WorkdayMonitor
echo =============================================
cd /d "%~dp0"
python -m pytest tests/ -v --tb=short
pause
