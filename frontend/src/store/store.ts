import { configureStore } from '@reduxjs/toolkit';
import stockReducer  from './stockSlice';
import signalReducer from './signalSlice';

export const store = configureStore({
  reducer: {
    stocks:  stockReducer,
    signals: signalReducer,
  },
});

export type RootState   = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
