import React, { useState, useEffect, useRef } from "react";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { FileSpreadsheet, BarChart3, ChevronDown, ChevronUp, X } from "lucide-react";

interface CsvData {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

interface CsvFileInfo {
  id: string;
  name: string;
  size?: number;
}

interface TabbedCsvPreviewProps {
  selectedFileIds: string[];
  uploadedFiles: CsvFileInfo[];
  maxPreviewRows?: number;
  onFileDataLoad: (fileId: string) => Promise<void>;
  onFileRemove?: (fileId: string) => void;
  csvData: { [fileId: string]: CsvData } | null;
  isLoadingCsv: boolean;
  loadingFiles: Set<string>;
  csvLoadProgress: {
    stage: string;
    progress: number;
    message: string;
    error?: string;
  };
}

export const TabbedCsvPreview: React.FC<TabbedCsvPreviewProps> = ({
  selectedFileIds,
  uploadedFiles,
  maxPreviewRows = 50,
  onFileDataLoad,
  onFileRemove,
  csvData,
  loadingFiles,
  csvLoadProgress,
}) => {
  const [activeTabId, setActiveTabId] = useState<string | null>(null);
  const [collapsedTabs, setCollapsedTabs] = useState<{ [fileId: string]: boolean }>({});
  const loadedFilesRef = useRef<Set<string>>(new Set());

  // Set active tab when files are selected
  useEffect(() => {
    if (selectedFileIds.length > 0 && !activeTabId) {
      setActiveTabId(selectedFileIds[0]);
    }
  }, [selectedFileIds, activeTabId]);

  // Track when files are successfully loaded
  useEffect(() => {
    if (csvData) {
      Object.keys(csvData).forEach(fileId => {
        if (csvData[fileId] && csvData[fileId].headers.length > 0) {
          loadedFilesRef.current.add(fileId);
        }
      });
    }
  }, [csvData]);

  // Note: File loading is now handled by TalkData.tsx to prevent redundant requests
  // This component only displays the loaded data

  const toggleTabCollapse = (fileId: string) => {
    setCollapsedTabs(prev => ({
      ...prev,
      [fileId]: !prev[fileId]
    }));
  };

  const handleFileRemove = (fileId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent tab selection when clicking the cross icon
    
    if (onFileRemove) {
      onFileRemove(fileId);
    }
    
    // If the removed file was active, switch to another tab
    if (activeTabId === fileId) {
      const remainingFiles = selectedFileIds.filter(id => id !== fileId);
      if (remainingFiles.length > 0) {
        setActiveTabId(remainingFiles[0]);
      } else {
        setActiveTabId(null);
      }
    }
  };

  const getFileInfo = (fileId: string) => {
    return uploadedFiles.find(file => file.id === fileId);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (selectedFileIds.length === 0) {
    return null;
  }

  return (
    <div className="w-full space-y-2">
      {/* Chrome-like Tab Bar */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-t-lg overflow-x-auto">
        {selectedFileIds.map((fileId, index) => {
          const fileInfo = getFileInfo(fileId);
          const isActive = activeTabId === fileId;
          const isLast = index === selectedFileIds.length - 1;
          
          return (
            <button
              key={fileId}
              onClick={() => setActiveTabId(fileId)}
              className={`
                flex items-center gap-2 px-4 py-2 text-sm font-medium border-r border-gray-200 dark:border-gray-700
                transition-all duration-200 min-w-0 flex-shrink-0 group
                ${isActive 
                  ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border-b-2 border-blue-500' 
                  : 'bg-gray-100 dark:bg-gray-700/50 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                }
                ${isLast ? 'border-r-0' : ''}
              `}
            >
              <FileSpreadsheet className="w-4 h-4 flex-shrink-0" />
              <span className="truncate max-w-32" title={fileInfo?.name || 'Unknown file'}>
                {fileInfo?.name || 'Unknown file'}
              </span>
              {fileInfo?.size && (
                <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                  ({formatFileSize(fileInfo.size)})
                </span>
              )}
              {onFileRemove && (
                <button
                  onClick={(e) => handleFileRemove(fileId, e)}
                  className="ml-1 p-0.5 rounded-full hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors duration-200 opacity-0 group-hover:opacity-100"
                  aria-label={`Remove ${fileInfo?.name || 'file'}`}
                  title={`Remove ${fileInfo?.name || 'file'}`}
                >
                  <X className="w-3 h-3 text-red-600 dark:text-red-400" />
                </button>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTabId && (
        <div className="bg-white dark:bg-gray-900 rounded-b-lg border border-t-0 border-gray-200 dark:border-gray-700">
          {loadingFiles.has(activeTabId) ? (
            <div className="p-6 space-y-3">
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
          ) : csvData && csvData[activeTabId] ? (
            <div className="p-2">
              {/* File Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-blue-100 dark:bg-blue-900/30 rounded">
                    <FileSpreadsheet className="w-3 h-3 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {getFileInfo(activeTabId)?.name || 'Data Preview'}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {csvData[activeTabId].totalRows} rows, {csvData[activeTabId].headers.length} columns
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => toggleTabCollapse(activeTabId)}
                  className="p-1 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded transition-colors duration-200"
                  aria-label={collapsedTabs[activeTabId] ? "Expand table" : "Collapse table"}
                >
                  {collapsedTabs[activeTabId] ? (
                    <ChevronDown className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  ) : (
                    <ChevronUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  )}
                </button>
              </div>

              {/* Collapsible Table */}
              <div 
                className={`overflow-hidden transition-all duration-300 ease-in-out ${
                  collapsedTabs[activeTabId] ? 'max-h-0 opacity-0' : 'max-h-96 opacity-100'
                }`}
              >
                <Card className="overflow-hidden border-0 shadow-lg bg-white dark:bg-gray-900">
                  <div className="relative">
                    {/* Gradient overlay for modern look */}
                    <div className="absolute inset-0 bg-gradient-to-br from-white via-blue-50/30 to-indigo-50/30 dark:from-gray-900 dark:via-blue-950/10 dark:to-indigo-950/10 pointer-events-none" />
                    
                    <div className="relative max-h-64 overflow-auto">
                      <Table className="w-full">
                        <TableHeader className="sticky top-0 z-10">
                          <TableRow className="border-b border-blue-200 dark:border-blue-800 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
                            {csvData[activeTabId].headers.map((header, index) => (
                              <TableHead 
                                key={index} 
                                className="px-3 py-2 text-left font-medium text-gray-700 dark:text-gray-300 min-w-32"
                              >
                                <div className="flex items-center gap-1">
                                  <div className="p-0.5 bg-blue-100 dark:bg-blue-900/40 rounded">
                                    <BarChart3 className="w-2.5 h-2.5 text-blue-600 dark:text-blue-400" />
                                  </div>
                                  <span className="truncate text-xs font-medium" title={header}>
                                    {header}
                                  </span>
                                </div>
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {csvData[activeTabId].rows.slice(0, maxPreviewRows).map((row, rowIndex) => (
                            <TableRow 
                              key={rowIndex} 
                              className="border-b border-gray-100 dark:border-gray-800 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-indigo-50/50 dark:hover:from-blue-950/20 dark:hover:to-indigo-950/20 transition-all duration-200"
                            >
                              {row.map((cell, cellIndex) => (
                                <TableCell 
                                  key={cellIndex} 
                                  className="px-3 py-2 text-xs min-w-32 hover:bg-white/50 dark:hover:bg-gray-800/50 transition-colors duration-200"
                                >
                                  <div className="flex items-center">
                                    {cell ? (
                                      <span 
                                        className="truncate text-gray-700 dark:text-gray-300" 
                                        title={cell}
                                      >
                                        {cell}
                                      </span>
                                    ) : (
                                      <span className="text-gray-400 dark:text-gray-500 italic text-xs bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full">
                                        empty
                                      </span>
                                    )}
                                  </div>
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          ) : csvLoadProgress.stage === 'error' ? (
            <div className="p-6 space-y-3">
              <div className="text-red-600 font-medium">
                ❌ {csvLoadProgress.message}
              </div>
              {csvLoadProgress.error && (
                <div className="text-sm text-red-600 bg-red-50 p-3 rounded border">
                  {csvLoadProgress.error}
                </div>
              )}
              <div className="flex gap-2">
                <button
                  onClick={() => onFileDataLoad(activeTabId)}
                  className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Retry Loading
                </button>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center text-muted-foreground">
              No data available for this file. Please try loading again.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
