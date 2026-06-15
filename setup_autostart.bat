@echo off
chcp 65001 >nul

SET PROJ=C:\Users\User\Downloads\06_Разработка ПО и Вайб-кодинг\06_14_Мониторинг\Мониторинг активности
SET PYTHON_DIR=C:\Users\User\AppData\Local\Python\pythoncore-3.14-64

REM --- Выбираем pythonw.exe (без окна) или python.exe как fallback ---
IF EXIST "%PYTHON_DIR%\pythonw.exe" (
    SET LAUNCHER=%PYTHON_DIR%\pythonw.exe
) ELSE (
    SET LAUNCHER=%PYTHON_DIR%\python.exe
    echo ВНИМАНИЕ: pythonw.exe не найден, используем python.exe
)

REM --- Создаём VBS-лаунчер (запуск без CMD-окна) ---
(
echo Set wsh = CreateObject^("WScript.Shell"^)
echo wsh.Run """%LAUNCHER%"" ""%PROJ%\main.py""", 0, False
) > "%PROJ%\launch_silent.vbs"

echo [1/3] launch_silent.vbs создан

REM --- Прописываем автозапуск в реестр ---
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v WorkdayMonitor /t REG_SZ /d "wscript.exe \"%PROJ%\launch_silent.vbs\"" /f >nul

echo [2/3] Автозапуск в реестре обновлён

REM --- Создаём ярлык на рабочем столе через PowerShell ---
powershell -NoProfile -Command ^
  "$wsh = New-Object -ComObject WScript.Shell;" ^
  "$sc = $wsh.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\WorkdayMonitor.lnk');" ^
  "$sc.TargetPath = 'wscript.exe';" ^
  "$sc.Arguments = '/b \"%PROJ%\launch_silent.vbs\"';" ^
  "$sc.WorkingDirectory = '%PROJ%';" ^
  "$sc.Description = 'WorkdayMonitor — мониторинг рабочего дня';" ^
  "$sc.Save();"

echo [3/3] Ярлык на рабочем столе создан

echo.
echo Готово! Теперь:
echo  - Двойной клик по ярлыку WorkdayMonitor на рабочем столе — запустит без CMD
echo  - При перезагрузке Windows — тоже запустится без CMD
echo  - Ярлык можно закрепить на панели задач (правой кнопкой - Закрепить)
echo.
pause
