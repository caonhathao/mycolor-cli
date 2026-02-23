@echo off
set "PROJECT_DIR=E:\ProjectDev\cli"
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "SCRIPT_FILE=%PROJECT_DIR%\myworld.py"
set "LOG_FILE=%PROJECT_DIR%\mw_crash.log"

:: Ensure we're in project directory (critical when double-clicking)
cd /d "%PROJECT_DIR%"

:: 1. Reset log
echo [START LOG] %date% %time% > "%LOG_FILE%"

:: 2. Kiểm tra wt.exe
where wt.exe >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Dang mo Windows Terminal...
    :: start "" = empty title so arguments parse correctly
    start "" wt.exe -d "%PROJECT_DIR%" --title "MYCOLOR CLI" powershell.exe -NoProfile -NoLogo -NoExit -Command "& '%PYTHON_EXE%' '%SCRIPT_FILE%'"
    echo WT da mo. Dong tab WT de thoat.
) else (
    echo Khong tim thay WT, chay PowerShell truc tiep...
    powershell.exe -NoProfile -NoLogo -NoExit -Command "& '%PYTHON_EXE%' '%SCRIPT_FILE%'"
)

:: Keep window open so you can see any errors
pause