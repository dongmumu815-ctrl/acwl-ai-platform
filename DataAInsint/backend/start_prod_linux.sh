#!/bin/bash
# DataAInsight 数据探查工具 - Linux生产环境启动脚本
# 
# 使用方法:
#   ./start_prod_linux.sh start [server_type]  - 启动服务（后台运行）
#   ./start_prod_linux.sh stop                - 停止服务
#   ./start_prod_linux.sh restart [server_type] - 重启服务
#   ./start_prod_linux.sh status              - 查看服务状态
#   ./start_prod_linux.sh logs                - 查看日志
#
# server_type 选项:
#   gunicorn  - 使用Gunicorn ASGI服务器（默认）
#   uvicorn   - 使用Uvicorn多进程模式
#   hypercorn - 使用Hypercorn ASGI服务器

# 配置变量
APP_NAME="dataainsight"
APP_MODULE="main:app"
HOST="0.0.0.0"
PORT="8001"
WORKERS="1"
PID_FILE="/tmp/${APP_NAME}.pid"
LOG_FILE="/tmp/${APP_NAME}.log"
ERROR_LOG_FILE="/tmp/${APP_NAME}_error.log"

# Gunicorn# 性能和超时配置
WORKER_TIMEOUT="300"         # Worker超时时间（秒）
WORKER_MEMORY_LIMIT="1024"    # Worker内存限制（MB）
MAX_REQUESTS="1000"          # 每个worker处理的最大请求数
MAX_REQUESTS_JITTER="100"    # 最大请求数的随机抖动
KEEP_ALIVE="5"               # Keep-alive连接超时时间（秒）
WORKER_CONNECTIONS="1000"     # 每个worker的最大并发连接数

# 系统级内存限制配置
MEMORY_LIMIT_GB="2"          # 系统内存限制（GB）
VIRTUAL_MEMORY_LIMIT="2097152" # 虚拟内存限制（KB，2GB）

# 获取脚本所在目录（当前就在backend目录中）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出函数
print_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

print_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# Python路径自动检测和配置
detect_python() {
    # 优先级顺序：python3 > python > python3.x
    local python_candidates="python3 python python3.12 python3.11 python3.10 python3.9 python3.8"
    
    for cmd in $python_candidates; do
        if command -v "$cmd" >/dev/null 2>&1; then
            # 检查是否为Python 3.x
            local version=$("$cmd" --version 2>&1)
            case "$version" in
                *"Python 3."*)
                    PYTHON_PATH="$cmd"
                    return 0
                    ;;
            esac
        fi
    done
    
    # 如果没有找到合适的Python，尝试使用环境变量或默认值
    if [ -n "$PYTHON" ] && command -v "$PYTHON" >/dev/null 2>&1; then
        PYTHON_PATH="$PYTHON"
        return 0
    fi
    
    return 1
}

# 检查Python环境
check_python() {
    # 首先尝试自动检测Python
    if ! detect_python; then
        print_error "未找到合适的Python 3.x解释器"
        print_error "请确保已安装Python 3.x并添加到PATH环境变量中"
        print_error "或者设置PYTHON环境变量指向Python可执行文件"
        exit 1
    fi
    
    # 验证Python可用性
    if ! command -v "$PYTHON_PATH" >/dev/null 2>&1; then
        print_error "Python 未找到: $PYTHON_PATH"
        exit 1
    fi
    
    # 检查Python版本
    local python_version=$("$PYTHON_PATH" --version 2>&1 | cut -d' ' -f2)
    print_info "使用Python: $PYTHON_PATH"
    print_info "Python版本: $python_version"
    
    # 检查Python版本是否满足要求（至少3.8）
    local major_version=$(echo "$python_version" | cut -d'.' -f1)
    local minor_version=$(echo "$python_version" | cut -d'.' -f2)
    
    if [ "$major_version" -lt 3 ] || [ "$major_version" -eq 3 -a "$minor_version" -lt 8 ]; then
        print_error "Python版本过低，需要Python 3.8或更高版本"
        exit 1
    fi
}

# 检查项目依赖
check_project_deps() {
    if [ -f "requirements.txt" ]; then
        print_info "检查项目依赖..."
        "$PYTHON_PATH" -m pip install -r requirements.txt
    else
        print_warn "未找到 requirements.txt 文件"
    fi
}

