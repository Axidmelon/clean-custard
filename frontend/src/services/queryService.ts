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

// Data analysis query functions
const askDataAnalysisQuestion = async (fileId: string, question: string): Promise<QueryResponse> => {
  const queryData: QueryRequest = {
    file_id: fileId,
    question: question,
    data_source: 'csv'
  };
  
  return askQuestion(queryData);
};

const askDatabaseQuestion = async (connectionId: string, question: string): Promise<QueryResponse> => {
  const queryData: QueryRequest = {
    connection_id: connectionId,
    question: question,
    data_source: 'database'
  };
  
  return askQuestion(queryData);
};

// AI routing query function
const askAIQuestion = async (
  fileId: string, 
  question: string, 
  userPreference?: 'sql' | 'python'
): Promise<QueryResponse> => {
  const queryData: QueryRequest = {
    file_id: fileId,
    question: question,
    data_source: 'auto',
    user_preference: userPreference
  };
  
  return askQuestion(queryData);
};

// CSV SQL query function
const askCSVSQLQuestion = async (fileId: string, question: string): Promise<QueryResponse> => {
  const queryData: QueryRequest = {
    file_id: fileId,
    question: question,
    data_source: 'csv_sql'
  };
  
  return askQuestion(queryData);
};

export const queryService = {
  askQuestion,
  askDataAnalysisQuestion,
  askDatabaseQuestion,
  askAIQuestion,        // NEW: AI-powered routing
  askCSVSQLQuestion     // NEW: CSV to SQL converter
};
