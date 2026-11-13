"""Health check and diagnostics endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.dependencies import get_db
from app.services.redis_client import get_redis
from app.services.market_data import get_market_status
from app.services.websocket_manager import manager as ws_manager

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Full system health check."""
    checks = {}

    # DB
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Redis
    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    checks["market_status"] = get_market_status()
    checks["websocket_clients"] = ws_manager.connection_count
    checks["timestamp"] = datetime.utcnow().isoformat()

    overall = "ok" if all(v == "ok" for k, v in checks.items() if k not in ("market_status", "websocket_clients", "timestamp")) else "degraded"
    return {"status": overall, "checks": checks}
