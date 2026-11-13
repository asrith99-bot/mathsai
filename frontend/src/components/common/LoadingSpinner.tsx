import React from 'react';

export const LoadingSpinner: React.FC<{ size?: number }> = ({ size = 24 }) => (
  <div
    className="inline-block border-2 border-accent border-t-transparent rounded-full animate-spin"
    style={{ width: size, height: size }}
    role="status"
    aria-label="Loading"
  />
);