# 检查并安装服务器依赖
check_server_deps() {
    local server_type=$1
    
    case $server_type in
        "gunicorn")
            if ! "$PYTHON_PATH" -c "import gunicorn" >/dev/null 2>&1; then
                print_warn "Gunicorn 未安装，正在安装..."
                "$PYTHON_PATH" -m pip install gunicorn
            fi
            # Gunicorn 使用 UvicornWorker 需要 uvicorn
            if ! "$PYTHON_PATH" -c "import uvicorn" >/dev/null 2>&1; then
                print_warn "Uvicorn 未安装，正在安装..."
                "$PYTHON_PATH" -m pip install uvicorn
            fi
            ;;
        "uvicorn")
            if ! "$PYTHON_PATH" -c "import uvicorn" >/dev/null 2>&1; then
                print_warn "Uvicorn 未安装，正在安装..."
                "$PYTHON_PATH" -m pip install uvicorn
            fi
            ;;
        "hypercorn")
            if ! "$PYTHON_PATH" -c "import hypercorn" >/dev/null 2>&1; then
                print_warn "Hypercorn 未安装，正在安装..."
                "$PYTHON_PATH" -m pip install hypercorn
            fi
            ;;
    esac
}

# 获取进程ID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

# 检查服务是否运行
is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# 启动服务
start_service() {
    local server_type=${1:-"gunicorn"}
    
    if is_running; then
        print_warn "服务已在运行中 (PID: $(get_pid))"
        return 1
    fi
    
    print_info "正在启动 DataAInsight 服务 (使用 $server_type)..."
    
    # 设置系统级内存限制
    print_info "设置系统级内存限制..."
    ulimit -v "$VIRTUAL_MEMORY_LIMIT"  # 虚拟内存限制
    ulimit -m $((MEMORY_LIMIT_GB * 1024 * 1024))  # 物理内存限制（KB）
    ulimit -n 65536  # 文件描述符限制
    
    print_info "当前内存限制设置:"
    print_info "  虚拟内存: $(ulimit -v) KB"
    print_info "  物理内存: $(ulimit -m) KB"
    print_info "  文件描述符: $(ulimit -n)"
    print_info "  内存限制: ${MEMORY_LIMIT_GB}GB"
    
    # 检查依赖
    check_python
    check_project_deps
    check_server_deps "$server_type"
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 根据服务器类型启动
    case $server_type in
        "gunicorn")
            nohup "$PYTHON_PATH" -m gunicorn -w "$WORKERS" -k uvicorn.workers.UvicornWorker \
                "$APP_MODULE" --bind "$HOST:$PORT" \
                --access-logfile "$LOG_FILE" \
                --error-logfile "$ERROR_LOG_FILE" \
                --log-level info \
                --timeout "$WORKER_TIMEOUT" \
                --max-requests "$MAX_REQUESTS" \
                --max-requests-jitter "$MAX_REQUESTS_JITTER" \
                --keep-alive "$KEEP_ALIVE" \
                --worker-connections "$WORKER_CONNECTIONS" \
                --preload \
                --daemon --pid "$PID_FILE" \
                > /dev/null 2>&1
            ;;
        "uvicorn")
            nohup "$PYTHON_PATH" -m uvicorn "$APP_MODULE" \
                --host "$HOST" --port "$PORT" \
                --workers "$WORKERS" \
                --access-log --log-level info \
                > "$LOG_FILE" 2>"$ERROR_LOG_FILE" & echo $! > "$PID_FILE"
            ;;
        "hypercorn")
            nohup "$PYTHON_PATH" -m hypercorn "$APP_MODULE" \
                --bind "$HOST:$PORT" \
                --workers "$WORKERS" \
                --access-log \
                > "$LOG_FILE" 2>"$ERROR_LOG_FILE" & echo $! > "$PID_FILE"
            ;;
        *)
            print_error "不支持的服务器类型: $server_type"
            print_info "支持的类型: gunicorn, uvicorn, hypercorn"
            exit 1
            ;;
    esac
    
    # 等待服务启动
    sleep 2
    
    if is_running; then
        print_info "服务启动成功!"
        print_info "PID: $(get_pid)"
        print_info "访问地址: http://$HOST:$PORT"
        print_info "API文档: http://$HOST:$PORT/docs"
        print_info "前端界面: http://$HOST:$PORT/dataainsight"
        print_info "日志文件: $LOG_FILE"
        print_info "错误日志: $ERROR_LOG_FILE"
    else
        print_error "服务启动失败，请检查日志: $ERROR_LOG_FILE"
        exit 1
    fi
}

