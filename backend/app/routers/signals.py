"""
Signal endpoints:
  GET /signals           – paginated signal history
  GET /signals/active    – all currently active signals
  GET /signals/dashboard – stats for main dashboard
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.db_models import Signal, Stock
from app.models.schemas import DashboardStatsOut, SignalOut
from app.services.market_data import get_market_status

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.get("/dashboard", response_model=DashboardStatsOut)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Count active signals by type
    result = await db.execute(
        select(Signal.signal_type, func.count(Signal.id).label("cnt"))
        .where(Signal.is_active == True)
        .group_by(Signal.signal_type)
    )
    type_counts = {row.signal_type: row.cnt for row in result}

    # Total active stocks
    total_q = await db.execute(select(func.count(Stock.id)).where(Stock.is_active == True))
    total_stocks = total_q.scalar() or 0

    # Top BUY / SELL signals by confidence
    top_buy_q = await db.execute(
        select(Signal)
        .where(Signal.is_active == True, Signal.signal_type == "BUY")
        .order_by(desc(Signal.confidence))
        .limit(5)
    )
    top_sell_q = await db.execute(
        select(Signal)
        .where(Signal.is_active == True, Signal.signal_type == "SELL")
        .order_by(desc(Signal.confidence))
        .limit(5)
    )
    recent_q = await db.execute(
        select(Signal)
        .order_by(desc(Signal.generated_at))
        .limit(10)
    )

    return DashboardStatsOut(
        total_stocks=total_stocks,
        buy_count=type_counts.get("BUY", 0),
        sell_count=type_counts.get("SELL", 0),
        hold_count=type_counts.get("HOLD", 0),
        bullish_count=type_counts.get("BUY", 0),
        bearish_count=type_counts.get("SELL", 0),
        market_status=get_market_status(),
        last_update=datetime.now(tz=timezone.utc),
        top_buy_signals=[SignalOut.model_validate(s) for s in top_buy_q.scalars().all()],
        top_sell_signals=[SignalOut.model_validate(s) for s in top_sell_q.scalars().all()],
        recent_signals=[SignalOut.model_validate(s) for s in recent_q.scalars().all()],
    )


@router.get("/active", response_model=List[SignalOut])
async def get_active_signals(
    signal_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Signal).where(Signal.is_active == True)
    if signal_type:
        stmt = stmt.where(Signal.signal_type == signal_type.upper())
    stmt = stmt.order_by(desc(Signal.generated_at))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("", response_model=List[SignalOut])
async def list_signals(
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Signal)
    if symbol:
        stmt = stmt.where(Signal.symbol == symbol.upper())
    if signal_type:
        stmt = stmt.where(Signal.signal_type == signal_type.upper())
    stmt = stmt.order_by(desc(Signal.generated_at)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
