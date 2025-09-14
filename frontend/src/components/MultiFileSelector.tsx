import React, { useState } from 'react';
import { Check, ChevronDown, FileSpreadsheet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface File {
  id: string;
  name: string;
  size: number;
  status: string;
}

interface MultiFileSelectorProps {
  files: File[];
  selectedFileIds: string[];
  onSelectionChange: (fileIds: string[]) => void;
  maxFiles?: number;
  className?: string;
}

export const MultiFileSelector: React.FC<MultiFileSelectorProps> = ({
  files,
  selectedFileIds,
  onSelectionChange,
  maxFiles = 10,
  className = ""
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter files based on search term and status
  const availableFiles = files.filter(file => 
    file.status === 'completed' && 
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedFiles = files.filter(file => selectedFileIds.includes(file.id));

  const handleFileToggle = (fileId: string) => {
    if (selectedFileIds.includes(fileId)) {
      // Remove file from selection
      onSelectionChange(selectedFileIds.filter(id => id !== fileId));
    } else {
      // Add file to selection (if under limit)
      if (selectedFileIds.length < maxFiles) {
        onSelectionChange([...selectedFileIds, fileId]);
      }
    }
  };


  const handleClearAll = () => {
    onSelectionChange([]);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`relative ${className}`}>
      {/* Clean dropdown trigger - similar to database dropdown */}
      <Card 
        className="cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between p-3">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">
              {selectedFiles.length === 0 
                ? 'Select CSV File(s)' 
                : `${selectedFiles.length} file${selectedFiles.length === 1 ? '' : 's'} selected`
              }
            </span>
          </div>
          <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </Card>

      {/* Dropdown Menu */}
      {isOpen && (
        <Card className="absolute top-full left-0 right-0 z-50 mt-1 max-h-64 overflow-hidden">
          <div className="p-2">
            {/* Search Input */}
            <div className="relative mb-2">
              <input
                type="text"
                placeholder="Search CSV files..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            {/* File List */}
            <div className="max-h-48 overflow-y-auto">
              {availableFiles.length === 0 ? (
                <div className="text-center py-4 text-sm text-muted-foreground">
                  {searchTerm ? 'No files match your search' : 'No CSV files available'}
                </div>
              ) : (
                <div className="space-y-1">
                  {availableFiles.map(file => {
                    const isSelected = selectedFileIds.includes(file.id);
                    const isDisabled = !isSelected && selectedFileIds.length >= maxFiles;
                    
                    return (
                      <div
                        key={file.id}
                        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                          isSelected 
                            ? 'bg-primary text-primary-foreground' 
                            : isDisabled
                            ? 'bg-muted text-muted-foreground cursor-not-allowed'
                            : 'hover:bg-muted'
                        }`}
                        onClick={() => !isDisabled && handleFileToggle(file.id)}
                      >
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <FileSpreadsheet className="w-4 h-4 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{file.name}</div>
                            <div className="text-xs opacity-75">{formatFileSize(file.size)}</div>
                          </div>
                        </div>
                        {isSelected && (
                          <Check className="w-4 h-4 flex-shrink-0" />
                        )}
                        {isDisabled && !isSelected && (
                          <span className="text-xs text-muted-foreground">Max reached</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-2 mt-2 border-t">
              <span className="text-xs text-muted-foreground">
                {selectedFileIds.length}/{maxFiles} files selected
              </span>
              <div className="flex gap-2">
                {selectedFileIds.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearAll}
                    className="h-6 px-2 text-xs text-muted-foreground hover:text-destructive"
                  >
                    Clear All
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsOpen(false)}
                  className="h-6 px-2 text-xs"
                >
                  Done
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Click outside to close */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default MultiFileSelector;
