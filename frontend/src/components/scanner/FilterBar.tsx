import React from 'react';
import type { SignalType } from '../../types';

interface FilterBarProps {
  search: string;
  onSearch: (v: string) => void;
  signalFilter: SignalType | 'ALL';
  onSignalFilter: (v: SignalType | 'ALL') => void;
  minConf: number;
  onMinConf: (v: number) => void;
  sortKey: string;
  onSort: (v: string) => void;
  sortDir: 'asc' | 'desc';
}

const FILTER_OPTS: Array<SignalType | 'ALL'> = ['ALL', 'BUY', 'SELL', 'HOLD'];
const SORT_OPTS = [
  { value: 'symbol',      label: 'Symbol' },
  { value: 'ltp',         label: 'LTP'    },
  { value: 'change_pct',  label: 'Change' },
  { value: 'rsi',         label: 'RSI'    },
  { value: 'confidence',  label: 'Conf.'  },
];

export const FilterBar: React.FC<FilterBarProps> = ({
  search, onSearch, signalFilter, onSignalFilter,
  minConf, onMinConf, sortKey, onSort, sortDir,
}) => (
  <div className="flex flex-wrap items-center gap-3 mb-4">
    {/* Search */}
    <input
      type="text"
      placeholder="Search symbol…"
      value={search}
      onChange={e => onSearch(e.target.value.toUpperCase())}
      className="bg-bg-card border border-bg-border rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-muted focus:outline-none focus:border-accent w-36"
    />

    {/* Signal filter */}
    <div className="flex gap-1">
      {FILTER_OPTS.map(opt => (
        <button
          key={opt}
          onClick={() => onSignalFilter(opt)}
          className={`px-2.5 py-1 rounded text-xs font-semibold font-mono transition-colors
            ${signalFilter === opt
              ? opt === 'BUY'  ? 'bg-signal-buy text-black'
              : opt === 'SELL' ? 'bg-signal-sell text-white'
              : opt === 'HOLD' ? 'bg-signal-hold text-black'
              : 'bg-accent text-white'
              : 'bg-bg-card text-muted hover:text-white border border-bg-border'
            }`}
        >
          {opt}
        </button>
      ))}
    </div>

    {/* Min confidence */}
    <div className="flex items-center gap-2 text-xs text-muted">
      <span>Min conf:</span>
      <select
        value={minConf}
        onChange={e => onMinConf(Number(e.target.value))}
        className="bg-bg-card border border-bg-border rounded px-2 py-1 text-white text-xs focus:outline-none"
      >
        {[0, 50, 60, 70, 80].map(v => (
          <option key={v} value={v / 100}>{v === 0 ? 'Any' : `${v}%+`}</option>
        ))}
      </select>
    </div>

    {/* Sort */}
    <div className="flex items-center gap-2 text-xs text-muted">
      <span>Sort:</span>
      <select
        value={sortKey}
        onChange={e => onSort(e.target.value)}
        className="bg-bg-card border border-bg-border rounded px-2 py-1 text-white text-xs focus:outline-none"
      >
        {SORT_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <span className="text-white">{sortDir === 'asc' ? '↑' : '↓'}</span>
    </div>
  </div>
);
