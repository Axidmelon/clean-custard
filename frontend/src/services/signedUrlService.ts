import { getApiBaseUrl } from '@/lib/constants';

export interface SignedUrlResponse {
  success: boolean;
  signed_url: string;
  expires_at: number;
  expires_in_hours: number;
  cached?: boolean; // Indicates if the response came from cache
  file_info: {
    filename: string;
    size: number;
    content_type: string;
    created_at: string;
  };
}


class SignedUrlService {
  private pendingRequests = new Map<string, Promise<SignedUrlResponse>>(); // Request deduplication only

  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
    };
  }


  async getSignedUrl(fileId: string, expirationHours: number = 4): Promise<SignedUrlResponse> {
    // Check if there's already a pending request for this file (deduplication only)
    const cacheKey = `${fileId}:${expirationHours}`;
    if (this.pendingRequests.has(cacheKey)) {
      console.log('⏳ Waiting for existing request for file:', fileId);
      return await this.pendingRequests.get(cacheKey)!;
    }

    // Create new request and store it to prevent duplicates
    const requestPromise = this.fetchSignedUrl(fileId, expirationHours);
    this.pendingRequests.set(cacheKey, requestPromise);

    try {
      const data = await requestPromise;
      console.log('🚀 Generated new signed URL for file:', fileId, 'expires at:', new Date(data.expires_at * 1000));
      return data;
    } finally {
      // Clean up pending request
      this.pendingRequests.delete(cacheKey);
    }
  }

  private async fetchSignedUrl(fileId: string, expirationHours: number): Promise<SignedUrlResponse> {
    console.log('🌐 Fetching new signed URL for file:', fileId, `(${expirationHours}h expiration)`);
    
    const response = await fetch(`${getApiBaseUrl()}/files/signed-url/${fileId}?expiration_hours=${expirationHours}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to get signed URL' }));
      throw new Error(errorData.detail || 'Failed to get signed URL');
    }

    const data: SignedUrlResponse = await response.json();
    
    if (data.cached) {
      console.log('✅ Received cached signed URL from backend for file:', fileId);
    } else {
      console.log('🆕 Generated new signed URL from backend for file:', fileId);
    }
    
    return data;
  }

  async fetchFileContentFromSignedUrl(signedUrl: string): Promise<string> {
    console.log('Fetching file content from signed URL');
    const response = await fetch(signedUrl, {
      method: 'GET',
      // No Authorization header needed for signed URLs
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch file content: ${response.status} ${response.statusText}`);
    }

    return response.text();
  }

  // No caching methods needed - signed URLs are generated on-demand
}

export const signedUrlService = new SignedUrlService();
