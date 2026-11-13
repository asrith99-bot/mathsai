"""
Pydantic schemas for FastAPI request/response validation.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────
# Stock
# ─────────────────────────────────────────
class StockBase(BaseModel):
    symbol: str
    name: str
    sector: Optional[str] = None
    exchange: str = "NSE"


class StockCreate(StockBase):
    pass


class StockOut(StockBase):
    id: int
    is_active: bool
    instrument_key: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Live Tick
# ─────────────────────────────────────────
class LiveTickOut(BaseModel):
    symbol: str
    ltp: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    traded_value: Optional[float] = None
    data_source: str
    freshness: str           # LIVE | DELAYED | STALE
    tick_timestamp: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# OHLCV
# ─────────────────────────────────────────
class OHLCVOut(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    timeframe: str
    data_source: str

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Technical Snapshot
# ─────────────────────────────────────────
class TechnicalSnapshotOut(BaseModel):
    symbol: str
    timestamp: datetime
    timeframe: str
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    sma_5: Optional[float] = None
    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    atr_14: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_lower: Optional[float] = None
    vwap: Optional[float] = None
    momentum_5: Optional[float] = None
    volatility: Optional[float] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Signal
# ─────────────────────────────────────────
class SignalOut(BaseModel):
    id: int
    symbol: str
    signal_type: str
    confidence: float
    entry_price: float
    stop_loss: float
    target_price: float
    rr_ratio: Optional[float] = None
    risk_per_share: Optional[float] = None
    reward_per_share: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    atr: Optional[float] = None
    model_version: Optional[str] = None
    data_source: Optional[str] = None
    freshness: Optional[str] = None
    is_active: bool
    generated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Scanner Row (combined tick + signal + tech)
# ─────────────────────────────────────────
class ScannerRowOut(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    ltp: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    signal_type: Optional[str] = None
    confidence: Optional[float] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    freshness: str = "STALE"
    signal_id: Optional[int] = None
    signal_generated_at: Optional[datetime] = None


# ─────────────────────────────────────────
# Dashboard Stats
# ─────────────────────────────────────────
class DashboardStatsOut(BaseModel):
    total_stocks: int
    buy_count: int
    sell_count: int
    hold_count: int
    bullish_count: int
    bearish_count: int
    market_status: str           # OPEN | CLOSED | PRE_OPEN | POST_CLOSE
    last_update: Optional[datetime] = None
    top_buy_signals: List[SignalOut] = []
    top_sell_signals: List[SignalOut] = []
    recent_signals: List[SignalOut] = []


# ─────────────────────────────────────────
# Backtesting
# ─────────────────────────────────────────
class BacktestResultOut(BaseModel):
    id: int
    model_version: str
    run_at: datetime
    start_date: Optional[Any] = None
    end_date: Optional[Any] = None
    accuracy: Optional[float] = None
    precision_buy: Optional[float] = None
    recall_buy: Optional[float] = None
    f1_buy: Optional[float] = None
    precision_sell: Optional[float] = None
    recall_sell: Optional[float] = None
    f1_sell: Optional[float] = None
    total_return: Optional[float] = None
    win_rate: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_trades: Optional[int] = None
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    equity_curve: Optional[List[Dict]] = None
    per_stock_stats: Optional[Dict] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Model Performance
# ─────────────────────────────────────────
class ModelVersionOut(BaseModel):
    id: int
    model_name: str
    version: str
    trained_at: datetime
    features: Optional[List[str]] = None
    feature_importances: Optional[Dict[str, float]] = None
    val_accuracy: Optional[float] = None
    val_f1: Optional[float] = None
    test_accuracy: Optional[float] = None
    test_f1: Optional[float] = None
    prediction_distribution: Optional[Dict[str, float]] = None
    training_samples: Optional[int] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# WebSocket message envelope
# ─────────────────────────────────────────
class WSMessage(BaseModel):
    type: str               # tick_update | signal_update | market_status
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