# 停止服务
stop_service() {
    if ! is_running; then
        print_warn "服务未运行"
        return 1
    fi
    
    local pid=$(get_pid)
    print_info "正在停止服务 (PID: $pid)..."
    
    # 发送TERM信号
    kill "$pid"
    
    # 等待进程结束
    local count=0
    while is_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # 如果进程仍在运行，强制杀死
    if is_running; then
        print_warn "进程未正常结束，强制终止..."
        kill -9 "$pid"
        sleep 1
    fi
    
    # 清理PID文件
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
    fi
    
    if ! is_running; then
        print_info "服务已停止"
    else
        print_error "服务停止失败"
        exit 1
    fi
}

# 重启服务
restart_service() {
    local server_type=${1:-"gunicorn"}
    print_info "正在重启服务..."
    stop_service
    sleep 1
    start_service "$server_type"
}

# 查看服务状态
show_status() {
    if is_running; then
        local pid=$(get_pid)
        print_info "服务正在运行"
        print_info "PID: $pid"
        print_info "访问地址: http://$HOST:$PORT"
        
        # 显示进程信息
        if command -v ps >/dev/null 2>&1; then
            echo
            print_info "进程信息:"
            ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem
        fi
        
        # 检查端口监听
        if command -v netstat >/dev/null 2>&1; then
            echo
            print_info "端口监听:"
            netstat -tlnp 2>/dev/null | grep ":$PORT " || echo "端口 $PORT 未找到监听进程"
        fi
    else
        print_warn "服务未运行"
        if [ -f "$PID_FILE" ]; then
            print_info "清理残留的PID文件..."
            rm -f "$PID_FILE"
        fi
    fi
}

# 查看日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_info "访问日志 (最后50行):"
        tail -n 50 "$LOG_FILE"
    else
        print_warn "日志文件不存在: $LOG_FILE"
    fi
    
    echo
    
    if [ -f "$ERROR_LOG_FILE" ]; then
        print_info "错误日志 (最后20行):"
        tail -n 20 "$ERROR_LOG_FILE"
    else
        print_warn "错误日志文件不存在: $ERROR_LOG_FILE"
    fi
}

# 显示帮助信息
show_help() {
    echo "DataAInsight 生产环境启动脚本"
    echo
    echo "用法: $0 {start|stop|restart|status|logs|help} [server_type]"
    echo
    echo "命令:"
    echo "  start [server_type]  启动服务（后台运行）"
    echo "  stop                 停止服务"
    echo "  restart [server_type] 重启服务"
    echo "  status               查看服务状态"
    echo "  logs                 查看日志"
    echo "  help                 显示此帮助信息"
    echo
    echo "服务器类型 (server_type):"
    echo "  gunicorn   使用Gunicorn ASGI服务器（默认，推荐）"
    echo "  uvicorn    使用Uvicorn多进程模式"
    echo "  hypercorn  使用Hypercorn ASGI服务器"
    echo
    echo "示例:"
    echo "  $0 start              # 使用默认的Gunicorn启动"
    echo "  $0 start uvicorn      # 使用Uvicorn启动"
    echo "  $0 restart gunicorn   # 重启Gunicorn服务"
    echo "  $0 status             # 查看服务状态"
    echo "  $0 logs               # 查看日志"
    echo
    echo "配置:"
    echo "  主机: $HOST"
    echo "  端口: $PORT"
    echo "  工作进程数: $WORKERS"
    echo "  Worker超时: ${WORKER_TIMEOUT}秒"
    echo "  内存限制: ${WORKER_MEMORY_LIMIT}MB"
    echo "  最大请求数: $MAX_REQUESTS"
    echo "  系统内存限制: ${MEMORY_LIMIT_GB}GB"
    echo "  虚拟内存限制: ${VIRTUAL_MEMORY_LIMIT}KB"
    echo "  PID文件: $PID_FILE"
    echo "  日志文件: $LOG_FILE"
    echo "  错误日志: $ERROR_LOG_FILE"
    echo
    echo "性能优化说明:"
    echo "  - Worker超时时间已设置为${WORKER_TIMEOUT}秒，适合处理大型SQL查询"
    echo "  - 启用了预加载模式(--preload)以减少内存使用"
    echo "  - 设置了最大请求数限制以防止内存泄漏"
    echo "  - 配置了连接池以提高并发性能"
}

# 主程序
case "$1" in
    "start")
        start_service "$2"
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service "$2"
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        print_error "请指定操作命令"
        echo
        show_help
        exit 1
        ;;
    *)
        print_error "未知命令: $1"
        echo
        show_help
        exit 1
        ;;
esac