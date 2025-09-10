import { useEffect, useRef, useState, useCallback } from 'react';
import { logError, logDebug } from '@/lib/logger';

interface WebSocketStatusManager {
  isConnected: boolean;
  subscribe: (connectionId: string, callback: (isConnected: boolean) => void) => () => void;
  reconnect: () => void;
}

class WebSocketStatusManagerImpl implements WebSocketStatusManager {
  private ws: WebSocket | null = null;
  private subscribers: Map<string, Set<(isConnected: boolean) => void>> = new Map();
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private baseReconnectDelay = 1000; // 1 second
  public isConnected = false;

  constructor() {
    this.connect();
  }

  private connect() {
    try {
      // Use the same base URL as the API but with WebSocket protocol
      const wsUrl = this.getWebSocketUrl();
      logDebug('Connecting to WebSocket status updates:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        logDebug('WebSocket status connection opened');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.clearReconnectTimeout();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          logError('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        logDebug('WebSocket status connection closed');
        this.isConnected = false;
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        logError('WebSocket status connection error:', error);
        this.isConnected = false;
      };

    } catch (error) {
      logError('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  private getWebSocketUrl(): string {
    // Convert API base URL to WebSocket URL
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    let wsUrl = apiBaseUrl;
    
    // Convert http to ws, https to wss
    if (wsUrl.startsWith('https://')) {
      wsUrl = wsUrl.replace('https://', 'wss://');
    } else if (wsUrl.startsWith('http://')) {
      wsUrl = wsUrl.replace('http://', 'ws://');
    } else if (wsUrl.startsWith('/')) {
      // Relative URL - use current protocol
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}${wsUrl}`;
    }
    
    return `${wsUrl}/status/ws`;
  }

  private handleMessage(data: any) {
    if (data.type === 'AGENT_STATUS_UPDATE') {
      const { agent_id, agentConnected } = data;
      logDebug(`WebSocket status update received: agent_id=${agent_id}, agentConnected=${agentConnected}`);
      logDebug(`Current subscribers: ${Array.from(this.subscribers.keys()).join(', ')}`);
      
      const callbacks = this.subscribers.get(agent_id);
      if (callbacks) {
        logDebug(`Found ${callbacks.size} callbacks for agent_id=${agent_id}`);
        callbacks.forEach(callback => callback(agentConnected));
      } else {
        logDebug(`No callbacks found for agent_id=${agent_id}`);
      }
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      logError('WebSocket reconnection', new Error('Max WebSocket reconnection attempts reached'));
      return;
    }

    this.clearReconnectTimeout();
    const delay = this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    logDebug(`Scheduling WebSocket reconnection in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private clearReconnectTimeout() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  subscribe(connectionId: string, callback: (isConnected: boolean) => void): () => void {
    logDebug(`Subscribing to status updates for connectionId: ${connectionId}`);
    
    if (!this.subscribers.has(connectionId)) {
      this.subscribers.set(connectionId, new Set());
    }
    
    this.subscribers.get(connectionId)!.add(callback);
    logDebug(`Total subscribers for ${connectionId}: ${this.subscribers.get(connectionId)!.size}`);

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(connectionId);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.subscribers.delete(connectionId);
          logDebug(`Unsubscribed and removed connectionId: ${connectionId}`);
        } else {
          logDebug(`Unsubscribed from connectionId: ${connectionId}, remaining: ${callbacks.size}`);
        }
      }
    };
  }

  reconnect() {
    this.reconnectAttempts = 0;
    this.clearReconnectTimeout();
    if (this.ws) {
      this.ws.close();
    }
    this.connect();
  }

  destroy() {
    this.clearReconnectTimeout();
    if (this.ws) {
      this.ws.close();
    }
    this.subscribers.clear();
  }
}

// Singleton instance
const statusManager = new WebSocketStatusManagerImpl();

// Export the status manager for app-level initialization
export { statusManager };

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    statusManager.destroy();
  });
}

export function useWebSocketStatus(connectionId: string) {
  const [agentConnected, setAgentConnected] = useState<boolean | null>(null);
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(statusManager.isConnected);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    // Subscribe to status updates for this connection
    unsubscribeRef.current = statusManager.subscribe(connectionId, (connected) => {
      setAgentConnected(connected);
    });

    // Track WebSocket connection status
    const checkConnection = () => {
      setIsWebSocketConnected(statusManager.isConnected);
    };
    
    const interval = setInterval(checkConnection, 1000);
    
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
      clearInterval(interval);
    };
  }, [connectionId]);

  const reconnect = useCallback(() => {
    statusManager.reconnect();
  }, []);

  return {
    agentConnected,
    isWebSocketConnected,
    reconnect
  };
}

// Hook for WebSocket connection status without requiring a specific connection ID
export function useWebSocketConnectionStatus() {
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(statusManager.isConnected);

  useEffect(() => {
    // Track WebSocket connection status
    const checkConnection = () => {
      setIsWebSocketConnected(statusManager.isConnected);
    };
    
    const interval = setInterval(checkConnection, 1000);
    
    return () => {
      clearInterval(interval);
    };
  }, []);

  const reconnect = useCallback(() => {
    statusManager.reconnect();
  }, []);

  return {
    isWebSocketConnected,
    reconnect
  };
}
