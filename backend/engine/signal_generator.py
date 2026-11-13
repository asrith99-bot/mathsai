"""
Signal Generation Engine.

Combines ML prediction + technical filters to produce
BUY / SELL / HOLD signals with risk parameters.

Filter rules:
  - Confidence must exceed configurable threshold.
  - For BUY:  RSI < 70 (not overbought) and price above VWAP.
  - For SELL: RSI > 30 (not oversold) and price below VWAP.
  - Risk-reward must meet minimum threshold.
  - Duplicate suppression: skip if last signal for symbol
    is same type and < 5 minutes old.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple

import pandas as pd
from loguru import logger

from app.config import settings
from engine.predictor import ModelPredictor, get_xgb_predictor
from engine.risk_manager import calculate_risk_profile, meets_rr_requirement

# ── In-memory last-signal cache (symbol → timestamp+type) ─────
# In production this should live in Redis to survive restarts.
_last_signal_cache: Dict[str, Tuple[str, datetime]] = {}
SIGNAL_COOLDOWN_SECONDS = 300   # 5 minutes


@dataclass
class GeneratedSignal:
    symbol: str
    signal_type: str          # BUY | SELL | HOLD
    confidence: float
    entry_price: float
    stop_loss: float
    target_price: float
    rr_ratio: float
    risk_per_share: float
    reward_per_share: float
    rsi: Optional[float]
    macd: Optional[float]
    atr: Optional[float]
    model_version: str
    data_source: str
    freshness: str
    high_volatility_warning: bool
    stale_data_warning: bool
    generated_at: datetime
    skipped: bool = False
    skip_reason: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items()}


def _technical_filter(
    signal_type: str,
    rsi: Optional[float],
    close: float,
    vwap: Optional[float],
    macd: Optional[float],
    macd_signal: Optional[float],
) -> Tuple[bool, str]:
    """
    Returns (passes, reason_if_filtered).
    """
    if signal_type == "BUY":
        if rsi is not None and rsi > 75:
            return False, f"RSI overbought ({rsi:.1f})"
        if vwap is not None and close < vwap * 0.995:
            return False, "Price below VWAP for BUY"
    elif signal_type == "SELL":
        if rsi is not None and rsi < 25:
            return False, f"RSI oversold ({rsi:.1f})"
        if vwap is not None and close > vwap * 1.005:
            return False, "Price above VWAP for SELL"
    return True, ""


def _is_duplicate(symbol: str, signal_type: str) -> Tuple[bool, str]:
    """Suppress duplicate signal within cooldown window."""
    if symbol in _last_signal_cache:
        last_type, last_ts = _last_signal_cache[symbol]
        age = (datetime.now(tz=timezone.utc) - last_ts).total_seconds()
        if last_type == signal_type and age < SIGNAL_COOLDOWN_SECONDS:
            return True, f"Duplicate {signal_type} within {age:.0f}s"
    return False, ""


def generate_signal(
    symbol: str,
    ohlcv_df: pd.DataFrame,
    indicators_df: pd.DataFrame,
    data_source: str = "unknown",
    freshness: str = "STALE",
    predictor: Optional[ModelPredictor] = None,
    confidence_threshold: Optional[float] = None,
) -> GeneratedSignal:
    """
    Main signal generation function for one symbol.

    Parameters:
        symbol:          NSE symbol string
        ohlcv_df:        DataFrame with OHLCV columns (used to build features)
        indicators_df:   DataFrame with computed technical indicators
        data_source:     'upstox', 'kite', 'yahoo', etc.
        freshness:       'LIVE', 'DELAYED', or 'STALE'
        predictor:       ModelPredictor instance (uses global XGB if None)
        confidence_threshold: override settings value

    Returns:
        GeneratedSignal dataclass
    """
    conf_threshold = confidence_threshold or settings.signal_confidence_threshold
    if predictor is None:
        predictor = get_xgb_predictor()

    # Latest row of indicators
    latest = indicators_df.iloc[-1]
    close        = float(latest.get("close",    0))
    rsi          = float(latest.get("rsi_14",   0)) if pd.notna(latest.get("rsi_14"))   else None
    macd_val     = float(latest.get("macd",     0)) if pd.notna(latest.get("macd"))     else None
    macd_sig_val = float(latest.get("macd_signal", 0)) if pd.notna(latest.get("macd_signal")) else None
    atr_val      = float(latest.get("atr_14",   0)) if pd.notna(latest.get("atr_14"))   else None
    vwap_val     = float(latest.get("vwap",     0)) if pd.notna(latest.get("vwap"))     else None

    def _skip(reason: str) -> GeneratedSignal:
        return GeneratedSignal(
            symbol=symbol, signal_type="HOLD", confidence=0.0,
            entry_price=close, stop_loss=close, target_price=close,
            rr_ratio=0.0, risk_per_share=0.0, reward_per_share=0.0,
            rsi=rsi, macd=macd_val, atr=atr_val,
            model_version=predictor.version,
            data_source=data_source, freshness=freshness,
            high_volatility_warning=False, stale_data_warning=(freshness == "STALE"),
            generated_at=datetime.now(tz=timezone.utc),
            skipped=True, skip_reason=reason,
        )

    # Refuse predictions on stale data
    if freshness == "STALE":
        return _skip("Data is STALE — refusing prediction")

    # ML prediction
    signal_type, confidence, probabilities = predictor.predict(ohlcv_df)

    # Confidence filter
    if confidence < conf_threshold and signal_type != "HOLD":
        logger.debug(f"{symbol}: {signal_type} confidence {confidence:.3f} < threshold {conf_threshold}")
        signal_type = "HOLD"
        confidence = probabilities.get("HOLD", confidence)

    # Duplicate suppression (only for directional signals)
    if signal_type in ("BUY", "SELL"):
        is_dup, dup_reason = _is_duplicate(symbol, signal_type)
        if is_dup:
            return _skip(dup_reason)

    # Technical filter
    if signal_type in ("BUY", "SELL"):
        passes, reason = _technical_filter(signal_type, rsi, close, vwap_val, macd_val, macd_sig_val)
        if not passes:
            logger.debug(f"{symbol}: Technical filter blocked {signal_type}: {reason}")
            return _skip(f"Technical filter: {reason}")

    # Risk calculation
    risk = calculate_risk_profile(
        signal_type=signal_type,
        current_price=close,
        atr=atr_val or 0,
        freshness=freshness,
    )

    # RR filter for directional signals
    if signal_type in ("BUY", "SELL") and not meets_rr_requirement(risk.rr_ratio):
        return _skip(f"R:R too low ({risk.rr_ratio:.2f} < {settings.risk_reward_ratio})")

    # Register in duplicate cache
    if signal_type in ("BUY", "SELL"):
        _last_signal_cache[symbol] = (signal_type, datetime.now(tz=timezone.utc))

    return GeneratedSignal(
        symbol=symbol,
        signal_type=signal_type,
        confidence=round(confidence, 4),
        entry_price=risk.entry_price,
        stop_loss=risk.stop_loss,
        target_price=risk.target_price,
        rr_ratio=risk.rr_ratio,
        risk_per_share=risk.risk_per_share,
        reward_per_share=risk.reward_per_share,
        rsi=rsi,
        macd=macd_val,
        atr=atr_val,
        model_version=predictor.version,
        data_source=data_source,
        freshness=freshness,
        high_volatility_warning=risk.high_volatility_warning,
        stale_data_warning=risk.stale_data_warning,
        generated_at=datetime.now(tz=timezone.utc),
        skipped=False,
    )
