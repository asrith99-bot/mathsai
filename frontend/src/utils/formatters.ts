import { Freshness, SignalType } from '../types';

export const formatPrice = (n?: number | null): string =>
  n == null ? '—' : `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const formatChange = (n?: number | null): string => {
  if (n == null) return '—';
  const sign = n >= 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}%`;
};

export const formatVolume = (n?: number | null): string => {
  if (n == null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
};

export const formatConfidence = (n?: number | null): string =>
  n == null ? '—' : `${(n * 100).toFixed(1)}%`;

export const formatRR = (n?: number | null): string =>
  n == null ? '—' : `1:${n.toFixed(2)}`;

export const formatPct = (n?: number | null): string => {
  if (n == null) return '—';
  const sign = n >= 0 ? '+' : '';
  return `${sign}${(n * 100).toFixed(2)}%`;
};

export const signalColor = (type?: SignalType | null): string => {
  if (type === 'BUY')  return 'text-signal-buy';
  if (type === 'SELL') return 'text-signal-sell';
  return 'text-signal-hold';
};

export const signalBg = (type?: SignalType | null): string => {
  if (type === 'BUY')  return 'bg-signal-buy-dim text-signal-buy';
  if (type === 'SELL') return 'bg-signal-sell-dim text-signal-sell';
  return 'bg-signal-hold-dim text-signal-hold';
};

export const changeColor = (n?: number | null): string => {
  if (n == null) return 'text-muted';
  return n >= 0 ? 'text-signal-buy' : 'text-signal-sell';
};

export const freshnessColor = (f: Freshness): string => {
  if (f === 'LIVE')    return 'text-signal-buy';
  if (f === 'DELAYED') return 'text-yellow-400';
  return 'text-signal-sell';
};

export const freshnessLabel = (f: Freshness): string => {
  if (f === 'LIVE')    return '🟢 LIVE';
  if (f === 'DELAYED') return '🟡 DELAYED';
  return '🔴 STALE';
};

export const timeAgo = (ts?: string | null): string => {
  if (!ts) return '—';
  const diff = (Date.now() - new Date(ts).getTime()) / 1000;
  if (diff < 60)   return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  return `${Math.round(diff / 3600)}h ago`;
};
