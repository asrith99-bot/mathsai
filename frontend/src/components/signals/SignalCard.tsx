import React from 'react';
import { SignalBadge } from '../common/Badge';
import { DataFreshness } from '../common/DataFreshness';
import {
  formatPrice, formatConfidence, formatRR, timeAgo
} from '../../utils/formatters';
import type { Signal } from '../../types';

export const SignalCard: React.FC<{ signal: Signal }> = ({ signal }) => (
  <div className="bg-bg-card border border-bg-border rounded-xl p-4 flex flex-col gap-3 animate-fade-in">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="font-mono font-bold text-white text-lg">{signal.symbol}</span>
        <SignalBadge type={signal.signal_type} size="md" />
      </div>
      <div className="text-xs text-muted font-mono">{timeAgo(signal.generated_at)}</div>
    </div>

    <div className="grid grid-cols-3 gap-3 text-center">
      <div>
        <div className="text-xs text-muted mb-1">Entry</div>
        <div className="font-mono text-sm font-semibold text-white">{formatPrice(signal.entry_price)}</div>
      </div>
      <div>
        <div className="text-xs text-muted mb-1">Stop-Loss</div>
        <div className="font-mono text-sm font-semibold text-signal-sell">{formatPrice(signal.stop_loss)}</div>
      </div>
      <div>
        <div className="text-xs text-muted mb-1">Target</div>
        <div className="font-mono text-sm font-semibold text-signal-buy">{formatPrice(signal.target_price)}</div>
      </div>
    </div>

    <div className="flex items-center justify-between text-xs">
      <span className="text-muted">Confidence: <span className="text-white font-mono">{formatConfidence(signal.confidence)}</span></span>
      <span className="text-muted">R:R <span className="text-white font-mono">{formatRR(signal.rr_ratio)}</span></span>
      {signal.freshness && (
        <DataFreshness freshness={signal.freshness} showTime={false} />
      )}
    </div>

    {signal.rsi && (
      <div className="flex gap-4 text-xs text-muted border-t border-bg-border pt-3">
        <span>RSI: <span className="text-white font-mono">{signal.rsi.toFixed(1)}</span></span>
        {signal.macd != null && (
          <span>MACD: <span className={`font-mono ${signal.macd >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
            {signal.macd.toFixed(2)}
          </span></span>
        )}
        {signal.atr != null && (
          <span>ATR: <span className="text-white font-mono">{signal.atr.toFixed(2)}</span></span>
        )}
      </div>
    )}
  </div>
);
