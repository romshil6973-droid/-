@echo off
chcp 65001 > nul
echo =============================================
echo  Шаг 1: Создаём локальный Git-репозиторий
echo =============================================
cd /d "%~dp0"

git init
git config user.email "romshil69.73@gmail.com"
git config user.name "Roman"

git add .
git commit -m "feat: initial commit - WorkdayMonitor v0.1"

echo.
echo =============================================
echo  Локальный репозиторий создан!
echo.
echo  СЛЕДУЮЩИЙ ШАГ:
echo  Запустите файл github_connect.bat
echo  (после того как создадите репозиторий на GitHub)
echo =============================================
pause
