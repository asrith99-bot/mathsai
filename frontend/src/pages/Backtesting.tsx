import React, { useEffect, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar,
} from 'recharts';
import { backtestApi } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { MOCK_BACKTEST } from '../utils/mockData';
import type { BacktestResult } from '../types';
import { formatPct } from '../utils/formatters';

const MetricCard: React.FC<{ label: string; value: string; color?: string; sub?: string }> = ({ label, value, color = 'text-white', sub }) => (
  <div className="bg-bg-card border border-bg-border rounded-xl p-4">
    <div className="text-xs text-muted mb-1 uppercase tracking-wider">{label}</div>
    <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
    {sub && <div className="text-xs text-muted mt-1">{sub}</div>}
  </div>
);

const tooltipStyle = { backgroundColor:'#1a1a28', border:'1px solid #2a2a3d', fontSize:12 };

export const Backtesting: React.FC = () => {
  const [results,   setResults]   = useState<BacktestResult[]>([]);
  const [selected,  setSelected]  = useState<BacktestResult | null>(null);
  const [loading,   setLoading]   = useState(true);
  const [running,   setRunning]   = useState(false);
  const [usingMock, setUsingMock] = useState(false);

  const load = () => {
    setLoading(true);
    backtestApi.list()
      .then(r => {
        if (r.length > 0) {
          setResults(r);
          setSelected(r[0]);
          setUsingMock(false);
        } else {
          setResults([MOCK_BACKTEST]);
          setSelected(MOCK_BACKTEST);
          setUsingMock(true);
        }
      })
      .catch(() => {
        setResults([MOCK_BACKTEST]);
        setSelected(MOCK_BACKTEST);
        setUsingMock(true);
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const triggerBacktest = async () => {
    setRunning(true);
    await backtestApi.run().catch(() => {});
    setTimeout(() => { setRunning(false); load(); }, 15_000);
  };

  const bt = selected;

  // Classification metrics for bar chart
  const classMetrics = bt ? [
    { name: 'BUY Precision',  value: +(( bt.precision_buy  ?? 0)*100).toFixed(1), fill:'#00d084' },
    { name: 'BUY Recall',     value: +(( bt.recall_buy     ?? 0)*100).toFixed(1), fill:'#00d084' },
    { name: 'BUY F1',         value: +(( bt.f1_buy         ?? 0)*100).toFixed(1), fill:'#00d084' },
    { name: 'SELL Precision', value: +(( bt.precision_sell ?? 0)*100).toFixed(1), fill:'#ff4d4d' },
    { name: 'SELL Recall',    value: +(( bt.recall_sell    ?? 0)*100).toFixed(1), fill:'#ff4d4d' },
    { name: 'SELL F1',        value: +(( bt.f1_sell        ?? 0)*100).toFixed(1), fill:'#ff4d4d' },
  ] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Backtesting Dashboard</h1>
          <p className="text-muted text-sm mt-1">
            Historical model performance · includes transaction costs &amp; slippage
          </p>
        </div>
        <button onClick={triggerBacktest} disabled={running}
          className="px-4 py-2 bg-accent hover:bg-accent/80 text-white rounded-lg text-sm font-semibold disabled:opacity-50">
          {running ? '⏳ Running…' : '▶ Run Backtest'}
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-24"><LoadingSpinner size={40} /></div>
      ) : !bt ? (
        <div className="text-muted text-center py-24">No results yet.</div>
      ) : (
        <>
          {/* Key metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            <MetricCard label="Total Return"  value={formatPct(bt.total_return)}  color={(bt.total_return??0)>=0?'text-signal-buy':'text-signal-sell'} sub="on ₹1L capital" />
            <MetricCard label="Win Rate"      value={`${((bt.win_rate??0)*100).toFixed(1)}%`} />
            <MetricCard label="Sharpe Ratio"  value={(bt.sharpe_ratio??0).toFixed(2)} />
            <MetricCard label="Max Drawdown"  value={formatPct(bt.max_drawdown)} color="text-signal-sell" />
            <MetricCard label="Total Trades"  value={String(bt.total_trades??0)} />
            <MetricCard label="Wins"          value={String(bt.winning_trades??0)} color="text-signal-buy" />
            <MetricCard label="Losses"        value={String(bt.losing_trades??0)}  color="text-signal-sell" />
            <MetricCard label="Avg Profit"    value={`₹${(bt.avg_profit??0).toFixed(0)}`} color="text-signal-buy" />
          </div>

          {/* Assumptions */}
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 text-xs text-yellow-400">
            ⚠ Assumptions: Transaction cost 0.10% · Slippage 0.05% · Model v{bt.model_version} ·
            Past performance does not guarantee future results.
          </div>

          {/* Equity curve */}
          {bt.equity_curve && bt.equity_curve.length > 0 && (
            <div className="bg-bg-card border border-bg-border rounded-xl p-5">
              <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-4">Equity Curve</h2>
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={bt.equity_curve}>
                  <defs>
                    <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#6c63ff" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6c63ff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3d" />
                  <XAxis dataKey="date" stroke="#5a5a7a" tick={{ fontSize:10 }} />
                  <YAxis stroke="#5a5a7a" tick={{ fontSize:10 }} tickFormatter={v=>`₹${(v/1000).toFixed(0)}K`} />
                  <Tooltip contentStyle={tooltipStyle}
                    formatter={(v:number) => [`₹${v.toLocaleString('en-IN')}`, 'Portfolio']} />
                  <Area type="monotone" dataKey="equity" stroke="#6c63ff" fill="url(#eqGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Classification metrics */}
          {classMetrics.length > 0 && (
            <div className="bg-bg-card border border-bg-border rounded-xl p-5">
              <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-4">Classification Metrics (%)</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={classMetrics} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3d" horizontal={false} />
                  <XAxis type="number" domain={[0,100]} stroke="#5a5a7a" tick={{ fontSize:10 }} />
                  <YAxis type="category" dataKey="name" stroke="#5a5a7a" tick={{ fontSize:11 }} width={110} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v:number) => [`${v}%`]} />
                  <Bar dataKey="value" radius={[0,4,4,0]}>
                    {classMetrics.map((e,i) => (
                      <rect key={i} fill={e.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Per-stock table */}
          {bt.per_stock_stats && (
            <div className="bg-bg-card border border-bg-border rounded-xl overflow-hidden">
              <div className="p-4 border-b border-bg-border text-sm font-semibold text-muted uppercase tracking-wider">
                Per-Stock Performance
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-muted border-b border-bg-border">
                    {['Symbol','Trades','Wins','Win Rate','P&L'].map(h=>(
                      <th key={h} className="text-left py-2 px-4 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(bt.per_stock_stats).map(([sym,s]) => (
                    <tr key={sym} className="border-b border-bg-border/50 hover:bg-surface transition-colors">
                      <td className="py-2 px-4 font-mono font-bold text-white">{sym}</td>
                      <td className="py-2 px-4 text-muted">{s.trades}</td>
                      <td className="py-2 px-4 text-signal-buy">{s.wins}</td>
                      <td className="py-2 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-bg-border rounded-full overflow-hidden">
                            <div className="h-full bg-signal-buy rounded-full" style={{ width:`${s.win_rate*100}%` }} />
                          </div>
                          <span className="font-mono text-xs">{(s.win_rate*100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className={`py-2 px-4 font-mono font-semibold ${s.total_pnl>=0?'text-signal-buy':'text-signal-sell'}`}>
                        {s.total_pnl>=0?'+':''}₹{s.total_pnl.toLocaleString('en-IN')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};
