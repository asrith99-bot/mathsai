"""
Tests for the technical indicator engine.
"""
import numpy as np
import pandas as pd
import pytest

from engine.indicators import compute_all_indicators


def _make_ohlcv(n: int = 100) -> pd.DataFrame:
    np.random.seed(42)
    close = 1000 + np.cumsum(np.random.randn(n) * 5)
    high  = close + np.abs(np.random.randn(n) * 3)
    low   = close - np.abs(np.random.randn(n) * 3)
    open_ = close + np.random.randn(n)
    vol   = np.random.randint(100_000, 1_000_000, n)
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": vol
    })


def test_rsi_range():
    df = compute_all_indicators(_make_ohlcv())
    rsi = df["rsi_14"].dropna()
    assert len(rsi) > 0
    assert rsi.min() >= 0
    assert rsi.max() <= 100


def test_macd_columns():
    df = compute_all_indicators(_make_ohlcv())
    assert "macd" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_hist" in df.columns


def test_sma_monotonic_on_rising():
    n = 100
    df = pd.DataFrame({
        "open":  np.arange(n, dtype=float),
        "high":  np.arange(n, dtype=float) + 1,
        "low":   np.arange(n, dtype=float) - 1,
        "close": np.arange(n, dtype=float),
        "volume": np.ones(n) * 1_000,
    })
    df = compute_all_indicators(df)
    # SMA_50 should be monotonically non-decreasing after warm-up
    sma = df["sma_50"].dropna()
    assert (sma.diff().dropna() >= -1e-9).all()


def test_atr_non_negative():
    df = compute_all_indicators(_make_ohlcv())
    atr = df["atr_14"].dropna()
    assert (atr >= 0).all()


def test_bollinger_bands_ordering():
    df = compute_all_indicators(_make_ohlcv())
    valid = df.dropna(subset=["bb_upper", "bb_mid", "bb_lower"])
    assert (valid["bb_upper"] >= valid["bb_mid"]).all()
    assert (valid["bb_mid"]   >= valid["bb_lower"]).all()


def test_vwap_positive():
    df = compute_all_indicators(_make_ohlcv())
    vwap = df["vwap"].dropna()
    assert (vwap > 0).all()
