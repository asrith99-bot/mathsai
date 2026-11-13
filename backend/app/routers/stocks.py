"""
Stocks endpoints:
  GET  /stocks               – list all active stocks
  POST /stocks               – add a stock to watchlist
  DELETE /stocks/{symbol}    – remove a stock
  GET  /stocks/{symbol}/ohlcv – historical candles
  GET  /stocks/scanner       – full scanner snapshot (all stocks + latest signal)
  GET  /stocks/{symbol}/detail – single stock detail with indicators
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.db_models import OHLCVData, Signal, Stock
from app.models.schemas import OHLCVOut, ScannerRowOut, StockCreate, StockOut
from app.services.redis_client import get_tick, get_active_signal
from app.services.market_data import market_data_provider

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("", response_model=List[StockOut])
async def list_stocks(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Stock)
    if active_only:
        stmt = stmt.where(Stock.is_active == True)
    result = await db.execute(stmt.order_by(Stock.symbol))
    return result.scalars().all()


@router.post("", response_model=StockOut, status_code=201)
async def add_stock(payload: StockCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Stock).where(Stock.symbol == payload.symbol.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Stock already exists")
    stock = Stock(**payload.model_dump(), symbol=payload.symbol.upper())
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    return stock


@router.delete("/{symbol}", status_code=204)
async def remove_stock(symbol: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    stock.is_active = False
    await db.commit()


@router.get("/scanner", response_model=List[ScannerRowOut])
async def get_scanner(
    signal_filter: Optional[str] = Query(None, description="BUY|SELL|HOLD"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns one row per active stock with live tick data,
    latest technical snapshot, and latest active signal.
    """
    stmt = select(Stock).where(Stock.is_active == True)
    if search:
        stmt = stmt.where(Stock.symbol.ilike(f"%{search.upper()}%"))
    result = await db.execute(stmt.order_by(Stock.symbol))
    stocks = result.scalars().all()

    rows: List[ScannerRowOut] = []
    for stock in stocks:
        # Get latest tick from Redis (fast path)
        tick = await get_tick(stock.symbol)
        signal_cache = await get_active_signal(stock.symbol)

        row = ScannerRowOut(
            symbol=stock.symbol,
            name=stock.name,
            sector=stock.sector,
        )

        if tick:
            row.ltp        = tick.get("ltp")
            row.change_pct = tick.get("change_pct")
            row.volume     = tick.get("volume")
            row.freshness  = tick.get("freshness", "STALE")

        if signal_cache:
            row.signal_type        = signal_cache.get("signal_type")
            row.confidence         = signal_cache.get("confidence")
            row.entry_price        = signal_cache.get("entry_price")
            row.stop_loss          = signal_cache.get("stop_loss")
            row.target_price       = signal_cache.get("target_price")
            row.signal_id          = signal_cache.get("id")
            row.signal_generated_at = signal_cache.get("generated_at")

        # DB fallback for technical snapshot
        if not tick:
            # Fetch latest DB tick or OHLCV
            ohlcv_q = await db.execute(
                select(OHLCVData)
                .where(OHLCVData.symbol == stock.symbol)
                .order_by(desc(OHLCVData.timestamp))
                .limit(1)
            )
            last_ohlcv = ohlcv_q.scalar_one_or_none()
            if last_ohlcv:
                row.ltp      = float(last_ohlcv.close)
                row.freshness = "STALE"

        # Apply filters
        if signal_filter and row.signal_type != signal_filter.upper():
            continue
        if min_confidence and (row.confidence or 0) < min_confidence:
            continue

        rows.append(row)
    return rows


@router.get("/{symbol}/ohlcv", response_model=List[OHLCVOut])
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query("5m", description="1m|5m|15m|1d"),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Return historical OHLCV candles from DB, falling back to Yahoo."""
    sym = symbol.upper()

    # Try DB first
    stmt = (
        select(OHLCVData)
        .where(OHLCVData.symbol == sym, OHLCVData.timeframe == timeframe)
        .order_by(desc(OHLCVData.timestamp))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if rows:
        return rows

    # Fallback: fetch live from Yahoo and return (but don't persist here)
    history = await market_data_provider.fetch_history(sym, period="30d", interval=timeframe)
    if not history:
        raise HTTPException(status_code=404, detail=f"No OHLCV data for {sym}")
    return [
        OHLCVOut(
            symbol=r["symbol"],
            timestamp=r["timestamp"],
            open=r["open"],
            high=r["high"],
            low=r["low"],
            close=r["close"],
            volume=r["volume"],
            vwap=None,
            timeframe=r["timeframe"],
            data_source=r["data_source"],
        )
        for r in history[-limit:]
    ]


@router.get("/{symbol}/detail")
async def get_stock_detail(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Returns stock info + current tick + latest signal + recent OHLCV.
    """
    sym = symbol.upper()
    result = await db.execute(select(Stock).where(Stock.symbol == sym))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    tick          = await get_tick(sym)
    active_signal = await get_active_signal(sym)

    # Recent signals from DB
    sig_q = await db.execute(
        select(Signal)
        .where(Signal.symbol == sym)
        .order_by(desc(Signal.generated_at))
        .limit(10)
    )
    recent_signals = sig_q.scalars().all()

    return {
        "stock": StockOut.model_validate(stock).model_dump(),
        "tick": tick,
        "active_signal": active_signal,
        "recent_signals": [
            {
                "id": s.id,
                "signal_type": s.signal_type,
                "confidence": float(s.confidence),
                "entry_price": float(s.entry_price),
                "stop_loss": float(s.stop_loss),
                "target_price": float(s.target_price),
                "rr_ratio": float(s.rr_ratio) if s.rr_ratio else None,
                "generated_at": s.generated_at.isoformat() if s.generated_at else None,
            }
            for s in recent_signals
        ],
    }
