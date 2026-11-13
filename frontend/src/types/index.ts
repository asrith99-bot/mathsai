// ─────────────────────────────────────────────────────────────
// Shared TypeScript types for the AI Stock Intelligence Platform
// ─────────────────────────────────────────────────────────────

export type SignalType = 'BUY' | 'SELL' | 'HOLD';
export type Freshness  = 'LIVE' | 'DELAYED' | 'STALE';
export type MarketStatus = 'OPEN' | 'CLOSED' | 'PRE_OPEN' | 'POST_CLOSE' | 'UNKNOWN';

export interface Stock {
  id: number;
  symbol: string;
  name: string;
  sector?: string;
  exchange: string;
  is_active: boolean;
  instrument_key?: string;
}

export interface LiveTick {
  symbol: string;
  ltp: number;
  open?: number;
  high?: number;
  low?: number;
  prev_close?: number;
  change_pct?: number;
  volume?: number;
  traded_value?: number;
  data_source: string;
  freshness: Freshness;
  tick_timestamp?: string;
  updated_at: string;
}

export interface OHLCVBar {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number;
  timeframe: string;
  data_source: string;
}

export interface Signal {
  id: number;
  symbol: string;
  signal_type: SignalType;
  confidence: number;
  entry_price: number;
  stop_loss: number;
  target_price: number;
  rr_ratio?: number;
  risk_per_share?: number;
  reward_per_share?: number;
  rsi?: number;
  macd?: number;
  atr?: number;
  model_version?: string;
  data_source?: string;
  freshness?: Freshness;
  is_active: boolean;
  generated_at: string;
}

export interface ScannerRow {
  symbol: string;
  name?: string;
  sector?: string;
  ltp?: number;
  change_pct?: number;
  volume?: number;
  rsi?: number;
  macd?: number;
  signal_type?: SignalType;
  confidence?: number;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  freshness: Freshness;
  signal_id?: number;
  signal_generated_at?: string;
  isNew?: boolean;   // frontend flag for highlight animation
}

export interface DashboardStats {
  total_stocks: number;
  buy_count: number;
  sell_count: number;
  hold_count: number;
  bullish_count: number;
  bearish_count: number;
  market_status: MarketStatus;
  last_update?: string;
  top_buy_signals: Signal[];
  top_sell_signals: Signal[];
  recent_signals: Signal[];
}

export interface BacktestResult {
  id: number;
  model_version: string;
  run_at: string;
  start_date?: string;
  end_date?: string;
  accuracy?: number;
  precision_buy?: number;
  recall_buy?: number;
  f1_buy?: number;
  precision_sell?: number;
  recall_sell?: number;
  f1_sell?: number;
  total_return?: number;
  win_rate?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  total_trades?: number;
  winning_trades?: number;
  losing_trades?: number;
  avg_profit?: number;
  avg_loss?: number;
  equity_curve?: Array<{ date: string; equity: number }>;
  per_stock_stats?: Record<string, { trades: number; wins: number; win_rate: number; total_pnl: number }>;
}

export interface ModelVersion {
  id: number;
  model_name: string;
  version: string;
  trained_at: string;
  features?: string[];
  feature_importances?: Record<string, number>;
  val_accuracy?: number;
  val_f1?: number;
  test_accuracy?: number;
  test_f1?: number;
  prediction_distribution?: Record<string, number>;
  training_samples?: number;
  is_active: boolean;
}

// WebSocket message types
export type WSMessageType = 'tick_update' | 'signal_update' | 'market_status' | 'pong';

export interface WSMessage {
  type: WSMessageType;
  symbol?: string;
  payload: Record<string, unknown>;
  timestamp: string;
}
