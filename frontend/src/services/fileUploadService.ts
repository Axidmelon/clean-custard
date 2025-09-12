import { UploadedFile } from '@/contexts/FileUploadContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface FileUploadResponse {
  success: boolean;
  message: string;
  file_info: {
    file_id: string;
    original_filename: string;
    file_size: number;
    file_path: string;
    file_url: string;
    content_type: string;
    upload_date: string;
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

    const response = await fetch(`${API_BASE_URL}/api/v1/files/upload`, {
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

    const response = await fetch(`${API_BASE_URL}/api/v1/files/upload-multiple`, {
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
    const response = await fetch(`${API_BASE_URL}/api/v1/files/delete/${encodeURIComponent(fileId)}`, {
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
    const response = await fetch(`${API_BASE_URL}/api/v1/files/info/${encodeURIComponent(filePath)}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to get file info' }));
      throw new Error(errorData.detail || 'Failed to get file info');
    }

    return response.json();
  }

  async getUploadedFiles(): Promise<{ success: boolean; files: any[]; count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/files/list`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to get uploaded files' }));
      throw new Error(errorData.detail || 'Failed to get uploaded files');
    }

    return response.json();
  }

  async getUploadServiceStatus(): Promise<UploadServiceStatus> {
    const response = await fetch(`${API_BASE_URL}/api/v1/files/status`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Failed to get upload service status');
    }

    return response.json();
  }

  // Helper method to convert backend file info to frontend UploadedFile format
  convertToUploadedFile(fileInfo: FileUploadResponse['file_info']): UploadedFile {
    return {
      id: fileInfo.file_id,
      name: fileInfo.original_filename,
      size: fileInfo.file_size,
      uploadDate: new Date(fileInfo.upload_date).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      }) + ' | ' + new Date(fileInfo.upload_date).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }),
      status: 'completed',
      file: undefined, // File object not available after upload
    };
  }

  // Helper method to convert backend file list data to frontend UploadedFile format
  convertFileListToUploadedFiles(files: any[]): UploadedFile[] {
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
