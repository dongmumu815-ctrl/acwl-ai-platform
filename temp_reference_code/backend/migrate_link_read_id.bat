@echo off
echo ===================================================
echo  link_read_id 字段迁移工具
echo ===================================================
echo.

echo 正在执行迁移...
echo.

python migrate_link_read_id.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 迁移失败！请检查错误信息。
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo 正在验证迁移结果...
echo.

python test_link_read_id_migration.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 验证失败！请检查错误信息。
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ===================================================
echo  迁移成功完成！
echo ===================================================
echo.
echo 请查看 LINK_READ_ID_MIGRATION.md 了解更多信息。
echo.

pause