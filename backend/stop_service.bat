@echo off
set "SVC=ToolingManagement"
where nssm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] nssm not found.
  pause
  exit /b 1
)
nssm stop %SVC%
nssm remove %SVC% confirm
echo Service %SVC% stopped and removed.
pause
