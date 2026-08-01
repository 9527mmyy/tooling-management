@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
set "ROOT=%~dp0"
set "SVC=ToolingManagement"

REM --- pick python interpreter (adjust for your machine) ---
set "PY="
if exist "%ROOT%venv\Scripts\python.exe" set "PY=%ROOT%venv\Scripts\python.exe"
if not defined PY if exist "C:\Users\CRUN\.workbuddy\binaries\python\envs\default\Scripts\python.exe" set "PY=C:\Users\CRUN\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not defined PY set "PY=python.exe"
REM On the deployment machine that uses QClaw's bundled python, uncomment the line below:
REM set "PY=C:\Program Files\QClaw\v0.2.35.624\resources\python\python.exe"

where nssm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] nssm not found. Install from https://nssm.cc and add to PATH, then re-run.
  pause
  exit /b 1
)

echo Registering Windows service %SVC% (port 5000) ...
nssm install %SVC% "%PY%"
nssm set %SVC% AppDirectory "%ROOT%"
nssm set %SVC% AppParameters "app.py"
nssm set %SVC% AppStdout "%ROOT%service.log"
nssm set %SVC% AppStderr "%ROOT%service.log"
nssm set %SVC% AppRotateFiles 1
nssm set %SVC% AppRotateBytes 1048576
nssm set %SVC% AppExit Default Restart
nssm set %SVC% Start SERVICE_DELAYED_AUTO_START
nssm set %SVC% DisplayName "Tooling Management"
nssm set %SVC% Description "Tooling fixture lifecycle management - Flask backend, auto-restart on crash"
nssm start %SVC%
echo Done. Check services.msc or run status.bat.
pause
