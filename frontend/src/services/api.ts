/**
 * REST API client — all calls fail silently and fall back to mock data.
 * Mock mode is active when VITE_MOCK_MODE=true or backend is unreachable.
 */
import axios from 'axios';
import type {
  BacktestResult, DashboardStats, ModelVersion,
  OHLCVBar, ScannerRow, Signal, Stock,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api';

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 4_000,
  headers: { 'Content-Type': 'application/json' },
});

// Silent error — returns null instead of throwing
const safe = <T>(promise: Promise<T>): Promise<T | null> =>
  promise.catch(() => null);

export const stocksApi = {
  list:    ()                        => safe(http.get<Stock[]>('/stocks').then(r => r.data)),
  add:     (payload: Partial<Stock>) => safe(http.post<Stock>('/stocks', payload).then(r => r.data)),
  remove:  (symbol: string)          => safe(http.delete(`/stocks/${symbol}`)),
  scanner: (params?: Record<string, string>) =>
    safe(http.get<ScannerRow[]>('/stocks/scanner', { params }).then(r => r.data)),
  ohlcv: (symbol: string, timeframe = '5m', limit = 200) =>
    safe(http.get<OHLCVBar[]>(`/stocks/${symbol}/ohlcv`, { params: { timeframe, limit } }).then(r => r.data)),
  detail: (symbol: string) =>
    safe(http.get(`/stocks/${symbol}/detail`).then(r => r.data)),
};

export const signalsApi = {
  dashboard: () => safe(http.get<DashboardStats>('/signals/dashboard').then(r => r.data)),
  active:    (type?: string) =>
    safe(http.get<Signal[]>('/signals/active', { params: type ? { signal_type: type } : {} }).then(r => r.data)),
  history:   (params?: Record<string, string | number>) =>
    safe(http.get<Signal[]>('/signals', { params }).then(r => r.data)),
};

export const backtestApi = {
  run:  () => safe(http.post('/backtest/run').then(r => r.data)),
  list: () => safe(http.get<BacktestResult[]>('/backtest').then(r => r.data)),
  get:  (id: number) => safe(http.get<BacktestResult>(`/backtest/${id}`).then(r => r.data)),
};

export const modelApi = {
  versions: () => safe(http.get<ModelVersion[]>('/model/versions').then(r => r.data)),
  active:   () => safe(http.get('/model/active').then(r => r.data)),
  train:    (model_type = 'xgboost') =>
    safe(http.post('/model/train', null, { params: { model_type } }).then(r => r.data)),
  reload:   () => safe(http.post('/model/reload').then(r => r.data)),
};

export const healthApi = {
  check: () => safe(http.get('/health').then(r => r.data)),
};
