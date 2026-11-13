"""
ATR-based Risk Management Engine.

For every BUY or SELL signal, calculates:
  - Entry price
  - Stop-Loss (ATR-based)
  - Target price (ATR × multiplier)
  - Risk per share
  - Potential reward per share
  - Risk-to-reward ratio

Displays warnings for high-volatility conditions.
"""
from dataclasses import dataclass
from typing import Optional
from app.config import settings


@dataclass
class RiskProfile:
    signal_type: str
    entry_price: float
    stop_loss: float
    target_price: float
    risk_per_share: float
    reward_per_share: float
    rr_ratio: float
    atr: float
    high_volatility_warning: bool
    stale_data_warning: bool


def calculate_risk_profile(
    signal_type: str,
    current_price: float,
    atr: float,
    freshness: str = "LIVE",
    atr_multiplier_sl: Optional[float] = None,
    atr_multiplier_tp: Optional[float] = None,
) -> RiskProfile:
    """
    Calculate entry/SL/target using ATR multiples.

    For BUY:
        entry     = current_price
        stop_loss = entry - (ATR × sl_mult)
        target    = entry + (ATR × tp_mult)

    For SELL:
        entry     = current_price
        stop_loss = entry + (ATR × sl_mult)
        target    = entry - (ATR × tp_mult)

    For HOLD: returns flat levels at current_price.
    """
    sl_mult = atr_multiplier_sl or settings.atr_multiplier_sl
    tp_mult = atr_multiplier_tp or settings.atr_multiplier_tp

    # Fallback if ATR is missing or zero
    if not atr or atr <= 0:
        atr = current_price * 0.005  # 0.5% of price as ATR fallback

    high_vol_warning = atr / current_price > 0.03   # ATR > 3% of price
    stale_warning    = freshness in ("STALE",)

    if signal_type == "BUY":
        entry        = current_price
        stop_loss    = round(entry - atr * sl_mult, 2)
        target_price = round(entry + atr * tp_mult, 2)
    elif signal_type == "SELL":
        entry        = current_price
        stop_loss    = round(entry + atr * sl_mult, 2)
        target_price = round(entry - atr * tp_mult, 2)
    else:  # HOLD
        entry = stop_loss = target_price = round(current_price, 2)

    risk_per_share   = round(abs(entry - stop_loss), 2)
    reward_per_share = round(abs(entry - target_price), 2)
    rr_ratio         = round(reward_per_share / risk_per_share, 2) if risk_per_share > 0 else 0.0

    return RiskProfile(
        signal_type=signal_type,
        entry_price=round(entry, 2),
        stop_loss=stop_loss,
        target_price=target_price,
        risk_per_share=risk_per_share,
        reward_per_share=reward_per_share,
        rr_ratio=rr_ratio,
        atr=round(atr, 4),
        high_volatility_warning=high_vol_warning,
        stale_data_warning=stale_warning,
    )


def meets_rr_requirement(
    rr_ratio: float,
    min_rr: Optional[float] = None,
) -> bool:
    """Returns True if the risk-reward ratio meets the configured minimum."""
    threshold = min_rr or settings.risk_reward_ratio
    return rr_ratio >= threshold
