/**
 * WebSocket client — disabled in mock/offline mode.
 * No connection attempts, no console errors.
 */
import type { WSMessage } from '../types';

type MessageHandler = (msg: WSMessage) => void;

class WSClient {
  private handlers: Set<MessageHandler> = new Set();

  connect(): void {
    // No-op in offline/mock mode
  }

  disconnect(): void {
    // No-op
  }

  subscribe(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }
}

export const wsClient = new WSClient();
