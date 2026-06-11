@echo off
cd /d "%~dp0\.."
set LOG=%~dp0build_log.txt
echo Build started > "%LOG%"

echo Installing PyInstaller...
pip install pyinstaller --quiet >> "%LOG%" 2>&1

echo Building EXE...
python -m PyInstaller _build\WorkdayMonitor.spec --distpath dist --workpath _build\work --noconfirm >> "%LOG%" 2>&1

if not exist "dist\WorkdayMonitor\WorkdayMonitor.exe" (
    echo ERROR: EXE build failed. See: %LOG%
    pause
    exit /b 1
)
echo EXE built OK.

if not exist "D:\Приложение для установки" mkdir "D:\Приложение для установки"
copy "Документы_ИС\04_Руководство_пользователя.docx" "D:\Приложение для установки\" 2>nul

echo Searching Inno Setup via registry...
set ISCC=
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\WOW6432Node\Jordan Russell\Inno Setup" /v RootPath 2^>nul') do set INNO_DIR=%%b
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Jordan Russell\Inno Setup" /v RootPath 2^>nul') do set INNO_DIR=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\SOFTWARE\Jordan Russell\Inno Setup" /v RootPath 2^>nul') do set INNO_DIR=%%b

if not "%INNO_DIR%"=="" (
    if exist "%INNO_DIR%\ISCC.exe" set ISCC=%INNO_DIR%\ISCC.exe
)

if exist "C:\Вайб-кодинг_Inno_Setup_6.7.1\ISCC.exe" set ISCC=C:\Вайб-кодинг_Inno_Setup_6.7.1\ISCC.exe
if "%ISCC%"=="" (
    for /f "delims=" %%i in ('where /r "%LOCALAPPDATA%" ISCC.exe 2^>nul') do set ISCC=%%i
)
if exist "C:\Вайб-кодинг_Inno_Setup_6.7.1\ISCC.exe" set ISCC=C:\Вайб-кодинг_Inno_Setup_6.7.1\ISCC.exe
if "%ISCC%"=="" (
    for /f "delims=" %%i in ('where /r "%APPDATA%" ISCC.exe 2^>nul') do set ISCC=%%i
)

echo ISCC: [%ISCC%] >> "%LOG%"
echo ISCC: [%ISCC%]

if exist "C:\Вайб-кодинг_Inno_Setup_6.7.1\ISCC.exe" set ISCC=C:\Вайб-кодинг_Inno_Setup_6.7.1\ISCC.exe
if "%ISCC%"=="" (
    echo.
    echo Inno Setup not found automatically.
    echo Enter full path to ISCC.exe manually:
    echo (Example: C:\Program Files ^(x86^)\Inno Setup 6\ISCC.exe)
    set /p ISCC="Path: "
)

if not exist "%ISCC%" (
    echo ERROR: ISCC.exe not found at [%ISCC%]
    pause
    exit /b 1
)

echo Running Inno Setup...
"%ISCC%" "_build\WorkdayMonitor.iss" >> "%LOG%" 2>&1
echo Inno Setup exit: %errorlevel% >> "%LOG%"

echo.
echo === DONE ===
dir "D:\Приложение для установки"
pause
