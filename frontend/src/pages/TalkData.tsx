import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useConnections } from "@/hooks/useConnections";
import { queryService } from "@/services/queryService";
import { QueryRequest, QueryResponse } from "@/types/api";
import { APP_CONFIG } from "@/lib/constants";

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  code?: string;
  error?: string;
}

export default function TalkData() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>("");
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !selectedConnectionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Make real API call to backend
      const queryRequest: QueryRequest = {
        connection_id: selectedConnectionId,
        question: userMessage.content
      };

      const response: QueryResponse = await queryService.askQuestion(queryRequest);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        code: response.sql_query
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Sorry, I encountered an error while processing your question: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-3rem)]">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground">Talk Data</h1>
        <p className="text-muted-foreground mt-1">
          Ask questions about your data in natural language
        </p>
        
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
                    {connection.name} ({connection.db_type})
                  </SelectItem>
                ))
              ) : (
                <SelectItem value="none" disabled>No connections available</SelectItem>
              )}
            </SelectContent>
          </Select>
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
                
                {message.code && (
                  <div className="mt-3 p-3 bg-muted rounded-md border">
                    <pre className="text-xs font-mono text-muted-foreground overflow-x-auto">
                      <code>{message.code}</code>
                    </pre>
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
      <div className="border-t border-border pt-4 bg-background">
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