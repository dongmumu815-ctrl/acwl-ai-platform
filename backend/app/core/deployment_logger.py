
from typing import Dict, List, Set
from fastapi import WebSocket
import asyncio
import logging
import time

logger = logging.getLogger(__name__)

class DeploymentLogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeploymentLogger, cls).__new__(cls)
            cls._instance.logs: Dict[str, List[str]] = {}
            cls._instance.connections: Dict[str, Set[WebSocket]] = {}
            cls._instance.loop = None
        return cls._instance

    def set_loop(self, loop):
        self._instance.loop = loop
        logger.info(f"DeploymentLogger loop set: {loop}")

    async def connect(self, channel_id: str, websocket: WebSocket):
        await websocket.accept()
        if channel_id not in self.connections:
            self.connections[channel_id] = set()
        self.connections[channel_id].add(websocket)
        
        # Send history
        if channel_id in self.logs:
            # Join logs to reduce network overhead if many lines
            # But streaming is better for real-time feel. 
            # For history, batching is fine.
            history = "".join(self.logs[channel_id])
            if history:
                await websocket.send_text(history)

    def disconnect(self, channel_id: str, websocket: WebSocket):
        if channel_id in self.connections:
            self.connections[channel_id].discard(websocket)
            if not self.connections[channel_id]:
                del self.connections[channel_id]
                # Optional: Clean up logs after some time or if empty
                # For now, keep logs until server restart or manual clean

    async def log(self, channel_id: str, message: str):
        """Async log method"""
        if channel_id not in self.logs:
            self.logs[channel_id] = []
        
        # Add newline if not present, to ensure proper formatting
        if not message.endswith('\n'):
            message += '\n'
            
        timestamp = time.strftime("[%H:%M:%S] ", time.localtime())
        full_message = f"{timestamp}{message}"
        
        self.logs[channel_id].append(full_message)
        
        # Broadcast
        if channel_id in self.connections:
            for connection in list(self.connections[channel_id]):
                try:
                    await connection.send_text(full_message)
                except Exception:
                    self.disconnect(channel_id, connection)

    def log_sync(self, channel_id: str, message: str):
        """Sync log method for use in threads"""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.log(channel_id, message), self.loop)
        else:
            # Fallback if loop not set or running (should not happen in FastAPI app)
            logger.warning(f"DeploymentLogger loop not ready (loop={self.loop}, running={self.loop.is_running() if self.loop else 'N/A'}), dropping log: {message}")

    def clear(self, channel_id: str):
        if channel_id in self.logs:
            del self.logs[channel_id]

deployment_logger = DeploymentLogger()
