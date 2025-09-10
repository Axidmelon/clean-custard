// Custom hooks for connection management using React Query
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { connectionService } from '@/services/connectionService';
import { 
  Connection, 
  CreateConnectionRequest 
} from '@/types/api';
import { APP_CONFIG } from '@/lib/constants';
import { logError, logDebug } from '@/lib/logger';
import { useWebSocketStatus } from './useWebSocketStatus';

// Query keys for React Query
export const QUERY_KEYS = {
  connections: ['connections'] as const,
  connectionsWithDetails: ['connections', 'with-details'] as const,
  connection: (id: string) => ['connections', id] as const,
  connectionStatus: (id: string) => ['connections', id, 'status'] as const,
};

// Hook to fetch all connections
export function useConnections() {
  return useQuery({
    queryKey: QUERY_KEYS.connections,
    queryFn: connectionService.getConnections,
    staleTime: APP_CONFIG.CACHE_TIMES.CONNECTIONS,
    refetchOnWindowFocus: false,
  });
}

// Hook to fetch connections with detailed information (for "Your Connections" section)
export function useConnectionsWithDetails() {
  return useQuery({
    queryKey: QUERY_KEYS.connectionsWithDetails,
    queryFn: connectionService.getConnectionsWithDetails,
    staleTime: APP_CONFIG.CACHE_TIMES.CONNECTION_DETAILS,
    refetchOnWindowFocus: false,
  });
}

// Hook to fetch a specific connection
export function useConnection(connectionId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.connection(connectionId),
    queryFn: () => connectionService.getConnection(connectionId),
    enabled: !!connectionId,
    staleTime: APP_CONFIG.CACHE_TIMES.CONNECTIONS,
  });
}

// Hook to fetch connection status with WebSocket real-time updates and polling fallback
export function useConnectionStatus(connectionId: string) {
  const [useWebSocket, setUseWebSocket] = useState(true);
  
  // Get the connection to extract agent_id
  const { data: connection } = useQuery({
    queryKey: QUERY_KEYS.connection(connectionId),
    queryFn: () => connectionService.getConnection(connectionId),
    enabled: !!connectionId,
    staleTime: APP_CONFIG.CACHE_TIMES.CONNECTIONS,
  });
  
  // WebSocket status hook - use agent_id if available, otherwise fall back to connectionId
  const agentId = connection?.agent_id || connectionId;
  logDebug(`useConnectionStatus: connectionId=${connectionId}, agentId=${agentId}, connection=${connection?.name}`);
  const { agentConnected: wsAgentConnected, isWebSocketConnected, reconnect } = useWebSocketStatus(agentId);
  
  // Polling fallback query
  const pollingQuery = useQuery({
    queryKey: QUERY_KEYS.connectionStatus(connectionId),
    queryFn: () => connectionService.getConnectionStatus(connectionId),
    enabled: !!connectionId && !useWebSocket,
    staleTime: 2 * 60 * 1000, // 2 minutes when using polling
    refetchInterval: 2 * 60 * 1000, // Poll every 2 minutes as fallback
  });

  // Switch to polling if WebSocket fails
  useEffect(() => {
    if (!isWebSocketConnected && useWebSocket) {
      logDebug('WebSocket disconnected, switching to polling fallback');
      setUseWebSocket(false);
    }
  }, [isWebSocketConnected, useWebSocket]);

  // Switch back to WebSocket if it reconnects
  useEffect(() => {
    if (isWebSocketConnected && !useWebSocket) {
      logDebug('WebSocket reconnected, switching back to real-time updates');
      setUseWebSocket(true);
    }
  }, [isWebSocketConnected, useWebSocket]);

  // Determine the current status
  const agentConnected = useWebSocket ? wsAgentConnected : pollingQuery.data?.agent_connected;
  const isLoading = useWebSocket ? wsAgentConnected === null : pollingQuery.isLoading;
  const error = useWebSocket ? null : pollingQuery.error;

  return {
    data: {
      agent_connected: agentConnected,
      status: agentConnected ? 'active' : 'disconnected',
      connection_id: connectionId,
    },
    isLoading,
    error,
    isWebSocketConnected,
    reconnect,
    refetch: pollingQuery.refetch,
  };
}

// Hook to create a new connection
export function useCreateConnection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: connectionService.createConnection,
    onSuccess: (newConnection) => {
      // Invalidate and refetch connections
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connections });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connectionsWithDetails });
      
      // Add the new connection to the cache
      queryClient.setQueryData(
        QUERY_KEYS.connection(newConnection.id),
        newConnection
      );
    },
    onError: (error) => {
      logError('Failed to create connection', error);
    },
  });
}

// Hook to delete a connection
export function useDeleteConnection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: connectionService.deleteConnection,
    onSuccess: (_, connectionId) => {
      // Remove the connection from cache
      queryClient.removeQueries({ queryKey: QUERY_KEYS.connection(connectionId) });
      queryClient.removeQueries({ queryKey: QUERY_KEYS.connectionStatus(connectionId) });
      
      // Invalidate connections list
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connections });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connectionsWithDetails });
    },
    onError: (error) => {
      logError('Failed to delete connection', error);
    },
  });
}

// Hook to refresh schema
export function useRefreshSchema() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ connectionId, agentId }: { connectionId: string; agentId: string }) =>
      connectionService.refreshSchema(connectionId, agentId),
    onSuccess: (_, { connectionId }) => {
      // Refresh the connection and its status
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connection(connectionId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connectionStatus(connectionId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connectionsWithDetails });
    },
    onError: (error) => {
      logError('Failed to refresh schema', error);
    },
  });
}

// Hook to manually refresh all connections data
export function useRefreshConnections() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connections });
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connectionsWithDetails });
  };
}
