@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
REM 依赖原系统 backend 的 venv（含 pyinstaller / pywebview / pillow）。
REM 目录约定：本工程在原系统仓库的 desktop\ 子目录，venv 位于 ..\backend\venv。
set "PY=%~dp0..\backend\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo [1/5] 同步源码快照（原系统只读）...
"%PY%" sync_src.py || goto err

echo.
echo [2/5] 生成应用图标...
"%PY%" make_icon.py || goto err

echo.
echo [3/5] 清理旧产物...
if exist build\dist rmdir /s /q build\dist
if exist build\work rmdir /s /q build\work

echo.
echo [4/5] PyInstaller 构建（onedir）...
"%PY%" -m PyInstaller --clean --noconfirm --distpath build\dist --workpath build\work tooling.spec || goto err

echo.
echo [5/5] 生成完整性校验清单（防篡改）...
"%PY%" make_integrity.py || goto err

echo.
echo ============================================================
echo   构建完成
echo   可执行文件: build\dist\ToolingManagement\ToolingManagement.exe
echo   完整性清单: build\dist\ToolingManagement\integrity.json
echo ============================================================
pause
exit /b 0

:err
echo.
echo *** 构建失败，请查看上方输出 ***
pause
exit /b 1
