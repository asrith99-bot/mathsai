import React from 'react';
import { useNavigate } from 'react-router-dom';
import { SignalBadge } from '../common/Badge';
import { DataFreshness } from '../common/DataFreshness';
import {
  formatPrice, formatChange, formatVolume,
  formatConfidence, changeColor, formatRR,
} from '../../utils/formatters';
import type { ScannerRow } from '../../types';

interface Props {
  rows: ScannerRow[];
}

export const StockTable: React.FC<Props> = ({ rows }) => {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="text-xs text-muted uppercase tracking-wider border-b border-bg-border">
            {['Symbol', 'LTP', 'Change', 'Volume', 'RSI', 'MACD', 'Signal', 'Conf.', 'Entry', 'SL', 'Target', 'R:R', 'Data'].map(h => (
              <th key={h} className="text-left py-2 px-3 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr
              key={row.symbol}
              onClick={() => navigate(`/stock/${row.symbol}`)}
              className={`border-b border-bg-border/50 hover:bg-bg-card/70 cursor-pointer transition-colors
                ${row.isNew ? 'animate-fade-in bg-accent/5' : ''}`}
            >
              <td className="py-2 px-3">
                <div className="font-mono font-semibold text-white">{row.symbol}</div>
                {row.sector && <div className="text-xs text-muted">{row.sector}</div>}
              </td>
              <td className="py-2 px-3 font-mono text-white">{formatPrice(row.ltp)}</td>
              <td className={`py-2 px-3 font-mono font-semibold ${changeColor(row.change_pct)}`}>
                {formatChange(row.change_pct)}
              </td>
              <td className="py-2 px-3 font-mono text-muted">{formatVolume(row.volume)}</td>
              <td className={`py-2 px-3 font-mono ${
                row.rsi == null ? 'text-muted' :
                row.rsi > 70 ? 'text-signal-sell' :
                row.rsi < 30 ? 'text-signal-buy' :
                'text-white'
              }`}>
                {row.rsi?.toFixed(1) ?? '—'}
              </td>
              <td className={`py-2 px-3 font-mono text-xs ${
                row.macd == null ? 'text-muted' :
                row.macd > 0 ? 'text-signal-buy' : 'text-signal-sell'
              }`}>
                {row.macd?.toFixed(2) ?? '—'}
              </td>
              <td className="py-2 px-3">
                {row.signal_type ? <SignalBadge type={row.signal_type} /> : <span className="text-muted">—</span>}
              </td>
              <td className="py-2 px-3 font-mono text-white">{formatConfidence(row.confidence)}</td>
              <td className="py-2 px-3 font-mono text-xs text-white">{formatPrice(row.entry_price)}</td>
              <td className="py-2 px-3 font-mono text-xs text-signal-sell">{formatPrice(row.stop_loss)}</td>
              <td className="py-2 px-3 font-mono text-xs text-signal-buy">{formatPrice(row.target_price)}</td>
              <td className="py-2 px-3 font-mono text-xs text-muted">
                {row.entry_price && row.stop_loss && row.target_price
                  ? formatRR(Math.abs(row.target_price - row.entry_price) / Math.abs(row.entry_price - row.stop_loss))
                  : '—'}
              </td>
              <td className="py-2 px-3">
                <DataFreshness freshness={row.freshness} showTime={false} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && (
        <div className="text-center py-16 text-muted">No stocks match the current filters.</div>
      )}
    </div>
  );
};
