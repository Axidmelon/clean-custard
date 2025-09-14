import { UploadedFile } from '@/contexts/FileUploadContext';
import { getApiBaseUrl } from '@/lib/constants';

export interface FileUploadResponse {
  success: boolean;
  message: string;
  file_info: {
    id: string; // Changed from file_id to id to match backend response
    original_filename: string;
    file_size: number;
    file_path: string;
    file_url: string;
    content_type: string;
    created_at: string; // Changed from upload_date to created_at to match backend response
    user_id: string;
  };
}

export interface MultipleFileUploadResponse {
  success: boolean;
  message: string;
  uploaded_files: FileUploadResponse['file_info'][];
  failed_files: {
    filename: string;
    error: string;
  }[];
}

export interface FileDeleteResponse {
  success: boolean;
  message: string;
}

export interface FileInfoResponse {
  success: boolean;
  file_info: {
    file_path: string;
    file_size: number;
    content_type: string;
    created: string;
    updated: string;
    public_url: string;
  };
}

export interface UploadServiceStatus {
  available: boolean;
  bucket_name: string;
  project_id: string;
}

class FileUploadService {
  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
    };
  }

  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${getApiBaseUrl()}/files/upload`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(errorData.detail || 'Upload failed');
    }

    return response.json();
  }

  async uploadMultipleFiles(files: File[]): Promise<MultipleFileUploadResponse> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await fetch(`${getApiBaseUrl()}/files/upload-multiple`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(errorData.detail || 'Upload failed');
    }

    return response.json();
  }

  async deleteFile(fileId: string): Promise<FileDeleteResponse> {
    const response = await fetch(`${getApiBaseUrl()}/files/delete/${encodeURIComponent(fileId)}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Delete failed' }));
      throw new Error(errorData.detail || 'Delete failed');
    }

    return response.json();
  }

  async getFileInfo(filePath: string): Promise<FileInfoResponse> {
    const response = await fetch(`${getApiBaseUrl()}/files/info/${encodeURIComponent(filePath)}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to get file info' }));
      throw new Error(errorData.detail || 'Failed to get file info');
    }

    return response.json();
  }

  async getUploadedFiles(): Promise<{ success: boolean; files: Record<string, unknown>[]; count: number }> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/files/list`, {
        method: 'GET',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to get uploaded files';
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          // If JSON parsing fails, use status text or default message
          errorMessage = response.statusText || errorMessage;
        }
        
        // Provide more specific error messages based on status code
        if (response.status === 401) {
          errorMessage = 'Authentication required. Please log in again.';
        } else if (response.status === 503) {
          errorMessage = 'Service temporarily unavailable. Please try again in a moment.';
        } else if (response.status === 500) {
          errorMessage = 'Server error occurred. Please try again or contact support.';
        }
        
        throw new Error(errorMessage);
      }

      const data = await response.json();
      
      // Validate response structure
      if (!data || typeof data.success !== 'boolean') {
        throw new Error('Invalid response format from server');
      }
      
      return data;
    } catch (error) {
      // Re-throw with more context if it's not already an Error object
      if (error instanceof Error) {
        throw error;
      } else {
        throw new Error(`Network error: ${String(error)}`);
      }
    }
  }

  async getUploadServiceStatus(): Promise<UploadServiceStatus> {
    const response = await fetch(`${getApiBaseUrl()}/files/status`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Failed to get upload service status');
    }

    return response.json();
  }

  async getFilesHealthStatus(): Promise<{ service: string; status: string; timestamp: string; checks: Record<string, unknown> }> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/files/health`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`Health check failed with status ${response.status}`);
      }

      return response.json();
    } catch (error) {
      throw new Error(`Failed to check files service health: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // Helper method to convert backend file info to frontend UploadedFile format
  convertToUploadedFile(fileInfo: FileUploadResponse['file_info']): UploadedFile {
    return {
      id: fileInfo.id, // Use 'id' instead of 'file_id'
      name: fileInfo.original_filename,
      size: fileInfo.file_size,
      uploadDate: new Date(fileInfo.created_at).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      }) + ' | ' + new Date(fileInfo.created_at).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }),
      status: 'completed',
      file: undefined, // File object not available after upload
    };
  }

  // Helper method to convert backend file list data to frontend UploadedFile format
  convertFileListToUploadedFiles(files: Record<string, unknown>[]): UploadedFile[] {
    return files.map(file => ({
      id: file.id,
      name: file.original_filename,
      size: file.file_size,
      uploadDate: new Date(file.created_at).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      }) + ' | ' + new Date(file.created_at).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }),
      status: 'completed' as const,
      file: undefined,
      filePath: file.file_path
    }));
  }
}

export const fileUploadService = new FileUploadService();
