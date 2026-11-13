# AI Stock Intelligence – API Reference

Base URL (dev): `http://localhost:8000`

## Authentication
Currently open in development mode. Set `SECRET_KEY` in `.env` for production.

## REST Endpoints

### Health
```
GET /health
```
Returns database, Redis, market status, and WebSocket client count.

### Stocks
```
GET  /stocks                     List active watchlist (50 stocks)
POST /stocks                     Add stock { symbol, name, sector }
DELETE /stocks/{symbol}          Deactivate stock
GET  /stocks/scanner             Live scanner — all stocks + current signals
GET  /stocks/{symbol}/ohlcv      Historical candles (params: timeframe, limit)
GET  /stocks/{symbol}/detail     Stock info + tick + signals
```

### Signals
```
GET /signals/dashboard           Dashboard summary statistics
GET /signals/active              All currently active signals
GET /signals                     Signal history (params: symbol, signal_type, limit, offset)
```

### Backtest
```
POST /backtest/run               Trigger background backtest run
GET  /backtest                   List all backtest results
GET  /backtest/{id}              Single backtest with equity curve
```

### Model
```
GET  /model/active               Active model info + metadata
GET  /model/versions             All trained model versions
POST /model/train                Trigger background retraining (param: model_type)
POST /model/reload               Hot-reload latest model from disk
```

## WebSocket

Connect to `ws://localhost:8000/ws`

Send `ping` → receive `{"type":"pong"}`

Incoming messages:

```json
// Price update
{ "type": "tick_update", "symbol": "RELIANCE", "payload": { "ltp": 2850.50, "change_pct": 1.2, "freshness": "DELAYED", ... }, "timestamp": "..." }

// New signal
{ "type": "signal_update", "symbol": "RELIANCE", "payload": { "signal_type": "BUY", "confidence": 0.74, "entry_price": 2850.50, ... }, "timestamp": "..." }

// Market status change
{ "type": "market_status", "payload": { "status": "OPEN" }, "timestamp": "..." }
```

## Data Freshness Labels

- `LIVE` — data < 30 seconds old (Upstox/Kite WebSocket)
- `DELAYED` — data 30s–5min old (Yahoo Finance polling)
- `STALE` — data > 5 minutes old or market closed

Signals are **never generated on STALE data**.
