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
        const storedUser = localStorage.getItem('user');
        
        if (storedToken && storedUser) {
          const parsedUser = JSON.parse(storedUser);
          
          // Verify token is still valid
          if (!isTokenExpired(storedToken)) {
            setToken(storedToken);
            setUser(parsedUser);
            logDebug('User authenticated from stored token');
          } else {
            logDebug('Stored token expired, clearing auth data');
            clearStoredToken();
            localStorage.removeItem('user');
          }
        }
      } catch (error) {
        logError('Failed to initialize auth', error);
        clearStoredToken();
        localStorage.removeItem('user');
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
      localStorage.setItem('user', JSON.stringify(userData));
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
    localStorage.removeItem('user');
    logDebug('User logged out');
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
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
