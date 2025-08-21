@echo off
chcp 65001 >nul
echo ========================================
echo    ACWL AI 数据平台 - 微服务集群启动器
echo ========================================
echo.

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python环境，请先安装Python 3.9+
    pause
    exit /b 1
)

:: 设置工作目录
cd /d "%~dp0"
echo [信息] 当前工作目录: %CD%
echo.

:: 检查主应用是否已启动
echo [检查] 检查主应用状态...
netstat -an | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口8000已被占用，主应用可能已在运行
    echo [提示] 如需重启，请先停止现有服务
    echo.
) else (
    echo [信息] 端口8000可用，准备启动主应用
    echo.
)

:: 显示菜单
:menu
echo ========================================
echo 请选择操作:
echo 1. 启动完整集群 (主应用 + 3调度器 + 3执行器)
echo 2. 仅启动主应用
echo 3. 启动调度器集群 (3个实例)
echo 4. 启动执行器集群 (3个实例)
echo 5. 自定义启动
echo 6. 查看集群状态
echo 7. 停止所有服务
echo 8. 初始化配置文件
echo 9. 退出
echo ========================================
set /p choice="请输入选项 (1-9): "

if "%choice%"=="1" goto start_full
if "%choice%"=="2" goto start_main
if "%choice%"=="3" goto start_schedulers
if "%choice%"=="4" goto start_executors
if "%choice%"=="5" goto custom_start
if "%choice%"=="6" goto show_status
if "%choice%"=="7" goto stop_all
if "%choice%"=="8" goto init_config
if "%choice%"=="9" goto exit

echo [错误] 无效选项，请重新选择
echo.
goto menu

:start_full
echo.
echo [启动] 启动完整集群...
echo [步骤1/3] 启动主应用...
start "ACWL-Main" cmd /k "python main.py"
timeout /t 5 /nobreak >nul

echo [步骤2/3] 启动调度器集群...
python cluster_manager.py start --schedulers 3
timeout /t 3 /nobreak >nul

echo [步骤3/3] 启动执行器集群...
python cluster_manager.py start --executors 3

echo.
echo [完成] 完整集群启动完成！
echo [访问] 主应用地址: http://localhost:8000
echo.
goto menu

:start_main
echo.
echo [启动] 启动主应用...
start "ACWL-Main" cmd /k "python main.py"
echo [完成] 主应用启动完成！
echo [访问] 主应用地址: http://localhost:8000
echo.
goto menu

:start_schedulers
echo.
echo [启动] 启动调度器集群...
python cluster_manager.py start --schedulers 3
echo [完成] 调度器集群启动完成！
echo.
goto menu

:start_executors
echo.
echo [启动] 启动执行器集群...
python cluster_manager.py start --executors 3
echo [完成] 执行器集群启动完成！
echo.
goto menu

:custom_start
echo.
echo [自定义启动]
set /p scheduler_count="请输入调度器数量 (0-5, 默认3): "
set /p executor_count="请输入执行器数量 (0-10, 默认3): "
set /p executor_group="请输入执行器分组 (默认为空，启动所有分组): "

if "%scheduler_count%"=="" set scheduler_count=3
if "%executor_count%"=="" set executor_count=3

echo.
echo [启动] 自定义启动: %scheduler_count%个调度器, %executor_count%个执行器

if not "%scheduler_count%"=="0" (
    if "%executor_group%"=="" (
        python cluster_manager.py start --schedulers %scheduler_count%
    ) else (
        python cluster_manager.py start --schedulers %scheduler_count%
    )
)

if not "%executor_count%"=="0" (
    if "%executor_group%"=="" (
        python cluster_manager.py start --executors %executor_count%
    ) else (
        python cluster_manager.py start --executors %executor_count% --group %executor_group%
    )
)

echo [完成] 自定义启动完成！
echo.
goto menu

:show_status
echo.
echo [状态] 查看集群状态...
python cluster_manager.py status
echo.
echo [提示] 按任意键返回菜单...
pause >nul
goto menu

:stop_all
echo.
echo [停止] 停止所有服务...
python cluster_manager.py stop
echo.
echo [提示] 如果主应用仍在运行，请手动关闭相应的命令行窗口
echo [完成] 集群服务停止完成！
echo.
goto menu

:init_config
echo.
echo [初始化] 创建默认配置文件...
python cluster_manager.py init-config
echo [完成] 配置文件初始化完成！
echo [位置] cluster_config.json
echo.
goto menu

:exit
echo.
echo [退出] 感谢使用 ACWL AI 数据平台！
echo [提示] 如有服务仍在运行，请记得及时停止
echo.
pause
exit /b 0