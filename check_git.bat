@echo off
chcp 65001 > nul
echo Проверка Git...
git --version
if %errorlevel% neq 0 (
    echo.
    echo РЕЗУЛЬТАТ: Git НЕ установлен.
    echo Нужно установить: https://git-scm.com/download/win
) else (
    echo.
    echo РЕЗУЛЬТАТ: Git установлен.
)
pause
