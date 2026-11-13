import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { Signal, DashboardStats } from '../types';
import { signalsApi } from '../services/api';

interface SignalState {
  activeSignals: Signal[];
  recentSignals: Signal[];
  dashboard: DashboardStats | null;
  loading: boolean;
  error: string | null;
}

const initialState: SignalState = {
  activeSignals: [],
  recentSignals: [],
  dashboard: null,
  loading: false,
  error: null,
};

export const fetchDashboard = createAsyncThunk('signals/dashboard', () =>
  signalsApi.dashboard()
);

export const fetchActiveSignals = createAsyncThunk('signals/active', () =>
  signalsApi.active()
);

const signalSlice = createSlice({
  name: 'signals',
  initialState,
  reducers: {
    addSignal(state, action: PayloadAction<Signal>) {
      // Prepend new signal, deduplicate by id
      const existing = state.activeSignals.findIndex(s => s.id === action.payload.id);
      if (existing === -1) {
        state.activeSignals.unshift(action.payload);
        if (state.activeSignals.length > 100) {
          state.activeSignals.pop();
        }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboard.pending,   (s) => { s.loading = true; })
      .addCase(fetchDashboard.fulfilled, (s, a) => {
        s.loading   = false;
        s.dashboard = a.payload;
        s.recentSignals = a.payload.recent_signals;
      })
      .addCase(fetchDashboard.rejected,  (s, a) => {
        s.loading = false;
        s.error   = a.error.message ?? 'Failed';
      })
      .addCase(fetchActiveSignals.fulfilled, (s, a) => {
        s.activeSignals = a.payload;
      });
  },
});

export const { addSignal } = signalSlice.actions;
export default signalSlice.reducer;
