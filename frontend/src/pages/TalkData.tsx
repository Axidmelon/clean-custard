import { useState, useRef, useEffect } from "react";
import { Bot, User, Database, RefreshCw, Upload, FileText, X, FileSpreadsheet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Callout, CalloutTitle, CalloutDescription } from "@/components/ui/callout";
import { useConnections } from "@/hooks/useConnections";
import { queryService } from "@/services/queryService";
import { QueryRequest, QueryResponse } from "@/types/api";
import { useFileUpload } from "@/contexts/FileUploadContext";
import { signedUrlService } from "@/services/signedUrlService";
import { SimpleChatEditor } from "@/components/blocknote/SimpleChatEditor";
import { SimpleDataTable } from "@/components/blocknote/SimpleDataTable";
import { RichTextDisplay } from "@/components/ui/RichTextDisplay";
// import { APP_CONFIG } from "@/lib/constants";

// Constants for CSV loading optimization
const CSV_LOAD_TIMEOUT = 30000; // 30 seconds
const MAX_PREVIEW_ROWS = 50; // Show only first 50 rows in preview
const MAX_FILE_SIZE_MB = 5; // 5MB limit for preview
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

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

interface CsvData {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

interface CsvLoadProgress {
  stage: 'fetching_url' | 'downloading' | 'parsing' | 'rendering' | 'complete' | 'error';
  progress: number; // 0-100
  message: string;
  error?: string;
}

export default function TalkData() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>("");
  const [selectedCsvFileId, setSelectedCsvFileId] = useState<string>("");
  const [csvData, setCsvData] = useState<CsvData | null>(null);
  const [isLoadingCsv, setIsLoadingCsv] = useState(false);
  const [csvLoadProgress, setCsvLoadProgress] = useState<CsvLoadProgress>({
    stage: 'complete',
    progress: 0,
    message: ''
  });
  const [csvLoadTimeout, setCsvLoadTimeout] = useState<NodeJS.Timeout | null>(null);
  const [agentStatus, setAgentStatus] = useState<{ [connectionId: string]: boolean }>({});
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Fetch connections
  const { data: connections, isLoading: connectionsLoading, error: connectionsError } = useConnections();
  
