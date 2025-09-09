// Connection API service
import { 
  Connection, 
  ConnectionWithDetails, 
  CreateConnectionRequest, 
  ConnectionStatus, 
  SchemaRefreshRequest, 
  SchemaRefreshResponse,
  ApiError
} from '@/types/api';
import { getApiBaseUrl } from '@/lib/constants';

// Helper function to get authentication headers
const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('access_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `HTTP error! status: ${response.status}`,
      status_code: response.status
    }));
    throw new Error(error.detail || 'An error occurred');
  }
  return response.json();
};

const getConnections = async (): Promise<Connection[]> => {
  const response = await fetch(`${getApiBaseUrl()}/connections`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse<Connection[]>(response);
};

const getConnection = async (connectionId: string): Promise<Connection> => {
  const response = await fetch(`${getApiBaseUrl()}/connections/${connectionId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse<Connection>(response);
};

const createConnection = async (connectionData: CreateConnectionRequest): Promise<Connection> => {
  const response = await fetch(`${getApiBaseUrl()}/connections`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(connectionData),
  });
  return handleResponse<Connection>(response);
};

const deleteConnection = async (connectionId: string): Promise<void> => {
  const response = await fetch(`${getApiBaseUrl()}/connections/${connectionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `HTTP error! status: ${response.status}`,
      status_code: response.status
    }));
    throw new Error(error.detail || 'Failed to delete connection');
  }
};

const getConnectionStatus = async (connectionId: string): Promise<ConnectionStatus> => {
  const response = await fetch(`${getApiBaseUrl()}/connections/${connectionId}/status`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse<ConnectionStatus>(response);
};

const refreshSchema = async (connectionId: string, agentId: string): Promise<SchemaRefreshResponse> => {
  const response = await fetch(`${getApiBaseUrl()}/connections/${connectionId}/refresh-schema`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ agent_id: agentId } as SchemaRefreshRequest),
  });
  return handleResponse<SchemaRefreshResponse>(response);
};

const getConnectionWithDetails = async (connectionId: string): Promise<ConnectionWithDetails> => {
  const [connection, status] = await Promise.all([
    getConnection(connectionId),
    getConnectionStatus(connectionId)
  ]);

  // Mock additional details since they're not in the current backend schema
  // In a real implementation, these would come from the backend
  const connectionDetails = {
    lastSync: connection.created_at, // Use created_at since we don't have updated_at
    recordCount: 0, // TODO: Get actual record count from backend
    isAgentConnected: status.agent_connected
  };

  return {
    ...connection,
    connectionDetails
  };
};

const getConnectionsWithDetails = async (): Promise<Connection[]> => {
  // For now, just return the simple connections list
  // This matches what the backend now returns
  return getConnections();
};

export const connectionService = {
  getConnections,
  getConnection,
  createConnection,
  deleteConnection,
  getConnectionStatus,
  refreshSchema,
  getConnectionWithDetails,
  getConnectionsWithDetails
};
