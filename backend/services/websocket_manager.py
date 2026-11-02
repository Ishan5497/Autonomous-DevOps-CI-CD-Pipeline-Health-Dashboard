import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import WebSocket

logger = logging.getLogger("autonomous_devops.websocket")


def _get_utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WebSocketManager:
    """
    Manages active WebSocket client connections and broadcasts real-time
    pipeline execution updates, build failures, and security alerts.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Stores the running asyncio event loop for threadsafe / sync dispatch."""
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        """Accepts a new incoming WebSocket connection and registers it."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Removes a disconnected WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcasts a JSON-serializable message to all active WebSocket clients.
        Automatically purges stale/dead connections.
        """
        if not self.active_connections:
            return

        dead_connections: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning(f"Error sending message to client: {exc}. Marking for removal.")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    def broadcast_sync(self, message: Dict[str, Any]):
        """
        Thread-safe and sync-friendly broadcast dispatch.
        Can be called from sync endpoints, background threads, or services.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = self._loop

        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
        else:
            try:
                asyncio.run(self.broadcast(message))
            except Exception as e:
                logger.error(f"Failed to dispatch sync broadcast: {e}")

    # ==========================================
    # High-level domain broadcast methods
    # ==========================================

    def broadcast_pipeline_update(
        self,
        run_data: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None,
    ):
        """Broadcasts a pipeline execution update (created, running, success, etc.)."""
        event = {
            "type": "PIPELINE_UPDATE",
            "timestamp": _get_utc_now_iso(),
            "data": run_data,
            "metrics": metrics,
        }
        self.broadcast_sync(event)

    def broadcast_build_failure(
        self,
        run_data: Dict[str, Any],
        failure_reason: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ):
        """Broadcasts a high-priority build or gate failure."""
        failure_payload = dict(run_data)
        if failure_reason:
            failure_payload["failure_reason"] = failure_reason

        event = {
            "type": "BUILD_FAILURE",
            "timestamp": _get_utc_now_iso(),
            "data": failure_payload,
            "metrics": metrics,
        }
        self.broadcast_sync(event)

    def broadcast_security_alert(
        self,
        findings: List[Dict[str, Any]],
        repository: str,
        commit_sha: Optional[str] = None,
        file_path: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ):
        """Broadcasts a critical security alert (secret leak, dangerous function, vulnerability)."""
        critical_count = sum(1 for f in findings if f.get("severity") == "CRITICAL")
        high_count = sum(1 for f in findings if f.get("severity") == "HIGH")

        event = {
            "type": "SECURITY_ALERT",
            "timestamp": _get_utc_now_iso(),
            "data": {
                "repository": repository,
                "commit_sha": commit_sha or "unknown",
                "file_path": file_path,
                "findings_count": len(findings),
                "critical_count": critical_count,
                "high_count": high_count,
                "findings": findings,
                "is_safe": False,
            },
            "metrics": metrics,
        }
        self.broadcast_sync(event)

    def broadcast_metrics_update(self, metrics: Dict[str, Any]):
        """Broadcasts real-time computed health metrics to update dashboard counters."""
        event = {
            "type": "METRICS_UPDATE",
            "timestamp": _get_utc_now_iso(),
            "metrics": metrics,
        }
        self.broadcast_sync(event)


# Global singleton instance
ws_manager = WebSocketManager()

