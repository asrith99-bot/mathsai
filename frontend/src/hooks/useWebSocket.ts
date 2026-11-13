/**
 * Hook that subscribes to the WebSocket and dispatches
 * Redux actions for tick_update and signal_update messages.
 */
import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import type { AppDispatch } from '../store/store';
import { wsClient } from '../services/wsClient';
import { updateTick } from '../store/stockSlice';
import { addSignal }  from '../store/signalSlice';
import type { WSMessage, LiveTick, Signal } from '../types';

export function useWebSocket() {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    wsClient.connect();

    const unsubscribe = wsClient.subscribe((msg: WSMessage) => {
      switch (msg.type) {
        case 'tick_update':
          dispatch(updateTick(msg.payload as unknown as LiveTick));
          break;
        case 'signal_update':
          dispatch(addSignal(msg.payload as unknown as Signal));
          break;
        default:
          break;
      }
    });

    return () => {
      unsubscribe();
      // Don't disconnect on unmount — keep single connection alive
    };
  }, [dispatch]);
}
