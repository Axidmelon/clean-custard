// Query API service
import { QueryRequest, QueryResponse, ApiError } from '@/types/api';
import { getApiBaseUrl } from '@/lib/constants';

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
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(queryData),
  });
  return handleResponse<QueryResponse>(response);
};

export const queryService = {
  askQuestion
};
