@echo off
echo ========================================
echo    ACWL AI 分散前端项目构建脚本
echo ========================================
echo.

set "start_time=%time%"
set "error_count=0"

echo 开始构建所有前端项目...
echo.

echo [1/3] 构建主前端 (ACWL AI大模型管理平台)...
cd /d "d:\works\codes\acwl-ai-data\frontend"
call npm run build
if %errorlevel% neq 0 (
    echo ❌ 主前端构建失败！
    set /a error_count+=1
) else (
    echo ✅ 主前端构建成功！
)
echo.

echo [2/3] 构建工作流前端 (ACWL AI工作流管理平台)...
cd /d "d:\works\codes\acwl-ai-data\taskflow-frontend"
call npm run build
if %errorlevel% neq 0 (
    echo ❌ 工作流前端构建失败！
    set /a error_count+=1
) else (
    echo ✅ 工作流前端构建成功！
)
echo.

echo [3/3] 构建数据中心前端 (数据资源中心)...
cd /d "d:\works\codes\acwl-ai-data\dc_frontend"
call npm run build
if %errorlevel% neq 0 (
    echo ❌ 数据中心前端构建失败！
    set /a error_count+=1
) else (
    echo ✅ 数据中心前端构建成功！
)
echo.

echo ========================================
echo           构建完成！
echo ========================================
echo.
echo 构建结果统计：
if %error_count% equ 0 (
    echo   ✅ 所有项目构建成功！
    echo   📁 构建文件位置：
    echo      - frontend/dist/
    echo      - taskflow-frontend/dist/
    echo      - dc_frontend/dist/
) else (
    echo   ❌ %error_count% 个项目构建失败
    echo   请检查错误信息并修复后重新构建
)
echo.
echo 构建开始时间: %start_time%
echo 构建结束时间: %time%
echo.

cd /d "d:\works\codes\acwl-ai-data"

if %error_count% neq 0 (
    echo 按任意键退出...
    pause >nul
    exit /b 1
) else (
    echo 按任意键退出...
    pause >nul
    exit /b 0
)