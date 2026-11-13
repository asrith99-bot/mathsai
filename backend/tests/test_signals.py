"""
Tests for signal generation and risk management.
"""
import numpy as np
import pandas as pd
import pytest

from engine.risk_manager import calculate_risk_profile, meets_rr_requirement
from engine.feature_engineering import build_feature_matrix, create_labels


def test_buy_sl_below_entry():
    rp = calculate_risk_profile("BUY", 1000.0, atr=20.0, freshness="LIVE")
    assert rp.stop_loss < rp.entry_price
    assert rp.target_price > rp.entry_price


def test_sell_sl_above_entry():
    rp = calculate_risk_profile("SELL", 1000.0, atr=20.0, freshness="LIVE")
    assert rp.stop_loss > rp.entry_price
    assert rp.target_price < rp.entry_price


def test_hold_flat():
    rp = calculate_risk_profile("HOLD", 1000.0, atr=0.0, freshness="LIVE")
    assert rp.entry_price == rp.stop_loss == rp.target_price


def test_rr_calculation():
    rp = calculate_risk_profile("BUY", 1000.0, atr=20.0, freshness="LIVE")
    expected_rr = rp.reward_per_share / rp.risk_per_share
    assert abs(rp.rr_ratio - expected_rr) < 0.01


def test_high_volatility_flag():
    # ATR > 3% of price
    rp = calculate_risk_profile("BUY", 1000.0, atr=35.0, freshness="LIVE")
    assert rp.high_volatility_warning


def test_stale_warning():
    rp = calculate_risk_profile("BUY", 1000.0, atr=10.0, freshness="STALE")
    assert rp.stale_data_warning


def test_label_creation():
    n = 200
    close = 1000 + np.cumsum(np.random.randn(n) * 2)
    df = pd.DataFrame({
        "open": close - 1, "high": close + 2, "low": close - 2,
        "close": close, "volume": np.ones(n) * 500_000,
    })
    df_labels = create_labels(df)
    assert "label" in df_labels.columns
    assert df_labels["label"].isin([0, 1, 2]).all()
    assert len(df_labels) == n - 1   # one row dropped for lookahead
