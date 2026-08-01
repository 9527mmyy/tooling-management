@echo off
chcp 65001 >nul
echo ===================================
echo   三系统状态检查 (工装/工艺/成本)
echo ===================================
echo.
echo [HTTP 在线状态]
for %%P in (5000 5001 5002) do (
  curl.exe -s -o nul -w "  端口 %%P : HTTP %%{http_code}\n" http://127.0.0.1:%%P/
)
echo.
echo [Windows 服务状态]
for %%S in (tooling-management process-dev cost-estimation) do (
  sc query %%S >nul 2>&1 && (sc query %%S | findstr /i "SERVICE_NAME STATE") || echo   %%S : 未注册服务
)
echo.
echo 局域网访问: http://172.16.120.79:端口/
pause
