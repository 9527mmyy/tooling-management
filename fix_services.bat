@echo off
chcp 65001 >nul
set LOG=D:\tooling-management\fix_log.txt
echo ===== FIX START %date% %time% ===== > "%LOG%"
echo [1/3] 复制 nssm 到 System32（稳定位置）... >> "%LOG%"
copy /Y "D:\tooling-management\nssm\nssm.exe" "%SystemRoot%\System32\nssm.exe" >> "%LOG%" 2>&1
echo [2/3] 修正三个服务的二进制路径为 System32\nssm.exe... >> "%LOG%"
for %%S in (tooling-management process-dev cost-estimation) do (
  sc config %%S binpath= "%SystemRoot%\System32\nssm.exe" >> "%LOG%" 2>&1
)
echo [3/3] 启动三个服务... >> "%LOG%"
for %%S in (tooling-management process-dev cost-estimation) do (
  net start %%S >> "%LOG%" 2>&1
)
echo ===== FIX END ===== >> "%LOG%"
type "%LOG%"
pause
