import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { LiveTick, ScannerRow } from '../types';
import { stocksApi } from '../services/api';

interface StockState {
  scannerRows: ScannerRow[];
  ticks: Record<string, LiveTick>;
  loading: boolean;
  error: string | null;
}

const initialState: StockState = {
  scannerRows: [],
  ticks: {},
  loading: false,
  error: null,
};

export const fetchScanner = createAsyncThunk('stocks/fetchScanner', async () => {
  const data = await stocksApi.scanner();
  return data ?? []; // null means backend unreachable — return empty, pages use mock
});

const stockSlice = createSlice({
  name: 'stocks',
  initialState,
  reducers: {
    updateTick(state, action: PayloadAction<LiveTick>) {
      const tick = action.payload;
      state.ticks[tick.symbol] = tick;
      // Update the matching scanner row
      const row = state.scannerRows.find(r => r.symbol === tick.symbol);
      if (row) {
        row.ltp        = tick.ltp;
        row.change_pct = tick.change_pct;
        row.volume     = tick.volume;
        row.freshness  = tick.freshness;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchScanner.pending,   (s) => { s.loading = true; s.error = null; })
      .addCase(fetchScanner.fulfilled, (s, a) => { s.loading = false; s.scannerRows = a.payload; })
      .addCase(fetchScanner.rejected,  (s, a) => { s.loading = false; s.error = a.error.message ?? 'Failed'; });
  },
});

export const { updateTick } = stockSlice.actions;
export default stockSlice.reducer;
