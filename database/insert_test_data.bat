@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ACWL-AI 测试数据插入工具 - Windows批处理脚本
REM 用于简化测试数据插入过程

echo.
echo ========================================
echo    ACWL-AI 测试数据插入工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 显示Python版本
echo 🐍 Python版本:
for /f "tokens=*" %%i in ('python --version') do echo    %%i
echo.

REM 检查pymysql是否安装
python -c "import pymysql" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  pymysql未安装，正在安装...
    pip install pymysql
    if errorlevel 1 (
        echo ❌ pymysql安装失败，请手动安装: pip install pymysql
        pause
        exit /b 1
    )
    echo ✅ pymysql安装成功
    echo.
)

REM 检查必要文件是否存在
if not exist "insert_test_data.py" (
    echo ❌ 错误: 未找到 insert_test_data.py 文件
    echo 请确保在正确的目录下运行此脚本
    pause
    exit /b 1
)

if not exist "test_data.sql" (
    echo ❌ 错误: 未找到 test_data.sql 文件
    echo 请确保测试数据文件存在
    pause
    exit /b 1
)

REM 显示菜单
echo 📋 请选择操作:
echo.
echo [1] 标准插入 (交互式)
echo [2] 清空数据后插入
echo [3] 强制插入 (无确认)
echo [4] 仅检查数据库连接
echo [5] 详细模式插入
echo [0] 退出
echo.
set /p choice="请输入选项 (0-5): "

if "%choice%"=="0" (
    echo 👋 再见！
    exit /b 0
)

if "%choice%"=="1" (
    echo 🚀 执行标准插入...
    python insert_test_data.py
) else if "%choice%"=="2" (
    echo 🧹 执行清空数据后插入...
    python insert_test_data.py --clear
) else if "%choice%"=="3" (
    echo ⚡ 执行强制插入...
    python insert_test_data.py --force
) else if "%choice%"=="4" (
    echo 🔍 检查数据库连接...
    python insert_test_data.py --check-only
) else if "%choice%"=="5" (
    echo 📊 执行详细模式插入...
    python insert_test_data.py --verbose
) else (
    echo ❌ 无效选项，请重新运行脚本
    pause
    exit /b 1
)

REM 检查执行结果
if errorlevel 1 (
    echo.
    echo ❌ 操作失败，请检查错误信息
) else (
    echo.
    echo ✅ 操作完成
)

echo.
echo 📖 更多选项请运行: python insert_test_data.py --help
echo.
pause