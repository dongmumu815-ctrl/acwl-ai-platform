#!/bin/bash

# 定义要添加的私有仓库地址
REGISTRY="10.20.1.204:5000"
DAEMON_JSON="/etc/docker/daemon.json"

echo "正在检查 Docker 配置: $DAEMON_JSON"
echo "目标仓库: $REGISTRY"

# 如果文件不存在，创建一个空的 JSON
if [ ! -f "$DAEMON_JSON" ]; then
    echo "{}" | sudo tee "$DAEMON_JSON" > /dev/null
    echo "创建了新的 $DAEMON_JSON 文件"
fi

# 使用 Python 进行安全的 JSON 更新
# 这样可以保留原有的其他配置（如 mirrors, runtimes 等）
sudo python3 -c "
import json
import os
import sys

file_path = '$DAEMON_JSON'
target_registry = '$REGISTRY'

try:
    with open(file_path, 'r') as f:
        try:
            content = f.read().strip()
            data = json.loads(content) if content else {}
        except json.JSONDecodeError:
            print(f'警告: {file_path} 格式错误，将被重置')
            data = {}
            
    # 获取或初始化 insecure-registries 列表
    registries = data.get('insecure-registries', [])
    
    if target_registry not in registries:
        print(f'添加 {target_registry} 到 insecure-registries...')
        registries.append(target_registry)
        data['insecure-registries'] = registries
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print('配置文件更新成功')
        sys.exit(100) # 返回 100 表示有修改
    else:
        print(f'{target_registry} 已存在，无需修改')
        sys.exit(0) # 返回 0 表示无修改

except Exception as e:
    print(f'发生错误: {e}')
    sys.exit(1)
"

# 捕获 Python 脚本的退出码
EXIT_CODE=$?

if [ $EXIT_CODE -eq 100 ]; then
    echo "配置已更新，正在重载 Docker..."
    if sudo systemctl reload docker; then
        echo "✅ Docker 重载成功！"
    else
        echo "⚠️ 重载失败，尝试重启 Docker..."
        sudo systemctl restart docker
        echo "✅ Docker 重启成功！"
    fi
elif [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 配置已存在，无需变更。"
else
    echo "❌ 更新失败，请检查文件权限或格式。"
    exit 1
fi
