import React from 'react';
import { freshnessColor, freshnessLabel, timeAgo } from '../../utils/formatters';
import type { Freshness } from '../../types';

interface Props {
  freshness: Freshness;
  timestamp?: string;
  showTime?: boolean;
}

export const DataFreshness: React.FC<Props> = ({ freshness, timestamp, showTime = true }) => (
  <span className={`inline-flex items-center gap-1 text-xs font-mono ${freshnessColor(freshness)}`}>
    {freshnessLabel(freshness)}
    {showTime && timestamp && (
      <span className="text-muted">({timeAgo(timestamp)})</span>
    )}
  </span>
);
