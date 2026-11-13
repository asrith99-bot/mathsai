import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
  icon?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, sub, color = 'text-white', icon }) => (
  <div className="bg-bg-card border border-bg-border rounded-xl p-5 flex flex-col gap-2">
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted uppercase tracking-widest">{label}</span>
      {icon && <span className="text-xl">{icon}</span>}
    </div>
    <div className={`text-3xl font-bold font-mono ${color}`}>{value}</div>
    {sub && <div className="text-xs text-muted">{sub}</div>}
  </div>
);
