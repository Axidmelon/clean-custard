import React, { useState, useEffect } from 'react';
import { getStoredToken, getStoredTokenData, storeToken, clearStoredToken, isTokenExpired } from '@/lib/tokenUtils';
import { logError, logDebug } from '@/lib/logger';
import { User, AuthContextType, AuthProviderProps } from './auth-constants';
import { AuthContext } from './auth-context';

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth data on app load
    const initializeAuth = async () => {
      try {
        const storedToken = getStoredToken();
        let storedUser = null;
        
        // Safely get user data from localStorage
        try {
          const userData = localStorage.getItem('user');
          if (userData) {
            storedUser = JSON.parse(userData);
          }
        } catch (storageError) {
          logError('Failed to read user data from localStorage', storageError);
          // Continue without user data - token validation will handle auth
        }
        
        if (storedToken && storedUser) {
          // Verify token is still valid
          if (!isTokenExpired(storedToken)) {
            setToken(storedToken);
            setUser(storedUser);
            logDebug('User authenticated from stored token');
          } else {
            logDebug('Stored token expired, clearing auth data');
            clearStoredToken();
            try {
              localStorage.removeItem('user');
            } catch (storageError) {
              logError('Failed to clear user data from localStorage', storageError);
            }
          }
        } else if (storedToken && !storedUser) {
          // Token exists but no user data - this shouldn't happen normally
          logDebug('Token found but no user data, clearing token');
          clearStoredToken();
        }
      } catch (error) {
        logError('Failed to initialize auth', error);
        clearStoredToken();
        try {
          localStorage.removeItem('user');
        } catch (storageError) {
          logError('Failed to clear user data from localStorage', storageError);
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    initializeAuth();
  }, []);

  const login = (userData: User, authToken: string) => {
    try {
      setUser(userData);
      setToken(authToken);
      storeToken(authToken);
      
      // Safely store user data
      try {
        localStorage.setItem('user', JSON.stringify(userData));
      } catch (storageError) {
        logError('Failed to store user data in localStorage', storageError);
        // Don't throw - token storage succeeded, user can still be logged in
      }
      
      logDebug('User logged in successfully', { userId: userData.id });
    } catch (error) {
      logError('Failed to store token during login', error);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    clearStoredToken();
    
    // Safely clear user data
    try {
      localStorage.removeItem('user');
    } catch (storageError) {
      logError('Failed to clear user data from localStorage', storageError);
    }
    
    logDebug('User logged out');
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      
      // Safely update user data in localStorage
      try {
        localStorage.setItem('user', JSON.stringify(updatedUser));
      } catch (storageError) {
        logError('Failed to update user data in localStorage', storageError);
        // Don't throw - state update succeeded
      }
      
      logDebug('User data updated', { userId: user.id });
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const currentToken = getStoredToken();
      if (!currentToken) {
        logDebug('No token to refresh');
        return false;
      }

      // For now, we'll just validate the current token
      // In a real implementation, you'd call a refresh endpoint
      if (isTokenExpired(currentToken)) {
        logDebug('Token is expired, user needs to re-login');
        logout();
        return false;
      }

      logDebug('Token is still valid');
      return true;
    } catch (error) {
      logError('Failed to refresh token', error);
      return false;
    }
  };

  const isAuthenticated = !!user && !!token;

  const value = {
    user,
    token,
    login,
    logout,
    updateUser,
    isAuthenticated,
    isLoading,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
