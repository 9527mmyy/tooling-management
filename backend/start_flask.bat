@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d D:\tooling-management\backend
ping -n 46 127.0.0.1 >nul
netstat -ano | findstr "0.0.0.0:5000" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo %date% %time% [INFO] already running, skip >> autostart.log
    exit /b 0
)
cscript //nologo run_hidden.vbs
echo %date% %time% [INFO] started >> autostart.log
