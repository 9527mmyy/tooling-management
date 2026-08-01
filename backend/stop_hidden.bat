@echo off
echo Stopping tooling management on port 5000 (by port, safe for other apps) ...
for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr "LISTENING" ^| findstr /r ":5000[ ]"') do (
  echo Killing PID %%A
  taskkill /PID %%A /F >nul 2>nul
)
echo Done. Run status.bat to confirm.
