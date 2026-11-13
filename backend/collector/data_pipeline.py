"""
Data Pipeline Coordinator.

Orchestrates the full data flow:
  1. Start market data collector (Upstox WS or Yahoo polling)
  2. For each tick: update Redis cache + broadcast via WebSocket
  3. Every N minutes: aggregate 5-min candle, compute indicators,
     run ML prediction, generate signal, persist to DB, broadcast signal
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from app.config import settings
from app.services.market_data import compute_freshness
from app.services.redis_client import (
    set_tick, get_tick, set_active_signal, set_market_status
)
from engine.indicators import compute_all_indicators
from engine.signal_generator import generate_signal

# Candle buffer: symbol → list of 1-minute OHLCV dicts
_candle_buffer: Dict[str, List[dict]] = {}

# How many 1-min bars to aggregate into one prediction window
SIGNAL_CANDLE_COUNT = 60   # 60 one-minute bars = 1 hour of context


async def on_tick_received(symbol: str, tick: dict) -> None:
    """
    Called by the data collector for every new tick.
    Updates Redis and broadcasts to WebSocket clients.
    """
    from app.services.websocket_manager import manager as ws_manager

    await set_tick(symbol, tick)
    await ws_manager.send_tick_update(symbol, tick)

    # Update the candle buffer
    _update_candle_buffer(symbol, tick)


def _update_candle_buffer(symbol: str, tick: dict) -> None:
    """Append tick to rolling candle buffer (simplified 1-min close tracking)."""
    if symbol not in _candle_buffer:
        _candle_buffer[symbol] = []

    buf = _candle_buffer[symbol]
    buf.append({
        "timestamp": tick.get("tick_timestamp") or datetime.now(tz=timezone.utc).isoformat(),
        "open":   tick.get("ltp", 0),
        "high":   tick.get("high", tick.get("ltp", 0)),
        "low":    tick.get("low",  tick.get("ltp", 0)),
        "close":  tick.get("ltp", 0),
        "volume": tick.get("volume", 0),
    })

    # Keep only last N candles
    if len(buf) > SIGNAL_CANDLE_COUNT * 2:
        _candle_buffer[symbol] = buf[-SIGNAL_CANDLE_COUNT:]


async def run_signal_loop(
    db_session_factory=None,
    interval_seconds: int = 300,  # Every 5 minutes
) -> None:
    """
    Background loop that processes all symbols and generates signals.
    Runs independently of the tick collection loop.
    """
    from app.services.websocket_manager import manager as ws_manager

    logger.info("Signal generation loop started (every 5 min)")

    while True:
        await asyncio.sleep(interval_seconds)
        try:
            market_status = _get_market_status_local()
            await set_market_status(market_status)

            if market_status not in ("OPEN", "PRE_OPEN"):
                logger.debug(f"Market {market_status}: skipping signal generation")
                continue

            symbols = list(_candle_buffer.keys())
            if not symbols:
                # Warm up: fetch historical data via Yahoo for initial candles
                logger.info("Warming up candle buffer from Yahoo Finance…")
                await _warm_up_buffers()
                continue

            processed = 0
            for symbol in symbols:
                try:
                    signal = await _process_symbol(symbol)
                    if signal and not signal.skipped and signal.signal_type in ("BUY", "SELL"):
                        signal_dict = signal.to_dict()
                        await set_active_signal(symbol, signal_dict)
                        await ws_manager.send_signal_update(signal_dict)

                        # Persist to DB if factory provided
                        if db_session_factory:
                            await _persist_signal(db_session_factory, signal)
                        processed += 1
                except Exception as exc:
                    logger.error(f"Signal processing failed for {symbol}: {exc}")

            logger.info(f"Signal loop: {processed} new signals from {len(symbols)} symbols")
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"Signal loop error: {exc}")


async def _process_symbol(symbol: str):
    """Build feature DF and run signal generator for one symbol."""
    buf = _candle_buffer.get(symbol, [])
    if len(buf) < 30:
        return None

    df = pd.DataFrame(buf[-SIGNAL_CANDLE_COUNT:])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")
    df = df[["open", "high", "low", "close", "volume"]].astype(float)

    df = compute_all_indicators(df)

    # Determine freshness from last tick
    last_tick = await get_tick(symbol)
    if last_tick:
        from datetime import datetime as dt
        ts_str = last_tick.get("tick_timestamp")
        if ts_str:
            ts = dt.fromisoformat(ts_str.replace("Z", "+00:00"))
            freshness = compute_freshness(ts)
        else:
            freshness = last_tick.get("freshness", "STALE")
        data_source = last_tick.get("data_source", "unknown")
    else:
        freshness = "STALE"
        data_source = "unknown"

    signal = generate_signal(
        symbol=symbol,
        ohlcv_df=df,
        indicators_df=df,
        data_source=data_source,
        freshness=freshness,
    )
    return signal


async def _warm_up_buffers() -> None:
    """Pre-fill candle buffers with Yahoo historical data at startup."""
    from app.services.market_data import YahooFallbackProvider
    from collector.yahoo_fallback import WATCHLIST

    provider = YahooFallbackProvider()
    for symbol in WATCHLIST:
        try:
            candles = await provider.fetch_history(symbol, period="5d", interval="1m")
            if candles:
                _candle_buffer[symbol] = [
                    {k: v for k, v in c.items() if k in ("timestamp", "open", "high", "low", "close", "volume")}
                    for c in candles[-SIGNAL_CANDLE_COUNT:]
                ]
        except Exception as exc:
            logger.warning(f"Warm-up failed for {symbol}: {exc}")
        await asyncio.sleep(0.5)
    logger.info(f"Buffer warm-up complete: {len(_candle_buffer)} symbols")


async def _persist_signal(db_session_factory, signal) -> None:
    """Persist a GeneratedSignal to PostgreSQL."""
    from app.models.db_models import Signal
    from sqlalchemy import select

    try:
        async with db_session_factory() as session:
            db_signal = Signal(
                symbol=signal.symbol,
                signal_type=signal.signal_type,
                confidence=signal.confidence,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                target_price=signal.target_price,
                rr_ratio=signal.rr_ratio,
                risk_per_share=signal.risk_per_share,
                reward_per_share=signal.reward_per_share,
                rsi=signal.rsi,
                macd=signal.macd,
                atr=signal.atr,
                model_version=signal.model_version,
                data_source=signal.data_source,
                freshness=signal.freshness,
            )
            session.add(db_signal)
            await session.commit()
    except Exception as exc:
        logger.error(f"Failed to persist signal for {signal.symbol}: {exc}")


def _get_market_status_local() -> str:
    from app.services.market_data import get_market_status
    return get_market_status()


async def start_data_pipeline(db_session_factory=None) -> None:
    """
    Entry point called from FastAPI startup.
    Starts the appropriate data collector and signal loop concurrently.
    """
    provider = settings.data_provider.lower()
    logger.info(f"Starting data pipeline with provider: {provider}")

    tasks = []

    if provider == "upstox" and settings.upstox_access_token:
        from collector.upstox_ws import UpstoxWSCollector
        collector = UpstoxWSCollector(
            access_token=settings.upstox_access_token,
            on_tick=on_tick_received,
        )
        tasks.append(asyncio.create_task(collector.connect()))
        logger.info("Upstox WebSocket collector task started (LIVE data)")
    else:
        from collector.yahoo_fallback import run_yahoo_collector
        from app.services.redis_client import set_tick as redis_set_tick
        from app.services.websocket_manager import manager as ws_manager

        async def yahoo_on_tick(symbol, tick):
            await on_tick_received(symbol, tick)

        tasks.append(asyncio.create_task(
            run_yahoo_collector(
                ws_manager=ws_manager,
                redis_set_tick_fn=redis_set_tick,
            )
        ))
        logger.info("Yahoo Finance polling collector task started (DELAYED data)")

    # Warm-up buffers first, then start signal loop
    await _warm_up_buffers()
    tasks.append(asyncio.create_task(
        run_signal_loop(db_session_factory=db_session_factory)
    ))

    logger.info("Data pipeline fully started")
    return tasks
