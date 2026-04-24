@echo off
set "PROJECT_DIR=E:\ProjectDev\cli"
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "SCRIPT_FILE=%PROJECT_DIR%\app\myworld.py"
set "LOG_FILE=%PROJECT_DIR%\logs\mw_crash.log"

cd /d "%PROJECT_DIR%"

title MYCOLOR CLI

"%PYTHON_EXE%" "%SCRIPT_FILE%" %* > "%LOG_FILE%" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [CRASH DETECTED] Check mw_crash.log for details:
    type "%LOG_FILE%"
)

pause