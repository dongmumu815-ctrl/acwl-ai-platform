import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance, AppDeployment
from app.models.server import Server
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
import paramiko

async def main():
    print("🚀 开始 SSH 诊断 vLLM 部署状态...")
    
    async with AsyncSessionLocal() as db:
        # 1. 查找状态为 installing 或 deploying 的部署
        stmt = select(AppDeployment).options(
            selectinload(AppDeployment.server),
            selectinload(AppDeployment.instance)
        ).where(
            AppDeployment.status.in_(["installing", "deploying"])
        ).order_by(desc(AppDeployment.updated_at)).limit(5)
        
        result = await db.execute(stmt)
        deployments = result.scalars().all()
        
        if not deployments:
            print("❌ 未找到处于安装或部署中的 vLLM 部署")
            return
            
        print(f"🔍 找到 {len(deployments)} 个活跃部署:")
        
        for deploy in deployments:
            if "vllm" not in deploy.instance.name.lower() and "vllm" not in str(deploy.instance.config).lower():
                continue
                
            server = deploy.server
            print(f"\n--- 部署 ID: {deploy.id} (实例: {deploy.instance.name}) ---")
            print(f"服务器: {server.ip_address} ({server.name})")
            print(f"状态: {deploy.status}")
            print(f"容器信息: {deploy.container_id}")
            
            # SSH 连接并检查状态
            await check_server_status(server, deploy.instance_id)

async def check_server_status(server, instance_id):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"📡 连接服务器 {server.ip_address}...")
        
        # 简化连接逻辑，直接使用密码或密钥
        connect_kwargs = {
            "hostname": server.ip_address,
            "port": server.ssh_port,
            "username": server.ssh_username,
            "timeout": 10
        }
        
        if server.ssh_password:
            connect_kwargs["password"] = server.ssh_password
        
        # 如果有密钥路径，也尝试添加（但在这种简单脚本中可能比较麻烦，先只支持密码或默认密钥）
        # 这里假设 server.ssh_key_path 是绝对路径
        if getattr(server, "ssh_key_path", None) and os.path.exists(server.ssh_key_path):
             connect_kwargs["key_filename"] = server.ssh_key_path
             
        ssh.connect(**connect_kwargs)
        
        # 1. 检查目录是否存在
        deploy_path = f"/opt/acwl-apps/instances/{instance_id}"
        stdin, stdout, stderr = ssh.exec_command(f"ls -ld {deploy_path}")
        output = stdout.read().decode().strip()
        if not output:
            print(f"❌ 部署目录不存在: {deploy_path}")
            return
        print(f"✅ 部署目录存在: {output}")
        
        # 2. 检查 docker-compose.yml
        stdin, stdout, stderr = ssh.exec_command(f"cat {deploy_path}/docker-compose.yml")
        compose_content = stdout.read().decode().strip()
        if not compose_content:
             print("❌ docker-compose.yml 为空或不存在")
        else:
             print(f"📄 docker-compose.yml 内容预览:\n{compose_content[:200]}...")

        # 3. 检查 Docker 容器状态
        # 假设容器名包含 instance_id 或 vllm
        # 先列出所有容器
        print("\n🐳 Docker 容器状态:")
        stdin, stdout, stderr = ssh.exec_command("docker ps -a --format 'table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}' | grep vllm")
        containers = stdout.read().decode().strip()
        print(containers if containers else "⚠️  未找到 vLLM 相关容器")
        
        # 5. 检查系统进程
        print("\n🔎 正在检查 Docker 相关进程:")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'docker|compose' | grep -v grep")
        processes = stdout.read().decode().strip()
        print(processes if processes else "⚠️  未发现正在运行的 Docker/Compose 进程")
        
        # 6. 检查磁盘空间
        print("\n💾 磁盘空间使用情况:")
        stdin, stdout, stderr = ssh.exec_command("df -h /opt/acwl-apps")
        disk = stdout.read().decode().strip()
        print(disk if disk else "❌ 无法获取磁盘空间信息")

        # 7. 手动尝试拉取镜像（如果未运行）
        if not processes and not containers:
            print("\n⚠️  既无容器也无进程，尝试手动验证 docker-compose 配置:")
            cmd = f"cd {deploy_path} && docker compose config"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            config_out = stdout.read().decode().strip()
            config_err = stderr.read().decode().strip()
            if config_err:
                print(f"❌ Docker Compose 配置验证失败:\n{config_err}")
            else:
                print("✅ Docker Compose 配置验证通过")
            
    except Exception as e:
        print(f"❌ SSH 连接或执行失败: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 发生错误: {e}")
