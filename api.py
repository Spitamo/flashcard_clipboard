from __future__ import annotations
import asyncio
from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.persistence.db import SqliteDB
from config import Config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        self._clients.remove(ws)

    async def broadcast(self, data: dict[str, Any]):
        for ws in list(self._clients):
            try:
                await ws.send_json(data)
            except Exception:
                self._clients.remove(ws)

manager = ConnectionManager()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()   
    except WebSocketDisconnect:
        manager.disconnect(ws)

@app.get("/flashcards")
def get_flashcards():
    cfg = Config()
    db = SqliteDB(cfg.sqlite_path)
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT source_text, translated_text, captured_at "
            "FROM flashcards ORDER BY captured_at DESC"
        ).fetchall()
    return [
        {"source": r[0], "translation": r[1], "captured_at": r[2]}
        for r in rows
    ]

async def notify_new_card(source: str, translation: str, captured_at: float):
    await manager.broadcast({
        "source": source,
        "translation": translation,
        "captured_at": captured_at,
    })