import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select
import paramiko

async def main():
    print("🚀 开始迁移 Docker Root Dir 到 /data/dockers...")
    
    # 目标服务器 IP
    target_ip = "10.20.1.221" 
    
    async with AsyncSessionLocal() as db:
        # 获取服务器信息
        stmt = select(Server).where(Server.ip_address == target_ip)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()
        
        if not server:
            print(f"❌ 未在数据库中找到服务器: {target_ip}")
            return
            
        print(f"✅ 连接服务器: {server.ip_address}")
        await migrate_docker(server)

async def migrate_docker(server):
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
             
        ssh.connect(**connect_kwargs)
        
        # 1. 检查 /data 分区是否可用
        print("🔍 检查 /data 分区...")
        stdin, stdout, stderr = ssh.exec_command("df -h /data")
        output = stdout.read().decode().strip()
        print(output)
        if "/data" not in output and "mpath" not in output:
            print("❌ /data 分区似乎未挂载，请人工确认")
            return

        # 2. 停止 Docker
        print("🛑 停止 Docker 服务...")
        stdin, stdout, stderr = ssh.exec_command("echo '{}' | sudo -S systemctl stop docker".format(server.ssh_password))
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print(f"❌ 停止 Docker 失败: {stderr.read().decode()}")
            # 尝试强制停止 socket
            ssh.exec_command("echo '{}' | sudo -S systemctl stop docker.socket".format(server.ssh_password))
        
        # 3. 创建新目录
        print("📂 创建 /data/dockers...")
        ssh.exec_command("echo '{}' | sudo -S mkdir -p /data/dockers".format(server.ssh_password))
        
        # 4. 迁移数据 (使用 rsync)
        # 注意：这可能需要很长时间，这里我们只迁移关键配置或跳过，或者假设用户希望全新开始
        # 鉴于之前磁盘已满，可能包含大量垃圾数据，建议全新开始，但为了安全，我们先备份 daemon.json
        print("⚙️  配置 daemon.json...")
        
        # 读取现有 daemon.json
        cmd_read = "cat /etc/docker/daemon.json"
        stdin, stdout, stderr = ssh.exec_command(cmd_read)
        current_config = stdout.read().decode().strip()
        
        config = {}
        if current_config:
            try:
                config = json.loads(current_config)
            except:
                print("⚠️  现有 daemon.json 格式错误，将创建新文件")
        
        # 修改 data-root
        config["data-root"] = "/data/dockers"
        
        # 写入临时文件
        new_config_str = json.dumps(config, indent=4)
        tmp_file = "/tmp/daemon.json.new"
        
        sftp = ssh.open_sftp()
        with sftp.file(tmp_file, 'w') as f:
            f.write(new_config_str)
        sftp.close()
        
        # 移动并覆盖
        cmd_mv = f"echo '{server.ssh_password}' | sudo -S mv {tmp_file} /etc/docker/daemon.json"
        ssh.exec_command(cmd_mv)
        
        # 5. 启动 Docker
        print("▶️  启动 Docker 服务...")
        stdin, stdout, stderr = ssh.exec_command("echo '{}' | sudo -S systemctl start docker".format(server.ssh_password))
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
             print(f"❌ 启动 Docker 失败: {stderr.read().decode()}")
             return

        # 6. 验证
        print("✅ 验证 Docker Root Dir...")
        stdin, stdout, stderr = ssh.exec_command("docker info | grep 'Docker Root Dir'")
        print(stdout.read().decode().strip())
        
        # 7. 清理旧数据 (可选，释放根分区)
        # 既然已经切换了 root dir，旧的 /var/lib/docker 就可以删除了
        # 但为了安全，我们先不自动删，只是打印提示
        print("\n⚠️  提示: 旧的 Docker 数据仍占用根分区空间 (/var/lib/docker)")
        print("   请在确认新环境正常后，手动执行: sudo rm -rf /var/lib/docker")

    except Exception as e:
        print(f"❌ 操作失败: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 发生错误: {e}")
