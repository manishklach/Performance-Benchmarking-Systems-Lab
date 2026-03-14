from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .web_snapshot import SnapshotCollector, frontend_root


def create_app(refresh_seconds: float = 2.0) -> FastAPI:
    collector = SnapshotCollector()
    app = FastAPI(title="AMD APU Browser Dashboard")
    web_root = frontend_root()
    static_root = web_root / "static"
    app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.get("/api/snapshot")
    async def api_snapshot():
        return collector.collect()

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
