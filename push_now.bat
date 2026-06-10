@echo off
cd /d "%~dp0"

set GIT=
if exist "C:\Program Files\Git\cmd\git.exe" set GIT=C:\Program Files\Git\cmd\git.exe
if exist "C:\Program Files (x86)\Git\cmd\git.exe" set GIT=C:\Program Files (x86)\Git\cmd\git.exe
if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe
if exist "%USERPROFILE%\AppData\Local\Programs\Git\cmd\git.exe" set GIT=%USERPROFILE%\AppData\Local\Programs\Git\cmd\git.exe

if "%GIT%"=="" (
    echo Git not found in common locations. Searching...
    for /f "delims=" %%i in ('where /r "C:\Program Files" git.exe 2^>nul') do set GIT=%%i
)

if "%GIT%"=="" (
    echo ERROR: git.exe not found. Please reinstall Git for Windows.
    pause
    exit /b 1
)

echo Found: %GIT%
"%GIT%" init
"%GIT%" config user.email "romshil69.73@gmail.com"
"%GIT%" config user.name "Roman"
"%GIT%" add .
"%GIT%" commit -m "feat: initial commit - WorkdayMonitor v0.1"
"%GIT%" remote remove origin 2>nul
"%GIT%" remote add origin https://github.com/romshil6973-droid/WorkdayMonitor.git
"%GIT%" branch -M main
"%GIT%" push -u origin main
echo.
echo === Done! https://github.com/romshil6973-droid/WorkdayMonitor ===
pause
