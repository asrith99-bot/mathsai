"""
ML Feature Engineering Pipeline.

Takes a DataFrame of OHLCV+indicator data for a single symbol
and produces a feature matrix X and label vector y.

Label definition:
  Look-ahead 5-minute candle return:
    > +0.3%  → BUY  (class 2)
    < -0.3%  → SELL (class 0)
    otherwise → HOLD (class 1)

Threshold is configurable via LABEL_THRESHOLD.
"""
import numpy as np
import pandas as pd
from typing import Tuple, List
from loguru import logger

LABEL_THRESHOLD = 0.003   # 0.3% move classifies as directional

# All features used in training and inference
FEATURE_COLUMNS: List[str] = [
    # Price-based
    "close", "open", "high", "low",
    "change_1", "change_3", "change_5",
    # Volume
    "volume", "volume_ratio",
    # Momentum
    "rsi_14",
    "macd", "macd_signal", "macd_hist",
    "momentum_5",
    # Trend
    "sma_5", "sma_10", "sma_20", "sma_50",
    "ema_9", "ema_21",
    "close_vs_sma20",    # (close - sma20) / sma20
    "close_vs_ema21",
    # Volatility
    "atr_14",
    "volatility",
    "bb_width",
    "bb_position",       # (close - bb_lower) / (bb_upper - bb_lower)
    # VWAP
    "vwap_diff",         # (close - vwap) / vwap
    # Candlestick
    "candle_body",
    "candle_upper_sh",
    "candle_lower_sh",
    "candle_bullish",
    # Time
    "hour", "minute", "day_of_week",
]

CLASS_MAP = {0: "SELL", 1: "HOLD", 2: "BUY"}
REVERSE_CLASS_MAP = {"SELL": 0, "HOLD": 1, "BUY": 2}


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features that need indicator columns to already be present."""
    df = df.copy()

    # Price changes
    df["change_1"] = df["close"].pct_change(1)
    df["change_3"] = df["close"].pct_change(3)
    df["change_5"] = df["close"].pct_change(5)

    # Volume ratio vs 20-period MA
    vol_ma = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / vol_ma.replace(0, np.nan)

    # Close relative to indicators
    df["close_vs_sma20"] = (df["close"] - df["sma_20"]) / df["sma_20"].replace(0, np.nan)
    df["close_vs_ema21"] = (df["close"] - df["ema_21"]) / df["ema_21"].replace(0, np.nan)

    # Bollinger position (0 = at lower band, 1 = at upper band)
    bb_range = (df["bb_upper"] - df["bb_lower"]).replace(0, np.nan)
    df["bb_position"] = (df["close"] - df["bb_lower"]) / bb_range

    # VWAP difference
    df["vwap_diff"] = (df["close"] - df["vwap"]) / df["vwap"].replace(0, np.nan)

    # Time features (requires datetime index)
    if isinstance(df.index, pd.DatetimeIndex):
        df["hour"]        = df.index.hour
        df["minute"]      = df.index.minute
        df["day_of_week"] = df.index.dayofweek
    elif "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
        df["hour"]        = ts.dt.hour
        df["minute"]      = ts.dt.minute
        df["day_of_week"] = ts.dt.dayofweek
    else:
        df["hour"] = df["minute"] = df["day_of_week"] = 0

    return df


def create_labels(df: pd.DataFrame, lookahead: int = 1) -> pd.DataFrame:
    """
    Create classification labels based on future return.
    lookahead=1 means the return of the next candle after the current one.
    The last `lookahead` rows will have NaN labels and must be dropped.
    """
    df = df.copy()
    future_close = df["close"].shift(-lookahead)
    future_return = (future_close - df["close"]) / df["close"]

    df["label"] = 1  # HOLD default
    df.loc[future_return >  LABEL_THRESHOLD, "label"] = 2  # BUY
    df.loc[future_return < -LABEL_THRESHOLD, "label"] = 0  # SELL

    # Drop lookahead rows — these are data-leak-free
    df = df.iloc[:-lookahead]
    return df


def build_feature_matrix(
    df: pd.DataFrame,
    lookahead: int = 1,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Full pipeline: derive features, create labels, return (X, y).
    Drops rows with NaN in feature columns.
    """
    df = add_derived_features(df)
    df = create_labels(df, lookahead=lookahead)

    available_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    missing = set(FEATURE_COLUMNS) - set(available_cols)
    if missing:
        logger.debug(f"Missing feature columns (will skip): {missing}")

    X = df[available_cols].copy()
    y = df["label"].copy()

    # Drop rows with any NaN in features or label
    valid_mask = X.notna().all(axis=1) & y.notna()
    X = X[valid_mask]
    y = y[valid_mask].astype(int)

    logger.debug(f"Feature matrix: {X.shape}, label distribution: {y.value_counts().to_dict()}")
    return X, y


def prepare_inference_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a single-row or multi-row feature DataFrame for model.predict().
    No labels are created.
    """
    df = add_derived_features(df)
    available_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    X = df[available_cols].copy()
    # Fill any NaN with 0 for inference (model was trained on clean data)
    X = X.fillna(0)
    return X
