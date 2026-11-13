"""
Yahoo Finance polling collector.
Runs as a background asyncio task.
Polls all 50 symbols at a configurable interval and pushes
tick data to Redis and broadcasts via WebSocket.

Data is ALWAYS labeled as DELAYED — yfinance does not provide live data.
"""
import asyncio
from datetime import datetime, timezone
from typing import List

from loguru import logger

WATCHLIST = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
    "BHARTIARTL", "ITC", "LT", "AXISBANK", "KOTAKBANK", "BAJFINANCE",
    "MARUTI", "SUNPHARMA", "TITAN", "TATAMOTORS", "M&M", "NTPC",
    "POWERGRID", "ONGC", "TATASTEEL", "JSWSTEEL", "HINDALCO", "WIPRO",
    "HCLTECH", "TECHM", "ULTRACEMCO", "ASIANPAINT", "NESTLEIND", "TRENT",
    "BEL", "ADANIPORTS", "COALINDIA", "GRASIM", "EICHERMOT", "DRREDDY",
    "CIPLA", "DIVISLAB", "APOLLOHOSP", "INDUSINDBK", "BANKBARODA", "PNB",
    "CANBK", "DLF", "GODREJCP", "SBILIFE", "HDFCLIFE", "LTIM", "ZOMATO",
    "HINDUNILVR",
]

POLL_INTERVAL_SECONDS = 60   # Poll every 60s to respect rate limits
BATCH_SIZE = 10              # Process in batches


async def run_yahoo_collector(
    ws_manager=None,
    redis_set_tick_fn=None,
):
    """
    Async polling loop.
    ws_manager: ConnectionManager instance for WebSocket broadcast
    redis_set_tick_fn: coroutine to cache tick in Redis
    """
    from app.services.market_data import YahooFallbackProvider
    provider = YahooFallbackProvider()

    logger.info("Yahoo Finance collector started (DELAYED data, ~60s poll)")

    while True:
        try:
            # Process in batches to avoid memory spikes
            for batch_start in range(0, len(WATCHLIST), BATCH_SIZE):
                batch = WATCHLIST[batch_start:batch_start + BATCH_SIZE]
                ticks = await provider.fetch_quotes(batch)

                for symbol, tick in ticks.items():
                    # Always DELAYED for Yahoo
                    tick["freshness"] = "DELAYED"
                    tick["data_source"] = "yahoo"

                    # Push to Redis
                    if redis_set_tick_fn:
                        await redis_set_tick_fn(symbol, tick)

                    # Broadcast via WebSocket
                    if ws_manager:
                        await ws_manager.send_tick_update(symbol, tick)

                # Small delay between batches
                await asyncio.sleep(1)

            logger.debug(f"Yahoo poll complete: {len(WATCHLIST)} symbols processed")

        except asyncio.CancelledError:
            logger.info("Yahoo collector cancelled")
            break
        except Exception as exc:
            logger.error(f"Yahoo collector error: {exc}")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
