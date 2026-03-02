#!/bin/bash
# init_doris_password.sh
# 这是一个初始化脚本，用于在 Doris FE 启动后设置 root 密码。
# 它会被挂载到容器中，并由 entrypoint 或后台任务执行。

# 等待 FE 启动 (端口 9030)
MAX_RETRIES=30
RETRY_INTERVAL=5

echo "Waiting for Doris FE to start on port 9030..."

for ((i=1; i<=MAX_RETRIES; i++)); do
    # 使用 mysql 客户端尝试连接
    # 注意：在容器内，如果没有 mysql 客户端，可能需要使用 curl 或者内置的 client
    # apache/doris 镜像通常包含 mysql 客户端
    if mysql -h127.0.0.1 -P9030 -uroot -e "SELECT 1" >/dev/null 2>&1; then
        echo "Doris FE is up!"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo "Timeout waiting for Doris FE."
        exit 1
    fi
    
    echo "Waiting... ($i/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

# 检查是否设置了 INITIAL_ROOT_PASSWORD 环境变量
if [ -z "$INITIAL_ROOT_PASSWORD" ]; then
    echo "INITIAL_ROOT_PASSWORD is not set. Skipping password initialization."
    exit 0
fi

echo "Setting root password..."

# 尝试设置密码
# SET PASSWORD FOR 'root' = PASSWORD('your_password');
# 或者在较新版本：ALTER USER 'root'@'%' IDENTIFIED BY 'your_password';

# 先尝试设置默认无密码用户的密码
mysql -h127.0.0.1 -P9030 -uroot -e "SET PASSWORD FOR 'root' = PASSWORD('$INITIAL_ROOT_PASSWORD');" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Root password set successfully."
else
    # 如果第一次失败，可能是因为已经有密码了，尝试用新密码登录验证
    if mysql -h127.0.0.1 -P9030 -uroot -p"$INITIAL_ROOT_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; then
        echo "Root password was already set correctly."
    else
        echo "Failed to set root password. It might have been changed already."
        # 尝试使用空密码登录再次确认（可能是语法错误）
        mysql -h127.0.0.1 -P9030 -uroot -e "ALTER USER 'root' IDENTIFIED BY '$INITIAL_ROOT_PASSWORD';" 2>/dev/null
        if [ $? -eq 0 ]; then
             echo "Root password set successfully (via ALTER USER)."
        else
             echo "Failed to set password with ALTER USER too."
        fi
    fi
fi
