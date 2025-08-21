@echo off
REM 启动执行器节点监控程序
REM 该程序会定期清理过期的执行器节点数据

echo 启动执行器节点监控程序...
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 启动监控程序
REM 参数说明:
REM --heartbeat-timeout: 心跳超时时间（秒），默认300秒（5分钟）
REM --cleanup-interval: 清理检查间隔（秒），默认600秒（10分钟）
REM --offline-retention: 离线节点保留时间（秒），默认3600秒（1小时）
REM --log-level: 日志级别，默认INFO

python executor_monitor.py --heartbeat-timeout 300 --cleanup-interval 600 --offline-retention 3600 --log-level INFO

echo.
echo 监控程序已退出
pause