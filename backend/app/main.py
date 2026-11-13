"""
AI Stock Intelligence Platform — FastAPI Application Entry Point

Startup sequence:
  1. Connect to PostgreSQL (create tables if missing)
  2. Connect to Redis
  3. Start data collection pipeline (Yahoo or Upstox)
  4. Start signal generation loop
  5. Serve REST API + WebSocket feed

WebSocket endpoint: ws://host/ws
  Clients receive JSON messages:
    { "type": "tick_update",   "symbol": "RELIANCE", "payload": {...}, "timestamp": "..." }
    { "type": "signal_update", "symbol": "RELIANCE", "payload": {...}, "timestamp": "..." }
    { "type": "market_status", "payload": {"status": "OPEN"},          "timestamp": "..." }
"""
import asyncio
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.dependencies import init_db, AsyncSessionLocal
from app.services.websocket_manager import manager as ws_manager
from app.routers import health, stocks, signals, backtest, model_perf


# ── Lifespan (startup / shutdown) ─────────────────────────────
_pipeline_tasks: List[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────
    logger.info("=== AI Stock Intelligence Platform starting ===")

    # Init DB tables (idempotent)
    await init_db()
    logger.info("Database tables verified")

    # Start data pipeline
    from collector.data_pipeline import start_data_pipeline
    tasks = await start_data_pipeline(db_session_factory=AsyncSessionLocal)
    _pipeline_tasks.extend(tasks)
    logger.info("Data pipeline started")

    yield

    # ── Shutdown ───────────────────────────────────────────────
    logger.info("Shutting down…")
    for task in _pipeline_tasks:
        task.cancel()
    if _pipeline_tasks:
        await asyncio.gather(*_pipeline_tasks, return_exceptions=True)
    logger.info("Pipeline stopped cleanly")


# ── FastAPI Application ────────────────────────────────────────
app = FastAPI(
    title="AI Stock Intelligence – Real-Time Intraday Signal Platform",
    description="50 NSE stocks | AI BUY/SELL/HOLD signals | Live market data",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"] + settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(signals.router)
app.include_router(backtest.router)
app.include_router(model_perf.router)


# ── WebSocket ─────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            # Keep connection alive; client sends pings
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception as exc:
        logger.warning(f"WS error: {exc}")
        ws_manager.disconnect(ws)


# ── Root ───────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": "AI Stock Intelligence Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/ws",
        "health": "/health",
    }
