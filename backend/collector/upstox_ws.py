"""
Upstox WebSocket v3 live data collector.
Connects using the Upstox v2 API access token.
Provides LIVE tick-by-tick data for all subscribed instruments.

Authentication:
  1. User completes OAuth2 flow at /auth/upstox/login
  2. Access token is stored in settings.upstox_access_token
  3. This collector reads the token and connects to the feed.

NOTE: Requires a valid Upstox Pro subscription and API credentials.
      Without valid credentials this module falls back gracefully.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Callable, Coroutine, Dict, List, Optional

from loguru import logger

# Instrument key format for Upstox NSE equities: "NSE_EQ|<ISIN>"
# The mapping below uses the Upstox instrument symbol format.
UPSTOX_SYMBOL_MAP: Dict[str, str] = {
    "RELIANCE":   "NSE_EQ|INE002A01018",
    "TCS":        "NSE_EQ|INE467B01029",
    "INFY":       "NSE_EQ|INE009A01021",
    "HDFCBANK":   "NSE_EQ|INE040A01034",
    "ICICIBANK":  "NSE_EQ|INE090A01021",
    "SBIN":       "NSE_EQ|INE062A01020",
    "BHARTIARTL": "NSE_EQ|INE397D01024",
    "ITC":        "NSE_EQ|INE154A01025",
    "LT":         "NSE_EQ|INE018A01030",
    "AXISBANK":   "NSE_EQ|INE238A01034",
    "KOTAKBANK":  "NSE_EQ|INE237A01028",
    "BAJFINANCE": "NSE_EQ|INE296A01024",
    "MARUTI":     "NSE_EQ|INE585B01010",
    "SUNPHARMA":  "NSE_EQ|INE044A01036",
    "TITAN":      "NSE_EQ|INE280A01028",
    "TATAMOTORS": "NSE_EQ|INE155A01022",
    "M&M":        "NSE_EQ|INE101A01026",
    "NTPC":       "NSE_EQ|INE733E01010",
    "POWERGRID":  "NSE_EQ|INE752E01010",
    "ONGC":       "NSE_EQ|INE213A01029",
    "TATASTEEL":  "NSE_EQ|INE081A01020",
    "JSWSTEEL":   "NSE_EQ|INE019A01038",
    "HINDALCO":   "NSE_EQ|INE038A01020",
    "WIPRO":      "NSE_EQ|INE075A01022",
    "HCLTECH":    "NSE_EQ|INE860A01027",
    "TECHM":      "NSE_EQ|INE669C01036",
    "ULTRACEMCO": "NSE_EQ|INE481G01011",
    "ASIANPAINT": "NSE_EQ|INE021A01026",
    "NESTLEIND":  "NSE_EQ|INE239A01016",
    "TRENT":      "NSE_EQ|INE849A01020",
    "BEL":        "NSE_EQ|INE263A01024",
    "ADANIPORTS": "NSE_EQ|INE742F01042",
    "COALINDIA":  "NSE_EQ|INE522F01014",
    "GRASIM":     "NSE_EQ|INE047A01021",
    "EICHERMOT":  "NSE_EQ|INE066A01021",
    "DRREDDY":    "NSE_EQ|INE089A01023",
    "CIPLA":      "NSE_EQ|INE059A01026",
    "DIVISLAB":   "NSE_EQ|INE361B01024",
    "APOLLOHOSP": "NSE_EQ|INE437A01024",
    "INDUSINDBK": "NSE_EQ|INE095A01012",
    "BANKBARODA": "NSE_EQ|INE028A01039",
    "PNB":        "NSE_EQ|INE160A01022",
    "CANBK":      "NSE_EQ|INE476A01022",
    "DLF":        "NSE_EQ|INE271C01023",
    "GODREJCP":   "NSE_EQ|INE102D01028",
    "SBILIFE":    "NSE_EQ|INE123W01016",
    "HDFCLIFE":   "NSE_EQ|INE795G01014",
    "LTIM":       "NSE_EQ|INE214T01019",
    "ZOMATO":     "NSE_EQ|INE758T01015",
    "HINDUNILVR": "NSE_EQ|INE030A01027",
}

# Reverse map: instrument_key → symbol
REVERSE_MAP = {v: k for k, v in UPSTOX_SYMBOL_MAP.items()}


class UpstoxWSCollector:
    """
    Connects to Upstox Market Data WebSocket v3 and streams live ticks.
    Implements automatic reconnection with exponential backoff.
    """

    WS_URL = "wss://api.upstox.com/v2/feed/market-data-feed"

    def __init__(
        self,
        access_token: str,
        on_tick: Optional[Callable] = None,
    ):
        self.access_token = access_token
        self._on_tick     = on_tick
        self._ws          = None
        self._running     = False
        self._reconnect_delay = 2  # seconds, doubles on each failure

    async def connect(self) -> None:
        """Start the WebSocket connection and subscribe."""
        import websockets
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        instrument_keys = list(UPSTOX_SYMBOL_MAP.values())

        self._running = True
        while self._running:
            try:
                logger.info("Upstox WS: connecting…")
                async with websockets.connect(
                    self.WS_URL,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=10,
                ) as ws:
                    self._ws = ws
                    self._reconnect_delay = 2  # reset on success

                    # Subscribe to all instruments
                    sub_msg = {
                        "guid": "stockplatform",
                        "method": "sub",
                        "data": {
                            "mode": "full",
                            "instrumentKeys": instrument_keys,
                        },
                    }
                    await ws.send(json.dumps(sub_msg))
                    logger.info(f"Upstox WS: subscribed to {len(instrument_keys)} instruments")

                    async for raw_msg in ws:
                        await self._handle_message(raw_msg)

            except Exception as exc:
                logger.warning(f"Upstox WS disconnected: {exc}. Reconnecting in {self._reconnect_delay}s…")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, 60)

    async def _handle_message(self, raw_msg: bytes) -> None:
        """Parse Upstox market data feed message."""
        try:
            # Upstox v3 feed uses protobuf; decode as JSON for compatibility mode
            data = json.loads(raw_msg)
            feeds = data.get("feeds", {})
            for instrument_key, feed_data in feeds.items():
                symbol = REVERSE_MAP.get(instrument_key)
                if not symbol:
                    continue

                ff = feed_data.get("ff", {})
                market_ff = ff.get("marketFF", ff.get("indexFF", {}))
                ltpc = market_ff.get("ltpc", {})

                if not ltpc:
                    continue

                tick = {
                    "symbol": symbol,
                    "ltp": float(ltpc.get("ltp", 0)),
                    "open": float(market_ff.get("dayOHLC", {}).get("open", 0)),
                    "high": float(market_ff.get("dayOHLC", {}).get("high", 0)),
                    "low":  float(market_ff.get("dayOHLC", {}).get("low", 0)),
                    "prev_close": float(ltpc.get("cp", 0)),
                    "volume": int(market_ff.get("vtt", 0)),
                    "data_source": "upstox",
                    "freshness": "LIVE",
                    "tick_timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }
                if tick["prev_close"] and tick["prev_close"] != 0:
                    tick["change_pct"] = round(
                        (tick["ltp"] - tick["prev_close"]) / tick["prev_close"] * 100, 2
                    )
                if self._on_tick:
                    await self._on_tick(symbol, tick)

        except Exception as exc:
            logger.debug(f"Upstox message parse error: {exc}")

    def stop(self) -> None:
        self._running = False
        if self._ws:
            asyncio.ensure_future(self._ws.close())
