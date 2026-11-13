# AI Stock Intelligence – Real-Time Intraday Signal Platform
## Architecture & Development Blueprint

---

## 1. System Overview

```
NSE Market Data Provider (Upstox / Zerodha Kite / Yahoo Finance fallback)
         │
         ▼
 WebSocket Data Collector (backend/collector/)
         │
         ▼
 Market Data Processing (backend/app/services/market_data.py)
         │
         ▼
 Technical Indicator Engine (backend/engine/indicators.py)
         │
         ▼
 AI Prediction Engine (backend/engine/predictor.py)
         │
         ▼
 Signal Generation Engine (backend/engine/signal_generator.py)
         │
         ▼
 Risk Management Engine (backend/engine/risk_manager.py)
         │
         ▼
 Redis (live cache) + PostgreSQL (persistence)
         │
         ▼
 FastAPI REST + WebSocket Server (backend/app/main.py)
         │
         ▼
 React Live Dashboard (frontend/)
```

---

## 2. Folder Structure

```
shiva/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── config.py                # Settings, env vars
│   │   ├── dependencies.py          # DI: DB, Redis, auth
│   │   ├── routers/
│   │   │   ├── stocks.py            # Stock list, prices, OHLCV
│   │   │   ├── signals.py           # Signal CRUD, history
│   │   │   ├── backtest.py          # Backtesting endpoints
│   │   │   ├── model_perf.py        # Model metrics
│   │   │   └── health.py            # Health check
│   │   ├── models/
│   │   │   ├── db_models.py         # SQLAlchemy ORM models
│   │   │   └── schemas.py           # Pydantic request/response schemas
│   │   └── services/
│   │       ├── market_data.py       # Data provider abstraction
│   │       ├── redis_client.py      # Redis helpers
│   │       └── websocket_manager.py # WS broadcast manager
│   ├── collector/
│   │   ├── upstox_ws.py             # Upstox WebSocket client
│   │   ├── yahoo_fallback.py        # yfinance polling fallback
│   │   └── data_pipeline.py        # Normalize + route ticks
│   ├── engine/
│   │   ├── indicators.py            # TA-Lib / pandas_ta calculations
│   │   ├── feature_engineering.py  # ML feature builder
│   │   ├── predictor.py             # Model inference (RF + XGBoost)
│   │   ├── signal_generator.py      # BUY/SELL/HOLD signal logic
│   │   ├── risk_manager.py          # ATR-based SL/TP/RR
│   │   └── trainer.py               # Model training pipeline
│   ├── ml_models/                   # Saved model artifacts (.pkl, .json)
│   ├── tests/
│   │   ├── test_indicators.py
│   │   ├── test_signals.py
│   │   └── test_api.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── database/
│   ├── schema.sql                   # PostgreSQL DDL
│   └── migrations/                  # Alembic migrations
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Topbar.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── StatCard.tsx
│   │   │   │   ├── SignalSummary.tsx
│   │   │   │   └── MarketStatus.tsx
│   │   │   ├── scanner/
│   │   │   │   ├── StockTable.tsx
│   │   │   │   └── FilterBar.tsx
│   │   │   ├── charts/
│   │   │   │   ├── CandlestickChart.tsx
│   │   │   │   ├── VolumeChart.tsx
│   │   │   │   └── IndicatorChart.tsx
│   │   │   ├── signals/
│   │   │   │   ├── SignalCard.tsx
│   │   │   │   └── SignalHistory.tsx
│   │   │   └── common/
│   │   │       ├── Badge.tsx
│   │   │       ├── DataFreshness.tsx
│   │   │       └── LoadingSpinner.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Scanner.tsx
│   │   │   ├── StockDetail.tsx
│   │   │   ├── SignalCenter.tsx
│   │   │   ├── Backtesting.tsx
│   │   │   └── ModelPerformance.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useStockData.ts
│   │   │   └── useSignals.ts
│   │   ├── services/
│   │   │   ├── api.ts               # REST API client
│   │   │   └── wsClient.ts          # WebSocket client
│   │   ├── store/
│   │   │   ├── stockSlice.ts
│   │   │   ├── signalSlice.ts
│   │   │   └── store.ts
│   │   ├── types/
│   │   │   └── index.ts             # Shared TypeScript types
│   │   ├── utils/
│   │   │   └── formatters.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── docs/
│   └── API.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 3. Database Schema (PostgreSQL)

### stocks
- id, symbol, name, sector, is_active, created_at

### ohlcv_data
- id, symbol, timestamp, open, high, low, close, volume, vwap, timeframe, data_source

### signals
- id, symbol, signal_type (BUY/SELL/HOLD), confidence, entry_price, stop_loss, target_price, rr_ratio, model_version, generated_at, is_active, data_freshness

### technical_snapshots
- id, symbol, timestamp, rsi, macd, macd_signal, sma5/10/20/50, ema9/21, atr, bb_upper/mid/lower, vwap, volume_ma

### backtest_results
- id, model_version, run_at, accuracy, precision, recall, f1, total_return, win_rate, sharpe_ratio, max_drawdown, metadata (JSON)

### model_versions
- id, model_name, version, trained_at, features (JSON), val_accuracy, test_accuracy, file_path, is_active

---

## 4. Data Provider Strategy

| Provider        | Type         | Use Case                            |
|-----------------|--------------|-------------------------------------|
| Upstox API v2   | WebSocket    | Live intraday ticks (primary)       |
| Zerodha Kite    | WebSocket    | Alternative live feed               |
| yfinance        | REST polling | Delayed/historical fallback         |
| NSE India       | REST         | Corporate actions, instrument list  |

Data freshness labels:
- 🟢 LIVE     — data < 30 seconds old
- 🟡 DELAYED  — data 30s–5min old
- 🔴 STALE    — data > 5 minutes old or market closed

---

## 5. ML Model Strategy

| Model         | Purpose                        | Library      |
|---------------|--------------------------------|--------------|
| Random Forest | Baseline classifier            | scikit-learn |
| XGBoost       | Primary production model       | xgboost      |
| LSTM          | Sequence model (optional v2)   | PyTorch      |

Training frequency: Nightly (using previous day's intraday data)
Inference: Per tick / per 1-minute OHLCV close

---

## 6. Development Milestones

| Stage | Description                                   |
|-------|-----------------------------------------------|
| 1     | Architecture, structure, DB schema            |
| 2     | Market data integration (Upstox + fallback)   |
| 3     | Historical data + feature engineering        |
| 4     | ML model training + evaluation                |
| 5     | Signal + risk engine                          |
| 6     | FastAPI backend + WebSocket                   |
| 7     | React frontend + dashboard                    |
| 8     | Backtesting + visualization                   |
| 9     | Testing, optimization, deployment             |
