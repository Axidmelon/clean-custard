import { getApiBaseUrl } from '@/lib/constants';

export interface SignedUrlResponse {
  success: boolean;
  signed_url: string;
  expires_at: number;
  expires_in_hours: number;
  file_info: {
    filename: string;
    size: number;
    content_type: string;
    created_at: string;
  };
}

interface CachedSignedUrl {
  url: string;
  expires_at: number;
  file_info: SignedUrlResponse['file_info'];
}

class SignedUrlService {
  private urlCache = new Map<string, CachedSignedUrl>();
  private readonly CACHE_BUFFER_MINUTES = 30; // Refresh URL 30 minutes before expiration

  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
    };
  }

  private isUrlExpired(cachedUrl: CachedSignedUrl): boolean {
    const now = Date.now() / 1000; // Convert to seconds
    const bufferTime = this.CACHE_BUFFER_MINUTES * 60; // Convert to seconds
    return cachedUrl.expires_at - now < bufferTime;
  }

  async getSignedUrl(fileId: string, expirationHours: number = 2): Promise<SignedUrlResponse> {
    // Check cache first
    const cached = this.urlCache.get(fileId);
    if (cached && !this.isUrlExpired(cached)) {
      console.log('Using cached signed URL for file:', fileId);
      return {
        success: true,
        signed_url: cached.url,
        expires_at: cached.expires_at,
        expires_in_hours: Math.ceil((cached.expires_at - Date.now() / 1000) / 3600),
        file_info: cached.file_info
      };
    }

    // Fetch new signed URL from backend
    console.log('Fetching new signed URL for file:', fileId);
    const response = await fetch(`${getApiBaseUrl()}/files/signed-url/${fileId}?expiration_hours=${expirationHours}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to get signed URL' }));
      throw new Error(errorData.detail || 'Failed to get signed URL');
    }

    const data: SignedUrlResponse = await response.json();

    // Cache the signed URL
    this.urlCache.set(fileId, {
      url: data.signed_url,
      expires_at: data.expires_at,
      file_info: data.file_info
    });

    console.log('Cached new signed URL for file:', fileId, 'expires at:', new Date(data.expires_at * 1000));
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

  clearCache(fileId?: string): void {
    if (fileId) {
      this.urlCache.delete(fileId);
      console.log('Cleared cache for file:', fileId);
    } else {
      this.urlCache.clear();
      console.log('Cleared all signed URL cache');
    }
  }

  getCacheStatus(): { total: number; expired: number; valid: number } {
    const now = Date.now() / 1000;
    let expired = 0;
    let valid = 0;

    this.urlCache.forEach(cached => {
      if (cached.expires_at < now) {
        expired++;
      } else {
        valid++;
      }
    });

    return {
      total: this.urlCache.size,
      expired,
      valid
    };
  }
}

export const signedUrlService = new SignedUrlService();
