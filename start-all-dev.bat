@echo off
echo ========================================
echo    ACWL AI 分散前端项目启动脚本
echo ========================================
echo.

echo 正在启动所有前端开发服务器...
echo.

echo [1/4] 启动后端API服务器 (端口: 8082)...
start "后端API" cmd /k "cd /d D:\works\codes\acwl-ai-data\backend && python main.py"
timeout /t 3 /nobreak >nul

echo [2/4] 启动主前端 (端口: 3000)...
echo cd /d D:\works\codes\acwl-ai-data\frontend > %temp%\start-frontend.bat
echo npm run dev >> %temp%\start-frontend.bat
start "主前端-ACWL AI大模型管理平台" cmd /k "%temp%\start-frontend.bat"
timeout /t 2 /nobreak >nul

echo [3/4] 启动工作流前端 (端口: 3001)...
echo cd /d D:\works\codes\acwl-ai-data\taskflow-frontend > %temp%\start-taskflow.bat
echo npm run dev >> %temp%\start-taskflow.bat
start "工作流前端-ACWL AI工作流管理平台" cmd /k "%temp%\start-taskflow.bat"
timeout /t 2 /nobreak >nul

echo [4/4] 启动数据中心前端 (端口: 3005)...
echo cd /d D:\works\codes\acwl-ai-data\dc_frontend > %temp%\start-dc.bat
echo npm run dev >> %temp%\start-dc.bat
start "数据中心前端-数据资源中心" cmd /k "%temp%\start-dc.bat"

echo.
echo ========================================
echo           启动完成！
echo ========================================
echo.
echo 服务访问地址：
echo   后端API:      http://localhost:8082
echo   主前端:       http://localhost:3000
echo   工作流前端:   http://localhost:3001
echo   数据中心前端: http://localhost:3005
echo.
echo 注意：请等待各服务完全启动后再访问
echo 如需停止所有服务，请关闭对应的命令行窗口
echo.
pause