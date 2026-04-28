@echo off
set "PROJECT_DIR=E:\ProjectDev\cli"
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "SCRIPT_FILE=%PROJECT_DIR%\app\settings_standalone.py"

cd /d "%PROJECT_DIR%"

wt.exe -d "%PROJECT_DIR%" "%PYTHON_EXE%" "%SCRIPT_FILE%"