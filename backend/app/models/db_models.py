"""
SQLAlchemy ORM models mapping to PostgreSQL schema.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Float,
    Integer, JSON, Numeric, String, Text, UniqueConstraint,
    func
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = "stocks"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    symbol         = Column(String(20), nullable=False, unique=True, index=True)
    name           = Column(String(100), nullable=False)
    sector         = Column(String(50))
    exchange       = Column(String(10), nullable=False, default="NSE")
    instrument_key = Column(String(50))   # Upstox key
    kite_token     = Column(Integer)      # Zerodha token
    is_active      = Column(Boolean, nullable=False, default=True, index=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OHLCVData(Base):
    __tablename__ = "ohlcv_data"
    __table_args__ = (UniqueConstraint("symbol", "timestamp", "timeframe"),)

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol      = Column(String(20), nullable=False, index=True)
    timestamp   = Column(DateTime(timezone=True), nullable=False, index=True)
    open        = Column(Numeric(12, 4), nullable=False)
    high        = Column(Numeric(12, 4), nullable=False)
    low         = Column(Numeric(12, 4), nullable=False)
    close       = Column(Numeric(12, 4), nullable=False)
    volume      = Column(BigInteger, nullable=False, default=0)
    vwap        = Column(Numeric(12, 4))
    timeframe   = Column(String(10), nullable=False, default="1min")
    data_source = Column(String(20), nullable=False, default="unknown")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class LiveTick(Base):
    __tablename__ = "live_ticks"

    symbol       = Column(String(20), primary_key=True)
    ltp          = Column(Numeric(12, 4), nullable=False)
    open         = Column(Numeric(12, 4))
    high         = Column(Numeric(12, 4))
    low          = Column(Numeric(12, 4))
    prev_close   = Column(Numeric(12, 4))
    change_pct   = Column(Numeric(8, 4))
    volume       = Column(BigInteger)
    traded_value = Column(Numeric(18, 2))
    data_source  = Column(String(20), nullable=False, default="unknown")
    freshness    = Column(String(10), nullable=False, default="STALE")
    tick_timestamp = Column(DateTime(timezone=True))
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TechnicalSnapshot(Base):
    __tablename__ = "technical_snapshots"
    __table_args__ = (UniqueConstraint("symbol", "timestamp", "timeframe"),)

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol      = Column(String(20), nullable=False, index=True)
    timestamp   = Column(DateTime(timezone=True), nullable=False, index=True)
    timeframe   = Column(String(10), nullable=False, default="5min")
    rsi_14      = Column(Numeric(8, 4))
    macd        = Column(Numeric(12, 6))
    macd_signal = Column(Numeric(12, 6))
    macd_hist   = Column(Numeric(12, 6))
    sma_5       = Column(Numeric(12, 4))
    sma_10      = Column(Numeric(12, 4))
    sma_20      = Column(Numeric(12, 4))
    sma_50      = Column(Numeric(12, 4))
    ema_9       = Column(Numeric(12, 4))
    ema_21      = Column(Numeric(12, 4))
    atr_14      = Column(Numeric(12, 6))
    bb_upper    = Column(Numeric(12, 4))
    bb_mid      = Column(Numeric(12, 4))
    bb_lower    = Column(Numeric(12, 4))
    bb_width    = Column(Numeric(8, 6))
    vwap        = Column(Numeric(12, 4))
    volume_ma20 = Column(BigInteger)
    momentum_5  = Column(Numeric(8, 4))
    volatility  = Column(Numeric(8, 6))
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class Signal(Base):
    __tablename__ = "signals"

    id               = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol           = Column(String(20), nullable=False, index=True)
    signal_type      = Column(String(10), nullable=False)
    confidence       = Column(Numeric(5, 4), nullable=False)
    entry_price      = Column(Numeric(12, 4), nullable=False)
    stop_loss        = Column(Numeric(12, 4), nullable=False)
    target_price     = Column(Numeric(12, 4), nullable=False)
    rr_ratio         = Column(Numeric(6, 2))
    risk_per_share   = Column(Numeric(12, 4))
    reward_per_share = Column(Numeric(12, 4))
    rsi              = Column(Numeric(8, 4))
    macd             = Column(Numeric(12, 6))
    atr              = Column(Numeric(12, 6))
    model_version    = Column(String(50))
    data_source      = Column(String(20))
    freshness        = Column(String(10))
    is_active        = Column(Boolean, nullable=False, default=True, index=True)
    is_triggered     = Column(Boolean, nullable=False, default=False)
    generated_at     = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at       = Column(DateTime(timezone=True))
    closed_at        = Column(DateTime(timezone=True))
    close_reason     = Column(String(20))


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    model_version    = Column(String(50), nullable=False)
    run_at           = Column(DateTime(timezone=True), server_default=func.now())
    start_date       = Column(Date)
    end_date         = Column(Date)
    accuracy         = Column(Numeric(6, 4))
    precision_buy    = Column(Numeric(6, 4))
    recall_buy       = Column(Numeric(6, 4))
    f1_buy           = Column(Numeric(6, 4))
    precision_sell   = Column(Numeric(6, 4))
    recall_sell      = Column(Numeric(6, 4))
    f1_sell          = Column(Numeric(6, 4))
    total_return     = Column(Numeric(8, 4))
    win_rate         = Column(Numeric(6, 4))
    sharpe_ratio     = Column(Numeric(8, 4))
    max_drawdown     = Column(Numeric(8, 4))
    total_trades     = Column(Integer)
    winning_trades   = Column(Integer)
    losing_trades    = Column(Integer)
    avg_profit       = Column(Numeric(10, 4))
    avg_loss         = Column(Numeric(10, 4))
    transaction_cost_pct = Column(Numeric(6, 4), default=0.001)
    slippage_pct     = Column(Numeric(6, 4), default=0.0005)
    equity_curve     = Column(JSON)
    per_stock_stats  = Column(JSON)
    extra_metadata   = Column(JSON)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    model_name              = Column(String(50), nullable=False)
    version                 = Column(String(50), nullable=False, unique=True)
    trained_at              = Column(DateTime(timezone=True), server_default=func.now())
    features                = Column(JSON)
    feature_importances     = Column(JSON)
    val_accuracy            = Column(Numeric(6, 4))
    val_f1                  = Column(Numeric(6, 4))
    test_accuracy           = Column(Numeric(6, 4))
    test_f1                 = Column(Numeric(6, 4))
    prediction_distribution = Column(JSON)
    training_samples        = Column(Integer)
    file_path               = Column(String(255))
    is_active               = Column(Boolean, nullable=False, default=False)
    notes                   = Column(Text)
    created_at              = Column(DateTime(timezone=True), server_default=func.now())
