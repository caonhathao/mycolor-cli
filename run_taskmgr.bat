@echo off
cd /d "%~dp0"
call .venv\Scripts\python.exe taskmgr_standalone.py
pause