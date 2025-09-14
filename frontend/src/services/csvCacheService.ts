import { getApiBaseUrl } from '@/lib/constants';

export interface CsvCacheResponse {
  success: boolean;
  message: string;
  cached: boolean;
  file_info: {
    filename: string;
    size: number;
    cached_at: string;
    expires_in_hours?: number;
  };
}

class CsvCacheService {
  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async cacheCsvFile(fileId: string): Promise<CsvCacheResponse> {
    console.log('Caching CSV file:', fileId);
    
    const response = await fetch(`${getApiBaseUrl()}/files/cache-csv/${fileId}`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to cache CSV file' }));
      throw new Error(errorData.detail || 'Failed to cache CSV file');
    }

    const data: CsvCacheResponse = await response.json();
    console.log('CSV file cached successfully:', data);
    return data;
  }

  async ensureCsvCached(fileId: string): Promise<boolean> {
    try {
      const result = await this.cacheCsvFile(fileId);
      return result.success && result.cached;
    } catch (error) {
      console.error('Failed to ensure CSV is cached:', error);
      return false;
    }
  }
}

export const csvCacheService = new CsvCacheService();
