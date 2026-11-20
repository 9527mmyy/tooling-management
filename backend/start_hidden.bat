@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

REM Resolve pythonw: project venv -> system python
set "PY="
if exist "%~dp0venv\Scripts\pythonw.exe" set "PY=%~dp0venv\Scripts\pythonw.exe"
if not defined PY set "PY=pythonw"

echo Starting tooling management on port 5000 (background, no console window)...
start "" "%PY%" app.py
echo Started. To stop: end pythonw in Task Manager, or run stop_hidden.bat
echo Tip: check status with status.bat
