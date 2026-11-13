import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { MOCK_DASHBOARD } from '../utils/mockData';

export function useSignals() {
  const { activeSignals, dashboard, recentSignals, loading, error } = useSelector(
    (s: RootState) => s.signals
  );

  // Always return mock dashboard — no API call
  return {
    activeSignals,
    dashboard: dashboard ?? MOCK_DASHBOARD,
    recentSignals,
    loading: false,
    error,
  };
}
