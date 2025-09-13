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

// Automatic CSV query function (AI routing decides the best service)
const askCSVQuestion = async (
  fileId: string, 
  question: string, 
  userPreference?: 'sql' | 'python'
): Promise<QueryResponse> => {
  const queryData: QueryRequest = {
    file_id: fileId,
    question: question,
    user_preference: userPreference
    // No data_source needed - AI routing is automatic
  };
  
  return askQuestion(queryData);
};

// Database query function (no AI routing)
const askDatabaseQuestion = async (connectionId: string, question: string): Promise<QueryResponse> => {
  const queryData: QueryRequest = {
    connection_id: connectionId,
    question: question
    // No data_source needed - goes directly to database
  };
  
  return askQuestion(queryData);
};

export const queryService = {
  askQuestion,
  askCSVQuestion,       // Automatic AI routing for CSV data
  askDatabaseQuestion   // Direct database queries (no AI routing)
};
