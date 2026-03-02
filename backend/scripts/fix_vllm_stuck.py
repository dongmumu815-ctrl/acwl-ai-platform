import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance, AppDeployment, AppStatus
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
import paramiko

async def main():
    print("🚀 开始检查 Docker 配置并重置部署状态...")
    
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
            print("⚠️  未找到处于安装或部署中的 vLLM 部署")
            return
            
        print(f"🔍 找到 {len(deployments)} 个活跃部署:")
        
        for deploy in deployments:
            if "vllm" not in deploy.instance.name.lower() and "vllm" not in str(deploy.instance.config).lower():
                continue
                
            server = deploy.server
            print(f"\n--- 部署 ID: {deploy.id} (实例: {deploy.instance.name}) ---")
            print(f"服务器: {server.ip_address}")
            
            # SSH 连接并检查状态
            is_root_dir_safe = await check_and_cleanup_server(server, deploy.instance_id)
            
            # 无论如何，都重置部署状态为 error，以便用户重试
            print(f"\n🔄 重置部署状态为 'error'...")
            deploy.status = "error"
            deploy.instance.status = AppStatus.error
            deploy.container_id = "Deploy failed: Disk full or process hung"
            await db.commit()
            print("✅ 状态已重置")

async def check_and_cleanup_server(server, instance_id):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 简化连接逻辑
        connect_kwargs = {
            "hostname": server.ip_address,
            "port": server.ssh_port,
            "username": server.ssh_username,
            "timeout": 10
        }
        if server.ssh_password:
            connect_kwargs["password"] = server.ssh_password
        if getattr(server, "ssh_key_path", None) and os.path.exists(server.ssh_key_path):
             connect_kwargs["key_filename"] = server.ssh_key_path
             
        ssh.connect(**connect_kwargs)
        
        # 1. 检查 Docker Root Dir
        print("🐳 检查 Docker Root Dir...")
        stdin, stdout, stderr = ssh.exec_command("docker info | grep 'Docker Root Dir'")
        root_dir_info = stdout.read().decode().strip()
        print(f"   {root_dir_info}")
        
        # 判断是否在根分区
        is_safe = False
        if "/var/lib/docker" in root_dir_info:
            print("⚠️  警告: Docker 使用默认路径 /var/lib/docker，位于根分区，空间紧张！")
        elif "/data" in root_dir_info:
            print("✅ Docker 已配置到数据分区")
            is_safe = True
        else:
            print(f"ℹ️  Docker 路径: {root_dir_info}")
            
        # 2. 尝试停止卡住的 docker compose 进程
        print("\n🛑 尝试停止卡住的 docker compose 进程...")
        # 查找包含 instance_id 的 compose 进程
        cmd = f"ps aux | grep 'docker compose' | grep '{instance_id}' | grep -v grep | awk '{{print $2}}'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        pids = stdout.read().decode().strip().split()
        
        if pids:
            print(f"   找到进程 PID: {pids}")
            kill_cmd = f"sudo kill -9 {' '.join(pids)}"
            stdin, stdout, stderr = ssh.exec_command(kill_cmd)
            print(f"   已发送 kill 信号")
        else:
            print("   未找到相关进程")
            
        # 3. 清理部分 Docker 缓存以释放急救空间
        print("\n🧹 尝试清理未使用的 Docker 数据 (prune)...")
        # 注意：这可能会删除其他未运行容器的镜像，需谨慎。但在磁盘已满情况下是必要的。
        # 使用 -f 强制执行
        stdin, stdout, stderr = ssh.exec_command("docker system prune -f")
        prune_out = stdout.read().decode().strip()
        print(f"   清理结果:\n{prune_out}")
        
        return is_safe
            
    except Exception as e:
        print(f"❌ SSH 操作失败: {e}")
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 发生错误: {e}")
