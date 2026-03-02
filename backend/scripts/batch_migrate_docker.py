import asyncio
import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select
import paramiko

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义远程执行的 Shell 脚本
MIGRATE_SCRIPT = r"""
#!/bin/bash
set -e

echo "🚀 Starting Docker migration check on $(hostname -I | awk '{print $1}')..."

# 1. Check current Docker Root Dir
CURRENT_ROOT=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo "")
if [ "$CURRENT_ROOT" == "/data/dockers" ]; then
    echo "✅ Docker is already using /data/dockers. Skipping."
    exit 0
fi

echo "ℹ️ Current Docker Root Dir: $CURRENT_ROOT"

# 2. Check if /data partition exists
if ! df -h /data | grep -q "/data"; then
    # Some systems might mount it differently, check mount point
    if ! mount | grep -q "on /data type"; then
        echo "❌ Error: /data partition not mounted or found!"
        exit 1
    fi
fi
echo "✅ /data partition found."

# 3. Stop Docker service
echo "🛑 Stopping Docker service..."
systemctl stop docker
systemctl stop docker.socket

# 4. Create new directory
echo "📂 Creating /data/dockers..."
mkdir -p /data/dockers

# 5. Update daemon.json using Python (to avoid dependency on jq)
echo "⚙️ Updating /etc/docker/daemon.json..."
python3 -c "
import json
import os

config_file = '/etc/docker/daemon.json'
if not os.path.exists(config_file):
    config = {}
else:
    try:
        with open(config_file, 'r') as f:
            content = f.read().strip()
            config = json.loads(content) if content else {}
    except Exception as e:
        print(f'Warning: Failed to parse existing config: {e}')
        config = {}

config['data-root'] = '/data/dockers'

with open(config_file, 'w') as f:
    json.dump(config, f, indent=4)
"

# 6. Start Docker service
echo "▶️ Starting Docker service..."
systemctl start docker

# 7. Verify
NEW_ROOT=$(docker info --format '{{.DockerRootDir}}')
if [ "$NEW_ROOT" == "/data/dockers" ]; then
    echo "✅ Success: Docker Root Dir migrated to /data/dockers"
else
    echo "❌ Failed: Docker Root Dir is $NEW_ROOT"
    exit 1
fi

echo "⚠️ Note: Old data at /var/lib/docker was NOT deleted. Please remove it manually after verification."
"""

async def main():
    logger.info("🚀 开始批量 Docker 迁移任务...")
    
    async with AsyncSessionLocal() as db:
        # 获取所有服务器
        stmt = select(Server).where(Server.is_active == True)
        result = await db.execute(stmt)
        servers = result.scalars().all()
        
        if not servers:
            logger.warning("❌ 未找到活跃服务器")
            return
            
        logger.info(f"📋 找到 {len(servers)} 台活跃服务器，准备开始检查与迁移...")
        
        results = []
        for server in servers:
            logger.info(f"\n--- 处理服务器: {server.ip_address} ({server.name}) ---")
            success, message = await process_server(server)
            results.append({
                "ip": server.ip_address,
                "name": server.name,
                "success": success,
                "message": message
            })
            
        # 汇总报告
        logger.info("\n📊 迁移任务汇总:")
        print(f"{'IP Address':<15} | {'Name':<20} | {'Status':<10} | {'Message'}")
        print("-" * 80)
        for res in results:
            status = "✅ OK" if res["success"] else "❌ FAIL"
            print(f"{res['ip']:<15} | {res['name']:<20} | {status:<10} | {res['message']}")

async def process_server(server: Server) -> Tuple[bool, str]:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        connect_kwargs = {
            "hostname": server.ip_address,
            "port": server.ssh_port,
            "username": server.ssh_username,
            "timeout": 20
        }
        if server.ssh_password:
            connect_kwargs["password"] = server.ssh_password
        
        # 尝试连接
        ssh.connect(**connect_kwargs)
        
        # 上传并执行脚本
        # 为了避免文件传输问题，直接通过 stdin 写入脚本并执行
        # 使用 sudo -S 从 stdin 读取密码
        
        # 构建命令：将脚本写入临时文件，赋予权限，然后执行
        # 注意：这里假设 server.ssh_username 有 sudo 权限
        
        remote_script_path = "/tmp/migrate_docker.sh"
        
        # 1. 写入脚本文件
        sftp = ssh.open_sftp()
        with sftp.file(remote_script_path, 'w') as f:
            f.write(MIGRATE_SCRIPT)
        sftp.close()
        
        # 2. 赋予执行权限
        ssh.exec_command(f"chmod +x {remote_script_path}")
        
        # 3. 执行脚本 (使用 sudo)
        logger.info(f"⏳ 正在 {server.ip_address} 上执行迁移脚本...")
        
        # 组合命令以处理 sudo 密码提示
        # 使用 -S 选项让 sudo 从 stdin 读取密码
        cmd = f"echo '{server.ssh_password}' | sudo -S {remote_script_path}"
        
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        
        # 实时读取输出
        output_lines = []
        while True:
            line = stdout.readline()
            if not line:
                break
            line = line.strip()
            if line:
                logger.info(f"   [{server.ip_address}] {line}")
                output_lines.append(line)
                
        exit_status = stdout.channel.recv_exit_status()
        
        # 清理脚本
        ssh.exec_command(f"rm {remote_script_path}")
        
        if exit_status == 0:
            # 检查输出中是否有跳过信息
            full_output = "\n".join(output_lines)
            if "Skipping" in full_output:
                return True, "Already Migrated"
            return True, "Migrated Successfully"
        else:
            return False, f"Script failed with exit code {exit_status}"

    except Exception as e:
        logger.error(f"❌ 连接或执行失败: {e}")
        return False, str(e)
    finally:
        ssh.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ 程序执行异常: {e}")
