@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
REM 系统安装的 Inno Setup 6 优先；未安装时回退到工程内置编译器目录。
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%CD%\tools\InnoSetup\ISCC.exe"

if not exist "%ISCC%" (
    echo.
    echo 未找到 Inno Setup 编译器，已检查：
    echo   C:\Program Files (x86)\Inno Setup 6\ISCC.exe
    echo   %CD%\tools\InnoSetup\ISCC.exe
    echo.
    pause
    exit /b 1
)

if not exist "build\dist\ToolingManagement\ToolingManagement.exe" (
    echo.
    echo 未找到程序产物，请先运行 build.bat 完成打包。
    echo.
    pause
    exit /b 1
)

echo 正在编译安装包...
"%ISCC%" /Qp installer.iss || goto err

echo.
echo ============================================================
echo   安装包已生成：
dir /b "build\installer\*.exe"
echo   目录：build\installer
echo ============================================================
pause
exit /b 0

:err
echo.
echo *** 安装包编译失败，请查看上方输出 ***
pause
exit /b 1
