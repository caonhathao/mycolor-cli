@echo off
set "PROJECT_DIR=E:\ProjectDev\cli"
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "SCRIPT_FILE=%PROJECT_DIR%\myworld.py"
set "LOG_FILE=%PROJECT_DIR%\mw_crash.log"

:: Nhảy vào thư mục dự án
cd /d "%PROJECT_DIR%"

:: Ép kích thước cửa sổ ngay lập tức
title MYCOLOR CLI - LAPTOP-J2I22MSG

:: Chạy Python và gộp stdout + stderr ( > log 2>&1)
:: Thêm %* để nhận mọi tham số truyền từ bên ngoài vào (như --hold nếu có)
"%PYTHON_EXE%" "%SCRIPT_FILE%" %* > "%LOG_FILE%" 2>&1

:: Nếu có lỗi (ERRORLEVEL != 0), hiển thị nội dung log ra màn hình
if %ERRORLEVEL% NEQ 0 (
    echo [CRASH DETECTED] Check mw_crash.log for details:
    type "%LOG_FILE%"
)

pause