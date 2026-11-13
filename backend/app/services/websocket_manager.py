"""
FastAPI WebSocket connection manager.
Maintains a set of active client connections and broadcasts messages.
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """Manages all active WebSocket client connections."""

    def __init__(self):
        self._active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.add(ws)
        logger.info(f"WS client connected. Total: {len(self._active)}")

    def disconnect(self, ws: WebSocket) -> None:
        self._active.discard(ws)
        logger.info(f"WS client disconnected. Total: {len(self._active)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Send a JSON message to all connected clients."""
        if not self._active:
            return
        payload = json.dumps(message, default=str)
        dead: List[WebSocket] = []
        for ws in list(self._active):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_tick_update(self, symbol: str, tick: dict) -> None:
        await self.broadcast({
            "type": "tick_update",
            "symbol": symbol,
            "payload": tick,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def send_signal_update(self, signal: dict) -> None:
        await self.broadcast({
            "type": "signal_update",
            "symbol": signal.get("symbol"),
            "payload": signal,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def send_market_status(self, status: str) -> None:
        await self.broadcast({
            "type": "market_status",
            "payload": {"status": status},
            "timestamp": datetime.utcnow().isoformat(),
        })

    @property
    def connection_count(self) -> int:
        return len(self._active)


# Singleton
manager = ConnectionManager()
