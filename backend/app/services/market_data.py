"""
Market data service abstraction.
Selects the configured provider (Upstox / Kite / Yahoo fallback)
and exposes a unified interface to the rest of the application.
"""
import asyncio
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional
from loguru import logger
from app.config import settings


# ─────────────────────────────────────────────────────────────────────────────
# Data freshness helper
# ─────────────────────────────────────────────────────────────────────────────

def compute_freshness(tick_ts: Optional[datetime]) -> str:
    """
    Returns 'LIVE', 'DELAYED', or 'STALE' based on how old the tick is.
    """
    if tick_ts is None:
        return "STALE"
    now = datetime.now(tz=timezone.utc)
    if tick_ts.tzinfo is None:
        tick_ts = tick_ts.replace(tzinfo=timezone.utc)
    age_seconds = (now - tick_ts).total_seconds()
    if age_seconds <= settings.live_threshold_seconds:
        return "LIVE"
    elif age_seconds <= settings.delayed_threshold_seconds:
        return "DELAYED"
    return "STALE"


# ─────────────────────────────────────────────────────────────────────────────
# Market hours
# ─────────────────────────────────────────────────────────────────────────────

def get_market_status() -> str:
    """
    Returns 'OPEN', 'CLOSED', 'PRE_OPEN', or 'POST_CLOSE' based on IST time.
    Does not account for NSE trading holidays.
    """
    try:
        import pytz
        ist = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(ist)
    except Exception:
        return "UNKNOWN"

    if now_ist.weekday() >= 5:  # Sat, Sun
        return "CLOSED"

    from datetime import time as dtime
    t = now_ist.time()
    if t < dtime(9, 0):
        return "CLOSED"
    elif t < dtime(9, 15):
        return "PRE_OPEN"
    elif t <= dtime(15, 30):
        return "OPEN"
    elif t <= dtime(16, 0):
        return "POST_CLOSE"
    else:
        return "CLOSED"


# ─────────────────────────────────────────────────────────────────────────────
# Yahoo Finance fallback provider
# ─────────────────────────────────────────────────────────────────────────────

class YahooFallbackProvider:
    """
    Uses yfinance to fetch delayed market data.
    NSE symbols require the '.NS' suffix on Yahoo Finance.
    Data is typically 15–20 minutes delayed.
    Label: DELAYED
    """

    @staticmethod
    def _yf_symbol(symbol: str) -> str:
        if symbol == "M&M":
            return "M%26M.NS"
        return f"{symbol}.NS"

    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_fetch, symbols)

    def _sync_fetch(self, symbols: List[str]) -> Dict[str, dict]:
        import yfinance as yf
        result: Dict[str, dict] = {}
        yf_syms = [self._yf_symbol(s) for s in symbols]
        try:
            tickers = yf.Tickers(" ".join(yf_syms))
            for sym, yf_sym in zip(symbols, yf_syms):
                try:
                    info = tickers.tickers[yf_sym].fast_info
                    history = tickers.tickers[yf_sym].history(period="1d", interval="1m")
                    if history.empty:
                        continue
                    last_row = history.iloc[-1]
                    tick_ts = datetime.now(tz=timezone.utc)
                    result[sym] = {
                        "symbol": sym,
                        "ltp": float(last_row["Close"]),
                        "open": float(history.iloc[0]["Open"]),
                        "high": float(history["High"].max()),
                        "low":  float(history["Low"].min()),
                        "prev_close": float(info.previous_close) if hasattr(info, "previous_close") else None,
                        "volume": int(last_row["Volume"]),
                        "data_source": "yahoo",
                        "freshness": "DELAYED",
                        "tick_timestamp": tick_ts.isoformat(),
                    }
                    if result[sym]["prev_close"] and result[sym]["prev_close"] != 0:
                        result[sym]["change_pct"] = round(
                            (result[sym]["ltp"] - result[sym]["prev_close"])
                            / result[sym]["prev_close"] * 100,
                            2,
                        )
                except Exception as exc:
                    logger.warning(f"Yahoo fetch failed for {sym}: {exc}")
        except Exception as exc:
            logger.error(f"Yahoo batch fetch failed: {exc}")
        return result

    async def fetch_history(
        self,
        symbol: str,
        period: str = "60d",
        interval: str = "5m",
    ) -> List[dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_history, symbol, period, interval)

    def _sync_history(self, symbol: str, period: str, interval: str) -> List[dict]:
        import yfinance as yf
        yf_sym = self._yf_symbol(symbol)
        try:
            df = yf.download(yf_sym, period=period, interval=interval, progress=False, auto_adjust=True)
            if df.empty:
                return []
            # Flatten MultiIndex columns (yfinance >=1.0)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [str(c[0]).lower() for c in df.columns]
            else:
                df.columns = [str(c).lower() for c in df.columns]
            if "adj close" in df.columns and "close" not in df.columns:
                df = df.rename(columns={"adj close": "close"})
            df = df.reset_index()
            rows = []
            for _, row in df.iterrows():
                ts = row.get("datetime") or row.get("date") or row.get("Datetime") or row.get("Date")
                if hasattr(ts, "to_pydatetime"):
                    ts = ts.to_pydatetime()
                rows.append({
                    "symbol": symbol,
                    "timestamp": ts,
                    "open":   float(row.get("open",   0)),
                    "high":   float(row.get("high",   0)),
                    "low":    float(row.get("low",    0)),
                    "close":  float(row.get("close",  0)),
                    "volume": int(row.get("volume",   0)),
                    "data_source": "yahoo",
                    "timeframe": interval,
                })
            return rows
        except Exception as exc:
            logger.error(f"Yahoo history failed for {symbol}: {exc}")
            return []


# ─────────────────────────────────────────────────────────────────────────────
# Provider factory
# ─────────────────────────────────────────────────────────────────────────────

def get_market_data_provider():
    provider = settings.data_provider.lower()
    if provider in ("yahoo_fallback", ""):
        logger.info("Using Yahoo Finance fallback provider (data is DELAYED ~15–20 min)")
        return YahooFallbackProvider()
    logger.warning(f"Provider '{provider}' REST fallback not fully implemented; using Yahoo")
    return YahooFallbackProvider()


market_data_provider = get_market_data_provider()
