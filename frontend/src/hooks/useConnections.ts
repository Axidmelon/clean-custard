// Custom hooks for connection management using React Query
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { connectionService } from '@/services/connectionService';
import { 
  Connection, 
  ConnectionWithDetails, 
  CreateConnectionRequest 
} from '@/types/api';
import { APP_CONFIG } from '@/lib/constants';
import { logError } from '@/lib/logger';

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

// Hook to fetch connection status
export function useConnectionStatus(connectionId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.connectionStatus(connectionId),
    queryFn: () => connectionService.getConnectionStatus(connectionId),
    enabled: !!connectionId,
    staleTime: APP_CONFIG.CACHE_TIMES.CONNECTION_STATUS,
    refetchInterval: APP_CONFIG.CACHE_TIMES.CONNECTION_STATUS,
  });
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
