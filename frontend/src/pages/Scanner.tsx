import React, { useMemo, useState } from 'react';
import { useStockData } from '../hooks/useStockData';
import { StockTable }   from '../components/scanner/StockTable';
import { FilterBar }    from '../components/scanner/FilterBar';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { MOCK_SCANNER_ROWS } from '../utils/mockData';
import type { SignalType, ScannerRow } from '../types';

export const Scanner: React.FC = () => {
  const { scannerRows, loading } = useStockData();

  const [search,       setSearch]       = useState('');
  const [signalFilter, setSignalFilter] = useState<SignalType | 'ALL'>('ALL');
  const [minConf,      setMinConf]      = useState(0);
  const [sortKey,      setSortKey]      = useState<string>('symbol');
  const [sortDir,      setSortDir]      = useState<'asc' | 'desc'>('asc');

  // Use real data if loaded, otherwise mock
  const baseRows: ScannerRow[] = scannerRows.length > 0 ? scannerRows : MOCK_SCANNER_ROWS;

  const handleSort = (key: string) => {
    if (key === sortKey) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const filtered = useMemo(() => {
    let rows = [...baseRows];
    if (search)              rows = rows.filter(r => r.symbol.includes(search.toUpperCase()));
    if (signalFilter !== 'ALL') rows = rows.filter(r => r.signal_type === signalFilter);
    if (minConf > 0)         rows = rows.filter(r => (r.confidence ?? 0) >= minConf);

    rows.sort((a, b) => {
      const av = (a as Record<string,unknown>)[sortKey] ?? '';
      const bv = (b as Record<string,unknown>)[sortKey] ?? '';
      if (typeof av === 'number' && typeof bv === 'number')
        return sortDir === 'asc' ? av - bv : bv - av;
      const as = String(av), bs = String(bv);
      if (as < bs) return sortDir === 'asc' ? -1 : 1;
      if (as > bs) return sortDir === 'asc' ?  1 : -1;
      return 0;
    });
    return rows;
  }, [baseRows, search, signalFilter, minConf, sortKey, sortDir]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Live Stock Scanner</h1>
          <p className="text-muted text-sm mt-1">
            {baseRows.length} stocks monitored · {filtered.length} shown
          </p>
        </div>
        {loading && <LoadingSpinner />}
      </div>

      <FilterBar
        search={search}        onSearch={setSearch}
        signalFilter={signalFilter} onSignalFilter={setSignalFilter}
        minConf={minConf}      onMinConf={setMinConf}
        sortKey={sortKey}      onSort={handleSort}
        sortDir={sortDir}
      />

      <div className="bg-bg-card border border-bg-border rounded-xl overflow-hidden">
        <StockTable rows={filtered} />
      </div>
    </div>
  );
};
