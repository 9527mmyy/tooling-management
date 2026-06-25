@echo off
chcp 65001 >nul
echo ========================================
echo   工装管理系统 - 环境安装
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 检测到 Python:
python --version

:: 安装依赖
echo.
echo [2/3] 安装 Python 依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [3/3] 初始化数据库...
python -c "from app import app; print('数据库初始化完成')"

echo.
echo ========================================
echo   安装完成！
echo   请双击 start.bat 启动系统
echo ========================================
pause
