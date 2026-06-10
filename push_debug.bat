@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo --- Шаг 1: Проверка Git ---
git --version
pause

echo --- Шаг 2: Инициализация ---
git init
git config user.email "romshil69.73@gmail.com"
git config user.name "Roman"
pause

echo --- Шаг 3: Добавляем файлы ---
git add .
git status
pause

echo --- Шаг 4: Коммит ---
git commit -m "feat: initial commit - WorkdayMonitor v0.1"
pause

echo --- Шаг 5: Подключаем GitHub ---
git remote remove origin 2>nul
git remote add origin https://github.com/romshil6973-droid/WorkdayMonitor.git
git remote -v
pause

echo --- Шаг 6: Push ---
git push -u origin main
pause
