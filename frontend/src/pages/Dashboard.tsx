import React from 'react';
import { useSignals } from '../hooks/useSignals';
import { StatCard }    from '../components/dashboard/StatCard';
import { MarketStatus } from '../components/dashboard/MarketStatus';
import { SignalCard }  from '../components/signals/SignalCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { MOCK_DASHBOARD } from '../utils/mockData';

export const Dashboard: React.FC = () => {
  const { dashboard, loading } = useSignals();

  if (loading && !dashboard) {
    return <div className="flex items-center justify-center h-64"><LoadingSpinner size={40} /></div>;
  }

  // Use real data if available, fall back to mock
  const d = (dashboard && dashboard.total_stocks > 0) ? dashboard : MOCK_DASHBOARD;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Market Dashboard</h1>
          <p className="text-muted text-sm mt-1">AI-powered signal monitoring for 50 NSE equities</p>
        </div>
        <MarketStatus status={d.market_status} lastUpdate={d.last_update ?? undefined} />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <StatCard label="Stocks"  value={d.total_stocks}  icon="◉" />
        <StatCard label="BUY"     value={d.buy_count}     color="text-signal-buy"  icon="▲" />
        <StatCard label="SELL"    value={d.sell_count}    color="text-signal-sell" icon="▼" />
        <StatCard label="HOLD"    value={d.hold_count}    color="text-signal-hold" icon="◈" />
        <StatCard label="Bullish" value={d.bullish_count} color="text-signal-buy"  />
        <StatCard label="Bearish" value={d.bearish_count} color="text-signal-sell" />
        <StatCard label="Market"  value={d.market_status}
          color={d.market_status === 'OPEN' ? 'text-signal-buy' : 'text-muted'} />
      </div>

      {/* Top signals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Top BUY Signals</h2>
          <div className="space-y-3">
            {d.top_buy_signals.map(s => <SignalCard key={s.id} signal={s} />)}
          </div>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Top SELL Signals</h2>
          <div className="space-y-3">
            {d.top_sell_signals.map(s => <SignalCard key={s.id} signal={s} />)}
          </div>
        </div>
      </div>

      {/* Recent activity */}
      <div>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Recent Signal Activity</h2>
        <div className="bg-bg-card border border-bg-border rounded-xl overflow-hidden divide-y divide-bg-border">
          {d.recent_signals.map(s => (
            <div key={s.id} className="flex items-center justify-between px-5 py-3 text-sm hover:bg-surface transition-colors">
              <div className="flex items-center gap-3">
                <span className="font-mono font-bold text-white w-28">{s.symbol}</span>
                <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded
                  ${s.signal_type==='BUY' ? 'bg-signal-buy-dim text-signal-buy'
                  : s.signal_type==='SELL' ? 'bg-signal-sell-dim text-signal-sell'
                  : 'bg-signal-hold-dim text-signal-hold'}`}>
                  {s.signal_type}
                </span>
              </div>
              <div className="flex items-center gap-6 text-xs text-muted font-mono">
                <span className="text-white">{(s.confidence * 100).toFixed(0)}% conf</span>
                <span>₹{s.entry_price.toLocaleString('en-IN')}</span>
                <span>SL ₹{s.stop_loss.toLocaleString('en-IN')}</span>
                <span>T ₹{s.target_price.toLocaleString('en-IN')}</span>
                <span className="text-muted">{new Date(s.generated_at).toLocaleTimeString('en-IN')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-muted text-center border-t border-bg-border pt-4">
        ⚠ AI signals are for informational purposes only. This is not financial advice. Data may be delayed. Verify before trading.
      </p>
    </div>
  );
};
