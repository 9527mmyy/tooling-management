@echo off
setlocal enabledelayedexpansion
title Tooling System - Port Status
echo ============================================
echo   Tooling Management - Port Status
echo ============================================
for %%P in (5000) do (
  set "PID="
  for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr "LISTENING" ^| findstr /r ":%%P[ ]"') do (
    set "PID=%%A"
  )
  if defined PID (
    echo [%%P] RUNNING  PID=!PID!
  ) else (
    echo [%%P] NOT RUNNING
  )
)
echo ============================================
echo 5000=tooling management
echo Press any key to exit...
pause >nul
