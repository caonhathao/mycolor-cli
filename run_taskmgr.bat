@echo off
set "PROJECT_DIR=E:\ProjectDev\cli"
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "SCRIPT_FILE=%PROJECT_DIR%\app\taskmgr_standalone.py"
set "LOG_FILE=%PROJECT_DIR%\logs\mw_crash.log"

cd /d "%PROJECT_DIR%"

title MYCOLOR CLI - Task Manager

"%PYTHON_EXE%" "%SCRIPT_FILE%" %* > "%LOG_FILE%" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [CRASH DETECTED] Check logs/mw_crash.log for details:
    type "%LOG_FILE%"
)

pause