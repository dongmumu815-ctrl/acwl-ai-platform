#!/bin/bash
# =================================================================
# Docker Root Dir 迁移脚本 (迁移到 /data/dockers)
# 
# 功能：
# 1. 检查 /data 分区是否存在
# 2. 自动停止 Docker 服务
# 3. 创建 /data/dockers 目录
# 4. 修改 daemon.json
# 5. 重启 Docker 服务
# 
# 注意：本脚本不会自动迁移旧数据 (rsync)，请按需手动执行
# =================================================================

set -e

# 必须以 root 运行
if [ "$EUID" -ne 0 ]; then 
  echo "❌ 请以 root 权限运行此脚本 (sudo ./migrate_docker.sh)"
  exit 1
fi

echo "🚀 开始 Docker 迁移检查..."

# 1. 检查是否已经迁移
CURRENT_ROOT=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo "")
if [ "$CURRENT_ROOT" == "/data/dockers" ]; then
    echo "✅ Docker 已经在使用 /data/dockers，无需迁移。"
    exit 0
fi

echo "ℹ️ 当前 Docker 路径: $CURRENT_ROOT"

# 2. 检查 /data 分区
echo "🔍 检查 /data 分区..."
if ! df -h /data | grep -q "/data"; then
    # 尝试检查挂载点
    if ! mount | grep -q "on /data type"; then
        echo "❌ 错误: 未检测到 /data 分区挂载！请确认磁盘状态。"
        echo "   (如果是通过其他路径挂载大磁盘，请修改脚本中的 TARGET_DIR)"
        exit 1
    fi
fi
echo "✅ /data 分区检测通过"

# 3. 停止 Docker
echo "🛑 正在停止 Docker 服务..."
systemctl stop docker
systemctl stop docker.socket || true

# 4. 创建目录
TARGET_DIR="/data/dockers"
echo "📂 创建目录: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

# 5. 修改 daemon.json
CONFIG_FILE="/etc/docker/daemon.json"
echo "⚙️ 修改配置文件: $CONFIG_FILE"

# 如果文件不存在，创建空 JSON
if [ ! -f "$CONFIG_FILE" ]; then
    echo "{}" > "$CONFIG_FILE"
fi

# 使用 python 修改 json (避免依赖 jq)
python3 -c "
import json
import os
import sys

config_file = '$CONFIG_FILE'
target_dir = '$TARGET_DIR'

try:
    with open(config_file, 'r') as f:
        content = f.read().strip()
        config = json.loads(content) if content else {}
except Exception as e:
    print(f'⚠️ 读取配置文件失败: {e}，将创建新配置')
    config = {}

# 设置 data-root
config['data-root'] = target_dir

try:
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    print('✅ daemon.json 更新成功')
except Exception as e:
    print(f'❌ 写入配置文件失败: {e}')
    sys.exit(1)
"

# 6. 启动 Docker
echo "▶️ 正在重启 Docker 服务..."
systemctl start docker

# 7. 验证
NEW_ROOT=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null)
if [ "$NEW_ROOT" == "$TARGET_DIR" ]; then
    echo ""
    echo "🎉 迁移成功！"
    echo "   新 Docker 路径: $NEW_ROOT"
    echo ""
    echo "⚠️  注意: 旧数据 ($CURRENT_ROOT) 仍然保留。"
    echo "   如果新环境运行正常，您可以手动删除旧数据以释放空间:"
    echo "   rm -rf $CURRENT_ROOT"
else
    echo "❌ 迁移失败，当前路径仍为: $NEW_ROOT"
    exit 1
fi
