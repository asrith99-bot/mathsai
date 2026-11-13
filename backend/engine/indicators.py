"""
Technical indicator calculations using pandas_ta.
All functions accept a pandas DataFrame with OHLCV columns
and return the same DataFrame with new indicator columns appended.

Columns expected: open, high, low, close, volume
"""
import numpy as np
import pandas as pd
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False

from loguru import logger


def _require_min_rows(df: pd.DataFrame, n: int, label: str) -> bool:
    if len(df) < n:
        logger.debug(f"Skipping {label}: need {n} rows, have {len(df)}")
        return False
    return True


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    if not _require_min_rows(df, period + 1, "RSI"):
        df["rsi_14"] = np.nan
        return df
    if PANDAS_TA_AVAILABLE:
        df["rsi_14"] = ta.rsi(df["close"], length=period)
    else:
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi_14"] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    if not _require_min_rows(df, slow + signal, "MACD"):
        df[["macd", "macd_signal", "macd_hist"]] = np.nan
        return df
    if PANDAS_TA_AVAILABLE:
        macd_df = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
        if macd_df is not None:
            df["macd"]        = macd_df.iloc[:, 0]
            df["macd_hist"]   = macd_df.iloc[:, 1]
            df["macd_signal"] = macd_df.iloc[:, 2]
    else:
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        df["macd"]        = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
        df["macd_hist"]   = df["macd"] - df["macd_signal"]
    return df


def add_sma(df: pd.DataFrame, periods: list[int] = [5, 10, 20, 50]) -> pd.DataFrame:
    for p in periods:
        col = f"sma_{p}"
        if len(df) >= p:
            df[col] = df["close"].rolling(window=p).mean()
        else:
            df[col] = np.nan
    return df


def add_ema(df: pd.DataFrame, periods: list[int] = [9, 21]) -> pd.DataFrame:
    for p in periods:
        col = f"ema_{p}"
        if len(df) >= p:
            df[col] = df["close"].ewm(span=p, adjust=False).mean()
        else:
            df[col] = np.nan
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    if not _require_min_rows(df, period + 1, "ATR"):
        df["atr_14"] = np.nan
        return df
    if PANDAS_TA_AVAILABLE:
        df["atr_14"] = ta.atr(df["high"], df["low"], df["close"], length=period)
    else:
        high_low   = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close  = (df["low"]  - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=period).mean()
    return df


def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
    if not _require_min_rows(df, period, "BB"):
        df[["bb_upper", "bb_mid", "bb_lower", "bb_width"]] = np.nan
        return df
    if PANDAS_TA_AVAILABLE:
        bb = ta.bbands(df["close"], length=period, std=std)
        if bb is not None:
            df["bb_lower"] = bb.iloc[:, 0]
            df["bb_mid"]   = bb.iloc[:, 1]
            df["bb_upper"] = bb.iloc[:, 2]
            df["bb_width"] = bb.iloc[:, 3]
    else:
        mid = df["close"].rolling(period).mean()
        std_dev = df["close"].rolling(period).std()
        df["bb_mid"]   = mid
        df["bb_upper"] = mid + std * std_dev
        df["bb_lower"] = mid - std * std_dev
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"].replace(0, np.nan)
    return df


def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Intraday VWAP: cumulative (price × volume) / cumulative volume.
    Resets at the start of each trading day.
    """
    if "volume" not in df.columns or df["volume"].sum() == 0:
        df["vwap"] = np.nan
        return df
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
    return df


def add_volume_ma(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    if len(df) >= period:
        df["volume_ma20"] = df["volume"].rolling(window=period).mean().fillna(0).astype(float)
    else:
        df["volume_ma20"] = 0.0
    return df


def add_momentum(df: pd.DataFrame, period: int = 5) -> pd.DataFrame:
    df["momentum_5"] = df["close"].pct_change(periods=period) * 100
    return df


def add_volatility(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """20-period rolling standard deviation of log returns."""
    log_ret = np.log(df["close"] / df["close"].shift(1))
    df["volatility"] = log_ret.rolling(window=period).std()
    return df


def add_candlestick_features(df: pd.DataFrame) -> pd.DataFrame:
    """Body size, upper/lower shadow as fractions of price range."""
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    df["candle_body"]     = (df["close"] - df["open"]).abs() / rng
    df["candle_upper_sh"] = (df["high"] - df[["open", "close"]].max(axis=1)) / rng
    df["candle_lower_sh"] = (df[["open", "close"]].min(axis=1) - df["low"]) / rng
    df["candle_bullish"]  = (df["close"] > df["open"]).astype(int)
    return df


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the full indicator suite to a OHLCV DataFrame.
    Input columns: open, high, low, close, volume (lowercase).
    """
    df = df.copy()
    df = add_rsi(df)
    df = add_macd(df)
    df = add_sma(df)
    df = add_ema(df)
    df = add_atr(df)
    df = add_bollinger_bands(df)
    df = add_vwap(df)
    df = add_volume_ma(df)
    df = add_momentum(df)
    df = add_volatility(df)
    df = add_candlestick_features(df)
    return df
