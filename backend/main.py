import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.models.database import init_db
from backend.services.websocket_manager import ws_manager
from backend.routers import (
    webhooks_router,
    security_router,
    pipeline_router,
    dashboard_router,
    websocket_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event to automatically initialize SQLite database tables and WebSocket loop."""
    init_db()
    try:
        ws_manager.set_loop(asyncio.get_running_loop())
    except Exception:
        pass
    yield


app = FastAPI(
    title="Autonomous DevOps & CI/CD Pipeline Health Dashboard",
    description=(
        "Autonomous DevOps backend monitoring pipeline runs, pull requests, "
        "and simulated GitHub/GitLab webhook events with integrated static analysis diff scanning."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(webhooks_router)
app.include_router(security_router)
app.include_router(pipeline_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)

# Mount frontend static directory if present
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    css_dir = os.path.join(frontend_dir, "css")
    js_dir = os.path.join(frontend_dir, "js")
    dist_assets = os.path.join(frontend_dir, "dist", "assets")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    if os.path.exists(dist_assets):
        app.mount("/assets", StaticFiles(directory=dist_assets), name="assets")


@app.get("/dashboard", summary="Interactive Web Telemetry Dashboard")
def serve_dashboard():
    dist_index = os.path.join(frontend_dir, "dist", "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"status": "Frontend UI not found"})


@app.get("/", summary="Root Health and API Index")
def root():
    return {
        "service": "Autonomous DevOps & CI/CD Pipeline Health Dashboard API",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "webhooks_github": "POST /api/v1/webhooks/github",
            "webhooks_gitlab": "POST /api/v1/webhooks/gitlab",
            "simulate_push": "POST /api/v1/webhooks/simulate/push",
            "simulate_pr": "POST /api/v1/webhooks/simulate/pull-request",
            "simulate_build": "POST /api/v1/webhooks/simulate/build-status",
            "pipeline_health": "GET /api/v1/pipeline/health",
            "pipeline_runs": "GET /api/v1/pipeline/runs",
            "security_scan_diff": "POST /api/v1/security/scan-diff",
            "security_findings": "GET /api/v1/security/findings",
            "dashboard_summary": "GET /api/v1/dashboard/summary",
            "websocket_telemetry": "WS /api/v1/ws",
            "websocket_status": "GET /api/v1/ws/status",
        },
    }


if __name__ == "__main__":
    import uvicorn
    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError:
        port = 8000
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
