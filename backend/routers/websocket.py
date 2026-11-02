import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.models.database import SessionLocal
from backend.services.websocket_manager import ws_manager
from backend.services.pipeline_health import PipelineHealthService

logger = logging.getLogger("autonomous_devops.websocket_router")
router = APIRouter(tags=["Real-Time WebSockets"])


def _get_health_metrics_dict() -> Dict[str, Any]:
    with SessionLocal() as db:
        metrics = PipelineHealthService.calculate_health(db)
        return metrics.model_dump()


@router.websocket("/ws")
@router.websocket("/api/v1/ws")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """
    Real-time telemetry WebSocket stream for connected frontend clients and monitors.
    Broadcasts live pipeline updates, build failures, and security alerts.
    """
    await ws_manager.connect(websocket)

    # Dispatch initial handshake with current system metrics
    try:
        current_metrics = _get_health_metrics_dict()
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to Autonomous DevOps Real-Time Telemetry Stream",
            "metrics": current_metrics,
        })
    except Exception as exc:
        logger.warning(f"Failed to send initial handshake to client: {exc}")

    try:
        while True:
            raw_text = await websocket.receive_text()
            if raw_text == "ping":
                await websocket.send_text("pong")
                continue

            try:
                msg = json.loads(raw_text)
                action = msg.get("action")

                if action == "get_metrics":
                    metrics = _get_health_metrics_dict()
                    await websocket.send_json({
                        "type": "METRICS_UPDATE",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "metrics": metrics,
                    })
                elif action == "ping":
                    await websocket.send_json({"type": "PONG", "timestamp": datetime.now(timezone.utc).isoformat()})
            except json.JSONDecodeError:
                # Text ping or non-json message
                if "ping" in raw_text.lower():
                    await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning(f"WebSocket client error: {exc}")
        ws_manager.disconnect(websocket)


@router.get("/api/v1/ws/status", summary="Get WebSocket Telemetry Service Status")
def get_websocket_status():
    """Returns active client count and telemetry broadcaster status."""
    return {
        "status": "online",
        "active_clients": len(ws_manager.active_connections),
        "endpoint": "/api/v1/ws",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

