import React, { useEffect, useState } from 'react';

export const Topbar: React.FC = () => {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const ti = setInterval(() => setNow(new Date()), 1_000);
    return () => clearInterval(ti);
  }, []);

  return (
    <header className="h-12 bg-bg-secondary border-b border-bg-border flex items-center justify-between px-6 shrink-0">
      <div className="text-sm text-muted font-mono">
        {now.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false })} IST
      </div>
      <div className="flex items-center gap-6 text-xs font-mono">
        <span className="text-muted font-semibold">◉ NSE CLOSED</span>
        <span className="text-signal-buy">System Ready</span>
      </div>
    </header>
  );
};
