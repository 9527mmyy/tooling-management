@echo off
chcp 65001 >nul
echo ============================================
echo   启动三系统 Windows 服务 (请右键以管理员运行)
echo ============================================
echo [1/2] 释放端口 5000/5001/5002（停残留进程）...
for %%P in (5000 5001 5002) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%P " ^| findstr LISTENING') do taskkill /PID %%A /F >nul 2>&1
)
timeout /t 2 >nul
echo [2/2] 启动服务...
net start tooling-management
net start process-dev
net start cost-estimation
echo.
echo 完成。可用 check_status.bat 验证在线状态。
pause
