#!/bin/bash
set -e

# 设置默认值
export HOST_IP=${HOST_IP:-$(hostname -i)}
export PORT=${PORT:-8000}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# 数据库连接信息检查
if [ -z "$MYSQL_HOST" ]; then
    echo "Warning: MYSQL_HOST not set, using default localhost"
else
    # 映射环境变量以匹配 app/core/config.py 中的 Settings
    export DB_HOST=$MYSQL_HOST
fi

if [ -n "$MYSQL_PORT" ]; then
    export DB_PORT=$MYSQL_PORT
fi

if [ -n "$MYSQL_USER" ]; then
    export DB_USER=$MYSQL_USER
fi

if [ -n "$MYSQL_PASSWORD" ]; then
    export DB_PASSWORD=$MYSQL_PASSWORD
fi

if [ -n "$MYSQL_DB" ]; then
    export DB_NAME=$MYSQL_DB
fi

# DataService 连接信息检查
if [ -z "$DB_SERVICE_HOST" ]; then
    echo "Warning: DB_SERVICE_HOST not set, SQL tasks may fail"
fi

case "$SERVICE_TYPE" in
    "scheduler")
        echo "Starting Scheduler Service..."
        NODE_ID=${NODE_ID:-scheduler-$(hostname)}
        NODE_NAME=${NODE_NAME:-scheduler-$(hostname)}
        
        exec python scheduler_service.py \
            --node-id "$NODE_ID" \
            --node-name "$NODE_NAME" \
            --host-ip "$HOST_IP" \
            --port "$PORT" \
            --log-level "$LOG_LEVEL"
        ;;
        
    "executor")
        echo "Starting Executor Service..."
        NODE_ID=${NODE_ID:-executor-$(hostname)}
        NODE_NAME=${NODE_NAME:-executor-$(hostname)}
        GROUP_ID=${GROUP_ID:-default}
        MAX_TASKS=${MAX_TASKS:-5}
        
        exec python executor_service.py \
            --node-id "$NODE_ID" \
            --node-name "$NODE_NAME" \
            --group-id "$GROUP_ID" \
            --host-ip "$HOST_IP" \
            --port "$PORT" \
            --max-concurrent-tasks "$MAX_TASKS" \
            --log-level "$LOG_LEVEL"
        ;;
        
    *)
        echo "Error: SERVICE_TYPE must be 'scheduler' or 'executor'"
        echo "Current value: $SERVICE_TYPE"
        exit 1
        ;;
esac
