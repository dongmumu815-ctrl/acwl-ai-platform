from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import paramiko
import json
import asyncio
import logging
from typing import Optional

from app.core.database import get_db
from app.models.server import Server
from app.api.v1.endpoints.auth import get_current_user_ws

router = APIRouter()
logger = logging.getLogger(__name__)

class MonitorSession:
    def __init__(self, websocket: WebSocket, server: Server):
        self.websocket = websocket
        self.server = server
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.monitoring = False

    async def connect(self):
        try:
            if self.server.ssh_key_path:
                self.client.connect(
                    hostname=self.server.ip_address,
                    port=self.server.ssh_port,
                    username=self.server.ssh_username,
                    key_filename=self.server.ssh_key_path,
                    timeout=10
                )
            else:
                self.client.connect(
                    hostname=self.server.ip_address,
                    port=self.server.ssh_port,
                    username=self.server.ssh_username,
                    password=self.server.ssh_password,
                    timeout=10
                )
            
            self.monitoring = True
            asyncio.create_task(self.start_monitoring())
            
        except Exception as e:
            logger.error(f"SSH connection failed for monitoring: {str(e)}")
            await self.websocket.send_json({"type": "error", "message": f"Connection failed: {str(e)}"})
            await self.close()

    async def start_monitoring(self):
        while self.monitoring:
            try:
                # 使用更精准的Shell脚本获取资源使用情况
                # 1. CPU: 读取 /proc/stat 两次采样计算差值
                # 2. Memory: 优先使用 MemAvailable，兼容旧系统
                # 3. GPU: 检测 nvidia-smi，支持多卡平均
                
                cmd = r"""
export LC_ALL=C

# CPU Usage Calculation
read cpu user nice system idle iowait irq softirq steal guest < /proc/stat
total1=$((user+nice+system+idle+iowait+irq+softirq+steal))
idle1=$idle

sleep 1

read cpu user nice system idle iowait irq softirq steal guest < /proc/stat
total2=$((user+nice+system+idle+iowait+irq+softirq+steal))
idle2=$idle

diff_total=$((total2-total1))
diff_idle=$((idle2-idle1))

if [ $diff_total -eq 0 ]; then
  cpu_usage=0
else
  cpu_usage=$((100*(diff_total-diff_idle)/diff_total))
fi

# Memory Usage Calculation
if grep -q MemAvailable /proc/meminfo; then
    mem_usage=$(awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}END{printf "%.2f", (t-a)/t*100}' /proc/meminfo)
else
    mem_usage=$(awk '/MemTotal/{t=$2}/MemFree/{f=$2}/Buffers/{b=$2}/^Cached/{c=$2}END{printf "%.2f", (t-f-b-c)/t*100}' /proc/meminfo)
fi

# GPU Usage Calculation
gpu_usage=0
gpu_count=0
if command -v nvidia-smi &> /dev/null; then
    gpu_stats=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$gpu_stats" ]; then
        gpu_usage=$(echo "$gpu_stats" | awk '{sum+=$1; n++} END {if (n > 0) print sum/n; else print 0}')
        gpu_count=$(echo "$gpu_stats" | wc -l)
    fi
fi

echo "$cpu_usage,$mem_usage,$gpu_usage,$gpu_count"
"""
                
                stdin, stdout, stderr = self.client.exec_command(cmd)
                output = stdout.read().decode().strip()
                
                if output:
                    parts = output.split(',')
                    if len(parts) >= 4:
                        data = {
                            "cpu_usage": float(parts[0]),
                            "memory_usage": float(parts[1]),
                            "gpu_usage": float(parts[2]),
                            "gpu_count": int(parts[3])
                        }
                        await self.websocket.send_json({"type": "monitor_data", "data": data})
                
                # 这里的sleep可以减少，因为脚本中已经sleep了1秒
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error reading monitor data: {str(e)}")
                # 不中断循环，尝试重试
                await asyncio.sleep(5)

    async def close(self):
        self.monitoring = False
        if self.client:
            self.client.close()

@router.websocket("/monitor/{server_id}")
async def monitor_websocket(
    websocket: WebSocket,
    server_id: int,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    session = None
    
    try:
        # 0. 验证用户身份
        if not token:
            await websocket.send_json({"type": "error", "message": "Missing authentication token"})
            await websocket.close()
            return
            
        user = await get_current_user_ws(token, db)
        if not user:
            await websocket.send_json({"type": "error", "message": "Invalid authentication token"})
            await websocket.close()
            return

        # 1. 获取服务器信息
        result = await db.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()
        
        if not server:
            await websocket.send_json({"type": "error", "message": "Server not found"})
            await websocket.close()
            return

        # 2. 建立监控会话
        session = MonitorSession(websocket, server)
        await session.connect()

        # 3. 保持连接
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info(f"Monitor WebSocket disconnected for server {server_id}")
    except Exception as e:
        logger.error(f"Monitor WebSocket error: {str(e)}")
    finally:
        if session:
            await session.close()
