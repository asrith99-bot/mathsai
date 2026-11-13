import React from 'react';
import type { MarketStatus as MS } from '../../types';
import { timeAgo } from '../../utils/formatters';

const colors: Record<string, string> = {
  OPEN:       'bg-signal-buy/15 text-signal-buy border-signal-buy/30',
  PRE_OPEN:   'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  CLOSED:     'bg-muted/15 text-muted border-muted/30',
  POST_CLOSE: 'bg-muted/15 text-muted border-muted/30',
  UNKNOWN:    'bg-muted/15 text-muted border-muted/30',
};

export const MarketStatus: React.FC<{ status: MS; lastUpdate?: string }> = ({ status, lastUpdate }) => (
  <div className={`inline-flex items-center gap-2 border rounded-full px-3 py-1 text-sm font-semibold ${colors[status] ?? colors.UNKNOWN}`}>
    <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
    NSE {status.replace('_', ' ')}
    {lastUpdate && <span className="text-xs font-normal opacity-70">· {timeAgo(lastUpdate)}</span>}
  </div>
);
