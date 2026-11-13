-- =============================================================
-- AI Stock Intelligence Platform — PostgreSQL Schema
-- =============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================
-- STOCKS: Master watchlist
-- =============================================================
CREATE TABLE IF NOT EXISTS stocks (
    id          SERIAL PRIMARY KEY,
    symbol      VARCHAR(20)  NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    sector      VARCHAR(50),
    exchange    VARCHAR(10)  NOT NULL DEFAULT 'NSE',
    instrument_key VARCHAR(50),          -- Upstox instrument key
    kite_token  INTEGER,                 -- Zerodha token
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stocks_symbol ON stocks(symbol);
CREATE INDEX idx_stocks_active ON stocks(is_active);

-- =============================================================
-- OHLCV DATA: Historical and live candles
-- =============================================================
CREATE TABLE IF NOT EXISTS ohlcv_data (
    id          BIGSERIAL PRIMARY KEY,
    symbol      VARCHAR(20)  NOT NULL,
    timestamp   TIMESTAMPTZ  NOT NULL,
    open        NUMERIC(12,4) NOT NULL,
    high        NUMERIC(12,4) NOT NULL,
    low         NUMERIC(12,4) NOT NULL,
    close       NUMERIC(12,4) NOT NULL,
    volume      BIGINT       NOT NULL DEFAULT 0,
    vwap        NUMERIC(12,4),
    timeframe   VARCHAR(10)  NOT NULL DEFAULT '1min',  -- 1min, 5min, 15min, 1d
    data_source VARCHAR(20)  NOT NULL DEFAULT 'unknown', -- upstox, kite, yahoo, simulated
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (symbol, timestamp, timeframe)
);

CREATE INDEX idx_ohlcv_symbol_ts ON ohlcv_data(symbol, timestamp DESC);
CREATE INDEX idx_ohlcv_timeframe ON ohlcv_data(timeframe);

-- =============================================================
-- LIVE TICKS: Latest price per stock (single row per symbol)
-- =============================================================
CREATE TABLE IF NOT EXISTS live_ticks (
    symbol          VARCHAR(20)  PRIMARY KEY,
    ltp             NUMERIC(12,4) NOT NULL,
    open            NUMERIC(12,4),
    high            NUMERIC(12,4),
    low             NUMERIC(12,4),
    prev_close      NUMERIC(12,4),
    change_pct      NUMERIC(8,4),
    volume          BIGINT,
    traded_value    NUMERIC(18,2),
    data_source     VARCHAR(20)  NOT NULL DEFAULT 'unknown',
    freshness       VARCHAR(10)  NOT NULL DEFAULT 'STALE',  -- LIVE, DELAYED, STALE
    tick_timestamp  TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- =============================================================
-- TECHNICAL SNAPSHOTS: Per symbol per candle
-- =============================================================
CREATE TABLE IF NOT EXISTS technical_snapshots (
    id          BIGSERIAL PRIMARY KEY,
    symbol      VARCHAR(20)  NOT NULL,
    timestamp   TIMESTAMPTZ  NOT NULL,
    timeframe   VARCHAR(10)  NOT NULL DEFAULT '5min',
    -- Momentum
    rsi_14      NUMERIC(8,4),
    macd        NUMERIC(12,6),
    macd_signal NUMERIC(12,6),
    macd_hist   NUMERIC(12,6),
    -- Moving Averages
    sma_5       NUMERIC(12,4),
    sma_10      NUMERIC(12,4),
    sma_20      NUMERIC(12,4),
    sma_50      NUMERIC(12,4),
    ema_9       NUMERIC(12,4),
    ema_21      NUMERIC(12,4),
    -- Volatility
    atr_14      NUMERIC(12,6),
    bb_upper    NUMERIC(12,4),
    bb_mid      NUMERIC(12,4),
    bb_lower    NUMERIC(12,4),
    bb_width    NUMERIC(8,6),
    -- Volume
    vwap        NUMERIC(12,4),
    volume_ma20 BIGINT,
    -- Price Action
    momentum_5  NUMERIC(8,4),
    volatility  NUMERIC(8,6),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (symbol, timestamp, timeframe)
);

CREATE INDEX idx_tech_symbol_ts ON technical_snapshots(symbol, timestamp DESC);

-- =============================================================
-- SIGNALS: Generated trading signals
-- =============================================================
CREATE TABLE IF NOT EXISTS signals (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20)  NOT NULL,
    signal_type     VARCHAR(10)  NOT NULL CHECK (signal_type IN ('BUY','SELL','HOLD')),
    confidence      NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    entry_price     NUMERIC(12,4) NOT NULL,
    stop_loss       NUMERIC(12,4) NOT NULL,
    target_price    NUMERIC(12,4) NOT NULL,
    rr_ratio        NUMERIC(6,2),
    risk_per_share  NUMERIC(12,4),
    reward_per_share NUMERIC(12,4),
    -- Technical summary (snapshot at signal generation)
    rsi             NUMERIC(8,4),
    macd            NUMERIC(12,6),
    atr             NUMERIC(12,6),
    -- Meta
    model_version   VARCHAR(50),
    data_source     VARCHAR(20),
    freshness       VARCHAR(10),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_triggered    BOOLEAN NOT NULL DEFAULT FALSE,  -- price hit entry
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    close_reason    VARCHAR(20)  -- SL_HIT, TARGET_HIT, EXPIRED, MANUAL
);

CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_type ON signals(signal_type);
CREATE INDEX idx_signals_active ON signals(is_active, generated_at DESC);
CREATE INDEX idx_signals_generated ON signals(generated_at DESC);

-- =============================================================
-- BACKTEST RESULTS
-- =============================================================
CREATE TABLE IF NOT EXISTS backtest_results (
    id              SERIAL PRIMARY KEY,
    model_version   VARCHAR(50) NOT NULL,
    run_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    start_date      DATE,
    end_date        DATE,
    -- Classification metrics
    accuracy        NUMERIC(6,4),
    precision_buy   NUMERIC(6,4),
    recall_buy      NUMERIC(6,4),
    f1_buy          NUMERIC(6,4),
    precision_sell  NUMERIC(6,4),
    recall_sell     NUMERIC(6,4),
    f1_sell         NUMERIC(6,4),
    -- Trading metrics
    total_return    NUMERIC(8,4),
    win_rate        NUMERIC(6,4),
    sharpe_ratio    NUMERIC(8,4),
    max_drawdown    NUMERIC(8,4),
    total_trades    INTEGER,
    winning_trades  INTEGER,
    losing_trades   INTEGER,
    avg_profit      NUMERIC(10,4),
    avg_loss        NUMERIC(10,4),
    -- Assumptions
    transaction_cost_pct NUMERIC(6,4) DEFAULT 0.001,
    slippage_pct    NUMERIC(6,4) DEFAULT 0.0005,
    -- Serialized data
    equity_curve    JSONB,
    per_stock_stats JSONB,
    metadata        JSONB
);

-- =============================================================
-- MODEL VERSIONS
-- =============================================================
CREATE TABLE IF NOT EXISTS model_versions (
    id              SERIAL PRIMARY KEY,
    model_name      VARCHAR(50) NOT NULL,   -- random_forest, xgboost
    version         VARCHAR(50) NOT NULL UNIQUE,
    trained_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    features        JSONB,
    feature_importances JSONB,
    val_accuracy    NUMERIC(6,4),
    val_f1          NUMERIC(6,4),
    test_accuracy   NUMERIC(6,4),
    test_f1         NUMERIC(6,4),
    prediction_distribution JSONB,         -- {BUY: %, SELL: %, HOLD: %}
    training_samples INTEGER,
    file_path       VARCHAR(255),
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================
-- SEED DATA: 50 NSE Stocks
-- =============================================================
INSERT INTO stocks (symbol, name, sector) VALUES
  ('RELIANCE',   'Reliance Industries Ltd',           'Energy'),
  ('TCS',        'Tata Consultancy Services Ltd',      'Technology'),
  ('INFY',       'Infosys Ltd',                        'Technology'),
  ('HDFCBANK',   'HDFC Bank Ltd',                      'Banking'),
  ('ICICIBANK',  'ICICI Bank Ltd',                     'Banking'),
  ('SBIN',       'State Bank of India',                'Banking'),
  ('BHARTIARTL', 'Bharti Airtel Ltd',                  'Telecom'),
  ('ITC',        'ITC Ltd',                            'FMCG'),
  ('LT',         'Larsen & Toubro Ltd',                'Infrastructure'),
  ('AXISBANK',   'Axis Bank Ltd',                      'Banking'),
  ('KOTAKBANK',  'Kotak Mahindra Bank Ltd',            'Banking'),
  ('BAJFINANCE', 'Bajaj Finance Ltd',                  'Finance'),
  ('MARUTI',     'Maruti Suzuki India Ltd',            'Automobile'),
  ('SUNPHARMA',  'Sun Pharmaceutical Industries Ltd',  'Pharma'),
  ('TITAN',      'Titan Company Ltd',                  'Consumer'),
  ('TATAMOTORS', 'Tata Motors Ltd',                    'Automobile'),
  ('M&M',        'Mahindra & Mahindra Ltd',            'Automobile'),
  ('NTPC',       'NTPC Ltd',                           'Energy'),
  ('POWERGRID',  'Power Grid Corporation of India Ltd','Energy'),
  ('ONGC',       'Oil and Natural Gas Corporation Ltd','Energy'),
  ('TATASTEEL',  'Tata Steel Ltd',                     'Metals'),
  ('JSWSTEEL',   'JSW Steel Ltd',                      'Metals'),
  ('HINDALCO',   'Hindalco Industries Ltd',            'Metals'),
  ('WIPRO',      'Wipro Ltd',                          'Technology'),
  ('HCLTECH',    'HCL Technologies Ltd',               'Technology'),
  ('TECHM',      'Tech Mahindra Ltd',                  'Technology'),
  ('ULTRACEMCO', 'UltraTech Cement Ltd',               'Cement'),
  ('ASIANPAINT', 'Asian Paints Ltd',                   'Consumer'),
  ('NESTLEIND',  'Nestle India Ltd',                   'FMCG'),
  ('TRENT',      'Trent Ltd',                          'Retail'),
  ('BEL',        'Bharat Electronics Ltd',             'Defence'),
  ('ADANIPORTS', 'Adani Ports and Special Economic Zone Ltd', 'Infrastructure'),
  ('COALINDIA',  'Coal India Ltd',                     'Energy'),
  ('GRASIM',     'Grasim Industries Ltd',              'Diversified'),
  ('EICHERMOT',  'Eicher Motors Ltd',                  'Automobile'),
  ('DRREDDY',    'Dr Reddy''s Laboratories Ltd',       'Pharma'),
  ('CIPLA',      'Cipla Ltd',                          'Pharma'),
  ('DIVISLAB',   'Divi''s Laboratories Ltd',           'Pharma'),
  ('APOLLOHOSP', 'Apollo Hospitals Enterprise Ltd',    'Healthcare'),
  ('INDUSINDBK', 'IndusInd Bank Ltd',                  'Banking'),
  ('BANKBARODA', 'Bank of Baroda',                     'Banking'),
  ('PNB',        'Punjab National Bank',               'Banking'),
  ('CANBK',      'Canara Bank',                        'Banking'),
  ('DLF',        'DLF Ltd',                            'Real Estate'),
  ('GODREJCP',   'Godrej Consumer Products Ltd',       'FMCG'),
  ('SBILIFE',    'SBI Life Insurance Company Ltd',     'Insurance'),
  ('HDFCLIFE',   'HDFC Life Insurance Company Ltd',    'Insurance'),
  ('LTIM',       'LTIMindtree Ltd',                    'Technology'),
  ('ZOMATO',     'Zomato Ltd',                         'Consumer Tech'),
  ('HINDUNILVR', 'Hindustan Unilever Ltd',             'FMCG')
ON CONFLICT (symbol) DO NOTHING;
