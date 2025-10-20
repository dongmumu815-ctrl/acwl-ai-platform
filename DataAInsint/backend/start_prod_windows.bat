@echo off
REM DataAInsight 数据探查工具 - Windows生产环境启动脚本
REM
REM 使用方法:
REM   start_prod_windows.bat start [server_type]  - 启动服务（后台运行）
REM   start_prod_windows.bat stop                - 停止服务
REM   start_prod_windows.bat restart [server_type] - 重启服务
REM   start_prod_windows.bat status              - 查看服务状态
REM   start_prod_windows.bat logs                - 查看日志
REM
REM server_type 选项:
REM   gunicorn  - 使用Gunicorn ASGI服务器（默认）
REM   uvicorn   - 使用Uvicorn多进程模式
REM   hypercorn - 使用Hypercorn ASGI服务器

setlocal enabledelayedexpansion

REM 配置变量
set APP_NAME=dataainsight
set APP_MODULE=main:app
set HOST=0.0.0.0
set PORT=8001
set WORKERS=4
set PID_FILE=%TEMP%\%APP_NAME%.pid
set LOG_FILE=%TEMP%\%APP_NAME%.log
set ERROR_LOG_FILE=%TEMP%\%APP_NAME%_error.log

REM Gunicorn 性能和超时配置
set WORKER_TIMEOUT=300
set WORKER_MEMORY_LIMIT=1024
set MAX_REQUESTS=1000
set MAX_REQUESTS_JITTER=100
set KEEP_ALIVE=5
set WORKER_CONNECTIONS=1000

REM 获取脚本所在目录（当前就在backend目录中）
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Python路径配置
set PYTHON_PATH=python

REM 颜色输出函数（Windows简化版）
set INFO_PREFIX=[INFO]
set WARN_PREFIX=[WARN]
set ERROR_PREFIX=[ERROR]

REM 检查Python环境
:check_python
%PYTHON_PATH% --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR_PREFIX% Python 未找到: %PYTHON_PATH%
    exit /b 1
)
for /f "tokens=2" %%i in ('%PYTHON_PATH% --version 2^>^&1') do (
    echo %INFO_PREFIX% 使用Python版本: %%i
)
goto :eof

REM 检查并安装服务器依赖
:check_server_deps
set server_type=%1
if "%server_type%"=="gunicorn" (
    %PYTHON_PATH% -c "import gunicorn" >nul 2>&1
    if errorlevel 1 (
        echo %WARN_PREFIX% Gunicorn 未安装，正在安装...
        %PYTHON_PATH% -m pip install gunicorn
    )
    %PYTHON_PATH% -c "import uvicorn" >nul 2>&1
    if errorlevel 1 (
        echo %WARN_PREFIX% Uvicorn 未安装，正在安装...
        %PYTHON_PATH% -m pip install uvicorn
    )
) else if "%server_type%"=="uvicorn" (
    %PYTHON_PATH% -c "import uvicorn" >nul 2>&1
    if errorlevel 1 (
        echo %WARN_PREFIX% Uvicorn 未安装，正在安装...
        %PYTHON_PATH% -m pip install uvicorn
    )
) else if "%server_type%"=="hypercorn" (
    %PYTHON_PATH% -c "import hypercorn" >nul 2>&1
    if errorlevel 1 (
        echo %WARN_PREFIX% Hypercorn 未安装，正在安装...
        %PYTHON_PATH% -m pip install hypercorn
    )
)
goto :eof

REM 检查项目依赖
:check_project_deps
if exist "requirements.txt" (
    echo %INFO_PREFIX% 检查项目依赖...
    %PYTHON_PATH% -m pip install -r requirements.txt
) else (
    echo %WARN_PREFIX% 未找到 requirements.txt 文件
)
goto :eof

REM 获取进程ID
:get_pid
if exist "%PID_FILE%" (
    set /p PID=<%PID_FILE%
) else (
    set PID=
)
goto :eof

REM 检查服务是否运行
:is_running
call :get_pid
if "%PID%"=="" (
    exit /b 1
)
tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
if errorlevel 1 (
    exit /b 1
)
exit /b 0

REM 启动服务
:start_service
set server_type=%1
if "%server_type%"=="" set server_type=gunicorn

call :is_running
if not errorlevel 1 (
    call :get_pid
    echo %WARN_PREFIX% 服务已在运行中 (PID: !PID!)
    exit /b 1
)

echo %INFO_PREFIX% 正在启动 DataAInsight 服务 (使用 %server_type%)...

REM 检查依赖
call :check_python
call :check_project_deps
call :check_server_deps %server_type%

REM 根据服务器类型启动
if "%server_type%"=="gunicorn" (
    start /b "" %PYTHON_PATH% -m gunicorn -w %WORKERS% -k uvicorn.workers.UvicornWorker %APP_MODULE% --bind %HOST%:%PORT% --access-logfile "%LOG_FILE%" --error-logfile "%ERROR_LOG_FILE%" --log-level info --timeout %WORKER_TIMEOUT% --max-requests %MAX_REQUESTS% --max-requests-jitter %MAX_REQUESTS_JITTER% --keep-alive %KEEP_ALIVE% --worker-connections %WORKER_CONNECTIONS% --preload
) else if "%server_type%"=="uvicorn" (
    start /b "" %PYTHON_PATH% -m uvicorn %APP_MODULE% --host %HOST% --port %PORT% --workers %WORKERS% --access-log --log-level info
) else if "%server_type%"=="hypercorn" (
    start /b "" %PYTHON_PATH% -m hypercorn %APP_MODULE% --bind %HOST%:%PORT% --workers %WORKERS% --access-log
) else (
    echo %ERROR_PREFIX% 不支持的服务器类型: %server_type%
    echo %INFO_PREFIX% 支持的类型: gunicorn, uvicorn, hypercorn
    exit /b 1
)

