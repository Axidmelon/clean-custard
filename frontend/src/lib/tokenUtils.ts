// Secure token utilities for authentication
import { logError, logDebug } from './logger';

export interface TokenData {
  token: string;
  expiresAt: number;
  userId: string;
}

export interface DecodedToken {
  sub: string; // user id
  exp: number; // expiration timestamp
  iat: number; // issued at timestamp
  email?: string;
  [key: string]: unknown;
}

// Token storage keys
const TOKEN_KEY = 'access_token';
const TOKEN_DATA_KEY = 'token_data';

// Token expiration buffer (5 minutes before actual expiration)
const TOKEN_BUFFER_MS = 5 * 60 * 1000;

/**
 * Decode JWT token without verification (client-side only)
 * Note: This is for display purposes only, actual verification happens on the server
 */
export const decodeToken = (token: string): DecodedToken | null => {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid token format');
    }
    
    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch (error) {
    logError('Failed to decode token', error);
    return null;
  }
};

/**
 * Check if token is expired or will expire soon
 */
export const isTokenExpired = (token: string): boolean => {
  const decoded = decodeToken(token);
  if (!decoded) return true;
  
  const now = Date.now() / 1000; // Convert to seconds
  const expirationTime = decoded.exp;
  
  // Consider token expired if it expires within the buffer time
  return now >= (expirationTime - TOKEN_BUFFER_MS / 1000);
};

/**
 * Get token expiration time in milliseconds
 */
export const getTokenExpirationTime = (token: string): number | null => {
  const decoded = decodeToken(token);
  if (!decoded) return null;
  
  return decoded.exp * 1000; // Convert to milliseconds
};

/**
 * Get time until token expires in milliseconds
 */
export const getTimeUntilExpiration = (token: string): number => {
  const expirationTime = getTokenExpirationTime(token);
  if (!expirationTime) return 0;
  
  const now = Date.now();
  return Math.max(0, expirationTime - now);
};

/**
 * Check if localStorage is available and accessible
 */
const isLocalStorageAvailable = (): boolean => {
  try {
    const testKey = '__localStorage_test__';
    localStorage.setItem(testKey, 'test');
    localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
};

/**
 * Store token securely with metadata
 */
export const storeToken = (token: string): void => {
  try {
    if (!isLocalStorageAvailable()) {
      logError('localStorage not available', new Error('localStorage access denied'));
      throw new Error('localStorage not available');
    }

    const decoded = decodeToken(token);
    if (!decoded) {
      throw new Error('Invalid token format');
    }
    
    const tokenData: TokenData = {
      token,
      expiresAt: decoded.exp * 1000,
      userId: decoded.sub
    };
    
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(TOKEN_DATA_KEY, JSON.stringify(tokenData));
    
    logDebug('Token stored successfully', { 
      userId: decoded.sub, 
      expiresAt: new Date(decoded.exp * 1000).toISOString() 
    });
  } catch (error) {
    logError('Failed to store token', error);
    throw error;
  }
};

/**
 * Get stored token if valid
 */
export const getStoredToken = (): string | null => {
  try {
    if (!isLocalStorageAvailable()) {
      logError('localStorage not available', new Error('localStorage access denied'));
      return null;
    }

    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return null;
    
    if (isTokenExpired(token)) {
      logDebug('Stored token is expired, removing');
      clearStoredToken();
      return null;
    }
    
    return token;
  } catch (error) {
    logError('Failed to get stored token', error);
    return null;
  }
};

/**
 * Get stored token data
 */
export const getStoredTokenData = (): TokenData | null => {
  try {
    if (!isLocalStorageAvailable()) {
      logError('localStorage not available', new Error('localStorage access denied'));
      return null;
    }

    const tokenDataStr = localStorage.getItem(TOKEN_DATA_KEY);
    if (!tokenDataStr) return null;
    
    const tokenData: TokenData = JSON.parse(tokenDataStr);
    
    // Verify token is still valid
    if (isTokenExpired(tokenData.token)) {
      clearStoredToken();
      return null;
    }
    
    return tokenData;
  } catch (error) {
    logError('Failed to get stored token data', error);
    return null;
  }
};

/**
 * Clear stored token and data
 */
export const clearStoredToken = (): void => {
  try {
    if (!isLocalStorageAvailable()) {
      logError('localStorage not available', new Error('localStorage access denied'));
      return;
    }

    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_DATA_KEY);
    logDebug('Token cleared from storage');
  } catch (error) {
    logError('Failed to clear stored token', error);
  }
};

/**
 * Check if user needs to refresh token soon
 */
export const shouldRefreshToken = (token: string): boolean => {
  const timeUntilExpiration = getTimeUntilExpiration(token);
  // Refresh if token expires within 10 minutes
  return timeUntilExpiration < 10 * 60 * 1000;
};

/**
 * Get token info for debugging
 */
export const getTokenInfo = (token: string) => {
  const decoded = decodeToken(token);
  if (!decoded) return null;
  
  return {
    userId: decoded.sub,
    email: decoded.email,
    issuedAt: new Date(decoded.iat * 1000).toISOString(),
    expiresAt: new Date(decoded.exp * 1000).toISOString(),
    isExpired: isTokenExpired(token),
    timeUntilExpiration: getTimeUntilExpiration(token),
    shouldRefresh: shouldRefreshToken(token)
  };
};
