
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from app.core.deployment_logger import deployment_logger

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/deploy/{instance_id}")
async def websocket_deploy_log(websocket: WebSocket, instance_id: int):
    channel_id = f"instance_{instance_id}"
    await deployment_logger.connect(channel_id, websocket)
    try:
        while True:
            # Just keep connection alive
            # We don't expect client to send much, maybe ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        deployment_logger.disconnect(channel_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {channel_id}: {e}")
        deployment_logger.disconnect(channel_id, websocket)
