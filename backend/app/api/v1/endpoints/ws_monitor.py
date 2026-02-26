from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
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

def format_size(kb: int) -> str:
    """Convert KB to human readable string"""
    if not kb:
        return "0 B"
    if kb < 1024:
        return f"{kb} KB"
    if kb < 1024 * 1024:
        return f"{kb / 1024:.1f} MB"
    if kb < 1024 * 1024 * 1024:
        return f"{kb / (1024 * 1024):.1f} GB"
    return f"{kb / (1024 * 1024 * 1024):.1f} TB"

class MonitorSession:
    def __init__(self, websocket: WebSocket, server: Server, db: AsyncSession):
        self.websocket = websocket
        self.server = server
        self.db = db
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.monitoring = False
        self.info_updated = False  # Flag to track if we've updated DB info
        self.task = None

    async def _update_db_info(self, mem_kb: int, disk_kb: int):
        """Auto-update server hardware info in DB if missing"""
        try:
            mem_str = format_size(mem_kb)
            disk_str = format_size(disk_kb)
            
            # Check if update is needed (only if currently empty or 0)
            should_update = False
            if not self.server.total_memory or self.server.total_memory == "0 B" or self.server.total_memory == "0":
                should_update = True
            if not self.server.total_storage or self.server.total_storage == "0 B" or self.server.total_storage == "0":
                should_update = True
                
            if should_update:
                stmt = (
                    update(Server)
                    .where(Server.id == self.server.id)
                    .values(
                        total_memory=mem_str,
                        total_storage=disk_str
                    )
                )
                await self.db.execute(stmt)
                await self.db.commit()
                logging.info(f"Auto-updated server {self.server.id} hardware info: Mem={mem_str}, Disk={disk_str}")
                
                # Update local object too
                self.server.total_memory = mem_str
                self.server.total_storage = disk_str
        except Exception as e:
            logging.error(f"Failed to auto-update server info: {str(e)}")

    async def connect(self):
        """Establish SSH connection."""
        try:
            logging.info(f"Attempting SSH connection to {self.server.ip_address}:{self.server.ssh_port}")
            loop = asyncio.get_event_loop()
            
            await loop.run_in_executor(
                None, 
                lambda: self.client.connect(
                    hostname=self.server.ip_address,
                    port=self.server.ssh_port,
                    username=self.server.ssh_username,
                    password=self.server.ssh_password,
                    key_filename=self.server.ssh_key_path or None,
                    timeout=10,
                    allow_agent=False,
                    look_for_keys=False
                )
            )
            logging.info(f"SSH connection established for {self.server.ip_address}")
            
            self.monitoring = True
            self.task = asyncio.create_task(self.start_monitoring())
            
        except Exception as e:
            logging.error(f"SSH connection failed for {self.server.ip_address}: {str(e)}")
            await self.websocket.send_json({
                "type": "error",
                "message": f"SSH connection failed: {str(e)}"
            })
            raise

    async def start_monitoring(self):
        """Start monitoring loop."""
        loop = asyncio.get_event_loop()
        
        while self.monitoring:
            try:
                def execute_ssh_command():
                    # Check connection
                    if not self.client.get_transport() or not self.client.get_transport().is_active():
                        # Try to reconnect
                        self.client.connect(
                            hostname=self.server.ip_address,
                            port=self.server.ssh_port,
                            username=self.server.ssh_username,
                            password=self.server.ssh_password,
                            key_filename=self.server.ssh_key_path or None,
                            timeout=10,
                            allow_agent=False,
                            look_for_keys=False
                        )

                    # Command to get CPU, Memory, Disk usage
                    # CPU: top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}'
                    # Memory: free -m | awk 'NR==2{printf "%.2f", $3*100/$2 }'
                    # Disk: df -h / | awk '$NF=="/"{printf "%s", $5}'
                    # GPU: nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits
                    
                    # 使用 bash 执行以确保兼容性，并初始化变量防止报错中断
                    cmd = r"""
export PATH=$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/cuda/bin
export LC_ALL=C

# Init defaults to avoid empty output
cpu_usage=0
mem_percent=0
gpu_info="0:0:0:0"
disk_data=""
mem_total=0
mem_used=0

# 1. CPU Usage
{
    read cpu user nice system idle iowait irq softirq steal guest < /proc/stat
    total1=$((user+nice+system+idle+iowait+irq+softirq+steal))
    idle1=$idle
    sleep 1
    read cpu user nice system idle iowait irq softirq steal guest < /proc/stat
    total2=$((user+nice+system+idle+iowait+irq+softirq+steal))
    idle2=$idle
    diff_total=$((total2-total1))
    diff_idle=$((idle2-idle1))
    if [ "$diff_total" -ne 0 ]; then
      cpu_usage=$((100*(diff_total-diff_idle)/diff_total))
    fi
} || true

# 2. Memory Usage (KB)
{
    mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    mem_avail=$(grep MemAvailable /proc/meminfo | awk '{print $2}')

    if [ -z "$mem_total" ]; then mem_total=0; fi
    if [ -z "$mem_avail" ]; then
        mem_free=$(grep MemFree /proc/meminfo | awk '{print $2}')
        mem_buffers=$(grep Buffers /proc/meminfo | awk '{print $2}')
        mem_cached=$(grep ^Cached /proc/meminfo | awk '{print $2}')
        
        if [ -z "$mem_free" ]; then mem_free=0; fi
        if [ -z "$mem_buffers" ]; then mem_buffers=0; fi
        if [ -z "$mem_cached" ]; then mem_cached=0; fi
        
        mem_avail=$((mem_free + mem_buffers + mem_cached))
    fi

    mem_used=$((mem_total - mem_avail))
    if [ "$mem_total" -gt 0 ]; then
        mem_percent=$(awk -v used="$mem_used" -v total="$mem_total" 'BEGIN {printf "%.1f", used*100/total}')
    fi
} || true

# 3. Disk Usage (KB)
{
    disk_data=$(df -P -k | grep -vE '^Filesystem|tmpfs|devtmpfs|overlay|iso9660|none|udev' | awk '{print $6 ":" $2 ":" $3}' | tr '\n' ';' | sed 's/;$//')
    if [ -z "$disk_data" ]; then
        disk_data=$(df -P -k / | awk 'NR==2 {print $6 ":" $2 ":" $3}')
    fi
} || true

# 4. GPU info
{
    if command -v nvidia-smi &> /dev/null; then
        gpu_stats=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits)
        if [ -n "$gpu_stats" ]; then
            gpu_info=$(echo "$gpu_stats" | awk -F', ' '{util+=$1; used+=$2; total+=$3; n++} END {if (n > 0) printf "%.1f:%d:%d:%d", util/n, used, total, n; else print "0:0:0:0"}')
        fi
    fi
} || true

# 输出格式: CPU% | Mem% | GPU_Info(Util:Used:Total:Count) | DiskData | MemTotal(KB) | MemUsed(KB)
# 使用默认值确保始终有输出
echo "${cpu_usage:-0}|${mem_percent:-0}|${gpu_info:-0:0:0:0}|${disk_data}|${mem_total:-0}|${mem_used:-0}"
"""

                    stdin, stdout, stderr = self.client.exec_command(cmd)
                    return stdout.read().decode().strip(), stderr.read().decode().strip()

                output, error = await loop.run_in_executor(None, execute_ssh_command)
                
                if error:
                    logging.warning(f"SSH command error for {self.server.ip_address}: {error}")

                if output:
                    # logging.info(f"Monitor output for {self.server.ip_address}: {output}")
                    parts = output.split('|')
                    if len(parts) >= 6:
                        cpu_usage = round(float(parts[0]), 1) if parts[0] else 0
                        mem_usage = round(float(parts[1]), 1) if parts[1] else 0
                        
                        # Parse GPU Info
                        gpu_util = 0.0
                        gpu_mem_used = 0
                        gpu_mem_total = 0
                        gpu_count = 0
                        
                        if parts[2] and ':' in parts[2]:
                            g_parts = parts[2].split(':')
                            if len(g_parts) >= 4:
                                gpu_util = round(float(g_parts[0]), 1)
                                gpu_mem_used = int(g_parts[1])  # MB
                                gpu_mem_total = int(g_parts[2]) # MB
                                gpu_count = int(g_parts[3])

                        disk_str = parts[3]
                        mem_total_kb = int(parts[4]) if parts[4] else 0
                        mem_used_kb = int(parts[5]) if parts[5] else 0
                        
                        disk_details = []
                        max_disk_usage = 0.0
                        
                        if disk_str:
                            for item in disk_str.split(';'):
                                if ':' in item:
                                    # mount:total:used
                                    d_parts = item.split(':')
                                    if len(d_parts) >= 3:
                                        mount = d_parts[0]
                                        try:
                                            total_kb = int(d_parts[1])
                                            used_kb = int(d_parts[2])
                                            
                                            usage_pct = 0.0
                                            if total_kb > 0:
                                                usage_pct = round(used_kb * 100 / total_kb, 1)
                                            
                                            disk_details.append({
                                                "mount_point": mount,
                                                "usage": usage_pct,
                                                "total_kb": total_kb,
                                                "used_kb": used_kb
                                            })
                                            if usage_pct > max_disk_usage:
                                                max_disk_usage = usage_pct
                                        except ValueError:
                                            continue

                        # Auto-update DB info if needed (only once per session or if missing)
                        if not self.info_updated and mem_total_kb > 0:
                            total_storage_kb = sum(d['total_kb'] for d in disk_details) if disk_details else 0
                            if total_storage_kb > 0:
                                await self._update_db_info(mem_total_kb, total_storage_kb)
                                self.info_updated = True

                        data = {
                            "cpu_usage": cpu_usage,
                            "memory_usage": mem_usage,
                            "memory_total_kb": mem_total_kb,
                            "memory_used_kb": mem_used_kb,
                            "gpu_usage": gpu_util,
                            "gpu_count": gpu_count,
                            "gpu_memory_used": gpu_mem_used,
                            "gpu_memory_total": gpu_mem_total,
                            "disk_usage": max_disk_usage,
                            "disk_details": disk_details
                        }
                        
                        await self.websocket.send_json({
                            "type": "monitor_data",
                            "data": data
                        })
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logging.error(f"Error reading monitor data for {self.server.ip_address}: {str(e)}")
                break

    async def close(self):
        self.monitoring = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
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
        session = MonitorSession(websocket, server, db)
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
