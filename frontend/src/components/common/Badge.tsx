import React from 'react';
import { signalBg } from '../../utils/formatters';
import type { SignalType } from '../../types';

interface BadgeProps {
  type: SignalType;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClass = { sm: 'text-xs px-1.5 py-0.5', md: 'text-sm px-2 py-1', lg: 'text-base px-3 py-1.5' };

export const SignalBadge: React.FC<BadgeProps> = ({ type, size = 'sm' }) => (
  <span className={`inline-flex items-center font-mono font-semibold rounded ${sizeClass[size]} ${signalBg(type)}`}>
    {type}
  </span>
);
