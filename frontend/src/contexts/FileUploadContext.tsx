import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { fileUploadService } from '@/services/fileUploadService';

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  uploadDate: string;
  status: 'progress' | 'completed' | 'failed';
  progress?: number;
  file?: File; // Store the actual file for TalkData usage
  filePath?: string; // Store the GCS file path for deletion
}

interface FileUploadContextType {
  uploadedFiles: UploadedFile[];
  isLoading: boolean;
  addUploadedFile: (file: File) => void;
  updateFileStatus: (fileId: string, status: 'progress' | 'completed' | 'failed', progress?: number) => void;
  removeUploadedFile: (fileId: string) => void;
  clearAllFiles: () => void;
  refreshUploadedFiles: () => Promise<void>;
}

const FileUploadContext = createContext<FileUploadContextType | undefined>(undefined);

export const useFileUpload = () => {
  const context = useContext(FileUploadContext);
  if (context === undefined) {
    throw new Error('useFileUpload must be used within a FileUploadProvider');
  }
  return context;
};

interface FileUploadProviderProps {
  children: ReactNode;
}

export const FileUploadProvider: React.FC<FileUploadProviderProps> = ({ children }) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load uploaded files from backend on component mount
  useEffect(() => {
    const loadUploadedFiles = async () => {
      try {
        console.log('🔄 Loading uploaded files from backend...');
        const response = await fileUploadService.getUploadedFiles();
        if (response.success) {
          const files = fileUploadService.convertFileListToUploadedFiles(response.files);
          setUploadedFiles(files);
          console.log(`✅ Loaded ${files.length} uploaded files`);
        } else {
          console.warn('⚠️ Failed to load uploaded files: response not successful');
        }
      } catch (error) {
        console.error('❌ Failed to load uploaded files:', error);
        
        // Check if it's an authentication error
        if (error instanceof Error && (
          error.message.includes('Authentication required') || 
          error.message.includes('401') ||
          error.message.includes('Unauthorized')
        )) {
          console.log('🔐 Authentication required - user may need to log in again');
          // Don't show error to user for auth issues, they'll be redirected to login
          // Clear any stale auth data
          try {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
          } catch (storageError) {
            console.warn('Failed to clear auth data:', storageError);
          }
        } else {
          console.warn('⚠️ Non-auth error loading files, continuing without file list');
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUploadedFiles();
  }, []);

  const addUploadedFile = async (file: File) => {
    const tempFile: UploadedFile = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      uploadDate: new Date().toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      }) + ' | ' + new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }),
      status: 'progress',
      progress: 0,
      file: file
    };

    setUploadedFiles(prev => [tempFile, ...prev]);

    try {
      // Upload file to backend/GCS
      const response = await fileUploadService.uploadFile(file);
      
      // Update file with backend response
      const uploadedFile: UploadedFile = {
        id: response.file_info.id, // Use 'id' instead of 'file_id' to match backend response
        name: response.file_info.original_filename,
        size: response.file_info.file_size,
        uploadDate: new Date(response.file_info.created_at).toLocaleDateString('en-GB', {
          day: '2-digit',
          month: 'long',
          year: 'numeric'
        }) + ' | ' + new Date(response.file_info.created_at).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: true
        }),
        status: 'completed',
        progress: 100,
        file: file,
        filePath: response.file_info.file_path
      };

      // Replace temp file with uploaded file
      setUploadedFiles(prev => prev.map(f => 
        f.id === tempFile.id ? uploadedFile : f
      ));

      console.log('✅ File upload completed successfully:', {
        tempId: tempFile.id,
        realId: uploadedFile.id,
        filename: uploadedFile.name
      });

      return uploadedFile.id;
    } catch (error) {
      // Update file status to failed
      setUploadedFiles(prev => prev.map(f => 
        f.id === tempFile.id ? { ...f, status: 'failed' as const } : f
      ));
      
      console.error('❌ File upload failed:', error);
      throw error;
    }
  };

  const updateFileStatus = (fileId: string, status: 'progress' | 'completed' | 'failed', progress?: number) => {
    setUploadedFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, status, progress } : f
    ));
  };

  const removeUploadedFile = async (fileId: string) => {
    try {
      // Delete from backend using file ID
      await fileUploadService.deleteFile(fileId);
      
      // Remove from local state
      setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    } catch (error) {
      console.error('Failed to delete file:', error);
      // Still remove from local state even if backend deletion fails
      setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    }
  };

  const clearAllFiles = () => {
    setUploadedFiles([]);
  };

  const refreshUploadedFiles = async () => {
    try {
      console.log('🔄 Refreshing uploaded files...');
      const response = await fileUploadService.getUploadedFiles();
      if (response.success) {
        const files = fileUploadService.convertFileListToUploadedFiles(response.files);
        setUploadedFiles(files);
        console.log(`✅ Refreshed ${files.length} uploaded files`);
      } else {
        console.warn('⚠️ Failed to refresh uploaded files: response not successful');
      }
    } catch (error) {
      console.error('❌ Failed to refresh uploaded files:', error);
      throw error;
    }
  };

  const value: FileUploadContextType = {
    uploadedFiles,
    isLoading,
    addUploadedFile,
    updateFileStatus,
    removeUploadedFile,
    clearAllFiles,
    refreshUploadedFiles
  };

  return (
    <FileUploadContext.Provider value={value}>
      {children}
    </FileUploadContext.Provider>
  );
};
