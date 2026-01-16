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

class SSHSession:
    def __init__(self, websocket: WebSocket, server: Server):
        self.websocket = websocket
        self.server = server
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.channel = None
        self.listening = False

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
            
            # 开启交互式shell
            self.channel = self.client.invoke_shell(term='xterm')
            self.channel.setblocking(0)
            self.listening = True
            
            # 开始监听SSH输出
            asyncio.create_task(self.listen_to_ssh())
            
        except Exception as e:
            logger.error(f"SSH connection failed: {str(e)}")
            await self.websocket.send_json({"type": "error", "message": f"Connection failed: {str(e)}"})
            await self.close()

    async def listen_to_ssh(self):
        while self.listening:
            try:
                if self.channel.recv_ready():
                    data = self.channel.recv(4096).decode('utf-8', errors='ignore')
                    if data:
                        await self.websocket.send_json({"type": "output", "data": data})
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error reading from SSH: {str(e)}")
                break

    async def handle_message(self, message: dict):
        if not self.channel:
            return

        msg_type = message.get("type")
        
        if msg_type == "input":
            data = message.get("data")
            if data:
                self.channel.send(data)
        
        elif msg_type == "resize":
            rows = message.get("rows")
            cols = message.get("cols")
            if rows and cols:
                self.channel.resize_pty(width=cols, height=rows)

    async def close(self):
        self.listening = False
        if self.client:
            self.client.close()

@router.websocket("/ssh/{server_id}")
async def ssh_websocket(
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

        # 2. 建立SSH会话
        session = SSHSession(websocket, server)
        await session.connect()

        # 3. 处理WebSocket消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await session.handle_message(message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for server {server_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        if session:
            await session.close()
