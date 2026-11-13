import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../store/store';
import { fetchScanner } from '../store/stockSlice';

export function useStockData() {
  const dispatch = useDispatch<AppDispatch>();
  const { scannerRows, ticks, loading, error } = useSelector((s: RootState) => s.stocks);

  useEffect(() => {
    // Try fetching — pages fall back to mock if this returns null/empty
    dispatch(fetchScanner());
  }, [dispatch]);

  return { scannerRows, ticks, loading, error };
}
