import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Database, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useConnections } from "@/hooks/useConnections";
import { queryService } from "@/services/queryService";
import { QueryRequest, QueryResponse } from "@/types/api";
// import { APP_CONFIG } from "@/lib/constants";

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  code?: string;
  error?: string;
  error_type?: 'agent_disconnected' | 'query_failed' | 'network_error' | 'unknown';
  data?: any[];
  columns?: string[];
  row_count?: number;
  can_retry?: boolean;
}

export default function TalkData() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>("");
  const [agentStatus, setAgentStatus] = useState<{ [connectionId: string]: boolean }>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Fetch connections
  const { data: connections, isLoading: connectionsLoading, error: connectionsError } = useConnections();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check agent status when connection is selected
  useEffect(() => {
    if (selectedConnectionId && connections) {
      checkAgentStatus(selectedConnectionId);
    }
  }, [selectedConnectionId, connections]);

  const checkAgentStatus = async (connectionId: string) => {
    try {
      // This would need to be implemented in your API
      // For now, we'll update status based on query results
      const response = await fetch(`/api/v1/connections/${connectionId}/status`);
      if (response.ok) {
        const data = await response.json();
        setAgentStatus(prev => ({
          ...prev,
          [connectionId]: data.agent_connected
        }));
      }
    } catch (error) {
      // If status check fails, assume agent is disconnected
      setAgentStatus(prev => ({
        ...prev,
        [connectionId]: false
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent, retryMessageId?: string) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !selectedConnectionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim()
    };

    if (!retryMessageId) {
      setMessages(prev => [...prev, userMessage]);
      setInput("");
    }
    setIsLoading(true);

    try {
      // Make real API call to backend
      const queryRequest: QueryRequest = {
        connection_id: selectedConnectionId,
        question: userMessage.content
      };

      const response: QueryResponse = await queryService.askQuestion(queryRequest);
      
      // Mark agent as connected on successful query
      setAgentStatus(prev => ({
        ...prev,
        [selectedConnectionId]: true
      }));
      
      const assistantMessage: Message = {
        id: retryMessageId || (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        code: response.sql_query,
        data: response.data,
        columns: response.columns,
        row_count: response.row_count
      };
      
      if (retryMessageId) {
        // Update existing error message
        setMessages(prev => prev.map(msg => 
          msg.id === retryMessageId ? assistantMessage : msg
        ));
      } else {
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      const errorType = getErrorType(error);
      const errorContent = getErrorMessage(error, errorType);
      
      // Update agent status based on error type
      if (errorType === 'agent_disconnected') {
        setAgentStatus(prev => ({
          ...prev,
          [selectedConnectionId]: false
        }));
      }
      
      const errorMessage: Message = {
        id: retryMessageId || (Date.now() + 1).toString(),
        type: 'assistant',
        content: errorContent,
        error: error instanceof Error ? error.message : 'Unknown error',
        error_type: errorType,
        can_retry: errorType === 'agent_disconnected' || errorType === 'network_error'
      };
      
      if (retryMessageId) {
        // Update existing message
        setMessages(prev => prev.map(msg => 
          msg.id === retryMessageId ? errorMessage : msg
        ));
      } else {
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getErrorType = (error: any): 'agent_disconnected' | 'query_failed' | 'network_error' | 'unknown' => {
    if (!error) return 'unknown';
    
    const errorMessage = error instanceof Error ? error.message : String(error);
    const errorString = errorMessage.toLowerCase();
    
    if (errorString.includes('503') || errorString.includes('not connected') || errorString.includes('agent')) {
      return 'agent_disconnected';
    }
    if (errorString.includes('network') || errorString.includes('fetch') || errorString.includes('connection')) {
      return 'network_error';
    }
    if (errorString.includes('query') || errorString.includes('sql')) {
      return 'query_failed';
    }
    return 'unknown';
  };

  const getErrorMessage = (error: any, errorType: string): string => {
    const baseMessage = error instanceof Error ? error.message : 'Unknown error';
    
    switch (errorType) {
      case 'agent_disconnected':
        return `The database agent is currently disconnected. Please wait a moment and try again. The agent should reconnect automatically.`;
      case 'network_error':
        return `Network connection issue. Please check your internet connection and try again.`;
      case 'query_failed':
        return `Query execution failed: ${baseMessage}`;
      default:
        return `Sorry, I encountered an error while processing your question: ${baseMessage}`;
    }
  };

  const handleRetry = (messageId: string, originalQuestion: string) => {
    setInput(originalQuestion);
    // Create a synthetic form event for retry
    const syntheticEvent = {
      preventDefault: () => {}
    } as React.FormEvent;
    handleSubmit(syntheticEvent, messageId);
  };

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-3rem)]">
      <div className="mb-6">
        {/* Connection Selection */}
        <div className="mt-4 flex gap-4 items-center">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">Database:</span>
          </div>
          <Select value={selectedConnectionId} onValueChange={setSelectedConnectionId}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select a database connection" />
            </SelectTrigger>
            <SelectContent>
              {connectionsLoading ? (
                <SelectItem value="loading" disabled>Loading connections...</SelectItem>
              ) : connectionsError ? (
                <SelectItem value="error" disabled>Error loading connections</SelectItem>
              ) : connections && connections.length > 0 ? (
                connections.map((connection) => (
                  <SelectItem key={connection.id} value={connection.id}>
                    <div className="flex items-center gap-2">
                      <span>{connection.name} ({connection.db_type})</span>
                      {agentStatus[connection.id] !== undefined && (
                        <div className={`w-2 h-2 rounded-full ${
                          agentStatus[connection.id] ? 'bg-green-500' : 'bg-red-500'
                        }`} title={agentStatus[connection.id] ? 'Agent Connected' : 'Agent Disconnected'} />
                      )}
                    </div>
                  </SelectItem>
                ))
              ) : (
                <SelectItem value="none" disabled>No connections available</SelectItem>
              )}
            </SelectContent>
          </Select>
          
          {/* Agent Status Indicator */}
          {selectedConnectionId && agentStatus[selectedConnectionId] !== undefined && (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-muted">
              <div className={`w-2 h-2 rounded-full ${
                agentStatus[selectedConnectionId] ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span className="text-xs text-muted-foreground">
                {agentStatus[selectedConnectionId] ? 'Agent Online' : 'Agent Offline'}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center space-y-3">
              <div className="w-16 h-16 bg-primary-light rounded-full flex items-center justify-center mx-auto">
                <Bot className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-muted-foreground">
                {!selectedConnectionId ? 'Select a database connection' : 'Start a conversation'}
              </h3>
              <p className="text-sm text-muted-foreground max-w-md">
                {!selectedConnectionId 
                  ? 'Please select a database connection above to start asking questions about your data.'
                  : 'Ask me anything about your data. I can help you generate queries, analyze trends, or explain insights.'
                }
              </p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type === 'assistant' && (
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-primary-foreground" />
              </div>
            )}
            
            <div className={`max-w-2xl ${message.type === 'user' ? 'order-2' : ''}`}>
              <Card className={`p-4 ${message.type === 'user' 
                ? 'bg-primary text-primary-foreground ml-12' 
                : message.error 
                  ? 'bg-destructive/10 border-destructive/20 ml-12'
                  : 'bg-card border-border'
              }`}>
                <p className={`text-sm leading-relaxed ${message.error ? 'text-destructive' : ''}`}>
                  {message.content}
                </p>
                
                {message.error && message.can_retry && (
                  <div className="mt-3 flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Find the original user question for this error
                        const messageIndex = messages.findIndex(m => m.id === message.id);
                        const originalQuestion = messageIndex > 0 ? messages[messageIndex - 1]?.content : '';
                        if (originalQuestion && originalQuestion !== message.content) {
                          handleRetry(message.id, originalQuestion);
                        }
                      }}
                      className="text-xs"
                      disabled={isLoading}
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      Retry Query
                    </Button>
                  </div>
                )}
                
                {message.code && (
                  <div className="mt-3 p-3 bg-muted rounded-md border">
                    <pre className="text-xs font-mono text-muted-foreground overflow-x-auto">
                      <code>{message.code}</code>
                    </pre>
                  </div>
                )}
                
                {message.data && message.data.length > 0 && message.columns && (
                  <div className="mt-3">
                    <div className="text-xs text-muted-foreground mb-2">
                      Results ({message.row_count} rows, showing first 10 columns):
                    </div>
                    <div className="overflow-x-auto border rounded-md">
                      <table className="w-full text-xs">
                        <thead className="bg-muted/50">
                          <tr>
                            {message.columns.slice(0, 10).map((column, index) => (
                              <th key={index} className="px-3 py-2 text-left font-medium border-b">
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {message.data.slice(0, 100).map((row, rowIndex) => (
                            <tr key={rowIndex} className="hover:bg-muted/20">
                              {message.columns?.slice(0, 10).map((_, colIndex) => (
                                <td key={colIndex} className="px-3 py-2 border-b">
                                  {row[colIndex] !== null && row[colIndex] !== undefined 
                                    ? String(row[colIndex]) 
                                    : <span className="text-muted-foreground italic">null</span>
                                  }
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {(message.row_count || 0) > 100 && (
                      <div className="text-xs text-muted-foreground mt-2">
                        Showing first 100 rows of {message.row_count} total results
                      </div>
                    )}
                  </div>
                )}
              </Card>
            </div>

            {message.type === 'user' && (
              <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center flex-shrink-0 order-1">
                <User className="w-4 h-4 text-muted-foreground" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-4">
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-primary-foreground" />
            </div>
            <Card className="p-4 bg-card border-border">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-100"></div>
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-200"></div>
              </div>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="pt-4 bg-background">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={!selectedConnectionId ? "Select a database connection first..." : "Ask a question about your data..."}
            className="flex-1 h-12 px-4 bg-card border-border focus:border-primary focus:ring-primary"
            disabled={isLoading || !selectedConnectionId}
          />
          <Button 
            type="submit" 
            size="lg"
            disabled={!input.trim() || isLoading || !selectedConnectionId}
            className="h-12 px-6 bg-primary hover:bg-primary-hover text-primary-foreground"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}