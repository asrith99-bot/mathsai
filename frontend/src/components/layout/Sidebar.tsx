import React from 'react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/',           icon: '◉', label: 'Dashboard'         },
  { to: '/scanner',    icon: '⊞', label: 'Live Scanner'      },
  { to: '/signals',    icon: '⚡', label: 'Signal Center'     },
  { to: '/backtest',   icon: '◑', label: 'Backtesting'       },
  { to: '/model',      icon: '◈', label: 'Model Performance' },
];

export const Sidebar: React.FC = () => (
  <aside className="w-56 min-h-screen bg-bg-secondary border-r border-bg-border flex flex-col py-6 px-3 shrink-0">
    {/* Logo */}
    <div className="px-3 mb-8">
      <div className="text-accent font-mono font-bold text-lg">AI⚡STOCKS</div>
      <div className="text-muted text-xs mt-0.5">NSE Signal Platform</div>
    </div>

    {/* Navigation */}
    <nav className="flex flex-col gap-1">
      {navItems.map(({ to, icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
            ${isActive
              ? 'bg-accent/15 text-accent'
              : 'text-muted hover:bg-bg-card hover:text-white'}`
          }
        >
          <span className="text-base">{icon}</span>
          {label}
        </NavLink>
      ))}
    </nav>

    {/* Bottom disclaimer */}
    <div className="mt-auto px-3 pt-6">
      <p className="text-xs text-muted leading-relaxed">
        Signals are for informational purposes only. Not financial advice. Past performance does not guarantee future results.
      </p>
    </div>
  </aside>
);
