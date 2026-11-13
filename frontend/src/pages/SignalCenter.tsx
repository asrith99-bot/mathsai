import React, { useEffect, useState } from 'react';
import { SignalCard } from '../components/signals/SignalCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { signalsApi } from '../services/api';
import { MOCK_SIGNALS } from '../utils/mockData';
import type { Signal, SignalType } from '../types';

export const SignalCenter: React.FC = () => {
  const [signals,  setSignals]  = useState<Signal[]>([]);
  const [filter,   setFilter]   = useState<SignalType | 'ALL'>('ALL');
  const [loading,  setLoading]  = useState(true);
  const [page,     setPage]     = useState(0);
  const [usingMock, setUsingMock] = useState(false);

  const PAGE_SIZE = 20;

  useEffect(() => {
    setLoading(true);
    signalsApi.history({
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      ...(filter !== 'ALL' ? { signal_type: filter } : {}),
    })
      .then(data => {
        if (data.length === 0 && page === 0) {
          // Fall back to mock
          const mock = filter === 'ALL' ? MOCK_SIGNALS
            : MOCK_SIGNALS.filter(s => s.signal_type === filter);
          setSignals(mock);
          setUsingMock(true);
        } else {
          setSignals(data);
          setUsingMock(false);
        }
      })
      .catch(() => {
        setSignals(MOCK_SIGNALS);
        setUsingMock(true);
      })
      .finally(() => setLoading(false));
  }, [filter, page]);

  const filters: Array<SignalType | 'ALL'> = ['ALL', 'BUY', 'SELL', 'HOLD'];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">AI Signal Center</h1>
        <p className="text-muted text-sm mt-1">
          Trading signals with entry, stop-loss, target and confidence
        </p>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2">
        {filters.map(f => (
          <button key={f} onClick={() => { setFilter(f); setPage(0); }}
            className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors
              ${filter === f
                ? f === 'BUY'  ? 'bg-signal-buy text-black'
                : f === 'SELL' ? 'bg-signal-sell text-white'
                : f === 'HOLD' ? 'bg-signal-hold text-black'
                : 'bg-accent text-white'
                : 'bg-bg-card text-muted hover:text-white border border-bg-border'}`}>
            {f}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-24"><LoadingSpinner size={40} /></div>
      ) : signals.length === 0 ? (
        <div className="text-muted text-center py-24">No signals found.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {signals.map(s => <SignalCard key={s.id} signal={s} />)}
        </div>
      )}

      <div className="flex justify-center gap-3">
        <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
          className="px-4 py-1.5 bg-bg-card border border-bg-border text-sm rounded disabled:opacity-30">
          ← Prev
        </button>
        <span className="text-muted text-sm py-1.5">Page {page + 1}</span>
        <button onClick={() => setPage(p => p + 1)} disabled={signals.length < PAGE_SIZE || usingMock}
          className="px-4 py-1.5 bg-bg-card border border-bg-border text-sm rounded disabled:opacity-30">
          Next →
        </button>
      </div>
    </div>
  );
};