REM 获取新启动进程的PID（简化处理）
timeout /t 2 /nobreak >nul
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq %APP_MODULE%*" /FO CSV ^| find "python.exe"') do (
    echo %%i > "%PID_FILE%"
    set NEW_PID=%%i
)

REM 等待服务启动
timeout /t 3 /nobreak >nul

call :is_running
if not errorlevel 1 (
    call :get_pid
    echo %INFO_PREFIX% 服务启动成功!
    echo %INFO_PREFIX% PID: !PID!
    echo %INFO_PREFIX% 访问地址: http://%HOST%:%PORT%
    echo %INFO_PREFIX% API文档: http://%HOST%:%PORT%/docs
    echo %INFO_PREFIX% 前端界面: http://%HOST%:%PORT%/dataainsight
    echo %INFO_PREFIX% 日志文件: %LOG_FILE%
    echo %INFO_PREFIX% 错误日志: %ERROR_LOG_FILE%
) else (
    echo %ERROR_PREFIX% 服务启动失败，请检查日志: %ERROR_LOG_FILE%
    exit /b 1
)
goto :eof

REM 停止服务
:stop_service
call :is_running
if errorlevel 1 (
    echo %WARN_PREFIX% 服务未运行
    exit /b 1
)

call :get_pid
echo %INFO_PREFIX% 正在停止服务 (PID: %PID%)...

REM 终止进程
taskkill /PID %PID% /F >nul 2>&1

REM 等待进程结束
timeout /t 2 /nobreak >nul

REM 清理PID文件
if exist "%PID_FILE%" del "%PID_FILE%"

call :is_running
if errorlevel 1 (
    echo %INFO_PREFIX% 服务已停止
) else (
    echo %ERROR_PREFIX% 服务停止失败
    exit /b 1
)
goto :eof

REM 重启服务
:restart_service
set server_type=%1
echo %INFO_PREFIX% 正在重启服务...
call :stop_service
timeout /t 1 /nobreak >nul
call :start_service %server_type%
goto :eof

REM 查看服务状态
:show_status
call :is_running
if not errorlevel 1 (
    call :get_pid
    echo %INFO_PREFIX% 服务正在运行
    echo %INFO_PREFIX% PID: !PID!
    echo %INFO_PREFIX% 访问地址: http://%HOST%:%PORT%
    echo %INFO_PREFIX% 前端界面: http://%HOST%:%PORT%/dataainsight
    echo.
    echo %INFO_PREFIX% 进程信息:
    tasklist /FI "PID eq !PID!" /FO TABLE
    echo.
    echo %INFO_PREFIX% 端口监听:
    netstat -an | find ":%PORT%"
) else (
    echo %WARN_PREFIX% 服务未运行
    exit /b 1
)
goto :eof

REM 查看日志
:show_logs
if exist "%LOG_FILE%" (
    echo %INFO_PREFIX% 访问日志 (最后20行):
    powershell "Get-Content '%LOG_FILE%' -Tail 20"
) else (
    echo %WARN_PREFIX% 日志文件不存在: %LOG_FILE%
)

echo.

if exist "%ERROR_LOG_FILE%" (
    echo %INFO_PREFIX% 错误日志 (最后20行):
    powershell "Get-Content '%ERROR_LOG_FILE%' -Tail 20"
) else (
    echo %WARN_PREFIX% 错误日志文件不存在: %ERROR_LOG_FILE%
)
goto :eof

REM 显示帮助信息
:show_help
echo DataAInsight 数据探查工具 - Windows生产环境启动脚本
echo.
echo 使用方法:
echo   %~nx0 start [server_type]  - 启动服务（后台运行）
echo   %~nx0 stop                - 停止服务
echo   %~nx0 restart [server_type] - 重启服务
echo   %~nx0 status              - 查看服务状态
echo   %~nx0 logs                - 查看日志
echo   %~nx0 help                - 显示帮助信息
echo.
echo server_type 选项:
echo   gunicorn  - 使用Gunicorn ASGI服务器（默认）
echo   uvicorn   - 使用Uvicorn多进程模式
echo   hypercorn - 使用Hypercorn ASGI服务器
echo.
echo 配置信息:
echo   应用名称: %APP_NAME%
echo   监听地址: %HOST%:%PORT%
echo   工作进程: %WORKERS%
echo   Worker超时: %WORKER_TIMEOUT%秒
echo   内存限制: %WORKER_MEMORY_LIMIT%MB
echo   最大请求数: %MAX_REQUESTS%
echo   PID文件: %PID_FILE%
echo   日志文件: %LOG_FILE%
echo   错误日志: %ERROR_LOG_FILE%
echo.
echo 性能优化说明:
echo   - Worker超时时间已设置为%WORKER_TIMEOUT%秒，适合处理大型SQL查询
echo   - 启用了预加载模式(--preload)以减少内存使用
echo   - 设置了最大请求数限制以防止内存泄漏
echo   - 配置了连接池以提高并发性能
goto :eof

REM 主程序
if "%1"=="start" (
    call :start_service %2
) else if "%1"=="stop" (
    call :stop_service
) else if "%1"=="restart" (
    call :restart_service %2
) else if "%1"=="status" (
    call :show_status
) else if "%1"=="logs" (
    call :show_logs
) else if "%1"=="help" (
    call :show_help
) else (
    echo %ERROR_PREFIX% 无效的命令: %1
    echo.
    call :show_help
    exit /b 1
)

endlocal