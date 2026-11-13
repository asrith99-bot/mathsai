# AI Stock Intelligence – Real-Time Intraday Signal Platform

> AI-powered trading signal platform for 50 NSE-listed equities.
> Generates BUY / SELL / HOLD signals with Entry, Stop-Loss and Target using XGBoost + technical indicators.

## ⚠️ Disclaimer

**This platform is for educational and informational purposes only. It is NOT financial advice. AI signals do not guarantee profits. All trading involves risk. Verify all signals independently before acting.**

---

## Architecture

```
Yahoo Finance / Upstox WebSocket
        ↓
Data Collector (Python async)
        ↓
Technical Indicator Engine (pandas-ta)
        ↓
XGBoost Prediction Engine
        ↓
Signal + Risk Management Engine
        ↓
Redis (live cache) + PostgreSQL (history)
        ↓
FastAPI REST + WebSocket (/ws)
        ↓
React Dashboard (Vite + Tailwind + TradingView)
```

## Data Sources

| Source         | Type     | Freshness | Note                              |
|----------------|----------|-----------|-----------------------------------|
| Yahoo Finance  | Polling  | DELAYED   | Default fallback, ~15–20 min delay |
| Upstox API v2  | WebSocket| LIVE      | Requires account + paid API plan  |
| Zerodha Kite   | WebSocket| LIVE      | Requires account + paid API plan  |

The app always displays the data freshness label: 🟢 LIVE / 🟡 DELAYED / 🔴 STALE.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ (or Docker)
- Redis 6+ (or Docker)

### 1. Clone and configure

```bash
cd shiva
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start infrastructure (Docker)

```bash
docker-compose up postgres redis -d
```

### 3. Backend setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Train the ML model (required before signals work)

```bash
cd backend
python -m engine.trainer
# Downloads ~60 days of 5-minute OHLCV data for 50 symbols
# Trains XGBoost classifier, saves to ml_models/
# Takes 5–15 minutes depending on internet speed
```

### 5. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs
WebSocket: ws://localhost:8000/ws

### 6. Frontend setup

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## Docker Full Stack

```bash
# Copy .env
cp .env.example .env

# Build and start everything
docker-compose up --build

# Frontend runs separately (not Dockerized by default)
cd frontend && npm install && npm run dev
```

---

## Configuration

All settings in `.env`:

| Variable                   | Default           | Description                      |
|----------------------------|-------------------|----------------------------------|
| `DATA_PROVIDER`            | `yahoo_fallback`  | `upstox`, `kite`, `yahoo_fallback` |
| `SIGNAL_CONFIDENCE_THRESHOLD` | `0.60`         | Min ML confidence for signals    |
| `RISK_REWARD_RATIO`        | `2.0`             | Min R:R to emit a signal         |
| `ATR_MULTIPLIER_SL`        | `1.5`             | ATR multiple for stop-loss       |
| `ATR_MULTIPLIER_TP`        | `3.0`             | ATR multiple for target          |
| `UPSTOX_ACCESS_TOKEN`      | _(empty)_         | Required for live data           |

---

## Pages

| Page              | Route         | Description                         |
|-------------------|---------------|-------------------------------------|
| Dashboard         | `/`           | Stats, top signals, recent activity |
| Live Scanner      | `/scanner`    | 50 stocks table with live signals   |
| Stock Detail      | `/stock/:sym` | Charts, indicators, signal history  |
| Signal Center     | `/signals`    | All signals with filtering          |
| Backtesting       | `/backtest`   | Historical performance metrics      |
| Model Performance | `/model`      | XGBoost metrics, feature importances|

---

## API Endpoints

| Method | Path                         | Description               |
|--------|------------------------------|---------------------------|
| GET    | /stocks                      | List all stocks           |
| GET    | /stocks/scanner              | Live scanner snapshot     |
| GET    | /stocks/{symbol}/ohlcv       | Historical OHLCV          |
| GET    | /stocks/{symbol}/detail      | Full stock detail         |
| GET    | /signals/dashboard           | Dashboard stats           |
| GET    | /signals/active              | Active signals            |
| GET    | /signals                     | Signal history            |
| POST   | /backtest/run                | Trigger backtest          |
| GET    | /backtest                    | List backtest results     |
| POST   | /model/train                 | Trigger model retraining  |
| GET    | /model/active                | Active model info         |
| WS     | /ws                          | Live market data stream   |
| GET    | /health                      | System health check       |

---

## ML Model

- **Algorithm**: XGBoost (primary), Random Forest (baseline)
- **Features**: 30+ including RSI, MACD, SMA/EMA, ATR, Bollinger Bands, VWAP, momentum, candlestick patterns
- **Target**: 5-minute price direction (BUY > +0.3% / SELL < -0.3% / HOLD)
- **Split**: Chronological 70/15/15 — no lookahead leakage
- **Retraining**: Manual via `/model/train` or scheduled nightly

---

## Project Structure

```
shiva/
├── backend/           # FastAPI + ML engine
│   ├── app/           # Routers, models, services
│   ├── collector/     # Market data collection
│   ├── engine/        # Indicators, ML, signals, risk
│   ├── ml_models/     # Trained model artifacts
│   └── tests/
├── frontend/          # React + TypeScript
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── store/
│       └── services/
├── database/          # PostgreSQL schema
├── docker-compose.yml
└── .env.example
```