  // Use shared file upload context
  const { addUploadedFile, uploadedFiles } = useFileUpload();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load CSV data when a CSV file is selected
  useEffect(() => {
    if (selectedCsvFileId) {
      loadCsvData(selectedCsvFileId);
    } else {
      setCsvData(null);
    }
  }, [selectedCsvFileId, uploadedFiles]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (csvLoadTimeout) {
        clearTimeout(csvLoadTimeout);
      }
    };
  }, [csvLoadTimeout]);

  const parseCsvContent = (content: string, maxRows: number = MAX_PREVIEW_ROWS): CsvData => {
    try {
      console.log('📊 Starting CSV parsing...', { contentLength: content.length, maxRows });
      
      const lines = content.split('\n').filter(line => line.trim() !== '');
      if (lines.length === 0) {
        console.log('❌ No lines found in CSV content');
        return { headers: [], rows: [], totalRows: 0 };
      }

      console.log('📄 CSV lines found:', lines.length);

      // Robust CSV parsing function
      const parseCsvLine = (line: string): string[] => {
        const result: string[] = [];
        let current = '';
        let inQuotes = false;
        let i = 0;
        
        while (i < line.length) {
          const char = line[i];
          const nextChar = line[i + 1];
          
          if (char === '"') {
            if (inQuotes && nextChar === '"') {
              // Escaped quote
              current += '"';
              i += 2;
            } else {
              // Toggle quote state
              inQuotes = !inQuotes;
              i++;
            }
          } else if (char === ',' && !inQuotes) {
            // Field separator
            result.push(current.trim());
            current = '';
            i++;
          } else {
            current += char;
            i++;
          }
        }
        
        // Add the last field
        result.push(current.trim());
        return result;
      };

      // Parse headers
      const headers = parseCsvLine(lines[0]);
      console.log('📋 Headers parsed:', { count: headers.length, headers: headers.slice(0, 5) });
      
      // Validate headers (should be reasonable number)
      if (headers.length > 1000) {
        console.error('❌ Too many columns detected:', headers.length, '- CSV parsing may have failed');
        return { headers: [], rows: [], totalRows: 0 };
      }
      
      // For large files, only parse the first maxRows rows for preview
      const totalRows = lines.length - 1; // Subtract header row
      const rowsToParse = Math.min(maxRows, totalRows);
      
      console.log('📊 Parsing rows:', { totalRows, rowsToParse });
      
      const rows: string[][] = [];
      for (let i = 1; i <= Math.min(rowsToParse + 1, lines.length - 1); i++) {
        try {
          const parsedRow = parseCsvLine(lines[i]);
          // Ensure row has same number of columns as headers
          if (parsedRow.length === headers.length) {
            rows.push(parsedRow);
          } else {
            console.warn(`⚠️ Row ${i} has ${parsedRow.length} columns, expected ${headers.length}`);
            // Pad or truncate row to match headers
            const paddedRow = new Array(headers.length).fill('');
            for (let j = 0; j < Math.min(parsedRow.length, headers.length); j++) {
              paddedRow[j] = parsedRow[j];
            }
            rows.push(paddedRow);
          }
        } catch (error) {
          console.warn(`⚠️ Error parsing row ${i}:`, error);
          // Add empty row to maintain structure
          rows.push(new Array(headers.length).fill(''));
        }
      }

      const result = {
        headers,
        rows,
        totalRows: totalRows
      };
      
      console.log('✅ CSV parsing complete:', {
        headers: result.headers.length,
        rows: result.rows.length,
        totalRows: result.totalRows,
        sampleRow: result.rows[0]?.slice(0, 3)
      });

      return result;
      
    } catch (error) {
      console.error('❌ CSV parsing failed:', error);
      return { headers: [], rows: [], totalRows: 0 };
    }
  };

  const loadCsvData = async (fileId: string) => {
    setIsLoadingCsv(true);
    setCsvData(null);
    
    // Clear any existing timeout
    if (csvLoadTimeout) {
      clearTimeout(csvLoadTimeout);
    }
    
    // Set up timeout
    const timeoutId = setTimeout(() => {
      console.error('CSV loading timeout after 30 seconds');
      setCsvLoadProgress({
        stage: 'error',
        progress: 0,
        message: 'Loading timeout',
        error: `File is too large or there are network issues. Please try a smaller file (under ${MAX_FILE_SIZE_MB}MB) or check your internet connection.`
      });
      setIsLoadingCsv(false);
    }, CSV_LOAD_TIMEOUT);
    
    setCsvLoadTimeout(timeoutId);
    
    try {
      const selectedFile = uploadedFiles.find(file => file.id === fileId);
      
      if (!selectedFile) {
        throw new Error('File not found');
      }
      
      // Check file size for preview
      if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
        const fileSizeMB = (selectedFile.size / (1024 * 1024)).toFixed(1);
        throw new Error(`File too large for preview (${fileSizeMB}MB). Maximum size for preview is ${MAX_FILE_SIZE_MB}MB. Please use a smaller file or contact support for large file processing.`);
      }
      
      if (selectedFile && selectedFile.file) {
        // Parse the local file (for files still in progress)
        console.log('📁 Loading CSV from local file:', selectedFile.name, `(${(selectedFile.size / 1024).toFixed(1)} KB)`);
        setCsvLoadProgress({
          stage: 'parsing',
          progress: 50,
          message: 'Parsing local file...'
        });
        
        const startTime = performance.now();
        const content = await selectedFile.file.text();
        const parseStartTime = performance.now();
        const parsedData = parseCsvContent(content);
        const parseEndTime = performance.now();
        
        console.log('✅ Local CSV parsing complete:', {
          fileName: selectedFile.name,
          fileSize: `${(selectedFile.size / 1024).toFixed(1)} KB`,
          totalRows: parsedData.totalRows,
          previewRows: parsedData.rows.length,
          columns: parsedData.headers.length,
          readTime: `${(parseStartTime - startTime).toFixed(0)}ms`,
          parseTime: `${(parseEndTime - parseStartTime).toFixed(0)}ms`,
          totalTime: `${(parseEndTime - startTime).toFixed(0)}ms`
        });
        
        setCsvData(parsedData);
        
        setCsvLoadProgress({
          stage: 'complete',
          progress: 100,
          message: 'CSV loaded successfully'
        });
      } else if (selectedFile && selectedFile.status === 'completed') {
        // For completed uploads, use signed URL for direct Cloudinary access
        console.log('☁️ Loading CSV via signed URL:', selectedFile.name, `(${(selectedFile.size / 1024).toFixed(1)} KB)`);
        
        setCsvLoadProgress({
          stage: 'fetching_url',
          progress: 10,
          message: 'Getting secure access URL...'
        });
        
        try {
          const urlStartTime = performance.now();
          // Get signed URL from backend (30 minutes expiration for enhanced security)
          const signedUrlResponse = await signedUrlService.getSignedUrl(fileId, 0.5);
          const urlEndTime = performance.now();
          
          console.log('🔑 Got signed URL:', {
            fileName: selectedFile.name,
            urlGenerationTime: `${(urlEndTime - urlStartTime).toFixed(0)}ms`,
            expirationTime: signedUrlResponse.expires_at
          });
          
          setCsvLoadProgress({
            stage: 'downloading',
            progress: 30,
            message: 'Downloading file from cloud...'
          });
          
          const downloadStartTime = performance.now();
          // Fetch content directly from Cloudinary using signed URL
          const content = await signedUrlService.fetchFileContentFromSignedUrl(signedUrlResponse.signed_url);
          const downloadEndTime = performance.now();
          
          console.log('📥 Downloaded from Cloudinary:', {
            fileName: selectedFile.name,
            downloadTime: `${(downloadEndTime - downloadStartTime).toFixed(0)}ms`,
            contentSize: `${(content.length / 1024).toFixed(1)} KB`
          });
          
          setCsvLoadProgress({
            stage: 'parsing',
            progress: 70,
            message: 'Processing CSV data...'
          });
          
          const parseStartTime = performance.now();
          const parsedData = parseCsvContent(content);
          const parseEndTime = performance.now();
          
          console.log('✅ CSV parsing complete:', {
            fileName: selectedFile.name,
            totalRows: parsedData.totalRows,
            previewRows: parsedData.rows.length,
            columns: parsedData.headers.length,
            parseTime: `${(parseEndTime - parseStartTime).toFixed(0)}ms`,
            totalTime: `${(parseEndTime - urlStartTime).toFixed(0)}ms`
          });
          
          setCsvLoadProgress({
            stage: 'rendering',
            progress: 90,
            message: 'Rendering preview...'
          });
          
          setCsvData(parsedData);
          
          setCsvLoadProgress({
            stage: 'complete',
            progress: 100,
            message: 'CSV preview ready'
          });
          
        } catch (signedUrlError) {
          console.warn('⚠️ Signed URL method failed, falling back to backend proxy:', {
            fileName: selectedFile.name,
            error: signedUrlError instanceof Error ? signedUrlError.message : 'Unknown error',
            fallbackMethod: 'backend_proxy'
          });
          
          setCsvLoadProgress({
            stage: 'downloading',
            progress: 30,
            message: 'Using backup method...'
          });
          
          const fallbackStartTime = performance.now();
          // Fallback to backend proxy method
          const response = await fetch(`/api/v1/files/content/${fileId}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            },
          });
          
          if (response.ok) {
            const content = await response.text();
            const parseStartTime = performance.now();
            const parsedData = parseCsvContent(content);
            const parseEndTime = performance.now();
            
            console.log('✅ Backend fallback successful:', {
              fileName: selectedFile.name,
              downloadTime: `${(parseStartTime - fallbackStartTime).toFixed(0)}ms`,
              parseTime: `${(parseEndTime - parseStartTime).toFixed(0)}ms`,
              totalTime: `${(parseEndTime - fallbackStartTime).toFixed(0)}ms`,
              totalRows: parsedData.totalRows,
              previewRows: parsedData.rows.length,
              columns: parsedData.headers.length
            });
            
            setCsvData(parsedData);
            
            setCsvLoadProgress({
              stage: 'complete',
              progress: 100,
              message: 'CSV preview ready (via backup)'
            });
          } else {
            throw new Error(`Failed to load CSV content from server: ${response.status} ${response.statusText}`);
          }
        }
      } else {
        throw new Error('File not found or upload not completed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      const selectedFile = uploadedFiles.find(file => file.id === fileId);
      
      console.error('❌ CSV loading failed:', {
        fileId,
        fileName: selectedFile?.name || 'Unknown',
        fileSize: selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : 'Unknown',
        error: errorMessage,
        errorType: error instanceof Error ? error.constructor.name : 'Unknown',
        timestamp: new Date().toISOString()
      });
      
      setCsvLoadProgress({
        stage: 'error',
        progress: 0,
        message: 'Failed to load CSV',
        error: errorMessage
      });
      
      setCsvData(null);
    } finally {
      // Clear timeout
      if (csvLoadTimeout) {
        clearTimeout(csvLoadTimeout);
        setCsvLoadTimeout(null);
      }
      setIsLoadingCsv(false);
    }
  };

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

  const handleSubmit = async (content: string, retryMessageId?: string) => {
    if (!content.trim() || isLoading || (!selectedConnectionId && !selectedCsvFileId)) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: content.trim()
    };

    if (!retryMessageId) {
      setMessages(prev => [...prev, userMessage]);
    }
    setIsLoading(true);

    try {
      let response: QueryResponse;
      
      // Determine data source and make appropriate API call
      if (selectedCsvFileId) {
        // Data analysis query
        response = await queryService.askDataAnalysisQuestion(selectedCsvFileId, userMessage.content);
      } else if (selectedConnectionId) {
        // Database query
        response = await queryService.askDatabaseQuestion(selectedConnectionId, userMessage.content);
        
        // Mark agent as connected on successful query
        setAgentStatus(prev => ({
          ...prev,
          [selectedConnectionId]: true
        }));
      } else {
        throw new Error("No data source selected");
      }
      
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
    handleSubmit(originalQuestion, messageId);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
      setUploadedFile(file);
      setIsUploadDialogOpen(false);
      // Add file to shared context immediately for TalkData (since it's used for analysis)
      try {
        await addUploadedFile(file);
        console.log('CSV file uploaded:', file.name);
      } catch (error) {
        console.error('Failed to upload CSV file:', error);
        alert('Failed to upload CSV file. Please try again.');
      }
    } else {
      alert('Please select a valid CSV file.');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
      setUploadedFile(file);
      setIsUploadDialogOpen(false);
      // Add file to shared context immediately for TalkData (since it's used for analysis)
      try {
        await addUploadedFile(file);
        console.log('CSV file uploaded via drag & drop:', file.name);
      } catch (error) {
        console.error('Failed to upload CSV file:', error);
        alert('Failed to upload CSV file. Please try again.');
      }
    } else {
      alert('Please drop a valid CSV file.');
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const clearUploadedFile = () => {
    setUploadedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };


  const closeUploadDialog = () => {
    setIsUploadDialogOpen(false);
    setDragOver(false);
  };

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      <div className="mb-6 px-4">
        {/* Connection and CSV File Selection */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* CSV File Selection */}
          <div className="w-full">
            <div className="flex items-center gap-3 mb-2">
              <FileSpreadsheet className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">CSV File:</span>
            </div>
            <select 
              value={selectedCsvFileId} 
              onChange={(e) => setSelectedCsvFileId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
            >
              <option value="">Select CSV file</option>
              {uploadedFiles && uploadedFiles.length > 0 ? (
                uploadedFiles
                  .filter(file => file.status === 'completed' && file.name.endsWith('.csv'))
                  .map((file) => {
                    const fileSizeKB = (file.size / 1024).toFixed(1);
                    return (
                      <option key={file.id} value={file.id}>
                        {file.name} ({fileSizeKB} KB)
                      </option>
                    );
                  })
              ) : (
                <option disabled>No CSV files uploaded</option>
              )}
            </select>
          </div>

          {/* Database Selection */}
          <div className="w-full">
            <div className="flex items-center gap-3 mb-2">
              <Database className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Database:</span>
            </div>
            <select 
              value={selectedConnectionId} 
              onChange={(e) => setSelectedConnectionId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
            >
              <option value="">Select database</option>
              {connectionsLoading ? (
                <option disabled>Loading connections...</option>
              ) : connectionsError ? (
                <option disabled>Error loading connections</option>
              ) : connections && connections.length > 0 ? (
                connections.map((connection) => (
                  <option key={connection.id} value={connection.id}>
                    {connection.name} ({connection.db_type})
                  </option>
                ))
              ) : (
                <option disabled>No connections available</option>
              )}
            </select>
          </div>
        </div>
        
        {/* Agent Status Indicator */}
        {selectedConnectionId && agentStatus[selectedConnectionId] !== undefined && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-muted mt-3">
            <div className={`w-2 h-2 rounded-full ${
              agentStatus[selectedConnectionId] ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-xs text-muted-foreground">
              {agentStatus[selectedConnectionId] ? 'Agent Online' : 'Agent Offline'}
            </span>
          </div>
        )}
      </div>


      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto scrollbar-hide space-y-4 pb-4 w-full max-w-full overflow-hidden">
        {messages.length === 0 && !selectedCsvFileId && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center space-y-3">
              <div className="w-16 h-16 bg-primary-light rounded-full flex items-center justify-center mx-auto">
                <Bot className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-muted-foreground">
                Select a data source
              </h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Please select either a database connection or an uploaded CSV file above to start asking questions about your data.
              </p>
            </div>
          </div>
        )}

        {/* CSV Data Preview - Inside Messages Container */}
        {selectedCsvFileId && (
          <div className="w-full overflow-hidden">
            
            {isLoadingCsv ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  {csvLoadProgress.message}
                </div>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${csvLoadProgress.progress}%` }}
                  ></div>
                </div>
                
                <div className="text-xs text-muted-foreground">
                  {csvLoadProgress.progress}% complete
                </div>
                
                {/* Stage indicator */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className={`px-2 py-1 rounded ${csvLoadProgress.stage === 'fetching_url' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100'}`}>
                    Getting URL
                  </span>
                  <span className={`px-2 py-1 rounded ${csvLoadProgress.stage === 'downloading' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100'}`}>
                    Downloading
                  </span>
                  <span className={`px-2 py-1 rounded ${csvLoadProgress.stage === 'parsing' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100'}`}>
                    Processing
                  </span>
                  <span className={`px-2 py-1 rounded ${csvLoadProgress.stage === 'rendering' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100'}`}>
                    Rendering
                  </span>
                </div>
              </div>
            ) : csvData ? (
              <SimpleDataTable csvData={csvData} maxPreviewRows={MAX_PREVIEW_ROWS} />
            ) : csvLoadProgress.stage === 'error' ? (
              <div className="space-y-3">
                <div className="text-red-600 font-medium">
                  ❌ {csvLoadProgress.message}
                </div>
                {csvLoadProgress.error && (
                  <div className="text-sm text-red-600 bg-red-50 p-3 rounded border">
                    {csvLoadProgress.error}
                  </div>
                )}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadCsvData(selectedCsvFileId)}
                    className="text-xs"
                  >
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Retry Loading
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedCsvFileId("")}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-muted-foreground">
                No data available. Please try selecting the file again.
              </div>
            )}
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type === 'assistant' && (
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-4 h-4 text-primary-foreground" />
              </div>
            )}
            
            <div className={`max-w-2xl ${message.type === 'user' ? 'order-2' : ''}`}>
              <div className="flex-1">
                <RichTextDisplay 
                  content={message.content}
                  variant={message.error ? 'error' : message.type === 'user' ? 'info' : 'default'}
                />
                
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
              </div>
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
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          className="hidden"
        />
        
        <SimpleChatEditor
          onSubmit={handleSubmit}
          disabled={isLoading || (!selectedConnectionId && !selectedCsvFileId)}
          placeholder={(!selectedConnectionId && !selectedCsvFileId) ? "Select a database connection or CSV file first..." : "Ask a question about your data..."}
        />
      </div>

      {/* CSV Upload Dialog */}
      <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Upload CSV File
            </DialogTitle>
            <DialogDescription>
              Select a CSV file to upload and analyze with your database connection.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Drag and Drop Area */}
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragOver 
                  ? 'border-primary bg-primary/5' 
                  : 'border-muted-foreground/25 hover:border-primary/50'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center">
                  <FileText className="w-6 h-6 text-muted-foreground" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">
                    Drag and drop your CSV file here
                  </p>
                  <p className="text-xs text-muted-foreground">
                    or click the button below to browse
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={triggerFileUpload}
                  className="mt-2"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Choose File
                </Button>
              </div>
            </div>

            {/* File Info */}
            {uploadedFile && (
              <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <FileText className="w-5 h-5 text-green-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-800">
                    {uploadedFile.name}
                  </p>
                  <p className="text-xs text-green-600">
                    {(uploadedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearUploadedFile}
                  className="text-green-600 hover:text-green-700"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeUploadDialog}>
              Cancel
            </Button>
            <Button 
              onClick={() => {
                if (uploadedFile) {
                  setIsUploadDialogOpen(false);
                } else {
                  triggerFileUpload();
                }
              }}
              disabled={!uploadedFile}
            >
              Upload File
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}