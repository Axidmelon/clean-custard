// Query API service
import { QueryRequest, QueryResponse, ApiError } from '@/types/api';
import { getApiBaseUrl } from '@/lib/constants';
import { logError } from '@/lib/logger';

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

const askQuestion = async (queryData: QueryRequest): Promise<QueryResponse> => {
  const response = await fetch(`${getApiBaseUrl()}/query`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(queryData),
  });
  return handleResponse<QueryResponse>(response);
};

export const queryService = {
  askQuestion
};
