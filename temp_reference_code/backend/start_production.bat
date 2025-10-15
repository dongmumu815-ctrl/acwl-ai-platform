@echo off
chcp 65001 >nul
echo ====================================
echo    CEPIEC API 生产环境启动脚本
echo ====================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH环境变量
    echo 请先安装Python并确保可以在命令行中使用
    pause
    exit /b 1
)

:: 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 🔧 检测到虚拟环境，正在激活...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  未检测到虚拟环境，使用系统Python
    echo 建议创建虚拟环境: python -m venv venv
)

:: 检查依赖
echo 🔍 检查依赖包...
python -c "import gunicorn, uvicorn, fastapi" >nul 2>&1
if errorlevel 1 (
    echo ❌ 缺少必要依赖包
    echo 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

:: 检查配置文件
if not exist ".env" (
    echo ⚠️  未找到.env配置文件
    if exist ".env.example" (
        echo 💡 建议复制.env.example为.env并配置相应参数
    )
    echo.
)

echo 🚀 启动生产环境服务器...
echo 📍 服务地址: http://localhost:8080
echo 📖 API文档: http://localhost:8080/docs
echo 🛑 按 Ctrl+C 停止服务器
echo.

:: 启动服务器
python start_production.py

echo.
echo 🛑 服务器已停止
pause