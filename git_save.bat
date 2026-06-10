@echo off
chcp 65001 > nul
cd /d "%~dp0"
set /p MSG="Комментарий к сохранению (Enter): "
if "%MSG%"=="" set MSG=update
git add .
git commit -m "%MSG%"
git push
echo.
echo Сохранено на GitHub!
pause
