// API types for connection management

export interface CreateConnectionRequest {
  name: string;
  db_type?: string;
  credentials?: Record<string, string>;
}

export interface Connection {
  id: string;
  name: string;
  db_type: string;
  status: string;
  created_at: string;
  api_key?: string; // Only present when creating a new connection
  agent_id?: string; // Unique agent identifier for WebSocket routing
  websocket_url?: string; // WebSocket URL for agent connection
}

export interface ConnectionWithDetails extends Connection {
  connectionDetails: {
    lastSync: string;
    recordCount: number;
    isAgentConnected: boolean;
  };
}

export interface ConnectionStatus {
  connection_id: string;
  agent_connected: boolean;
  status: 'active' | 'disconnected';
}

export interface SchemaRefreshRequest {
  agent_id: string;
}

export interface SchemaRefreshResponse {
  message: string;
  connection_id: string;
  connection_name: string;
  agent_id: string;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Query types
export interface QueryRequest {
  connection_id?: string;
  file_id?: string;
  file_ids?: string[]; // Support for multiple files
  question: string;
  data_source?: 'auto' | 'database' | 'data_analysis_service' | 'csv_to_sql_converter'; // Optional - automatic routing
  user_preference?: 'sql' | 'python';
}

export interface QueryResponse {
  answer: string;
  sql_query: string;
  data: any[];
  columns: string[];
  row_count: number;
  ai_routing?: {
    service_used: string;
    reasoning: string;
    confidence: number;
  };
}
