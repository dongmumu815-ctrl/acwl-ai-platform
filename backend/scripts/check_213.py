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
    print(f"🚀 开始诊断服务器 {target_ip} 的 Docker 配置与 Harbor 连接性...")
    
    async with AsyncSessionLocal() as db:
        # 获取服务器信息
        stmt = select(Server).where(Server.ip_address == target_ip)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()
        
        if not server:
            print(f"❌ 未在数据库中找到服务器: {target_ip}")
            return
            
        await check_server(server)

async def check_server(server):
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
        
        # 1. 检查 Docker Root Dir
        print("\n[1/3] 检查 Docker Root Dir...")
        stdin, stdout, stderr = ssh.exec_command("docker info | grep 'Docker Root Dir'")
        root_dir = stdout.read().decode().strip()
        print(f"   {root_dir}")
        if "/data/dockers" in root_dir:
            print("   ✅ Docker Root Dir 迁移成功")
        else:
            print(f"   ⚠️  Docker Root Dir 似乎未迁移: {root_dir}")

        # 2. 检查 daemon.json 内容 (特别是 insecure-registries)
        print("\n[2/3] 检查 /etc/docker/daemon.json...")
        stdin, stdout, stderr = ssh.exec_command("sudo cat /etc/docker/daemon.json")
        config_content = stdout.read().decode().strip()
        print(f"   当前配置:\n{config_content}")
        
        try:
            config = json.loads(config_content)
            insecure = config.get("insecure-registries", [])
            print(f"   insecure-registries: {insecure}")
            
            harbor_ip = "10.20.1.204:5000"
            if harbor_ip in insecure:
                print(f"   ✅ 已包含 Harbor 地址 {harbor_ip}")
            else:
                print(f"   ❌ 缺少 Harbor 地址 {harbor_ip}，这会导致拉取镜像失败！")
        except Exception as e:
            print(f"   ❌ 解析 JSON 失败: {e}")

        # 3. 检查网络连接性 (ping 和 telnet/curl)
        print("\n[3/3] 检查 Harbor 网络连接性 (10.20.1.204:5000)...")
        
        # Ping
        stdin, stdout, stderr = ssh.exec_command("ping -c 3 10.20.1.204")
        if stdout.channel.recv_exit_status() == 0:
             print("   ✅ Ping 10.20.1.204 成功")
        else:
             print("   ❌ Ping 10.20.1.204 失败")
             
        # Curl
        stdin, stdout, stderr = ssh.exec_command("curl -v http://10.20.1.204:5000/v2/")
        output = stdout.read().decode() + stderr.read().decode()
        if "200 OK" in output or "401 Unauthorized" in output:
             print("   ✅ Curl http://10.20.1.204:5000/v2/ 成功 (服务可达)")
        elif "Connection refused" in output:
             print("   ❌ Connection refused (服务未启动或端口不通)")
        else:
             print(f"   ⚠️  Curl 结果异常:\n{output[:200]}...")

    except Exception as e:
        print(f"❌ 操作失败: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 发生错误: {e}")
