@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================
REM CEPIEC API Windows环境启动脚本
REM 使用Waitress作为WSGI服务器
REM ========================================

echo.
echo ========================================
echo 🪟 CEPIEC API Windows环境启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 显示Python版本
echo ✅ Python版本:
for /f "tokens=*" %%i in ('python --version') do echo    %%i
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"
echo 📁 工作目录: %CD%
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 🔧 检测到虚拟环境，正在激活...
    call venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
    echo.
) else if exist "..\venv\Scripts\activate.bat" (
    echo 🔧 检测到上级目录虚拟环境，正在激活...
    call ..\venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
    echo.
) else (
    echo ⚠️  未检测到虚拟环境，使用系统Python
    echo.
)

REM 检查必要的包
echo 🔍 检查依赖包...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo ❌ FastAPI未安装
    goto :install_deps
)

python -c "import waitress" >nul 2>&1
if errorlevel 1 (
    echo ❌ Waitress未安装
    goto :install_deps
)

python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo ❌ Uvicorn未安装
    goto :install_deps
)

echo ✅ 所有依赖包已安装
echo.
goto :start_server

:install_deps
echo.
echo 📦 正在安装依赖包...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖包安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖包安装完成
    echo.
) else (
    echo ❌ 未找到requirements.txt文件
    pause
    exit /b 1
)

:start_server
REM 检查配置文件
if not exist ".env" (
    echo ⚠️  未找到.env配置文件
    if exist ".env.example" (
        echo 💡 建议复制.env.example为.env并配置相应参数
    )
    echo.
)

REM 显示启动选项
echo 🚀 请选择启动模式:
echo    1. 生产模式 (Waitress, 8080端口)
echo    2. 开发模式 (Uvicorn, 8080端口, 自动重载)
echo    3. 自定义端口生产模式
echo    4. 退出
echo.
set /p choice=请输入选择 (1-4): 

if "%choice%"=="1" goto :prod_mode
if "%choice%"=="2" goto :dev_mode
if "%choice%"=="3" goto :custom_port
if "%choice%"=="4" goto :exit
echo 无效选择，默认使用生产模式
goto :prod_mode

:prod_mode
echo.
echo 🏭 启动生产环境服务器 (Waitress)...
echo 📍 服务地址: http://localhost:8080
echo 📖 API文档: http://localhost:8080/docs
echo 🛑 按 Ctrl+C 停止服务器
echo.
python start_windows.py
goto :end

:dev_mode
echo.
echo 🔧 启动开发环境服务器 (Uvicorn)...
echo 📍 服务地址: http://localhost:8080
echo 📖 API文档: http://localhost:8080/docs
echo 🔄 自动重载已启用
echo 🛑 按 Ctrl+C 停止服务器
echo.
python start_windows.py --dev --reload
goto :end

:custom_port
echo.
set /p port=请输入端口号 (默认8080): 
if "%port%"=="" set port=8080
echo.
echo 🏭 启动生产环境服务器 (Waitress)...
echo 📍 服务地址: http://localhost:%port%
echo 📖 API文档: http://localhost:%port%/docs
echo 🛑 按 Ctrl+C 停止服务器
echo.
python start_windows.py --port %port%
goto :end

:end
echo.
echo 🛑 服务器已停止
pause
goto :exit

:exit
echo.
echo 👋 感谢使用 CEPIEC API 服务器
echo.