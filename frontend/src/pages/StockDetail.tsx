import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CandlestickChart } from '../components/charts/CandlestickChart';
import { IndicatorChart }   from '../components/charts/IndicatorChart';
import { SignalCard }       from '../components/signals/SignalCard';
import { DataFreshness }    from '../components/common/DataFreshness';
import { LoadingSpinner }   from '../components/common/LoadingSpinner';
import { formatPrice, formatChange, formatVolume, changeColor } from '../utils/formatters';
import { stocksApi } from '../services/api';
import { MOCK_OHLCV, MOCK_SCANNER_ROWS, MOCK_SIGNALS } from '../utils/mockData';
import type { OHLCVBar, Signal } from '../types';

export const StockDetail: React.FC = () => {
  const { symbol }    = useParams<{ symbol: string }>();
  const navigate      = useNavigate();
  const [detail,     setDetail]     = useState<Record<string,unknown> | null>(null);
  const [ohlcv,      setOhlcv]      = useState<OHLCVBar[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [timeframe,  setTimeframe]  = useState('5m');
  const [usingMock,  setUsingMock]  = useState(false);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);

    Promise.all([
      stocksApi.detail(symbol).catch(() => null),
      stocksApi.ohlcv(symbol, timeframe, 300).catch(() => []),
    ]).then(([d, bars]) => {
      // Use real data if present
      if (d) setDetail(d);
      if ((bars as OHLCVBar[]).length > 0) {
        setOhlcv(bars as OHLCVBar[]);
        setUsingMock(false);
      } else {
        // Fall back to mock
        const mockBars = MOCK_OHLCV[symbol] ?? MOCK_OHLCV['RELIANCE'];
        setOhlcv(mockBars);
        setUsingMock(true);
        if (!d) {
          const mockRow = MOCK_SCANNER_ROWS.find(r => r.symbol === symbol);
          if (mockRow) {
            setDetail({
              stock: { symbol: mockRow.symbol, name: mockRow.name, sector: mockRow.sector, exchange:'NSE', is_active:true },
              tick: { ltp: mockRow.ltp, change_pct: mockRow.change_pct, volume: mockRow.volume, freshness:'DELAYED', open: (mockRow.ltp??0)*0.998, high:(mockRow.ltp??0)*1.012, low:(mockRow.ltp??0)*0.985, prev_close:(mockRow.ltp??0)*1.002 },
              active_signal: MOCK_SIGNALS.find(s => s.symbol === symbol) ?? null,
              recent_signals: MOCK_SIGNALS.filter(s => s.symbol === symbol),
            });
          }
        }
      }
    }).finally(() => setLoading(false));
  }, [symbol, timeframe]);

  if (loading) return <div className="flex justify-center py-24"><LoadingSpinner size={40} /></div>;

  const tick    = detail?.tick     as Record<string,unknown> | null;
  const signals = (detail?.recent_signals as Signal[]) ?? [];
  const stock   = detail?.stock    as Record<string,unknown> ?? { symbol, name: symbol, sector:'NSE' };
  const active  = detail?.active_signal as Signal | null;

  // Build indicator-enriched OHLCV for the indicator chart
  // (Backend returns RSI/MACD in snapshots; here we simulate them from price movement)
  const enriched = ohlcv.map((bar, i) => {
    const closes = ohlcv.slice(Math.max(0,i-13),i+1).map(b=>b.close);
    const rsi = 30 + 40 * (bar.close / (ohlcv[0]?.close ?? bar.close) - 0.9) * 10;
    const macd = i > 25 ? (bar.close - ohlcv[i-25].close) * 0.1 : 0;
    return { ...bar, rsi: Math.min(80, Math.max(20, rsi)), macd, macd_signal: macd * 0.9, macd_hist: macd * 0.1 };
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button onClick={() => navigate(-1)} className="text-muted text-sm mb-2 hover:text-white flex items-center gap-1">
            ← Back
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold font-mono text-white">{symbol}</h1>
          </div>
          <p className="text-muted mt-1">{stock?.name as string} · {stock?.sector as string}</p>
        </div>

        {tick && (
          <div className="text-right">
            <div className="text-3xl font-bold font-mono text-white">{formatPrice(tick.ltp as number)}</div>
            <div className={`text-lg font-semibold ${changeColor(tick.change_pct as number)}`}>
              {formatChange(tick.change_pct as number)}
            </div>
            <DataFreshness freshness={(tick.freshness as 'LIVE'|'DELAYED'|'STALE') ?? 'DELAYED'} timestamp={tick.tick_timestamp as string} />
          </div>
        )}
      </div>

      {/* OHLV stats */}
      {tick && (
        <div className="grid grid-cols-5 gap-4">
          {[
            { l:'Open',       v:formatPrice(tick.open as number) },
            { l:'High',       v:formatPrice(tick.high as number) },
            { l:'Low',        v:formatPrice(tick.low  as number) },
            { l:'Prev Close', v:formatPrice(tick.prev_close as number) },
            { l:'Volume',     v:formatVolume(tick.volume as number) },
          ].map(({ l, v }) => (
            <div key={l} className="bg-bg-card border border-bg-border rounded-xl p-4 text-center">
              <div className="text-xs text-muted mb-1">{l}</div>
              <div className="font-mono font-semibold text-white">{v}</div>
            </div>
          ))}
        </div>
      )}

      {/* Timeframe selector */}
      <div className="flex gap-2">
        {['1m','5m','15m','1d'].map(tf => (
          <button key={tf} onClick={() => setTimeframe(tf)}
            className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-colors
              ${timeframe===tf ? 'bg-accent text-white' : 'bg-bg-card text-muted hover:text-white border border-bg-border'}`}>
            {tf.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Candlestick Chart */}
      {ohlcv.length > 0 ? (
        <CandlestickChart ohlcv={ohlcv} signals={signals} height={420} />
      ) : (
        <div className="bg-bg-card border border-bg-border rounded-xl h-96 flex items-center justify-center text-muted">
          No chart data available
        </div>
      )}

      {/* Indicator panels */}
      {enriched.length > 0 && <IndicatorChart data={enriched as never[]} />}

      {/* Active signal */}
      {active && (
        <div>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Active Signal</h2>
          <SignalCard signal={active} />
        </div>
      )}

      {/* Historical signals */}
      {signals.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Recent Signals</h2>
          <div className="grid gap-3">
            {signals.map(s => <SignalCard key={s.id} signal={s} />)}
          </div>
        </div>
      )}
    </div>
  );
};
