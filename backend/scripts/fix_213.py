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
    target_ip = "10.20.1.213"
    print(f"🚀 开始修复服务器 {target_ip} 的 Docker 配置...")
    
    async with AsyncSessionLocal() as db:
        # 获取服务器信息
        stmt = select(Server).where(Server.ip_address == target_ip)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()
        
        if not server:
            print(f"❌ 未在数据库中找到服务器: {target_ip}")
            return
            
        await fix_server(server)

async def fix_server(server):
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
        print(f"✅ 已连接到 {server.ip_address}")
        
        # 1. 修复 daemon.json
        print("⚙️  正在修复 /etc/docker/daemon.json ...")
        
        # 完整的标准配置
        new_config = {
            "data-root": "/data/dockers",
            "insecure-registries": ["10.20.1.204:5000"],
            "log-driver": "json-file",
            "log-opts": {
                "max-size": "100m",
                "max-file": "3"
            }
        }
        
        # 写入临时文件
        tmp_file = "/tmp/daemon.json.fix"
        sftp = ssh.open_sftp()
        with sftp.file(tmp_file, 'w') as f:
            f.write(json.dumps(new_config, indent=4))
        sftp.close()
        
        # 覆盖
        cmd_mv = f"echo '{server.ssh_password}' | sudo -S mv {tmp_file} /etc/docker/daemon.json"
        ssh.exec_command(cmd_mv)
        print("✅ 配置文件已更新")

        # 2. 重启 Docker
        print("🔄 重启 Docker 服务...")
        stdin, stdout, stderr = ssh.exec_command(f"echo '{server.ssh_password}' | sudo -S systemctl restart docker")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
             print(f"❌ 重启 Docker 失败: {stderr.read().decode()}")
             return
        print("✅ Docker 服务已重启")

        # 3. 再次验证连接
        print("🔍 验证 Harbor 连接性...")
        stdin, stdout, stderr = ssh.exec_command("curl -v http://10.20.1.204:5000/v2/")
        output = stdout.read().decode() + stderr.read().decode()
        
        if "200 OK" in output or "401 Unauthorized" in output:
             print("✅ Harbor 连接成功！")
        else:
             print(f"❌ Harbor 连接仍然失败: {output[:100]}...")

    except Exception as e:
        print(f"❌ 操作失败: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 发生错误: {e}")
