from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .trace_capture import TraceCaptureManager
from .web_snapshot import SnapshotCollector, frontend_root


def create_app(refresh_seconds: float = 2.0) -> FastAPI:
    trace_manager = TraceCaptureManager()
    collector = SnapshotCollector(trace_manager=trace_manager)
    app = FastAPI(title="AMD APU Browser Dashboard")
    web_root = frontend_root()
    static_root = web_root / "static"
    app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.get("/api/snapshot")
    async def api_snapshot():
        return collector.collect()

    @app.get("/api/trace/status")
    async def api_trace_status():
        return trace_manager.status()

    @app.post("/api/trace/start")
    async def api_trace_start(payload: dict | None = None):
        body = payload or {}
        profiles = body.get("profiles")
        duration = int(body.get("duration_sec") or 15)
        return trace_manager.start_capture(profiles=profiles, duration_sec=duration)

    @app.post("/api/trace/stop")
    async def api_trace_stop():
        return trace_manager.stop_capture(reason="manual")

    @app.get("/")
    async def index():
        return FileResponse(web_root / "index.html")

    @app.websocket("/ws/live")
    async def ws_live(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                await websocket.send_json(collector.collect())
                await asyncio.sleep(refresh_seconds)
        except WebSocketDisconnect:
            return
        except Exception:
            try:
                await websocket.close()
            except RuntimeError:
                return

    return app


def run_web_server(host: str, port: int, refresh_seconds: float) -> None:
    app = create_app(refresh_seconds=refresh_seconds)
    uvicorn.run(app, host=host, port=port, log_level="warning")
